import json
import os
from datetime import datetime
from typing import Any

import lark_oapi as lark
from dotenv import load_dotenv
from lark_oapi.api.bitable.v1 import (
    AppTableRecord,
    CreateAppTableRecordRequest,
    CreateAppTableRecordResponse,
)

from feishu_client import get_access_token

load_dotenv()

# Field names must stay in sync with the target Bitable table. If the visible
# field names change in Feishu, update this mapping before writing records.
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
    "need_confirm": "需要确认的字段列表"
}


def decode_raw_content(raw_content: bytes | str | None) -> Any:
    """Decode raw SDK response content for readable error output.

    Args:
        raw_content: The raw response content returned by the Feishu SDK.

    Returns:
        Parsed JSON when possible, otherwise decoded text or None.
    """
    if raw_content is None:
        return None

    text = raw_content.decode("utf-8") if isinstance(raw_content, bytes) else raw_content
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def build_owner_value(todo: dict[str, Any]) -> list[dict[str, str]] | None:
    """Build the payload for a Bitable person field.

    Args:
        todo: Todo dictionary that may contain ``owner_open_ids`` or
            ``owner_open_id``.

    Returns:
        A Feishu person-field value, or None when the todo has no owner.
    """
    owner_open_ids = todo.get("owner_open_ids")
    if owner_open_ids:
        return [{"id": open_id} for open_id in owner_open_ids if open_id]

    owner_open_id = todo.get("owner_open_id")
    if owner_open_id:
        return [{"id": owner_open_id}]

    return None


def build_fields(todo: dict[str, Any]) -> dict[str, Any]:
    """Convert a todo dictionary into SDK-compatible Bitable fields.

    Args:
        todo: Todo dictionary. ``title`` is required for this smoke test.

    Returns:
        A dictionary keyed by visible Bitable field names.

    Raises:
        KeyError: If ``title`` is missing.
        ValueError: If ``deadline`` exists but is not in ``YYYY-MM-DD`` format.
    """
    fields: dict[str, Any] = {
        FIELD_NAMES["title"]: todo["title"],
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

    if todo.get("deadline"):
        dt = datetime.strptime(todo["deadline"], "%Y-%m-%d")
        # Feishu Bitable date fields expect Unix timestamp in milliseconds.
        fields[FIELD_NAMES["deadline"]] = int(dt.timestamp() * 1000)

    return {k: v for k, v in fields.items() if v not in (None, "")}


def build_request_option() -> lark.RequestOption:
    """Build an SDK request option with the current tenant access token.

    Returns:
        A Feishu SDK ``RequestOption`` configured with tenant authentication.
    """
    tenant_access_token = get_access_token()
    return lark.RequestOption.builder().tenant_access_token(tenant_access_token).build()


def write_todo(app_token: str, table_id: str, todo: dict[str, Any]) -> str | None:
    """Create one Bitable record through the Feishu SDK.

    Args:
        app_token: Feishu Bitable app token.
        table_id: Target table ID.
        todo: Todo dictionary to write.

    Returns:
        The created record ID on success, otherwise None.
    """
    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()

    request: CreateAppTableRecordRequest = (
        CreateAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .request_body(AppTableRecord.builder().fields(build_fields(todo)).build())
        .build()
    )

    option = build_request_option()
    response: CreateAppTableRecordResponse = client.bitable.v1.app_table_record.create(request, option)

    if not response.success():
        raw = decode_raw_content(response.raw.content if response.raw else None)
        print("写入失败：")
        print(f"code={response.code}, msg={response.msg}, log_id={response.get_log_id()}")
        print(json.dumps(raw, indent=2, ensure_ascii=False) if isinstance(raw, dict) else raw)
        return None

    record_id = response.data.record.record_id
    print(f"✅ 写入成功！record_id: {record_id}")
    return record_id


if __name__ == "__main__":
    app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
    table_id = os.getenv("FEISHU_TABLE_ID")

    if not app_token or not table_id:
        raise ValueError("缺少 FEISHU_BITABLE_APP_TOKEN 或 FEISHU_TABLE_ID 配置")

    test_todo = {
        "title": "优化移动端首页加载速度",
        "description": "针对弱网环境下的首屏渲染进行专项优化，目标是将加载时间缩短30%",
        "owner_open_id": "ou_e128bfd18f90e64471a0b5d2bfb56ff8",
        "deadline": "2026-05-05",
        "status": "待处理",
        "priority": "P1",
        "source_type": "产品需求",
        "source_link": "https://open.feishu.cn/document/home/index",
        "source_link_text": "飞书开放平台文档",
        "evidence": "性能分析工具截图",
    }

    write_todo(app_token, table_id, test_todo)
