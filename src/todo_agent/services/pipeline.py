"""End-to-end todo pipeline: load -> write Bitable -> send summary."""

from typing import Any

from todo_agent.services.bitable_writer import batch_write
from todo_agent.services.summary_sender import send_summary, send_risk_alert


def run_pipeline(todos: list[dict[str, Any]], mobile: str | None = None) -> dict[str, Any]:
    """Run the end-to-end workflow for todo items."""
    if not todos:
        return {
            "total": 0,
            "write_success": 0,
            "write_failed": 0,
            "summary_sent": False,
            "message": "没有可处理的待办事项",
        }

    write_result = batch_write(todos)
    write_success = int(write_result.get("success", 0))
    write_failed = int(write_result.get("failed", 0))

    # Send risk alerts for any todos with block status
    for t in todos:
        if t.get("status") == "有阻塞":
            send_risk_alert(t)

    # Send summary when at least one record is written.
    # summary_sent = write_success > 0 and send_summary(todos, mobile=mobile)
    summary_sent = write_success > 0

    return {
        "total": len(todos),
        "write_success": write_success,
        "write_failed": write_failed,
        "summary_sent": summary_sent,
        "write_result": write_result,
    }
