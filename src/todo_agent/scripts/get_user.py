"""
Script to test retrieving open_id from mention_user elements in a Feishu Docx document.
Usage: python src/todo_agent/scripts/get_user.py <document_id>
"""

import sys
import json
import requests
from todo_agent.clients.auth import get_access_token
from todo_agent.config import config

def find_mention_user(data, path=""):
    """Recursively search for mention_user in block data."""
    if isinstance(data, dict):
        if "mention_user" in data:
            print(f"\nFound at {path + '.mention_user' if path else 'mention_user'}:")
            mention_data = data["mention_user"]
            print(json.dumps(mention_data, indent=2, ensure_ascii=False))
            print(f"-> user_id (usually open_id): {mention_data.get('user_id')}")
        for k, v in data.items():
            find_mention_user(v, f"{path}.{k}" if path else k)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            find_mention_user(item, f"{path}[{i}]")

def test_get_mention_user(document_id: str):
    try:
        token = get_access_token()
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return

    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    print(f"Fetching blocks for document: {document_id}")
    params = {"page_size": 500}

    response = requests.get(url, headers=headers, params=params, timeout=config.request_timeout)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != 0:
        print(f"API Error: {data}")
        return

    blocks = data.get("data", {}).get("items", [])
    print(f"Found {len(blocks)} blocks. Searching for mention_user...")

    find_mention_user(blocks)

def test_get_comments(file_token: str):
    """
    Test retrieving comment users' open_id from a document.
    """
    try:
        token = get_access_token()
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return

    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/comments"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"\nFetching comments for file: {file_token}")
    params = {"file_type": "docx"}

    response = requests.get(url, headers=headers, params=params, timeout=config.request_timeout)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != 0:
        print(f"API Error (comments): {data}")
        return

    comments = data.get("data", {}).get("items", [])
    print(f"Found {len(comments)} comments.")

    for comment in comments:
        open_id = comment.get("user_id")
        print(f"Comment by Open ID: {open_id}")

if __name__ == "__main__":
    doc_id = 'ZbGXd6ykno87XSxxuaUcJQnCnmb'
    if doc_id:
        test_get_mention_user(doc_id)
        # test_get_comments(doc_id)
    else:
        print("document_id cannot be empty.")
