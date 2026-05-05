"""Low-level Feishu Bitable API helpers."""

import json
from typing import Any

import requests

from todo_agent.clients.auth import get_access_token
from todo_agent.config import config


def _log_error_response(resp: requests.Response) -> None:
    """Best-effort logging of Feishu API error responses."""
    try:
        print(f"❌ API Error Response JSON: {resp.json()}")
    except ValueError:
        print(f"❌ API Error Response Text: {resp.text}")


def batch_create_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch create records in the configured Feishu Bitable table."""
    app_token, table_id = config.require_bitable_config()
    token = get_access_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"records": records},
        timeout=config.request_timeout,
    )
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error_response(resp)
        raise
    return resp.json()


def batch_update_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch update records in the configured Feishu Bitable table."""
    app_token, table_id = config.require_bitable_config()
    token = get_access_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"records": records},
        timeout=config.request_timeout,
    )
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error_response(resp)
        raise
    return resp.json()


def search_records(filter_info: dict[str, Any]) -> dict[str, Any]:
    """Search records using the Bitable search API."""
    app_token, table_id = config.require_bitable_config()
    token = get_access_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"filter": filter_info},
        timeout=config.request_timeout,
    )
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error_response(resp)
        raise
    return resp.json()


def print_bitable_error(prefix: str, result: dict[str, Any]) -> None:
    """Print a readable Feishu Bitable API error."""
    print(f"{prefix}: {json.dumps(result, ensure_ascii=False)}")
