"""Feishu IM (group chat) extractor."""

from typing import Any

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.feishu_api import get_chat_history
from todo_extractor.llm.client import extract_todos_by_llm


class FeishuIMExtractor(BaseExtractor):
    """Extract todo items from Feishu group chat messages."""

    def extract(self, chat_id: str, hours: int = 24) -> list[dict[str, Any]]:
        """Extract todos from Feishu group chat history.

        Args:
            chat_id: Feishu chat ID
            hours: Number of hours to look back (default: 24)

        Returns:
            List of extracted todo items
        """
        print(f"💬 开始从群消息抽取：{chat_id}（最近 {hours} 小时）")

        # Step 1: Get chat history
        messages = get_chat_history(chat_id, hours=hours)

        if not messages:
            print("⚠️  未获取到群消息")
            return []

        # Step 2: Sort messages by time (oldest first)
        # Messages are returned in descending order, so reverse them
        messages_sorted = sorted(messages, key=lambda x: x.get('time', ''))

        # Step 3: Format messages as text with timestamp
        text = "\n".join([
            f"[{msg['time']}] [{msg['sender']}]: {msg['content']}"
            for msg in messages_sorted
        ])
        print(f"✅ 消息格式化完成，共 {len(messages_sorted)} 条消息，{len(text)} 字符")

        # Step 4: Extract todos using LLM
        todos = extract_todos_by_llm(text, source_type=self.source_type)

        # Step 5: Add source_link to each todo
        source_link = f"https://feishu.cn/messenger/chat/{chat_id}"
        for todo in todos:
            todo["source_link"] = source_link

        print(f"✅ 群消息抽取完成：{len(todos)} 条事项")
        return todos

    @property
    def source_type(self) -> str:
        return "群消息"
