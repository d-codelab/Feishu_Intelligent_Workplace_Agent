"""Integration layer: connects todo_extractor with todo_agent.

This module bridges the extraction pipeline (todo_extractor) with the
processing pipeline (todo_agent), enabling end-to-end automation.
"""

import sys
from pathlib import Path
from typing import Optional, Dict

# Add src to path to import both packages
sys.path.insert(0, str(Path(__file__).parent / "src"))

from todo_extractor.extractors.feishu_doc import FeishuDocExtractor
from todo_extractor.extractors.feishu_im import FeishuIMExtractor
from todo_extractor.extractors.feishu_calendar import FeishuCalendarExtractor
from todo_extractor.extractors.feishu_task import FeishuTaskExtractor
from todo_extractor.extractors.feishu_minutes import FeishuMinutesExtractor
from todo_extractor.pipeline import extract_pipeline
from todo_agent.services.pipeline import run_pipeline


def extract_and_process_doc(doc_token: str, mobile: Optional[str] = None) -> Dict:
    """Extract todos from a Feishu document and process them.

    Args:
        doc_token: Feishu document token
        mobile: Mobile number for notification (optional)

    Returns:
        Dictionary with results:
            {
                "extracted": 5,
                "written": 5,
                "notified": True,
                "validation_issues": [...]
            }
    """
    print("=" * 60)
    print("📄 飞书文档 Todo 抽取与处理")
    print("=" * 60)

    # Step 1: Extract todos from document
    extractor = FeishuDocExtractor()
    extract_result = extract_pipeline(extractor, doc_token=doc_token)

    if not extract_result["success"]:
        return {
            "error": extract_result["error"],
            "extracted": 0,
            "written": 0,
            "notified": False,
        }

    todos = extract_result["todos"]
    print(f"\n✅ 抽取完成：{extract_result['count']} 条事项")

    if not todos:
        print("⚠️  没有可处理的事项")
        return {
            "extracted": 0,
            "written": 0,
            "notified": False,
            "validation_issues": extract_result["validation_issues"],
        }

    # Step 2: Process todos (write to Bitable + send notification)
    print("\n" + "=" * 60)
    print("📊 写入多维表格并发送通知")
    print("=" * 60)

    process_result = run_pipeline(todos, mobile=mobile)

    print("\n" + "=" * 60)
    print("✅ 流程完成")
    print("=" * 60)

    return {
        "extracted": extract_result["count"],
        "written": process_result["write_success"],
        "notified": process_result["summary_sent"],
        "validation_issues": extract_result["validation_issues"],
    }


def extract_and_process_chat(
    chat_id: str,
    hours: int = 24,
    mobile: Optional[str] = None
) -> Dict:
    """Extract todos from Feishu group chat and process them.

    Args:
        chat_id: Feishu chat ID
        hours: Number of hours to look back (default: 24)
        mobile: Mobile number for notification (optional)

    Returns:
        Dictionary with results:
            {
                "extracted": 3,
                "written": 3,
                "notified": True,
                "validation_issues": [...]
            }
    """
    print("=" * 60)
    print(f"💬 群消息 Todo 抽取与处理（最近 {hours} 小时）")
    print("=" * 60)

    # Step 1: Extract todos from chat
    extractor = FeishuIMExtractor()
    extract_result = extract_pipeline(extractor, chat_id=chat_id, hours=hours)

    if not extract_result["success"]:
        return {
            "error": extract_result["error"],
            "extracted": 0,
            "written": 0,
            "notified": False,
        }

    todos = extract_result["todos"]
    print(f"\n✅ 抽取完成：{extract_result['count']} 条事项")

    if not todos:
        print("⚠️  没有可处理的事项")
        return {
            "extracted": 0,
            "written": 0,
            "notified": False,
            "validation_issues": extract_result["validation_issues"],
        }

    # Step 2: Process todos (write to Bitable + send notification)
    print("\n" + "=" * 60)
    print("📊 写入多维表格并发送通知")
    print("=" * 60)

    process_result = run_pipeline(todos, mobile=mobile)

    print("\n" + "=" * 60)
    print("✅ 流程完成")
    print("=" * 60)

    return {
        "extracted": extract_result["count"],
        "written": process_result["write_success"],
        "notified": process_result["summary_sent"],
        "validation_issues": extract_result["validation_issues"],
    }


