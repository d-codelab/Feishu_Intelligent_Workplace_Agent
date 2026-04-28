# bot_sender.py
import json

import requests
from dotenv import load_dotenv

from feishu_client import get_access_token

load_dotenv()

TEST_MOBILE = "13349952475"

with open("mock_data/data.json", "r", encoding="utf-8") as file:
    data = json.load(file)


def build_text_content(message: str) -> str:
    return json.dumps({"text": message}, ensure_ascii=False)


def get_user_open_id_by_mobile(mobile: str, include_resigned: bool = True) -> str | None:
    """通过手机号查询用户 open_id"""
    token = get_access_token()
    url = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id"

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"mobiles": [mobile], "include_resigned": include_resigned},
    )
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


def send_text(message: str, receive_id: str, receive_id_type: str = "open_id") -> bool:
    """向用户发送纯文本消息"""
    token = get_access_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    resp = requests.post(
        url,
        params={"receive_id_type": receive_id_type},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": receive_id,
            "msg_type": "text",
            "content": build_text_content(message),
        },
    )
    result = resp.json()
    if result.get("code") == 0:
        print("✅ 消息发送成功")
        return True

    print(f"❌ 消息发送失败: {result}")
    return False


def send_summary(todos: list[dict]) -> bool:
    """根据 todos 列表生成并发送汇总消息"""
    total = len(todos)
    no_owner = sum(1 for t in todos if not t.get("owner_open_id") and not t.get("owner_open_ids"))
    blocked = sum(1 for t in todos if t.get("status") == "阻塞" or t.get("risk_or_blocker"))

    message = (
        f"今日自动整理出 {total} 个团队事项，"
        f"其中 {no_owner} 个缺少负责人，"
        f"{blocked} 个存在阻塞风险。"
        f"请查看「团队重点事项推进总表」。"
    )

    open_id = get_user_open_id_by_mobile(TEST_MOBILE)
    if not open_id:
        return False

    return send_text(message, receive_id=open_id, receive_id_type="open_id")


if __name__ == "__main__":
    test_todos = data
    send_summary(test_todos)
