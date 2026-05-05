"""Feishu API helpers for reading documents and messages."""

import re
import json
import requests
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Union, List, Dict

from todo_extractor.clients.auth import get_access_token, REQUEST_TIMEOUT

BASE_URL = "https://open.feishu.cn/open-apis"


@dataclass
class Document:
    """完整文档"""
    doc_id: str
    title: str
    markdown: str = ""  # 完整 markdown 文本
    elements: dict = field(default_factory=dict)  # 结构化元素统计


# ==================== Blocks API 解析逻辑 ====================

def extract_text_from_elements(elements: list) -> str:
    """从 text_run elements 中提取纯文本"""
    if not elements:
        return ""
    texts = []
    for elem in elements:
        text_run = elem.get("text_run", {})
        content = text_run.get("content", "")
        texts.append(content)
    return "".join(texts)


def parse_text_block(block: dict) -> str:
    """解析文本段落 block"""
    text_obj = block.get("text", {})
    elements = text_obj.get("elements", [])
    return extract_text_from_elements(elements)


def parse_heading_block(block: dict) -> str:
    """解析标题 block"""
    block_type = block.get("block_type", 3)
    # 尝试所有可能的标题字段
    text_obj = block.get("heading1", block.get("heading2", block.get("heading3",
                  block.get("heading4", block.get("heading5", block.get("heading6",
                  block.get("heading7", block.get("heading8", block.get("heading9", {})))))))))
    elements = text_obj.get("elements", [])
    text = extract_text_from_elements(elements)
    level = block_type - 2  # 3→h1, 4→h2, ..., 11→h9
    return "#" * level + " " + text


def parse_code_block(block: dict) -> str:
    """解析代码块"""
    code_obj = block.get("code", {})
    elements = code_obj.get("elements", [])
    return extract_text_from_elements(elements)


def parse_image_block(block: dict) -> str:
    """解析图片 block"""
    image_obj = block.get("image", {})
    token = image_obj.get("token", "")
    width = image_obj.get("width", 0)
    height = image_obj.get("height", 0)
    return f'<image token="{token}" width="{width}" height="{height}"/>'


def parse_sheet_block(block: dict) -> str:
    """解析 sheet 引用 block"""
    sheet_obj = block.get("sheet", {})
    token = sheet_obj.get("token", "")
    return f'<sheet token="{token}"/>'


def parse_bitable_block(block: dict) -> str:
    """解析多维表格 block"""
    bitable_obj = block.get("bitable", {})
    token = bitable_obj.get("token", "")
    return f'<bitable token="{token}"/>'


def parse_file_block(block: dict) -> str:
    """解析文件 block"""
    file_obj = block.get("file", {})
    name = file_obj.get("name", "文件")
    token = file_obj.get("token", "")
    return f'[📎 {name}](file://{token})'


def parse_divider_block(block: dict) -> str:
    """解析分割线"""
    return "\n---\n"


