"""Service for writing todo records into Feishu Bitable."""
from __future__ import annotations

from typing import Any

from todo_agent.clients.bitable import batch_create_records, batch_update_records, print_bitable_error, search_records
from todo_agent.services.todo_mapper import FIELD_NAMES, todo_to_fields


def check_existing_system_ids(system_ids: list[str]) -> dict[str, str]:
    """Search for existing records by system_id and return a mapping of system_id -> record_id."""
    if not system_ids:
        return {}

    found_ids = {}
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
                    record_id = item.get("record_id")
                    if sid and record_id:
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
                            found_ids[sid] = record_id
        except Exception as e:
            print(f"⚠️ 查询已存在的提醒失败：{e}")

    return found_ids


def batch_write(todos: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch write (upsert) todos into the configured Feishu Bitable table."""
    if not todos:
        return {"success": 0, "failed": 0, "record_ids": [], "updated": 0}

    all_records = [{"fields": todo_to_fields(todo)} for todo in todos]

    # Identify duplicate system IDs
    system_ids = [
        r["fields"].get(FIELD_NAMES["system_id"])
        for r in all_records
        if r["fields"].get(FIELD_NAMES["system_id"])
    ]
    existing_sids = check_existing_system_ids(system_ids)

    records_to_create = []
    records_to_update = []

    for r in all_records:
        sid = r["fields"].get(FIELD_NAMES["system_id"])
        if sid and sid in existing_sids:
            records_to_update.append({
                "record_id": existing_sids[sid],
                "fields": r["fields"]
            })
            print(f"ℹ️ 准备更新已存在的待办，系统ID: {sid}")
        else:
            records_to_create.append(r)

    if not records_to_create and not records_to_update:
        print("ℹ️ 没有新的待办需要写入或更新")
        return {"success": 0, "failed": 0, "record_ids": [], "updated": 0}

    created_count = 0
    updated_count = 0
    failed_count = 0
    record_ids = []

    # Create new records
    if records_to_create:
        result_c = batch_create_records(records_to_create)
        if result_c.get("code") == 0:
            created = result_c.get("data", {}).get("records", [])
            created_count = len(created)
            record_ids.extend([r["record_id"] for r in created])
            print(f"✅ 批量新建成功：{created_count} 条")
        else:
            failed_count += len(records_to_create)
            print_bitable_error("❌ 批量新建失败", result_c)

    # Update existing records
    if records_to_update:
        result_u = batch_update_records(records_to_update)
        if result_u.get("code") == 0:
            updated = result_u.get("data", {}).get("records", [])
            updated_count = len(updated)
            record_ids.extend([r["record_id"] for r in updated])
            print(f"✅ 批量更新成功：{updated_count} 条")
        else:
            failed_count += len(records_to_update)
            print_bitable_error("❌ 批量更新失败", result_u)

    return {
        "success": created_count,
        "updated": updated_count,
        "failed": failed_count,
        "record_ids": record_ids,
    }
