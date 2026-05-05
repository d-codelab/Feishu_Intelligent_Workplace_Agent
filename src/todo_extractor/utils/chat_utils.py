"""群聊消息预处理工具"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any


def preprocess_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """过滤无效消息，提高信噪比

    Args:
        messages: 原始消息列表

    Returns:
        过滤后的消息列表
    """
    # 无效消息模式
    NOISE_PATTERNS = [
        r'^[哈嘿呵嗯啊哦嘛呀]+$',  # 纯语气词
        r'^[👍😄😊🙏💪😂🤣😭😱🔥]+$',  # 纯表情
        r'^(收到|好的|OK|ok|知道了|明白|了解|懂了)$',  # 简单确认
        r'^\[图片\]$',  # 纯图片
        r'^\[文件\]$',  # 纯文件
        r'^\[视频\]$',  # 纯视频
        r'^\[语音\]$',  # 纯语音
        r'^\.+$',  # 纯句号
        r'^\?+$',  # 纯问号
    ]

    filtered = []
    for msg in messages:
        content = msg.get('content', '').strip()

        # 跳过空消息
        if not content:
            continue

        # 跳过噪声消息
        is_noise = any(re.match(pattern, content) for pattern in NOISE_PATTERNS)
        if is_noise:
            continue

        filtered.append(msg)

    return filtered


def resolve_relative_time(text: str, base_date: datetime = None) -> str:
    """将相对时间转换为绝对日期

    Args:
        text: 包含时间表达的文本
        base_date: 基准日期（默认为当前日期）

    Returns:
        YYYY-MM-DD 格式的日期字符串，无法解析返回 "待确认"
    """
    if base_date is None:
        base_date = datetime.now()

    text = text.lower()

    # 今天/今日
    if "今天" in text or "今日" in text:
        return base_date.strftime("%Y-%m-%d")

    # 明天/明日
    if "明天" in text or "明日" in text:
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # 后天
    if "后天" in text:
        return (base_date + timedelta(days=2)).strftime("%Y-%m-%d")

    # 下周X
    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
    for day_name, day_num in weekday_map.items():
        if f"下周{day_name}" in text:
            days_ahead = day_num - base_date.weekday() + 7
            if days_ahead <= 0:
                days_ahead += 7
            return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # 本周X / 周X
    for day_name, day_num in weekday_map.items():
        if f"本周{day_name}" in text or (f"周{day_name}" in text and "下周" not in text):
            days_ahead = day_num - base_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # 本月底
    if "本月底" in text or "月底" in text:
        # 获取下个月的第一天，然后减一天
        if base_date.month == 12:
            next_month = base_date.replace(year=base_date.year + 1, month=1, day=1)
        else:
            next_month = base_date.replace(month=base_date.month + 1, day=1)
        last_day = next_month - timedelta(days=1)
        return last_day.strftime("%Y-%m-%d")

    # 下月初
    if "下月初" in text or "下个月初" in text:
        if base_date.month == 12:
            return f"{base_date.year + 1}-01-01"
        else:
            return f"{base_date.year}-{base_date.month + 1:02d}-01"

    # X天后
    match = re.search(r'(\d+)\s*天[后內内之]', text)
    if match:
        days = int(match.group(1))
        return (base_date + timedelta(days=days)).strftime("%Y-%m-%d")

    # X周后
    match = re.search(r'(\d+)\s*周[后內内之]', text)
    if match:
        weeks = int(match.group(1))
        return (base_date + timedelta(weeks=weeks)).strftime("%Y-%m-%d")

    # 具体日期：MM-DD 或 M月D日
    match = re.search(r'(\d{1,2})[月\-](\d{1,2})', text)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = base_date.year

        # 如果日期已经过了，可能是指明年
        try:
            target_date = datetime(year, month, day)
            if target_date < base_date:
                year += 1
            return f"{year}-{month:02d}-{day:02d}"
        except ValueError:
            pass

    return "待确认"


def format_messages_for_llm(messages: List[Dict[str, Any]], include_context: bool = True) -> str:
    """将消息格式化为 LLM 输入文本

    Args:
        messages: 消息列表
        include_context: 是否包含上下文信息

    Returns:
        格式化后的文本
    """
    if not messages:
        return ""

    lines = []

    if include_context:
        # 添加时间上下文
        first_time = messages[0].get('time', '')
        last_time = messages[-1].get('time', '')
        lines.append(f"# 群聊记录时间范围：{first_time} 至 {last_time}")
        lines.append(f"# 当前日期：{datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"# 消息总数：{len(messages)} 条\n")

    # 格式化每条消息
    for msg in messages:
        time = msg.get('time', '')
        sender = msg.get('sender', 'Unknown')
        content = msg.get('content', '')
        lines.append(f"[{time}] [{sender}]: {content}")

    return "\n".join(lines)


def extract_user_mentions(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """统计消息中提到的用户（用于识别负责人）

    Args:
        messages: 消息列表

    Returns:
        用户提及次数字典 {user_id: count}
    """
    mentions = {}

    for msg in messages:
        content = msg.get('content', '')

        # 提取 @用户
        at_mentions = re.findall(r'@(\w+)', content)
        for user in at_mentions:
            mentions[user] = mentions.get(user, 0) + 1

    return mentions


def split_by_topic(messages: List[Dict[str, Any]], max_gap_minutes: int = 30) -> List[List[Dict[str, Any]]]:
    """根据时间间隔将消息分段（简单的话题分段）

    Args:
        messages: 消息列表（按时间排序）
        max_gap_minutes: 最大时间间隔（分钟），超过此间隔视为新话题

    Returns:
        分段后的消息列表
    """
    if not messages:
        return []

    segments = []
    current_segment = [messages[0]]

    for i in range(1, len(messages)):
        prev_msg = messages[i - 1]
        curr_msg = messages[i]

        # 解析时间
        try:
            prev_time = datetime.strptime(prev_msg['time'], '%Y-%m-%d %H:%M:%S')
            curr_time = datetime.strptime(curr_msg['time'], '%Y-%m-%d %H:%M:%S')

            # 计算时间差
            time_diff = (curr_time - prev_time).total_seconds() / 60

            if time_diff > max_gap_minutes:
                # 时间间隔过大，开始新段落
                segments.append(current_segment)
                current_segment = [curr_msg]
            else:
                current_segment.append(curr_msg)
        except (ValueError, KeyError):
            # 时间解析失败，继续添加到当前段落
            current_segment.append(curr_msg)

    # 添加最后一个段落
    if current_segment:
        segments.append(current_segment)

    return segments


def get_message_stats(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """获取消息统计信息

    Args:
        messages: 消息列表

    Returns:
        统计信息字典
    """
    if not messages:
        return {
            'total_count': 0,
            'unique_senders': 0,
            'time_span_hours': 0,
            'avg_message_length': 0
        }

    # 统计发言人
    senders = set(msg.get('sender', '') for msg in messages)

    # 计算时间跨度
    try:
        first_time = datetime.strptime(messages[0]['time'], '%Y-%m-%d %H:%M:%S')
        last_time = datetime.strptime(messages[-1]['time'], '%Y-%m-%d %H:%M:%S')
        time_span_hours = (last_time - first_time).total_seconds() / 3600
    except (ValueError, KeyError):
        time_span_hours = 0

    # 计算平均消息长度
    total_length = sum(len(msg.get('content', '')) for msg in messages)
    avg_length = total_length / len(messages) if messages else 0

    return {
        'total_count': len(messages),
        'unique_senders': len(senders),
        'time_span_hours': round(time_span_hours, 2),
        'avg_message_length': round(avg_length, 1)
    }
