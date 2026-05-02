"""LLM client for todo extraction."""

import json
from typing import Any

from openai import OpenAI

from todo_extractor.llm.prompts import TODO_EXTRACTION_PROMPT, CHAT_TODO_EXTRACTION_PROMPT, SYSTEM_PROMPT

# ========== 配置信息 ==========
LLM_MODEL = "ep-20260423223132-gxqgd"
LLM_API_KEY = "ark-d61ab9da-a6f4-4a5e-94b3-c1ca9c4874eb-0f8ce"
LLM_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
LLM_TEMPERATURE = 0.1
LLM_REQUEST_TIMEOUT = 180
# ==============================


def extract_todos_by_llm(text: str, source_type: str = "会议纪要") -> list[dict[str, Any]]:
    """Extract todo items from text using LLM.

    Args:
        text: Input text (meeting notes, documents, chat logs, etc.)
        source_type: Source type label

    Returns:
        List of extracted todo items

    Raises:
        RuntimeError: If extraction fails
    """
    client = OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_API_BASE
    )

    # Choose prompt based on source type
    if source_type == "群消息":
        prompt_template = CHAT_TODO_EXTRACTION_PROMPT
    else:
        prompt_template = TODO_EXTRACTION_PROMPT

    prompt = prompt_template.format(input_text=text)

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE,
            timeout=LLM_REQUEST_TIMEOUT,
        )

        raw_output = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if raw_output.startswith("```json"):
            raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output.replace("```", "").strip()

        result = json.loads(raw_output)

        # Handle case where LLM returns array directly
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict) and "items" in result:
            items = result["items"]
        else:
            raise RuntimeError(f"意外的 LLM 输出格式: {type(result)}")

        # Post-process: add source_type and detect fields needing confirmation
        for item in items:
            item["来源类型"] = source_type

            # Auto-detect fields needing confirmation
            need_confirm = []
            if item.get("负责人") in ["待确认", "", None]:
                need_confirm.append("负责人")
            if item.get("截止时间") in ["待确认", "尽快", "", None]:
                need_confirm.append("截止时间")
            if item.get("当前状态") == "待确认":
                need_confirm.append("状态")

            item["待确认项"] = need_confirm

        print(f"✅ LLM 抽取成功：{len(items)} 条事项")
        return items

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}")
        print(f"原始输出：{raw_output[:200]}")
        raise RuntimeError(f"JSON 解析失败: {e}")

    except Exception as e:
        print(f"❌ LLM 抽取失败：{e}")
        raise RuntimeError(f"LLM 抽取失败: {e}")


def validate_todos(items: list[dict[str, Any]]) -> list[str]:
    """Validate extracted todo items.
 
    Args:
        items: List of todo items

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    required_fields = [
        "事项标题", "事项描述", "负责人", "截止时间",
        "当前状态", "优先级", "来源类型", "原文依据"
    ]

    for idx, item in enumerate(items):
        for field in required_fields:
            if field not in item:
                issues.append(f"第 {idx+1} 条事项缺少字段：{field}")

        # Check if evidence is empty
        if not item.get("原文依据", "").strip():
            issues.append(f"第 {idx+1} 条事项缺少原文依据")

    return issues
