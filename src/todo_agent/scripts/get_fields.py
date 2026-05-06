"""Script for printing configured Bitable field metadata."""

from __future__ import annotations

import json
import os
from typing import Any

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import ListAppTableFieldRequest, ListAppTableFieldResponse

from todo_agent.clients.auth import get_access_token
from todo_agent.config import config


def decode_raw_content(raw_content: bytes | str | None) -> Any:
    """Decode raw SDK response content for diagnostic printing."""
    if raw_content is None:
        return None

    text = raw_content.decode("utf-8") if isinstance(raw_content, bytes) else raw_content
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def get_fields() -> None:
    """Print field-name to field-ID mapping for the configured Bitable table."""
    token = get_access_token()
    app_token, table_id = config.require_bitable_config()

    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()
    request: ListAppTableFieldRequest = (
        ListAppTableFieldRequest.builder().app_token(app_token).table_id(table_id).build()
    )

    option = lark.RequestOption.builder().tenant_access_token(token).build()
    response: ListAppTableFieldResponse = client.bitable.v1.app_table_field.list(request, option)

    if not response.success():
        raw = decode_raw_content(response.raw.content if response.raw else None)
        print("字段查询失败：")
        print(f"code={response.code}, msg={response.msg}, log_id={response.get_log_id()}")
        print(json.dumps(raw, indent=4, ensure_ascii=False) if isinstance(raw, dict) else raw)
        return

    items = response.data.items or []
    print("字段名 → field_id 映射：")
    for field in items:
        print(f"  '{field.field_name}': '{field.field_id}'")


if __name__ == "__main__":
    get_fields()
