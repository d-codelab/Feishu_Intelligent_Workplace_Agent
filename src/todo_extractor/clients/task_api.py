"""Feishu Task API helpers."""

import requests
from datetime import datetime
from typing import List, Dict

# ========== 配置信息 ==========
USER_TOKEN = "u-cBQu3Q3hV9JrwTehhsg5t.l45leghlqjWOGa2Ag005RI"
REQUEST_TIMEOUT = 10
# ==============================


def get_tasks_all(token: str, max_count: int = 200) -> List[Dict]:
    """Get all tasks with pagination.

    Args:
        token: User access token
        max_count: Maximum number of tasks to fetch

    Returns:
        List of tasks

    Raises:
        RuntimeError: If request fails
    """
    all_tasks = []
    page_token = None

    while len(all_tasks) < max_count:
        page_size = min(50, max_count - len(all_tasks))
        url = "https://open.feishu.cn/open-apis/task/v2/tasks"
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token

        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 0:
            raise RuntimeError(f"获取任务失败: {result}")

        data = result.get("data", {})
        items = data.get("items", [])
        all_tasks.extend(items)

        if not data.get("has_more"):
            break
        page_token = data.get("page_token")

    print(f"✅ 获取到 {len(all_tasks)} 个任务")
    return all_tasks


def convert_task_to_todo(task: Dict) -> Dict:
    """Convert Feishu task to todo item format.

    Args:
        task: Task dict from API

    Returns:
        Todo item dict matching the required schema
    """
    # Extract basic info
    summary = task.get("summary", "")
    description = task.get("description", "")
    guid = task.get("guid", "")
    url = task.get("url", "")

    # Extract assignees (deduplicate by id)
    members = task.get("members", [])
    assignee_dict = {}
    for m in members:
        if m.get("role") == "assignee":
            member_id = m.get("id")
            if member_id and member_id not in assignee_dict:
                # assignee_dict[member_id] = m.get("name", "")  # assignee_dict[member_id] = member_id
                assignee_dict[member_id] = member_id

    assignee_names = list(assignee_dict.values())
    owner = ", ".join(assignee_names) if assignee_names else None

    # Extract start time
    start = task.get("start", {})
    start_time = None
    if start and start.get("timestamp"):
        try:
            start_dt = datetime.fromtimestamp(int(start.get("timestamp")) / 1000)
            if start.get("is_all_day"):
                start_time = start_dt.strftime("%Y-%m-%d")
            else:
                start_time = start_dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass

    # Extract due time
    due = task.get("due", {})
    deadline = None
    if due and due.get("timestamp"):
        try:
            due_dt = datetime.fromtimestamp(int(due.get("timestamp")) / 1000)
            if due.get("is_all_day"):
                deadline = due_dt.strftime("%Y-%m-%d")
            else:
                deadline = due_dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass

    # Determine status
    status_map = {
        "todo": "待开始",
        "doing": "进行中",
        "done": "已完成"
    }
    api_status = task.get("status", "todo")
    completed_at = task.get("completed_at")

    if completed_at and completed_at != "0":
        status = "已完成"
    else:
        status = status_map.get(api_status, "待开始")

    # Extract priority from custom fields
    priority = None
    custom_fields = task.get("custom_fields", [])
    for field in custom_fields:
        field_name = field.get("name", "")
        if "优先级" in field_name or "priority" in field_name.lower():
            # Try different value types
            if field.get("text_value"):
                priority = field.get("text_value")
            elif field.get("single_select_value"):
                priority = field.get("single_select_value")
            break

    # Build todo item with Chinese field names
    todo = {
        "事项标题": summary or "无标题",
        "事项描述": description or summary or "无描述",
        "负责人": owner,
        "开始时间": start_time,
        "截止时间": deadline,
        "当前状态": status,
        "优先级": priority,
        "来源类型": "飞书任务",
        "来源链接": url or f"任务ID: {guid}",
        "原文依据": "无",  # Tasks don't need evidence
        "风险/阻塞": None,
        "待确认项": []
    }

    # Mark fields that need confirmation
    if not owner:
        todo["待确认项"].append("负责人")
    if not deadline:
        todo["待确认项"].append("截止时间")
    if not start_time:
        todo["待确认项"].append("开始时间")

    return todo
