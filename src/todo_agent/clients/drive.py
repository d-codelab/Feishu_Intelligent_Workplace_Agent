from typing import Any

import lark_oapi as lark
from lark_oapi.api.drive.v1 import ListFileRequest

from todo_agent.config import config


def list_files_in_folder(folder_token: str) -> list[dict[str, Any]]:
    """List files in a drive folder using official SDK."""
    app_id, app_secret = config.require_app_credentials()
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    request: ListFileRequest = ListFileRequest.builder() \
        .folder_token(folder_token) \
        .order_by("EditedTime") \
        .direction("DESC") \
        .build()

    response = client.drive.v1.file.list(request)

    if not response.success():
        raise RuntimeError(
            f"client.drive.v1.file.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: {response.raw.content}"
        )

    return [{"token": f.token, "name": f.name, "type": f.type} for f in response.data.files]
