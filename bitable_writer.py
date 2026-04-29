# bitable_writer.py
import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from feishu_client import get_access_token

import json
# 打开 JSON 文件 (指定 utf-8 编码)
with open('mock_data/todo_result_feishu_doc.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

load_dotenv()

APP_TOKEN = os.getenv("FEISHU_BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("FEISHU_TABLE_ID")

FIELD_NAMES = {
    "title": "待办标题",
    "description": "描述",
    "owner": "负责人",
    "deadline": "截止日期",
    "priority": "优先级",
    "status": "状态",
    "source_type": "来源渠道",
    "source_link": "来源链接",
    "evidence": "原文证据/背景",
    "need_confirm": "待确认字段",
}

VALID_PRIORITIES = {"P0", "P1", "P2"}
VALID_STATUSES = {"待处理", "进行中", "已完成", "阻塞"}


def build_owner_value(todo: dict):
    owner_open_ids = todo.get("owner_open_ids")
    if owner_open_ids:
        return [{"id": open_id} for open_id in owner_open_ids if open_id]

    owner_open_id = todo.get("owner_open_id")
    if owner_open_id:
        return [{"id": owner_open_id}]

    return None


def normalize_need_confirm(value) -> list[str]:
    """将上游传入的 need_confirm 统一转换为字段名列表"""
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
        return [value]
    return [str(value)]


def append_need_confirm(need_confirm: list[str], field_name: str) -> None:
    """追加需要确认的字段名，并保持去重"""
    if field_name not in need_confirm:
        need_confirm.append(field_name)


def build_need_confirm(todo: dict) -> list[str]:
    """根据上游标记和本地基础校验生成需要确认的字段名列表"""
    need_confirm = normalize_need_confirm(todo.get("need_confirm"))

    if not build_owner_value(todo):
        append_need_confirm(need_confirm, FIELD_NAMES["owner"])

    deadline = todo.get("deadline")
    if not deadline:
        append_need_confirm(need_confirm, FIELD_NAMES["deadline"])
    else:
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            append_need_confirm(need_confirm, FIELD_NAMES["deadline"])

    priority = todo.get("priority")
    if priority and priority not in VALID_PRIORITIES:
        append_need_confirm(need_confirm, FIELD_NAMES["priority"])

    status = todo.get("status")
    if status and status not in VALID_STATUSES:
        append_need_confirm(need_confirm, FIELD_NAMES["status"])

    return need_confirm


def format_need_confirm_value(need_confirm: list[str]) -> str:
    """按 JSON 数组字符串写入多维表格，便于人工查看和后续程序解析"""
    return json.dumps(need_confirm, ensure_ascii=False)


def todo_to_fields(todo: dict) -> dict:
    """将 Agent 输出的 todo dict 转换为 Bitable 字段格式"""
    fields = {
        FIELD_NAMES["title"]: todo.get("title", "（无标题）"),
        FIELD_NAMES["description"]: todo.get("description", ""),
        FIELD_NAMES["status"]: todo.get("status", "待处理"),
        FIELD_NAMES["priority"]: todo.get("priority", "P2"),
        FIELD_NAMES["source_type"]: todo.get("source_type", ""),
        FIELD_NAMES["evidence"]: todo.get("evidence", ""),
    }

    source_link = todo.get("source_link")
    if source_link:
        source_link_text = todo.get("source_link_text", "查看来源")
        fields[FIELD_NAMES["source_link"]] = {"text": source_link_text, "link": source_link}

    owner_value = build_owner_value(todo)
    if owner_value:
        fields[FIELD_NAMES["owner"]] = owner_value

    deadline = todo.get("deadline")
    if deadline:
        try:
            dt = datetime.strptime(deadline, "%Y-%m-%d")
            fields[FIELD_NAMES["deadline"]] = int(dt.timestamp() * 1000)
        except ValueError:
            pass

    need_confirm = build_need_confirm(todo)
    if need_confirm:
        fields[FIELD_NAMES["need_confirm"]] = format_need_confirm_value(need_confirm)

    return {k: v for k, v in fields.items() if v not in (None, "", [])}


def batch_write(todos: list[dict]) -> dict:
    """批量写入，返回写入统计"""
    if not APP_TOKEN or not TABLE_ID:
        raise ValueError("缺少 FEISHU_BITABLE_APP_TOKEN 或 FEISHU_TABLE_ID 配置")

    token = get_access_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_create"

    records = [{"fields": todo_to_fields(todo)} for todo in todos]
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"records": records},
    )
    result = resp.json()

    if result.get("code") == 0:
        created = result.get("data", {}).get("records", [])
        print(f"✅ 批量写入成功：{len(created)} 条")
        return {"success": len(created), "failed": 0, "record_ids": [r["record_id"] for r in created]}

    print(f"❌ 批量写入失败: {json.dumps(result, ensure_ascii=False)}")
    return {"success": 0, "failed": len(todos), "error": result}


if __name__ == "__main__":
    mock_todos = data['items']
    batch_write(mock_todos)
