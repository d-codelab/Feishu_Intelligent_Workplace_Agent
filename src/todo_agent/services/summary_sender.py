"""Build and send Feishu todo summary cards."""

from typing import Any

from todo_agent.clients.im import get_user_open_id_by_mobile, send_interactive_card
from todo_agent.config import config


def get_bitable_url() -> str:
    """Build the web URL for the configured Bitable table."""
    if config.bitable_app_token and config.bitable_table_id:
        return f"https://feishu.cn/base/{config.bitable_app_token}?table={config.bitable_table_id}"
    return ""


def build_bitable_link_text() -> str:
    """Build Feishu markdown link text for the Bitable table."""
    url = get_bitable_url()
    if url:
        return f"[团队重点事项推进总表]({url})"
    return "团队重点事项推进总表"


def build_summary_card(todos: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an interactive card summarizing todo extraction results."""
    total = len(todos)
    no_owner = sum(1 for t in todos if not t.get("owner_open_id") and not t.get("owner_open_ids"))
    blocked = sum(1 for t in todos if t.get("status") == "阻塞" or t.get("risk_or_blocker"))

    at_list = ""
    for t in todos:
        if t.get("owner_open_id"):
            print(f"Processing owner for todo '{t.get('title', 'N/A')}': owner_open_id={t['owner_open_id']}")
            at_list += f'<at id="{t["owner_open_id"]}"></at> '
        if t.get("owner_open_ids"):
            for oid in t["owner_open_ids"]:
                if oid:
                    at_list += f'<at id="{oid}"></at> '

    content_text = (
        f"今日自动整理出 **{total}** 个团队事项\n"
        f"- 缺少负责人：**{no_owner}** 个\n"
        f"- 存在阻塞风险：**{blocked}** 个\n\n"
        f"请查看{build_bitable_link_text()}。\n"
    )
    if at_list:
        content_text += f"\n相关负责人：{at_list}"

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "新增事项总结"},
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content_text,
                },
            }
        ],
    }


def send_summary(todos: list[dict[str, Any]], mobile: str | None = None) -> bool:
    """Send todo summary card to the project group chat and @ all owners."""
    if not config.feishu_chat_id:
        print("❌ 未配置群聊 ID (FEISHU_CHAT_ID)")
        return False

    card = build_summary_card(todos)
    return send_interactive_card(
        card,
        receive_id=config.feishu_chat_id,
        receive_id_type="chat_id"
    )
