"""Runtime configuration for the todo agent project.

All environment-variable access is centralized here so service modules do not
need to know how configuration is loaded.
"""

import os
import json
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
print(f"Project root directory: {PROJECT_ROOT}")  # Debug log to verify path resolution
MOCK_DATA_DIR = PROJECT_ROOT / "mock_data"
DEFAULT_MOCK_TODOS_PATH = MOCK_DATA_DIR / "data.json"
FALLBACK_MOCK_TODOS_PATH = MOCK_DATA_DIR / "todo_result_feishu_doc.json"
TARGET_DOCS_PATH = MOCK_DATA_DIR / "target_docs.json"


@dataclass(frozen=True)
class FeishuConfig:
    """Feishu-related runtime configuration."""

    app_id: str | None = os.getenv("FEISHU_APP_ID")
    app_secret: str | None = os.getenv("FEISHU_APP_SECRET")
    bitable_app_token: str | None = os.getenv("FEISHU_BITABLE_APP_TOKEN")
    bitable_table_id: str | None = os.getenv("FEISHU_BITABLE_TABLE_ID")
    user_access_token: str | None = os.getenv("FEISHU_USER_ACCESS_TOKEN")
    feishu_chat_id: str | None = os.getenv("FEISHU_CHAT_ID")
    request_timeout: int = int(os.getenv("FEISHU_REQUEST_TIMEOUT", "10"))
    doc_token: str | None = os.getenv("FEISHU_DOC_TOKEN")
    target_docs: list[dict[str, str]] = None

    def __post_init__(self):
        # Load target docs for scheduled tasks from json file
        try:
            with open(TARGET_DOCS_PATH, 'r', encoding='utf-8') as f:
                docs = json.load(f)
                object.__setattr__(self, 'target_docs', docs)
        except Exception as e:
            print(f"Warning: Failed to load target docs from {TARGET_DOCS_PATH}: {e}")
            object.__setattr__(self, 'target_docs', [])

    def require_app_credentials(self) -> tuple[str, str]:
        """Return app credentials or raise when missing."""
        if not self.app_id or not self.app_secret:
            raise ValueError("缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET 配置")
        return self.app_id, self.app_secret

    def require_bitable_config(self) -> tuple[str, str]:
        """Return Bitable app token and table ID or raise when missing."""
        if not self.bitable_app_token or not self.bitable_table_id:
            raise ValueError("缺少 FEISHU_BITABLE_APP_TOKEN 或 FEISHU_BITABLE_TABLE_ID 配置")
        return self.bitable_app_token, self.bitable_table_id

    def require_user_access_token(self) -> str:
        """Return user access token or raise when missing."""
        if not self.user_access_token:
            raise ValueError("缺少 FEISHU_USER_ACCESS_TOKEN 配置")
        return self.user_access_token


config = FeishuConfig()
