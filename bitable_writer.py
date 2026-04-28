# bitable_writer.py
import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from feishu_client import get_access_token

import json
# 打开 JSON 文件 (指定 utf-8 编码)
with open('mock_data/data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

load_dotenv()

APP_TOKEN = os.getenv("FEISHU_BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("FEISHU_TABLE_ID")

FIELD_NAMES = {
    "title": "待办标题",
    "description": "描述",
    "owner": "负责人",
    "deadline": "截止日期",
    "priority": "优先级",
    "status": "状态",
    "source_type": "来源渠道",
    "source_link": "来源链接",
    "evidence": "原文证据/背景",
}


def build_owner_value(todo: dict):
    owner_open_ids = todo.get("owner_open_ids")
    if owner_open_ids:
        return [{"id": open_id} for open_id in owner_open_ids if open_id]

    owner_open_id = todo.get("owner_open_id")
    if owner_open_id:
        return [{"id": owner_open_id}]

    return None


def todo_to_fields(todo: dict) -> dict:
    """将 Agent 输出的 todo dict 转换为 Bitable 字段格式"""
    fields = {
        FIELD_NAMES["title"]: todo.get("title", "（无标题）"),
        FIELD_NAMES["description"]: todo.get("description", ""),
        FIELD_NAMES["status"]: todo.get("status", "待处理"),
        FIELD_NAMES["priority"]: todo.get("priority", "P2"),
        FIELD_NAMES["source_type"]: todo.get("source_type", ""),
        FIELD_NAMES["evidence"]: todo.get("evidence", ""),
    }

    source_link = todo.get("source_link")
    if source_link:
        source_link_text = todo.get("source_link_text", "查看来源")
        fields[FIELD_NAMES["source_link"]] = {"text": source_link_text, "link": source_link}

    owner_value = build_owner_value(todo)
    if owner_value:
        fields[FIELD_NAMES["owner"]] = owner_value

    deadline = todo.get("deadline")
    if deadline:
        try:
            dt = datetime.strptime(deadline, "%Y-%m-%d")
            fields[FIELD_NAMES["deadline"]] = int(dt.timestamp() * 1000)
        except ValueError:
            pass

    return {k: v for k, v in fields.items() if v not in (None, "", [])}


def batch_write(todos: list[dict]) -> dict:
    """批量写入，返回写入统计"""
    if not APP_TOKEN or not TABLE_ID:
        raise ValueError("缺少 FEISHU_BITABLE_APP_TOKEN 或 FEISHU_TABLE_ID 配置")

    token = get_access_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_create"

    records = [{"fields": todo_to_fields(todo)} for todo in todos]
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"records": records},
    )
    result = resp.json()

    if result.get("code") == 0:
        created = result.get("data", {}).get("records", [])
        print(f"✅ 批量写入成功：{len(created)} 条")
        return {"success": len(created), "failed": 0, "record_ids": [r["record_id"] for r in created]}

    print(f"❌ 批量写入失败: {json.dumps(result, ensure_ascii=False)}")
    return {"success": 0, "failed": len(todos), "error": result}


if __name__ == "__main__":
    mock_todos = data
    batch_write(mock_todos)
