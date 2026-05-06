"""Feishu Open API authentication client."""

import time
from typing import Any

import requests

# ========== 配置信息 ==========
FEISHU_APP_ID = "cli_a973eb3d38b81cca"
FEISHU_APP_SECRET = "X8tBNt9clhrJZBxtcPsDmgjOpuXAGeKc"
REQUEST_TIMEOUT = 10
# ==============================

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}


def get_access_token(force_refresh: bool = False) -> str:
    """Get a Feishu tenant access token with in-process caching.

    Args:
        force_refresh: Force refresh the token even if cached

    Returns:
        Valid tenant_access_token

    Raises:
        RuntimeError: If token request fails
    """
    now = time.time()
    cached_token = _token_cache.get("token")
    if cached_token and not force_refresh and now < float(_token_cache.get("expires_at", 0)):
        return str(cached_token)

    resp = requests.post(
        TOKEN_URL,
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
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

    print(f"Token 获取成功，有效期 {expire_seconds}s")
    return token