def parse_block(block: dict, block_cache: dict, page_id: str = "") -> str:
    """递归解析单个 block"""
    block_type = block.get("block_type", 2)
    block_id = block.get("block_id", "")
    children_ids = block.get("children", [])
    children = [block_cache.get(cid, {}) for cid in children_ids]

    if block_type == 1:
        # page block：递归处理子元素
        results = [parse_block(c, block_cache, block_id) for c in children]
        return "\n".join(filter(None, results))

    elif block_type in [3, 4, 5, 6, 7, 8, 9, 10, 11]:
        # heading 1-9
        return parse_heading_block(block)

    elif block_type == 2:
        # text paragraph
        return parse_text_block(block)

    elif block_type == 12:
        # bullet list (无序列表)
        text = parse_text_block(block)
        return f"- {text}"

    elif block_type == 13:
        # ordered list (有序列表)
        ordered_obj = block.get("ordered", {})
        elements = ordered_obj.get("elements", [])
        text = extract_text_from_elements(elements)
        sequence = ordered_obj.get("style", {}).get("sequence", "1")
        return f"{sequence}. {text}"

    elif block_type == 14:
        # code block
        code_text = parse_code_block(block)
        lang = block.get("code", {}).get("style", {}).get("language", "")
        return f"```{lang}\n{code_text}\n```"

    elif block_type == 15:
        # quote
        text = parse_text_block(block)
        return "> " + text

    elif block_type == 17:
        # todo block (待办事项) - 重要！
        todo_obj = block.get("todo", {})
        elements = todo_obj.get("elements", [])
        text = extract_text_from_elements(elements)
        style = todo_obj.get("style", {})
        done = style.get("done", False)
        checkbox = "[x]" if done else "[ ]"
        return f"- {checkbox} {text}"

    elif block_type == 18:
        # bitable (多维表格)
        return parse_bitable_block(block)

    elif block_type == 19:
        # callout (高亮块) - 可能包含重要事项
        # 递归处理子元素
        results = [parse_block(c, block_cache, block_id) for c in children]
        inner = "\n".join(filter(None, results))
        return f'> 💡 {inner}'

    elif block_type == 22:
        # divider (分割线)
        return parse_divider_block(block)

    elif block_type == 23:
        # file (文件)
        return parse_file_block(block)

    elif block_type == 27:
        # image
        return parse_image_block(block)

    elif block_type == 30:
        # sheet (电子表格)
        return parse_sheet_block(block)

    elif block_type == 31:
        # table (表格) - 递归处理表格行
        results = [parse_block(c, block_cache, block_id) for c in children]
        return "\n".join(filter(None, results))

    elif block_type == 32:
        # table_cell (表格单元格)
        text = parse_text_block(block)
        return f"| {text} "

    elif block_type == 34:
        # quote_container (引用容器)
        results = [parse_block(c, block_cache, block_id) for c in children]
        quoted = "\n".join(filter(None, results))
        return "> " + quoted.replace("\n", "\n> ")

    elif block_type == 35:
        # task (任务 Block) - 重要！
        task_obj = block.get("task", {})
        task_id = task_obj.get("task_id", "")
        # 递归处理子元素获取任务描述
        results = [parse_block(c, block_cache, block_id) for c in children]
        task_text = "\n".join(filter(None, results))
        return f"- [ ] {task_text} (task_id: {task_id})"

    elif block_type in [36, 37, 38, 39]:
        # OKR 相关 - 递归处理子元素
        results = [parse_block(c, block_cache, block_id) for c in children]
        return "\n".join(filter(None, results))

    else:
        # 未知类型：尝试从 text 字段取
        if "text" in block:
            return parse_text_block(block)
        # 如果有子元素，递归处理
        if children:
            results = [parse_block(c, block_cache, block_id) for c in children]
            return "\n".join(filter(None, results))
        return ""


