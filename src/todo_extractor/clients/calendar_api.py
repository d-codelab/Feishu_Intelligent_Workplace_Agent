"""Feishu Calendar API helpers."""

import requests
from datetime import datetime, timedelta

# ========== 配置信息 ==========
APP_ID = "cli_a964a649df78dceb"
APP_SECRET = "y83yTWnKjYv0JnHkD5XarhQAW4B7oJJO"
REQUEST_TIMEOUT = 10
BASE_URL = "https://open.feishu.cn/open-apis"
# ==============================


def get_tenant_token() -> str:
    """获取 tenant_access_token（实时请求）

    Returns:
        Tenant access token

    Raises:
        RuntimeError: If request fails
    """
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}

    resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()

    if result.get("code") != 0:
        raise RuntimeError(f"获取 tenant token 失败: {result}")

    return result["tenant_access_token"]


def get_calendar_list() -> list[dict]:
    """Get user's calendar list (使用 Tenant Token).

    Returns:
        List of calendars

    Raises:
        RuntimeError: If request fails
    """
    token = get_tenant_token()
    url = f"{BASE_URL}/calendar/v4/calendars"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()

    if result.get("code") != 0:
        raise RuntimeError(f"获取日历列表失败: {result}")

    return result["data"]["calendar_list"]


def get_events(
    calendar_id: str,
    start_time: str,
    end_time: str,
    page_token: str = None
) -> dict:
    """Get calendar events for a single page (使用 Tenant Token).

    Args:
        calendar_id: Calendar ID (可使用 "primary" 表示主日历)
        start_time: Start time in ISO 8601 format (e.g., "2026-05-01T00:00:00+08:00")
        end_time: End time in ISO 8601 format
        page_token: Page token for pagination (optional)

    Returns:
        API response dict with "items", "has_more", "page_token"

    Raises:
        RuntimeError: If request fails
    """
    token = get_tenant_token()
    url = f"{BASE_URL}/calendar/v4/calendars/{calendar_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        # "start_time": start_time,
        # "end_time": end_time,
        "page_size": 50
    }
    if page_token:
        params["page_token"] = page_token

    resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()

    if result.get("code") != 0:
        raise RuntimeError(f"获取日历事件失败: {result}")

    return result.get("data", {})


def get_all_events(
    calendar_id: str,
    start_time: str,
    end_time: str
) -> list[dict]:
    """Get all calendar events with automatic pagination (使用 Tenant Token).

    Args:
        calendar_id: Calendar ID (可使用 "primary" 表示主日历)
        start_time: Start time in ISO 8601 format (e.g., "2026-05-01T00:00:00+08:00")
        end_time: End time in ISO 8601 format

    Returns:
        List of all events

    Raises:
        RuntimeError: If request fails
    """
    all_events = []
    page_token = None

    while True:
        result = get_events(calendar_id, start_time, end_time, page_token)
        items = result.get("items", [])
        all_events.extend(items)

        if not result.get("has_more"):
            break
        page_token = result.get("page_token")

    print(f"✅ 获取到 {len(all_events)} 个日历事件")
    return all_events


def get_upcoming_events(calendar_id: str, days: int = 7) -> list[dict]:
    """Get upcoming events for the next N days (使用 Tenant Token).

    Args:
        calendar_id: Calendar ID (可使用 "primary" 表示主日历)
        days: Number of days to look ahead

    Returns:
        List of events
    """
    now = datetime.now()
    start_time = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    end_dt = now + timedelta(days=days)
    end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    return get_all_events(calendar_id, start_time, end_time)


def format_event_text(event: dict) -> str:
    """Format a calendar event as plain text for LLM extraction.

    Args:
        event: Calendar event dict

    Returns:
        Formatted text string
    """
    summary = event.get("summary", "无标题")

    # start and end are dicts with "date_time" or "date" field
    start_obj = event.get("start", {})
    end_obj = event.get("end", {})

    location = event.get("location", {}).get("name", "") if event.get("location") else ""
    description = event.get("description", "")

    # Format time
    time_str = ""
    try:
        start_time = start_obj.get("date_time") or start_obj.get("date", "")
        end_time = end_obj.get("date_time") or end_obj.get("date", "")

        if start_time and end_time:
            time_str = f"{start_time} ~ {end_time}"
        elif start_time:
            time_str = start_time
        else:
            time_str = "时间待定"
    except Exception as e:
        time_str = f"时间解析失败: {e}"

    text = f"标题: {summary}\n"
    text += f"时间: {time_str}\n"

    if location:
        text += f"地点: {location}\n"
    if description:
        text += f"描述: {description}\n"

    return text