def extract_and_process_calendar(
    days: int = 7,
    calendar_id: Optional[str] = None,
    mobile: Optional[str] = None
) -> Dict:
    """Extract todos from Feishu calendar and process them.

    Args:
        days: Number of days to look ahead (default: 7)
        calendar_id: Calendar ID (uses primary calendar if not provided)
        mobile: Mobile number for notification (optional)

    Returns:
        Dictionary with results:
            {
                "extracted": 4,
                "written": 4,
                "notified": True,
                "validation_issues": [...]
            }
    """
    print("=" * 60)
    print(f"📅 日历 Todo 抽取与处理（接下来 {days} 天）")
    print("=" * 60)

    # Step 1: Extract todos from calendar
    extractor = FeishuCalendarExtractor()
    extract_result = extract_pipeline(extractor, calendar_id=calendar_id, days=days)

    if not extract_result["success"]:
        return {
            "error": extract_result["error"],
            "extracted": 0,
            "written": 0,
            "notified": False,
        }

    todos = extract_result["todos"]
    print(f"\n✅ 抽取完成：{extract_result['count']} 条事项")

    if not todos:
        print("⚠️  没有可处理的事项")
        return {
            "extracted": 0,
            "written": 0,
            "notified": False,
            "validation_issues": extract_result["validation_issues"],
        }

    # Step 2: Process todos (write to Bitable + send notification)
    print("\n" + "=" * 60)
    print("📊 写入多维表格并发送通知")
    print("=" * 60)

    process_result = run_pipeline(todos, mobile=mobile)

    print("\n" + "=" * 60)
    print("✅ 流程完成")
    print("=" * 60)

    return {
        "extracted": extract_result["count"],
        "written": process_result["write_success"],
        "notified": process_result["summary_sent"],
        "validation_issues": extract_result["validation_issues"],
    }


def extract_and_process_task(
    max_count: int = 200,
    mobile: Optional[str] = None
) -> Dict:
    """Extract todos from Feishu tasks and process them.

    Args:
        max_count: Maximum number of tasks to fetch (default: 200)
        mobile: Mobile number for notification (optional)

    Returns:
        Dictionary with results:
            {
                "extracted": 5,
                "written": 5,
                "notified": True,
                "validation_issues": [...]
            }
    """
    print("=" * 60)
    print(f"📋 任务 Todo 抽取与处理（最多 {max_count} 个）")
    print("=" * 60)

    # Step 1: Extract todos from tasks
    extractor = FeishuTaskExtractor()
    extract_result = extract_pipeline(extractor, max_count=max_count)

    if not extract_result["success"]:
        return {
            "error": extract_result["error"],
            "extracted": 0,
            "written": 0,
            "notified": False,
        }

    todos = extract_result["todos"]
    print(f"\n✅ 抽取完成：{extract_result['count']} 条事项")

    if not todos:
        print("⚠️  没有可处理的事项")
        return {
            "extracted": 0,
            "written": 0,
            "notified": False,
            "validation_issues": extract_result["validation_issues"],
        }

    # Step 2: Process todos (write to Bitable + send notification)
    print("\n" + "=" * 60)
    print("📊 写入多维表格并发送通知")
    print("=" * 60)

    process_result = run_pipeline(todos, mobile=mobile)

    print("\n" + "=" * 60)
    print("✅ 流程完成")
    print("=" * 60)

    return {
        "extracted": extract_result["count"],
        "written": process_result["write_success"],
        "notified": process_result["summary_sent"],
        "validation_issues": extract_result["validation_issues"],
    }


def extract_and_process_minutes(
    minute_token: str,
    mobile: Optional[str] = None
) -> Dict:
    """Extract todos from Feishu Minutes (妙记) and process them.

    Args:
        minute_token: Minutes token (from URL, e.g., obcnb4r7575w2m39416cvaj3)
        mobile: Mobile number for notification (optional)

    Returns:
        Dictionary with results:
            {
                "extracted": 5,
                "written": 5,
                "notified": True,
                "validation_issues": [...]
            }
    """
    print("=" * 60)
    print(f"📝 妙记 Todo 抽取与处理")
    print("=" * 60)

    # Step 1: Extract todos from minutes
    extractor = FeishuMinutesExtractor()
    extract_result = extract_pipeline(extractor, minute_token=minute_token)

    if not extract_result["success"]:
        return {
            "error": extract_result["error"],
            "extracted": 0,
            "written": 0,
            "notified": False,
        }

    todos = extract_result["todos"]
    print(f"\n✅ 抽取完成：{extract_result['count']} 条事项")

    if not todos:
        print("⚠️  没有可处理的事项")
        return {
            "extracted": 0,
            "written": 0,
            "notified": False,
            "validation_issues": extract_result["validation_issues"],
        }

    # Step 2: Process todos (write to Bitable + send notification)
    print("\n" + "=" * 60)
    print("📊 写入多维表格并发送通知")
    print("=" * 60)

    process_result = run_pipeline(todos, mobile=mobile)

    print("\n" + "=" * 60)
    print("✅ 流程完成")
    print("=" * 60)

    return {
        "extracted": extract_result["count"],
        "written": process_result["write_success"],
        "notified": process_result["summary_sent"],
        "validation_issues": extract_result["validation_issues"],
    }


if __name__ == "__main__":
    # Example usage
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Test with document extraction
    doc_token = os.getenv("TEST_DOC_TOKEN", "FVsKw2E0xiEOGwkTezhcvyHEnNc")
    mobile = os.getenv("FEISHU_TEST_MOBILE", "13349952475")

    result = extract_and_process_doc(doc_token=doc_token, mobile=mobile)

    print("\n" + "=" * 60)
    print("📈 最终结果")
    print("=" * 60)
    print(f"抽取：{result.get('extracted', 0)} 条")
    print(f"写入：{result.get('written', 0)} 条")
    print(f"通知：{'成功' if result.get('notified') else '失败'}")

    if result.get("validation_issues"):
        print(f"\n⚠️  验证问题：")
        for issue in result["validation_issues"]:
            print(f"  - {issue}")
