"""Feishu IM (group chat) extractor."""

from typing import Any
from datetime import datetime

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.feishu_api import get_chat_history
from todo_extractor.llm.client import extract_todos_by_llm
from todo_extractor.utils.chat_utils import (
    preprocess_messages,
    format_messages_for_llm,
    get_message_stats,
    split_by_topic
)
from todo_extractor.utils.deduplicator import deduplicate_todos


class FeishuIMExtractor(BaseExtractor):
    """Extract todo items from Feishu group chat messages."""

    def __init__(self, mode: str = "realtime"):
        """Initialize extractor.

        Args:
            mode: Extraction mode
                - "realtime": Fast single-stage extraction (default)
                - "batch": Enhanced extraction with preprocessing and deduplication
        """
        self.mode = mode

    def extract(self, chat_id: str, hours: int = 24) -> list[dict[str, Any]]:
        """Extract todos from Feishu group chat history.

        Args:
            chat_id: Feishu chat ID
            hours: Number of hours to look back (default: 24)

        Returns:
            List of extracted todo items
        """
        print(f"[群消息抽取] 开始处理：{chat_id}（最近 {hours} 小时，模式：{self.mode}）")

        # Step 1: Get chat history
        messages = get_chat_history(chat_id, hours=hours)

        if not messages:
            print("[群消息抽取] 未获取到群消息")
            return []

        # Step 2: Sort messages by time (oldest first)
        messages_sorted = sorted(messages, key=lambda x: x.get('time', ''))
        print(f"[群消息抽取] 获取到 {len(messages_sorted)} 条原始消息")

        # Choose extraction strategy based on mode
        if self.mode == "batch":
            return self._batch_extract(chat_id, messages_sorted)
        else:
            return self._realtime_extract(chat_id, messages_sorted)

    def _realtime_extract(self, chat_id: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fast single-stage extraction (for real-time scenarios).

        Args:
            chat_id: Feishu chat ID
            messages: Sorted messages

        Returns:
            List of extracted todo items
        """
        # Format messages as text with timestamp
        text = "\n".join([
            f"[{msg['time']}] [{msg['sender']}]: {msg['content']}"
            for msg in messages
        ])
        print(f"[实时模式] 消息格式化完成，共 {len(text)} 字符")

        # Extract todos using LLM
        todos = extract_todos_by_llm(text, source_type=self.source_type)

        # Add source_link to each todo
        source_link = f"https://feishu.cn/messenger/chat/{chat_id}"
        for todo in todos:
            todo["source_link"] = source_link

        print(f"[实时模式] 抽取完成：{len(todos)} 条事项")
        return todos

    def _batch_extract(self, chat_id: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enhanced batch extraction with preprocessing and deduplication.

        Pipeline:
        1. Preprocess messages (filter noise)
        2. Get message statistics
        3. Format for LLM with context
        4. Extract todos
        5. Deduplicate
        6. Post-process

        Args:
            chat_id: Feishu chat ID
            messages: Sorted messages

        Returns:
            List of extracted todo items
        """
        # Step 1: Preprocess messages (filter noise)
        messages_filtered = preprocess_messages(messages)
        print(f"[批量模式] 预处理完成：{len(messages)} -> {len(messages_filtered)} 条消息（过滤 {len(messages) - len(messages_filtered)} 条噪声）")

        if not messages_filtered:
            print("[批量模式] 过滤后无有效消息")
            return []

        # Step 2: Get message statistics
        stats = get_message_stats(messages_filtered)
        print(f"[批量模式] 消息统计：{stats['unique_senders']} 人参与，时间跨度 {stats['time_span_hours']} 小时，平均消息长度 {stats['avg_message_length']} 字符")

        # Step 3: Check if we need to split by topic
        # For large message volumes (>200 messages), split by topic
        if len(messages_filtered) > 200:
            print(f"[批量模式] 消息量较大（{len(messages_filtered)} 条），按话题分段处理")
            segments = split_by_topic(messages_filtered, max_gap_minutes=30)
            print(f"[批量模式] 分段完成：{len(segments)} 个话题段")

            all_todos = []
            for i, segment in enumerate(segments, 1):
                print(f"[批量模式] 处理第 {i}/{len(segments)} 段（{len(segment)} 条消息）")
                text = format_messages_for_llm(segment, include_context=True)
                todos = extract_todos_by_llm(text, source_type=self.source_type)
                all_todos.extend(todos)
                print(f"[批量模式] 第 {i} 段抽取：{len(todos)} 条事项")

            print(f"[批量模式] 分段抽取完成：共 {len(all_todos)} 条事项")
        else:
            # Step 4: Format messages for LLM with context
            text = format_messages_for_llm(messages_filtered, include_context=True)
            print(f"[批量模式] 消息格式化完成，共 {len(text)} 字符")

            # Step 5: Extract todos using LLM
            all_todos = extract_todos_by_llm(text, source_type=self.source_type)
            print(f"[批量模式] LLM 抽取完成：{len(all_todos)} 条事项")

        # Step 6: Deduplicate
        original_count = len(all_todos)
        all_todos = deduplicate_todos(all_todos)
        print(f"[批量模式] 去重完成：{original_count} -> {len(all_todos)} 条事项（去重 {original_count - len(all_todos)} 条）")

        # Step 7: Add source_link to each todo
        source_link = f"https://feishu.cn/messenger/chat/{chat_id}"
        for todo in all_todos:
            todo["source_link"] = source_link

        # Step 8: Filter by confidence (optional, only in batch mode)
        confidence_threshold = 0.6
        filtered_todos = [todo for todo in all_todos if todo.get("置信度", 0) >= confidence_threshold]
        if len(filtered_todos) < len(all_todos):
            print(f"[批量模式] 置信度过滤：{len(all_todos)} -> {len(filtered_todos)} 条事项（过滤 {len(all_todos) - len(filtered_todos)} 条低置信度）")
            all_todos = filtered_todos

        print(f"[批量模式] 抽取完成：{len(all_todos)} 条事项")
        return all_todos

    @property
    def source_type(self) -> str:
        return "群聊消息"
