"""Feishu Task extractor."""

from typing import Any, Optional, List, Dict

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.task_api import (
    get_tasks_all,
    convert_task_to_todo,
    USER_TOKEN
)


class FeishuTaskExtractor(BaseExtractor):
    """Extract todos from Feishu tasks."""

    def __init__(self, user_token: Optional[str] = None):
        """Initialize task extractor.

        Args:
            user_token: User access token (optional, uses default if not provided)
        """
        self.user_token = user_token or USER_TOKEN

    @property
    def source_type(self) -> str:
        return "飞书任务"

    def extract(self, max_count: int = 200) -> List[Dict[str, Any]]:
        """Extract todos from tasks.

        Args:
            max_count: Maximum number of tasks to fetch (default: 200)

        Returns:
            List of extracted todo items
        """
        # Get all tasks
        tasks = get_tasks_all(self.user_token, max_count)

        if not tasks:
            print("⚠️  未找到任务")
            return []

        # Filter incomplete tasks
        incomplete_tasks = []
        for task in tasks:
            completed_at = task.get("completed_at")
            is_completed = completed_at and completed_at != "0"
            if not is_completed:
                incomplete_tasks.append(task)

        print(f"✅ 找到 {len(incomplete_tasks)} 个未完成任务")

        if not incomplete_tasks:
            return []

        # Convert tasks to todos directly (no LLM needed)
        todos = []
        for task in incomplete_tasks:
            todo = convert_task_to_todo(task)
            todos.append(todo)

        print(f"✅ 转换完成：{len(todos)} 条事项")

        return todos

