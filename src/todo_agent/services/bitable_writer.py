"""Service for writing todo records into Feishu Bitable."""

from typing import Any

from todo_agent.clients.bitable import batch_create_records, print_bitable_error, search_records
from todo_agent.services.todo_mapper import FIELD_NAMES, todo_to_fields


def check_existing_system_ids(system_ids: list[str]) -> set[str]:
    """Search for existing records by system_id and return a set of found IDs."""
    if not system_ids:
        return set()

    found_ids = set()
    system_id_field = FIELD_NAMES["system_id"]

    # We can batch conditions using OR if there are many,
    # but for simplicity, we search all records having system_id in our list.
    conditions = [
        {
            "field_name": system_id_field,
            "operator": "is",
            "value": [sid],
        }
        for sid in system_ids
    ]

    # Bitable search API allows max 100 conditions in 'OR'. Since this is a demo,
    # we assume the batch size is well within limits.
    if conditions:
        filter_info = {"conjunction": "or", "conditions": conditions}
        try:
            result = search_records(filter_info)
            if result.get("code") == 0:
                items = result.get("data", {}).get("items", [])
                for item in items:
                    sid = item.get("fields", {}).get(system_id_field)
                    if sid:
                        # Extract the string if Bitable returned a list or complex object
                        if isinstance(sid, list):
                            # The first element could be a dict or a string depending on the field config
                            if len(sid) > 0:
                                val = sid[0]
                                if isinstance(val, dict) and "text" in val:
                                    sid = val["text"]
                                else:
                                    sid = str(val)
                            else:
                                sid = None
                        if isinstance(sid, str):
                            found_ids.add(sid)
        except Exception as e:
            print(f"⚠️ 查询已存在的提醒失败：{e}")

    return found_ids


def batch_write(todos: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch write todos into the configured Feishu Bitable table."""
    if not todos:
        return {"success": 0, "failed": 0, "record_ids": []}

    all_records = [{"fields": todo_to_fields(todo)} for todo in todos]

    # Identify duplicate system IDs
    system_ids = [
        r["fields"].get(FIELD_NAMES["system_id"])
        for r in all_records
        if r["fields"].get(FIELD_NAMES["system_id"])
    ]
    existing_sids = check_existing_system_ids(system_ids)

    records = []
    for r in all_records:
        sid = r["fields"].get(FIELD_NAMES["system_id"])
        if sid and sid in existing_sids:
            print(f"ℹ️ 跳过重复的待办，系统ID: {sid}")
            continue
        records.append(r)

    if not records:
        print("ℹ️ 没有新的待办需要写入")
        return {"success": 0, "failed": 0, "record_ids": []}

    result = batch_create_records(records)

    if result.get("code") == 0:
        created = result.get("data", {}).get("records", [])
        print(f"✅ 批量写入成功：{len(created)} 条")
        return {
            "success": len(created),
            "failed": 0,
            "record_ids": [r["record_id"] for r in created],
        }

    print_bitable_error("❌ 批量写入失败", result)
    return {"success": 0, "failed": len(todos), "error": result}