def fetch_blocks(token: str, doc_token: str) -> List[dict]:
    """分页获取文档所有 blocks"""
    blocks_url = f"{BASE_URL}/docx/v1/documents/{doc_token}/blocks"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"document_revision_id": -1}

    all_blocks = []
    page_token = None

    while True:
        params_local = params.copy()
        if page_token:
            params_local["page_token"] = page_token

        resp = requests.get(blocks_url, headers=headers, params=params_local, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 0:
            raise RuntimeError(f"获取 blocks 失败: {result}")

        items = result.get("data", {}).get("items", [])
        all_blocks.extend(items)

        has_more = result.get("data", {}).get("has_more", False)
        if not has_more:
            break

        page_token = result.get("data", {}).get("page_token", "")

    return all_blocks


def rebuild_markdown_from_blocks(blocks: List[dict]) -> str:
    """从 blocks 重建完整 markdown"""
    block_cache = {b["block_id"]: b for b in blocks}

    # 找到 page block
    page_block = None
    for b in blocks:
        if b.get("block_type") == 1:
            page_block = b
            break

    if not page_block:
        raise RuntimeError("未找到 page block")

    return parse_block(page_block, block_cache)


def extract_structured_elements(markdown: str) -> Dict:
    """从 markdown 中提取结构化元素"""
    elements = {
        "images": [],
        "sheets": [],
        "bitables": [],
        "files": [],
        "todos": [],
        "tasks": [],
        "code_blocks": [],
        "tables": [],
        "callouts": []
    }

    lines = markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # 图片
        img_match = re.search(r'<image token="([^"]+)"([^/]*)/?>', line)
        if img_match:
            token = img_match.group(1)
            rest = img_match.group(2)
            w_match = re.search(r'width="?(\d+)', rest)
            h_match = re.search(r'height="?(\d+)', rest)
            elements["images"].append({
                "token": token,
                "width": int(w_match.group(1)) if w_match else 0,
                "height": int(h_match.group(1)) if h_match else 0,
                "raw": line
            })

        # Sheet 引用
        sheet_match = re.search(r'<sheet token="([^"]+)"', line)
        if sheet_match:
            elements["sheets"].append({
                "token": sheet_match.group(1),
                "raw": line
            })

        # Bitable (多维表格)
        bitable_match = re.search(r'<bitable token="([^"]+)"', line)
        if bitable_match:
            elements["bitables"].append({
                "token": bitable_match.group(1),
                "raw": line
            })

        # 文件
        file_match = re.search(r'\[📎 ([^\]]+)\]\(file://([^\)]+)\)', line)
        if file_match:
            elements["files"].append({
                "name": file_match.group(1),
                "token": file_match.group(2),
                "raw": line
            })

        # 待办事项 (checkbox)
        todo_match = re.search(r'^- \[([ x])\] (.+)', line.strip())
        if todo_match:
            checked = todo_match.group(1) == 'x'
            text = todo_match.group(2)
            # 排除任务类型（带 task_id）
            if "task_id:" not in text:
                elements["todos"].append({
                    "checked": checked,
                    "text": text,
                    "raw": line
                })

        # 任务 (带 task_id)
        task_match = re.search(r'- \[ \] (.+) \(task_id: ([^\)]+)\)', line)
        if task_match:
            elements["tasks"].append({
                "text": task_match.group(1),
                "task_id": task_match.group(2),
                "raw": line
            })

        # Callout (高亮块)
        if line.strip().startswith("> 💡"):
            elements["callouts"].append({"raw": line})

        # 代码块
        if line.strip().startswith("```") and not line.strip().endswith("```"):
            lang = line.strip()[3:].strip() or "text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            elements["code_blocks"].append({
                "language": lang,
                "content": "\n".join(code_lines)
            })

        # 表格
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = []
            for tl in table_lines:
                if "---" in tl:
                    continue
                cells = [c.strip() for c in tl.strip("|").split("|")]
                rows.append(cells)
            if rows:
                elements["tables"].append({
                    "headers": rows[0] if rows else [],
                    "rows": rows[1:] if len(rows) > 1 else [],
                    "raw": "\n".join(table_lines)
                })
            i -= 1

        i += 1

    return elements


