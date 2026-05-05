"""LLM client for todo extraction."""

import json
from typing import Any

from openai import OpenAI

from todo_extractor.llm.prompts import (
    CHAT_TODO_EXTRACTION_PROMPT,
    COARSE_EXTRACTION_PROMPT,
    REFINE_EXTRACTION_PROMPT,
    SYSTEM_PROMPT,
    TODO_EXTRACTION_PROMPT,
)

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
    if source_type in ["群消息", "群聊消息"]:
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

            # Validate and set default confidence if missing
            if "置信度" not in item or item["置信度"] is None:
                item["置信度"] = 0.5  # Default to medium confidence
            else:
                # Ensure confidence is a float between 0 and 1
                try:
                    confidence = float(item["置信度"])
                    item["置信度"] = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    item["置信度"] = 0.5

            # Auto-detect fields needing confirmation
            need_confirm = []
            if item.get("负责人") in ["待确认", "", None]:
                need_confirm.append("负责人")
            if item.get("截止时间") in ["待确认", "尽快", "", None]:
                need_confirm.append("截止时间")
            if item.get("当前状态") == "待确认":
                need_confirm.append("状态")

            item["待确认项"] = need_confirm

        # Filter out low confidence items (optional: can be configured)
        # For now, we keep all items but log a warning for low confidence ones
        low_confidence_count = sum(1 for item in items if item["置信度"] < 0.5)
        if low_confidence_count > 0:
            print(f"⚠️  发现 {low_confidence_count} 条低置信度事项（< 0.5），建议人工确认")

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

        # Validate confidence score
        if "置信度" in item:
            try:
                confidence = float(item["置信度"])
                if not (0.0 <= confidence <= 1.0):
                    issues.append(f"第 {idx+1} 条事项置信度超出范围 [0, 1]: {confidence}")
            except (ValueError, TypeError):
                issues.append(f"第 {idx+1} 条事项置信度格式错误: {item['置信度']}")

    return issues


def coarse_extract_todos(text: str, source_type: str = "会议纪要") -> list[dict[str, Any]]:
    """粗抽取阶段：宽松模式，尽可能多地抽取潜在TODO事项。

    Args:
        text: 输入文本（文档块、会议纪要等）
        source_type: 来源类型标签

    Returns:
        粗抽取的TODO事项列表（可能包含噪声）

    Raises:
        RuntimeError: 抽取失败时抛出
    """
    client = OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_API_BASE
    )

    prompt = COARSE_EXTRACTION_PROMPT.format(input_text=text)

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

        # Clean markdown code blocks
        if raw_output.startswith("```json"):
            raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output.replace("```", "").strip()

        result = json.loads(raw_output)

        # Handle different output formats
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict) and "items" in result:
            items = result["items"]
        else:
            raise RuntimeError(f"意外的 LLM 输出格式: {type(result)}")

        # Post-process
        for item in items:
            item["来源类型"] = source_type

            # Validate confidence
            if "置信度" not in item or item["置信度"] is None:
                item["置信度"] = 0.5
            else:
                try:
                    confidence = float(item["置信度"])
                    item["置信度"] = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    item["置信度"] = 0.5

        print(f"✅ 粗抽取成功：{len(items)} 条候选事项")
        return items

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}")
        print(f"原始输出：{raw_output[:200]}")
        raise RuntimeError(f"JSON 解析失败: {e}")

    except Exception as e:
        print(f"❌ 粗抽取失败：{e}")
        raise RuntimeError(f"粗抽取失败: {e}")


def refine_todos_batch(todos: list[dict[str, Any]], batch_size: int = 20) -> list[dict[str, Any]]:
    """精筛选阶段：严格判断，过滤噪声，保留高质量TODO事项。

    Args:
        todos: 粗抽取的TODO事项列表
        batch_size: 每批处理的事项数量

    Returns:
        精筛选后的高质量TODO事项列表

    Raises:
        RuntimeError: 筛选失败时抛出
    """
    if not todos:
        return []

    client = OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_API_BASE
    )

    refined_items = []

    # Process in batches
    for i in range(0, len(todos), batch_size):
        batch = todos[i:i + batch_size]
        batch_json = json.dumps(batch, ensure_ascii=False, indent=2)

        prompt = REFINE_EXTRACTION_PROMPT.format(candidates=batch_json)

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

            # Clean markdown code blocks
            if raw_output.startswith("```json"):
                raw_output = raw_output.replace("```json", "").replace("```", "").strip()
            elif raw_output.startswith("```"):
                raw_output = raw_output.replace("```", "").strip()

            result = json.loads(raw_output)

            # Handle different output formats
            if isinstance(result, list):
                batch_refined = result
            elif isinstance(result, dict) and "items" in result:
                batch_refined = result["items"]
            else:
                raise RuntimeError(f"意外的 LLM 输出格式: {type(result)}")

            # Post-process
            for item in batch_refined:
                # Validate confidence
                if "置信度" not in item or item["置信度"] is None:
                    item["置信度"] = 0.5
                else:
                    try:
                        confidence = float(item["置信度"])
                        item["置信度"] = max(0.0, min(1.0, confidence))
                    except (ValueError, TypeError):
                        item["置信度"] = 0.5

                # Auto-detect fields needing confirmation
                need_confirm = []
                if item.get("负责人") in ["待确认", "", None]:
                    need_confirm.append("负责人")
                if item.get("截止时间") in ["待确认", "尽快", "", None]:
                    need_confirm.append("截止时间")
                if item.get("当前状态") == "待确认":
                    need_confirm.append("状态")

                item["待确认项"] = need_confirm

            refined_items.extend(batch_refined)
            print(f"✅ 批次 {i//batch_size + 1} 精筛选完成：{len(batch)} → {len(batch_refined)} 条")

        except json.JSONDecodeError as e:
            print(f"❌ 批次 {i//batch_size + 1} JSON 解析失败：{e}")
            print(f"原始输出：{raw_output[:200]}")
            # Continue with next batch instead of failing completely
            continue

        except Exception as e:
            print(f"❌ 批次 {i//batch_size + 1} 精筛选失败：{e}")
            # Continue with next batch
            continue

    print(f"✅ 精筛选完成：{len(todos)} → {len(refined_items)} 条高质量事项")
    return refined_items


