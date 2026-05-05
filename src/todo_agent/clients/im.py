"""Low-level Feishu IM and contact API helpers."""

import json
import requests
from typing import Any
import lark_oapi as lark
from lark_oapi.api.im.v1 import ListChatRequest

from todo_agent.clients.auth import get_access_token
from todo_agent.config import config

MESSAGE_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
USER_BATCH_GET_ID_URL = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id"


def get_user_open_id_by_mobile(mobile: str, include_resigned: bool = True) -> str | None:
    """Query a Feishu user's open ID by mobile number."""
    token = get_access_token()
    resp = requests.post(
        USER_BATCH_GET_ID_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"mobiles": [mobile], "include_resigned": include_resigned},
        timeout=config.request_timeout,
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("code") != 0:
        print(f"❌ 用户查询失败: {result}")
        return None

    user_list = result.get("data", {}).get("user_list", [])
    if not user_list:
        print("❌ 未查询到匹配用户")
        return None

    open_id = user_list[0].get("user_id")
    if not open_id:
        print(f"❌ 查询成功但缺少 user_id: {result}")
        return None

    print(f"✅ 用户查询成功，open_id: {open_id}")
    return open_id


def send_interactive_card(card: dict[str, Any], receive_id: str, receive_id_type: str = "open_id") -> bool:
    """Send a Feishu interactive card message."""
    token = get_access_token()
    resp = requests.post(
        MESSAGE_URL,
        params={"receive_id_type": receive_id_type},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
        json={
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        },
        timeout=config.request_timeout,
    )
    if resp.status_code != 200:
        print(f"❌ API Request Failed [Status {resp.status_code}]: {resp.text}")
        return False

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return False

    result = resp.json()
    if result.get("code") == 0:
        print("✅ 卡片发送成功")
        return True

    print(f"❌ 卡片发送失败: {result}")
    return False

def list_chats() -> list[dict[str, Any]]:
    """List chats the bot is in."""
    app_id, app_secret = config.require_app_credentials()
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    request: ListChatRequest = ListChatRequest.builder() \
        .sort_type("ByCreateTimeAsc") \
        .page_size(100) \
        .build()

    response = client.im.v1.chat.list(request)

    if not response.success():
        raise RuntimeError(
            f"client.im.v1.chat.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: {response.raw.content}"
        )

    return [{"chat_id": c.chat_id, "name": c.name} for c in response.data.items] if response.data.items else []
