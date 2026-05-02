"""Feishu Minutes (妙记) extractor."""

from typing import Dict, List, Any, Optional
from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.minutes_api import (
    get_minutes_transcript,
    USER_TOKEN
)
from todo_extractor.llm.client import extract_todos_by_llm


class FeishuMinutesExtractor(BaseExtractor):
    """Extract todos from Feishu Minutes (妙记)."""

    def __init__(self, user_token: Optional[str] = None):
        """Initialize extractor.

        Args:
            user_token: User access token (optional, uses default if not provided)
        """
        self.user_token = user_token or USER_TOKEN

    @property
    def source_type(self) -> str:
        """Return source type identifier."""
        return "飞书妙记"

    def extract(self, minute_token: str) -> List[Dict[str, Any]]:
        """Extract todos from minutes.

        Args:
            minute_token: Minutes token (from URL, e.g., obcnb4r7575w2m39416cvaj3)

        Returns:
            List of extracted todo items
        """
        print(f"\n{'='*60}")
        print(f"开始抽取妙记 Todo")
        print(f"{'='*60}")
        print(f"妙记 Token: {minute_token}")

        # Get minutes transcript (returns plain text)
        text = get_minutes_transcript(self.user_token, minute_token)
        print(f"✅ 获取完成，文本长度: {len(text)} 字符")

        # Extract todos using LLM
        todos = extract_todos_by_llm(text, self.source_type)

        # Add metadata
        minute_url = f"https://jcneyh7qlo8i.feishu.cn/minutes/{minute_token}"
        for todo in todos:
            if not todo.get("source_link"):
                todo["source_link"] = minute_url

        print(f"✅ 抽取完成：{len(todos)} 条事项")
        return todos
