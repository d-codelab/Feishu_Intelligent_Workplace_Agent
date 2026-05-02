"""Feishu Minutes (妙记) API helpers."""

import requests

# ========== 配置信息 ==========
USER_TOKEN = "u-dsDwouGNF5NofiY8TjtAIl10lyjghlghW0GaZwU024o6"
REQUEST_TIMEOUT = 10
# ==============================


def get_minutes_transcript(token: str, minute_token: str) -> str:
    """Get minutes transcript content.

    Args:
        token: User access token
        minute_token: Minutes token (from URL, e.g., obcnb4r7575w2m39416cvaj3)

    Returns:
        Transcript text content (plain text, not JSON)

    Raises:
        RuntimeError: If request fails
    """
    url = f"https://open.feishu.cn/open-apis/minutes/v1/minutes/{minute_token}/transcript"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.encoding = 'utf-8'  # Important: specify encoding

    if resp.status_code != 200:
        raise RuntimeError(f"获取妙记失败: {resp.status_code} - {resp.text[:200]}")

    print(f"✅ 获取妙记成功")
    return resp.text  # Return plain text directly


def format_minutes_text(text: str) -> str:
    """Format minutes transcript text for LLM extraction.

    Args:
        text: Raw transcript text

    Returns:
        Formatted text string (just return as-is since it's already plain text)
    """
    # The API returns plain text directly, so we just return it
    return text
