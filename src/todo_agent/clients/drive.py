import requests
from typing import Any
from todo_agent.clients.auth import get_access_token
from todo_agent.config import config

def list_files_in_folder(folder_token: str) -> list[dict[str, Any]]:
    """List files in a drive folder."""
    url = f"https://open.feishu.cn/open-apis/drive/v1/files"
    params = {"folder_token": folder_token}
    headers = {"Authorization": f"Bearer {get_access_token()}"}

    resp = requests.get(url, params=params, headers=headers, timeout=config.request_timeout)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取文件夹下文件失败: {data}")

    return data.get("data", {}).get("files", [])
