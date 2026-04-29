"""Script for listing Feishu chats visible to a user token."""

import json
from typing import Any

import lark_oapi as lark
from lark_oapi.api.im.v1 import ListChatRequest, ListChatResponse

from todo_agent.config import config


def decode_raw_content(raw_content: bytes | str | None) -> Any:
    """Decode raw SDK error content for diagnostic logs."""
    if raw_content is None:
        return None

    text = raw_content.decode("utf-8") if isinstance(raw_content, bytes) else raw_content
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def get_chat_id() -> None:
    """List chats and print the SDK response data."""
    user_access_token = config.require_user_access_token()
    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()

    request: ListChatRequest = ListChatRequest.builder().sort_type("ByCreateTimeAsc").page_size(20).build()
    option = lark.RequestOption.builder().user_access_token(user_access_token).build()
    response: ListChatResponse = client.im.v1.chat.list(request, option)

    if not response.success():
        raw = decode_raw_content(response.raw.content if response.raw else None)
        lark.logger.error(
            "client.im.v1.chat.list failed, "
            f"code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, "
            f"resp: {json.dumps(raw, indent=4, ensure_ascii=False) if isinstance(raw, dict) else raw}"
        )
        return

    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    get_chat_id()
