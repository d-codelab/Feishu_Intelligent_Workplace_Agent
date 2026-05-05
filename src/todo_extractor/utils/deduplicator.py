"""TODO item deduplication module."""

from typing import List, Dict, Any
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing spaces and converting to lowercase."""
    if not text:
        return ""
    return text.replace(" ", "").replace("\n", "").lower()


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher.

    Returns:
        float: Similarity score between 0 and 1
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    if not norm1 or not norm2:
        return 0.0

    return SequenceMatcher(None, norm1, norm2).ratio()


def deduplicate_todos(
    todos: List[Dict[str, Any]],
    title_threshold: float = 0.85,
    keep_higher_confidence: bool = True
) -> List[Dict[str, Any]]:
    """Deduplicate TODO items based on title similarity and assignee.

    Args:
        todos: List of TODO items to deduplicate
        title_threshold: Similarity threshold for title matching (0-1)
        keep_higher_confidence: If True, keep the item with higher confidence when duplicates are found

    Returns:
        List of deduplicated TODO items

    Deduplication rules:
        1. Same assignee + highly similar title (>= threshold) → duplicate
        2. When duplicates found:
           - If keep_higher_confidence=True: keep the one with higher confidence
           - Otherwise: keep the first occurrence
    """
    if not todos:
        return []

    # Track which items to keep
    keep_indices = set(range(len(todos)))

    # Compare each pair of items
    for i in range(len(todos)):
        if i not in keep_indices:
            continue

        item1 = todos[i]
        assignee1 = item1.get("负责人", "")
        title1 = item1.get("事项标题", "")
        confidence1 = item1.get("置信度", 0.5)

        for j in range(i + 1, len(todos)):
            if j not in keep_indices:
                continue

            item2 = todos[j]
            assignee2 = item2.get("负责人", "")
            title2 = item2.get("事项标题", "")
            confidence2 = item2.get("置信度", 0.5)

            # Rule 1: Same assignee (skip if either is "待确认")
            if assignee1 in ["待确认", "", None] or assignee2 in ["待确认", "", None]:
                continue

            if normalize_text(assignee1) != normalize_text(assignee2):
                continue

            # Rule 2: Highly similar title
            similarity = calculate_similarity(title1, title2)
            if similarity >= title_threshold:
                # Found duplicate - decide which one to remove
                if keep_higher_confidence:
                    # Remove the one with lower confidence
                    if confidence1 >= confidence2:
                        keep_indices.discard(j)
                        print(f"🔄 去重：移除重复事项 #{j+1} (置信度 {confidence2:.2f}) - 与 #{i+1} (置信度 {confidence1:.2f}) 相似度 {similarity:.2f}")
                    else:
                        keep_indices.discard(i)
                        print(f"🔄 去重：移除重复事项 #{i+1} (置信度 {confidence1:.2f}) - 与 #{j+1} (置信度 {confidence2:.2f}) 相似度 {similarity:.2f}")
                        break  # Item i is removed, no need to continue comparing it
                else:
                    # Keep first occurrence
                    keep_indices.discard(j)
                    print(f"🔄 去重：移除重复事项 #{j+1} - 与 #{i+1} 相似度 {similarity:.2f}")

    # Return deduplicated items
    result = [todos[i] for i in sorted(keep_indices)]

    removed_count = len(todos) - len(result)
    if removed_count > 0:
        print(f"✅ 去重完成：移除 {removed_count} 条重复事项，保留 {len(result)} 条")

    return result


def merge_duplicate_info(item1: Dict[str, Any], item2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge information from two duplicate items (advanced feature, not used in basic deduplication).

    This function can be used to combine information from duplicate items instead of simply discarding one.
    For example, merge "原文依据" from both items, or combine "风险/阻塞" information.

    Args:
        item1: First TODO item
        item2: Second TODO item (duplicate of item1)

    Returns:
        Merged TODO item
    """
    merged = item1.copy()

    # Merge "原文依据" - combine evidence from both items
    evidence1 = item1.get("原文依据", "")
    evidence2 = item2.get("原文依据", "")
    if evidence1 and evidence2 and evidence1 != evidence2:
        merged["原文依据"] = f"{evidence1}\n---\n{evidence2}"

    # Merge "风险/阻塞" - combine risk information
    risk1 = item1.get("风险/阻塞", "")
    risk2 = item2.get("风险/阻塞", "")
    if risk1 and risk2 and risk1 != risk2:
        merged["风险/阻塞"] = f"{risk1}；{risk2}"
    elif risk2 and not risk1:
        merged["风险/阻塞"] = risk2

    # Use the higher confidence score
    merged["置信度"] = max(item1.get("置信度", 0.5), item2.get("置信度", 0.5))

    return merged
