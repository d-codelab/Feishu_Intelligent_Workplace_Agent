import json
import os
from datetime import datetime

import lark_oapi as lark
from dotenv import load_dotenv
from lark_oapi.api.bitable.v1 import *

from feishu_client import get_access_token

load_dotenv()

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


def build_fields(todo: dict) -> dict:
    fields = {
        FIELD_NAMES["title"]: todo["title"],
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

    if todo.get("deadline"):
        dt = datetime.strptime(todo["deadline"], "%Y-%m-%d")
        fields[FIELD_NAMES["deadline"]] = int(dt.timestamp() * 1000)

    return {k: v for k, v in fields.items() if v not in (None, "")}


def build_request_option() -> lark.RequestOption:
    tenant_access_token = get_access_token()
    return lark.RequestOption.builder().tenant_access_token(tenant_access_token).build()


def write_todo(app_token: str, table_id: str, todo: dict):
    client = lark.Client.builder() \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    request: CreateAppTableRecordRequest = CreateAppTableRecordRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .request_body(AppTableRecord.builder().fields(build_fields(todo)).build()) \
        .build()

    option = build_request_option()
    response: CreateAppTableRecordResponse = client.bitable.v1.app_table_record.create(request, option)

    if not response.success():
        raw = response.raw.content.decode("utf-8") if isinstance(response.raw.content, bytes) else response.raw.content
        print("写入失败：")
        print(f"code={response.code}, msg={response.msg}, log_id={response.get_log_id()}")
        try:
            print(json.dumps(json.loads(raw), indent=2, ensure_ascii=False))
        except Exception:
            print(raw)
        return None

    record_id = response.data.record.record_id
    print(f"✅ 写入成功！record_id: {record_id}")
    return record_id


if __name__ == "__main__":
    app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
    table_id = os.getenv("FEISHU_TABLE_ID")

    if not app_token or not table_id:
        raise ValueError("缺少 FEISHU_BITABLE_APP_TOKEN 或 FEISHU_TABLE_ID 配置")

    test_todo = {
        "title": "优化移动端首页加载速度",
        "description": "针对弱网环境下的首屏渲染进行专项优化，目标是将加载时间缩短30%",
        "owner_open_id": "ou_e128bfd18f90e64471a0b5d2bfb56ff8",
        "deadline": "2026-05-05",
        "status": "待处理",
        "priority": "P1",
        "source_type": "产品需求",
        "source_link": "https://open.feishu.cn/document/home/index",
        "source_link_text": "飞书开放平台文档",
        "evidence": "性能分析工具截图"
    }

    write_todo(app_token, table_id, test_todo)