def semantic_dedup(todos: list[dict[str, Any]], threshold: float = 0.85) -> list[dict[str, Any]]:
    """语义去重：使用中文 Embedding 模型计算语义相似度。

    优先使用 text2vec-base-chinese 模型，如果不可用则降级为规则去重。

    Args:
        todos: TODO事项列表
        threshold: 相似度阈值（0-1），超过此值视为重复

    Returns:
        去重后的TODO事项列表
    """
    if len(todos) <= 1:
        return todos

    try:
        # 尝试使用 Embedding 模型
        from todo_extractor.utils.semantic_dedup import semantic_dedup_todos

        print(f"[去重] 使用 Embedding 模型进行语义去重...")
        return semantic_dedup_todos(todos, threshold=threshold)

    except ImportError:
        print("[警告] semantic_dedup 模块不可用，降级为规则去重")
        return _rule_based_dedup(todos, threshold)

    except Exception as e:
        print(f"[警告] Embedding 去重失败: {e}，降级为规则去重")
        return _rule_based_dedup(todos, threshold)


def _rule_based_dedup(todos: list[dict[str, Any]], threshold: float = 0.85) -> list[dict[str, Any]]:
    """规则去重：使用文本相似度算法（降级方案）

    Args:
        todos: TODO事项列表
        threshold: 相似度阈值

    Returns:
        去重后的TODO事项列表
    """
    from difflib import SequenceMatcher

    def text_similarity(text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()

    print(f"[去重] 正在对 {len(todos)} 条事项进行规则去重...")

    # 标记要保留的索引
    keep_indices = set(range(len(todos)))
    merged_count = 0

    for i in range(len(todos)):
        if i not in keep_indices:
            continue

        for j in range(i + 1, len(todos)):
            if j not in keep_indices:
                continue

            todo_i = todos[i]
            todo_j = todos[j]

            # 计算标题相似度
            title_sim = text_similarity(
                todo_i.get('事项标题', ''),
                todo_j.get('事项标题', '')
            )

            # 计算描述相似度
            desc_sim = text_similarity(
                todo_i.get('事项描述', ''),
                todo_j.get('事项描述', '')
            )

            # 检查负责人是否相同
            same_owner = (
                todo_i.get('负责人') == todo_j.get('负责人') and
                todo_i.get('负责人') not in ['待确认', '', None]
            )

            # 判断是否重复
            is_duplicate = False

            # 规则1: 标题完全相同 + 负责人相同
            if title_sim == 1.0 and same_owner:
                is_duplicate = True

            # 规则2: 标题高度相似 + 负责人相同
            elif title_sim >= threshold and same_owner:
                is_duplicate = True

            # 规则3: 标题和描述都相似 + 负责人相同
            elif title_sim >= 0.7 and desc_sim >= 0.7 and same_owner:
                is_duplicate = True

            # 规则4: 标题高度相似，即使负责人不同（可能是同一任务）
            elif title_sim >= 0.9:
                is_duplicate = True

            if is_duplicate:
                # 保留置信度更高的
                conf_i = todo_i.get('置信度', 0.5)
                conf_j = todo_j.get('置信度', 0.5)

                if conf_j > conf_i:
                    # 保留 j，移除 i
                    keep_indices.discard(i)
                    merged_count += 1
                    break
                else:
                    # 保留 i，移除 j
                    keep_indices.discard(j)
                    merged_count += 1

    result = [todos[i] for i in sorted(keep_indices)]
    print(f"[成功] 规则去重完成：{len(todos)} -> {len(result)} 条（合并 {merged_count} 条重复）")
    return result
