import json
import os

import lark_oapi as lark
from dotenv import load_dotenv
from lark_oapi.api.bitable.v1 import *

from feishu_client import get_access_token

load_dotenv()


def get_fields():
    token = get_access_token()
    app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
    table_id = os.getenv("FEISHU_TABLE_ID")

    if not app_token or not table_id:
        raise ValueError("缺少 FEISHU_BITABLE_APP_TOKEN 或 FEISHU_TABLE_ID 配置")

    client = lark.Client.builder() \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    request: ListAppTableFieldRequest = ListAppTableFieldRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .build()

    option = lark.RequestOption.builder().tenant_access_token(token).build()
    response: ListAppTableFieldResponse = client.bitable.v1.app_table_field.list(request, option)

    if not response.success():
        raw = response.raw.content.decode("utf-8") if isinstance(response.raw.content, bytes) else response.raw.content
        print("字段查询失败：")
        print(f"code={response.code}, msg={response.msg}, log_id={response.get_log_id()}")
        try:
            print(json.dumps(json.loads(raw), indent=4, ensure_ascii=False))
        except Exception:
            print(raw)
        return

    items = response.data.items or []
    print("字段名 → field_id 映射：")
    for field in items:
        print(f"  '{field.field_name}': '{field.field_id}'")


if __name__ == "__main__":
    get_fields()
