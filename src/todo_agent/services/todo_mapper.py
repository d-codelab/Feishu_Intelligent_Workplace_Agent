"""Todo-to-Bitable field mapping and validation rules."""

import json
from datetime import datetime
from typing import Any

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


def build_owner_value(todo: dict[str, Any]) -> list[dict[str, str]] | None:
    """Build the Bitable person-field value from owner open IDs."""
    owner_open_ids = todo.get("owner_open_ids")
    if owner_open_ids:
        return [{"id": open_id} for open_id in owner_open_ids if open_id]

    owner_open_id = todo.get("owner_open_id")
    if owner_open_id:
        return [{"id": owner_open_id}]

    return None


def normalize_need_confirm(value: Any) -> list[str]:
    """Normalize upstream ``need_confirm`` into a list of field names."""
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
    """Append a field name to need-confirm list while preserving uniqueness."""
    if field_name not in need_confirm:
        need_confirm.append(field_name)


def build_need_confirm(todo: dict[str, Any]) -> list[str]:
    """Merge upstream need-confirm values with local validation results."""
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
    """Format need-confirm field as a JSON-array string for Bitable text cells."""
    return json.dumps(need_confirm, ensure_ascii=False)


def todo_to_fields(todo: dict[str, Any]) -> dict[str, Any]:
    """Convert one normalized todo dict into Feishu Bitable field payload."""
    fields: dict[str, Any] = {
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
