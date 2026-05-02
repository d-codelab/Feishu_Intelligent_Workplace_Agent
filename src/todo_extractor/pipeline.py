"""End-to-end extraction pipeline."""

from typing import Any

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.llm.client import validate_todos


def extract_pipeline(extractor: BaseExtractor, **kwargs) -> dict[str, Any]:
    """Execute the extraction pipeline.

    Args:
        extractor: Extractor instance (FeishuDocExtractor, FeishuIMExtractor, etc.)
        **kwargs: Extractor-specific parameters (e.g., doc_token, chat_id)

    Returns:
        Dictionary with extraction results:
            {
                "success": True/False,
                "todos": [...],
                "count": 5,
                "source_type": "飞书文档",
                "validation_issues": [...]  # Empty if valid
            }
    """
    try:
        # Step 1: Extract todos
        todos = extractor.extract(**kwargs)

        # Step 2: Validate extracted todos
        validation_issues = validate_todos(todos)

        if validation_issues:
            print("⚠️  发现验证问题：")
            for issue in validation_issues:
                print(f"  - {issue}")

        return {
            "success": True,
            "todos": todos,
            "count": len(todos),
            "source_type": extractor.source_type,
            "validation_issues": validation_issues,
        }

    except Exception as e:
        print(f"❌ 抽取流程失败：{e}")
        return {
            "success": False,
            "error": str(e),
            "todos": [],
            "count": 0,
            "source_type": extractor.source_type,
            "validation_issues": [],
        }