def read_feishu_doc(doc_token: str, return_structured: bool = False, use_blocks_api: bool = True) -> Union[str, Document]:
    """Read content from a Feishu document (new docx format).

    Args:
        doc_token: Feishu document token
        return_structured: If True, return Document object with structured elements
        use_blocks_api: If True, use blocks API (recommended); if False, use raw_content API

    Returns:
        Plain text content (default) or Document object (if return_structured=True)

    Raises:
        RuntimeError: If document reading fails
    """
    token = get_access_token()

    # 1. 获取文档元信息（标题）
    doc_url = f"{BASE_URL}/docx/v1/documents/{doc_token}"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(doc_url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()

    if result.get("code") != 0:
        raise RuntimeError(f"读取文档失败: {result}")

    title = result.get("data", {}).get("document", {}).get("title", "未命名文档")

    # 2. 获取文档内容
    if use_blocks_api:
        # 使用 blocks API（推荐，支持更多元素类型）
        blocks = fetch_blocks(token, doc_token)
        markdown_text = rebuild_markdown_from_blocks(blocks)
    else:
        # 使用 raw_content API（简单但功能有限）
        content_url = f"{BASE_URL}/docx/v1/documents/{doc_token}/raw_content"
        resp = requests.get(content_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 0:
            raise RuntimeError(f"读取文档内容失败: {result}")

        markdown_text = result.get("data", {}).get("content", "")

    # 如果只需要纯文本，直接返回
    if not return_structured:
        return markdown_text

    # 3. 提取结构化元素
    elements = extract_structured_elements(markdown_text)

    # 4. 构建 Document 对象
    doc = Document(
        doc_id=doc_token,
        title=title,
        markdown=markdown_text,
        elements=elements
    )

    return doc


def get_chat_history(chat_id: str, hours: int = 24) -> list[dict]:
    """Get chat history from a Feishu group chat.

    Args:
        chat_id: Feishu chat ID
        hours: Number of hours to look back

    Returns:
        List of messages with format:
            [{"content": "...", "sender": "...", "time": timestamp}]

    Raises:
        RuntimeError: If message fetching fails
    """
    import json as json_lib

    token = get_access_token()
    url = f"{BASE_URL}/im/v1/messages"

    params = {
        "container_id_type": "chat",
        "container_id": chat_id,
        "page_size": 50,
        # "sort_type": "ByCreateTimeDesc",  # Latest first
    }

    headers = {"Authorization": f"Bearer {token}"}

    messages = []
    page_token = None
    max_messages = hours * 50  # Rough estimate: 50 messages per hour

    while len(messages) < max_messages:
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 0:
            raise RuntimeError(f"获取群消息失败: {result}")

        items = result.get("data", {}).get("items", [])

        # Flag to check if we've reached messages older than cutoff
        should_stop = False
        cutoff_timestamp = (datetime.now() - timedelta(hours=hours)).timestamp()

        for item in items:
            msg_type = item.get("msg_type")
            body = item.get("body", {})
            content_raw = body.get("content", "")

            # Extract text content based on message type
            content = ""

            if msg_type == "text":
                # Text message: content is JSON string
                try:
                    content_obj = json_lib.loads(content_raw)
                    content = content_obj.get("text", "")
                except json_lib.JSONDecodeError:
                    content = content_raw

            elif msg_type == "post":
                # Rich text message: extract all text elements
                try:
                    content_obj = json_lib.loads(content_raw)
                    post_content = content_obj.get("content", [])
                    text_parts = []
                    for row in post_content:
                        for element in row:
                            if element.get("tag") == "text":
                                text_parts.append(element.get("text", ""))
                    content = "\n".join(text_parts)
                except (json_lib.JSONDecodeError, TypeError):
                    content = str(content_raw)

            elif msg_type == "system":
                # System message: skip
                continue

            # Get sender name
            sender_info = item.get("sender", {})
            sender_name = sender_info.get("id", "unknown")

            # Get create time
            create_time = item.get("create_time", "")

            # Check if message is within time range
            if create_time:
                msg_timestamp = int(create_time) / 1000
                if msg_timestamp < cutoff_timestamp:
                    # Message is too old, mark to stop after this page
                    should_stop = True
                    continue

            # Format timestamp to readable datetime
            formatted_time = ""
            if create_time:
                try:
                    msg_timestamp = int(create_time) / 1000
                    dt = datetime.fromtimestamp(msg_timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, OSError):
                    formatted_time = create_time

            # Only add messages with content
            if content.strip():
                messages.append({
                    "content": content,
                    "sender": sender_name,
                    "time": formatted_time,
                })

        # Stop if we've reached old messages
        if should_stop:
            print(f"获取到 {len(messages)} 条群消息（最近 {hours} 小时）")
            break

        # Check if there are more pages
        has_more = result.get("data", {}).get("has_more", False)
        if not has_more:
            break

        page_token = result.get("data", {}).get("page_token")
        if not page_token:
            break

    print(f"获取到 {len(messages)} 条群消息")
    return messages
