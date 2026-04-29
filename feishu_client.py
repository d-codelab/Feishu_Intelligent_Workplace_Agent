# feishu_client.py
import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
REQUEST_TIMEOUT = 10

_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}


def get_access_token(force_refresh: bool = False) -> str:
    """Get a Feishu tenant access token."""
    if not APP_ID or not APP_SECRET:
        raise ValueError("缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET 配置")

    now = time.time()
    cached_token = _token_cache.get("token")
    if cached_token and not force_refresh and now < float(_token_cache.get("expires_at", 0)):
        return str(cached_token)

    resp = requests.post(
        TOKEN_URL,
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()

    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data}")

    expire_seconds = int(data.get("expire", 7200))
    token = data["tenant_access_token"]
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + max(expire_seconds - 60, 0)

    print(f"✅ token 获取成功，有效期 {expire_seconds}s")
    return token


if __name__ == "__main__":
    token = get_access_token()
    print(f"token: {token[:20]}...")
