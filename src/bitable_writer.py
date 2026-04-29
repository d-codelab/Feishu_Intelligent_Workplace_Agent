"""Compatibility entrypoint for Bitable batch writing.

Prefer importing ``batch_write`` from ``todo_agent.services.bitable_writer`` in
new code.
"""

from todo_agent.config import DEFAULT_MOCK_TODOS_PATH, FALLBACK_MOCK_TODOS_PATH
from todo_agent.services.bitable_writer import batch_write
from todo_agent.utils.json_loader import load_todo_items


def load_default_todos() -> list[dict]:
    """Load mock todos from the preferred fixture, falling back to legacy data."""
    path = DEFAULT_MOCK_TODOS_PATH if DEFAULT_MOCK_TODOS_PATH.exists() else FALLBACK_MOCK_TODOS_PATH
    return load_todo_items(path)


if __name__ == "__main__":
    batch_write(load_default_todos())
