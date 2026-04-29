"""Compatibility entrypoint for sending todo summary cards.

Prefer importing from ``todo_agent.services.summary_sender`` in new code.
"""

from todo_agent.config import FALLBACK_MOCK_TODOS_PATH
from todo_agent.services.summary_sender import send_summary
from todo_agent.utils.json_loader import load_todo_items


if __name__ == "__main__":
    send_summary(load_todo_items(FALLBACK_MOCK_TODOS_PATH))
