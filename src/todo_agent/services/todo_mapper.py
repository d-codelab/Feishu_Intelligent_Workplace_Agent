"""Todo-to-Bitable field mapping and validation rules."""

import json
import hashlib
from datetime import datetime
from typing import Any

FIELD_NAMES = {
    "title": "事项标题",
    "description": "事项描述",
    "owner": "负责人",
    "created_time": "开始时间",
    "deadline": "截止时间",
    "priority": "优先级",
    "status": "当前状态",
    "source_type": "来源类型",
    "source_link": "来源链接",
    "evidence": "原文依据",
    "need_confirm": "待确认项",
    "risk_or_blocker": "风险/阻塞",
    "system_id": "系统ID",
}

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_STATUSES = {"待开始", "进行中", "已完成", "有阻塞", "已延期", "待确认"}


def build_owner_value(todo: dict[str, Any]) -> list[dict[str, str]] | None:
    """Build the Bitable person-field value from owner open IDs."""
    raw_ids = []

    # 提取可能存在的 owner_open_ids
    if "owner_open_ids" in todo:
        val = todo["owner_open_ids"]
        if isinstance(val, list):
            raw_ids.extend(val)
        elif isinstance(val, str):
            raw_ids.extend(val.split(","))

    # 提取单数的 owner_open_id
    if "owner_open_id" in todo:
        val = todo["owner_open_id"]
        if isinstance(val, list):
            raw_ids.extend(val)
        elif isinstance(val, str):
            raw_ids.extend(val.split(","))

    valid_ids = []
    for oid in raw_ids:
        if isinstance(oid, str):
            oid = oid.strip()
            # 严格校验：必须是非空，且格式符合飞书的 open_id (ou_ 开头) 提取不出时可能为"未提及"等普通字符串
            if oid and oid.startswith("ou_"):
                if oid not in valid_ids:
                    valid_ids.append(oid)

    if valid_ids:
        return [{"id": oid} for oid in valid_ids]

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

    if not todo.get("source_link"):
        append_need_confirm(need_confirm, FIELD_NAMES["source_link"])

    return need_confirm


def todo_to_fields(todo: dict[str, Any]) -> dict[str, Any]:
    """Convert one normalized todo dict into Feishu Bitable field payload."""
    fields: dict[str, Any] = {
        FIELD_NAMES["title"]: todo.get("title", "（无标题）"),
        FIELD_NAMES["description"]: todo.get("description", ""),
        FIELD_NAMES["status"]: todo.get("status", "待确认"),
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
        # 之前的代码注释掉
        # fields[FIELD_NAMES["need_confirm"]] = need_confirm
        # 转换为字符串，多行文本类型写入
        fields[FIELD_NAMES["need_confirm"]] = "，".join(need_confirm)

    source_type = str(todo.get("source_type", ""))
    title = str(todo.get("title", ""))
    sys_id_str = f"{source_type}_{title}".encode("utf-8")
    fields[FIELD_NAMES["system_id"]] = hashlib.md5(sys_id_str).hexdigest()

    return {k: v for k, v in fields.items() if v not in (None, "", [])}
