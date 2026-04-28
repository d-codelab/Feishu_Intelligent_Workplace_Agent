# feishu_client.py
import os, requests
from dotenv import load_dotenv
load_dotenv()

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

def get_access_token() -> str:
    """获取 tenant_access_token，有效期 2 小时"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取 token 失败: {data}")
    print(f"✅ token 获取成功，有效期 {data['expire']}s")
    return data["tenant_access_token"]

if __name__ == "__main__":
    token = get_access_token()
    print(f"token: {token[:20]}...")