# bot_sender.py
import json
import os

import requests
from dotenv import load_dotenv

from feishu_client import get_access_token

load_dotenv()

TEST_MOBILE = "13349952475"
BITABLE_APP_TOKEN = os.getenv("FEISHU_BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("FEISHU_TABLE_ID")

with open("mock_data/data.json", "r", encoding="utf-8") as file:
    data = json.load(file)


def build_text_content(message: str) -> str:
    return json.dumps({"text": message}, ensure_ascii=False)


def get_bitable_url() -> str:
    if BITABLE_APP_TOKEN and TABLE_ID:
        return f"https://feishu.cn/base/{BITABLE_APP_TOKEN}?table={TABLE_ID}"
    return ""


def build_bitable_link_text() -> str:
    url = get_bitable_url()
    if url:
        return f"[团队重点事项推进总表]({url})"
    return "团队重点事项推进总表"


def build_card_content(card: dict) -> str:
    """构建飞书交互卡片消息 content"""
    return json.dumps(card, ensure_ascii=False)


def build_summary_card(todos: list[dict]) -> dict:
    total = len(todos)
    no_owner = sum(1 for t in todos if not t.get("owner_open_id") and not t.get("owner_open_ids"))
    blocked = sum(1 for t in todos if t.get("status") == "阻塞" or t.get("risk_or_blocker"))

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "团队重点事项汇总"},
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"今日自动整理出 **{total}** 个团队事项\n"
                        f"- 缺少负责人：**{no_owner}** 个\n"
                        f"- 存在阻塞风险：**{blocked}** 个\n\n"
                        f"请查看{build_bitable_link_text()}。"
                    ),
                },
            }
        ],
    }


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


def send_card(card: dict, receive_id: str, receive_id_type: str = "open_id") -> bool:
    """向用户发送飞书交互卡片消息"""
    token = get_access_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    resp = requests.post(
        url,
        params={"receive_id_type": receive_id_type},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": build_card_content(card),
        },
    )
    result = resp.json()
    if result.get("code") == 0:
        print("✅ 卡片发送成功")
        return True

    print(f"❌ 卡片发送失败: {result}")
    return False


def send_summary(todos: list[dict]) -> bool:
    """根据 todos 列表生成并发送汇总消息"""
    open_id = get_user_open_id_by_mobile(TEST_MOBILE)
    if not open_id:
        return False

    return send_card(build_summary_card(todos), receive_id=open_id, receive_id_type="open_id")


if __name__ == "__main__":
    test_todos = data
    send_summary(test_todos)
