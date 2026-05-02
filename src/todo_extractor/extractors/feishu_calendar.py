"""Feishu Calendar extractor."""

from typing import Any, Optional, List, Dict

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.calendar_api import (
    get_calendar_list,
    get_upcoming_events,
    format_event_text
)
from todo_extractor.llm.client import extract_todos_by_llm


class FeishuCalendarExtractor(BaseExtractor):
    """Extract todos from Feishu calendar events."""

    @property
    def source_type(self) -> str:
        return "飞书日历"

    def extract(self, calendar_id: Optional[str] = None, days: int = 7) -> List[Dict[str, Any]]:
        """Extract todos from calendar events.

        Args:
            calendar_id: Specific calendar ID (if None, extracts from all calendars)
            days: Number of days to look ahead (default: 7)

        Returns:
            List of extracted todo items
        """
        all_todos = []

        # If specific calendar_id provided, only extract from that calendar
        if calendar_id:
            print(f"✅ 使用指定日历: {calendar_id}")
            todos = self._extract_from_calendar(calendar_id, days)
            all_todos.extend(todos)
        else:
            # Get all calendars and extract from each
            print("📅 获取日历列表...")
            calendars = get_calendar_list()
            print(f"✅ 找到 {len(calendars)} 个日历")

            for cal in calendars:
                cal_id = cal["calendar_id"]
                cal_name = cal.get("summary", cal_id)
                cal_type = cal.get("type", "unknown")

                print(f"\n📆 处理日历: [{cal_type}] {cal_name}")

                todos = self._extract_from_calendar(cal_id, days, cal_name)
                all_todos.extend(todos)

        print(f"\n✅ 总共提取到 {len(all_todos)} 个待办事项")
        return all_todos

    def _extract_from_calendar(
        self,
        calendar_id: str,
        days: int,
        calendar_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract todos from a single calendar.

        Args:
            calendar_id: Calendar ID
            days: Number of days to look ahead
            calendar_name: Calendar name for metadata (optional)

        Returns:
            List of extracted todo items
        """
        # Get upcoming events
        events = get_upcoming_events(calendar_id, days)

        if not events:
            print(f"  ⚠️  未找到日历事件")
            return []

        print(f"  ✅ 找到 {len(events)} 个日历事件")

        # Format events as text
        event_texts = []
        for event in events:
            event_text = format_event_text(event)
            event_texts.append(event_text)

        combined_text = "\n\n".join(event_texts)

        # Extract todos using LLM
        todos = extract_todos_by_llm(combined_text, source_type=self.source_type)

        # Add calendar-specific metadata
        calendar_label = calendar_name or calendar_id
        for todo in todos:
            todo["来源链接"] = f"飞书日历 - {calendar_label}（接下来 {days} 天）"

        print(f"  ✅ 提取到 {len(todos)} 个待办事项")
        return todos
