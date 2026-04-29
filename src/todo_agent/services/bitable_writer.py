"""Service for writing todo records into Feishu Bitable."""

from typing import Any

from todo_agent.clients.bitable import batch_create_records, print_bitable_error
from todo_agent.services.todo_mapper import todo_to_fields


def batch_write(todos: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch write todos into the configured Feishu Bitable table."""
    if not todos:
        return {"success": 0, "failed": 0, "record_ids": []}

    records = [{"fields": todo_to_fields(todo)} for todo in todos]
    result = batch_create_records(records)

    if result.get("code") == 0:
        created = result.get("data", {}).get("records", [])
        print(f"✅ 批量写入成功：{len(created)} 条")
        return {"success": len(created), "failed": 0, "record_ids": [r["record_id"] for r in created]}

    print_bitable_error("❌ 批量写入失败", result)
    return {"success": 0, "failed": len(todos), "error": result}
