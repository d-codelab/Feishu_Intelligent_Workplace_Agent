"""JSON loading helpers."""

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    """Load a JSON file with UTF-8 encoding."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_todo_items(path: Path) -> list[dict[str, Any]]:
    """Load todo items from either a JSON list or an object with an ``items`` list."""
    payload = load_json(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise ValueError(f"无法从 {path} 读取待办列表：期望 JSON 数组或包含 items 数组的对象")
