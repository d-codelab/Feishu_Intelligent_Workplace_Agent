"""Compatibility entrypoint for Feishu authentication.

Prefer importing from ``todo_agent.clients.auth`` in new code.
"""

from todo_agent.clients.auth import get_access_token


if __name__ == "__main__":
    token = get_access_token()
    print(f"token: {token[:20]}...")
