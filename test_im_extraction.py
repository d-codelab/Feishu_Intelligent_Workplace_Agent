"""Test script for IM extraction with preprocessing."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from todo_extractor.extractors.feishu_im import FeishuIMExtractor


def test_realtime_mode():
    """Test realtime extraction mode."""
    print("=" * 80)
    print("测试实时模式（单阶段抽取）")
    print("=" * 80)

    extractor = FeishuIMExtractor(mode="realtime")


    chat_id = "oc_9a79e9273b6328fd16f9aa55e89c923d"
    hours = 96  # Last 4 days

    todos = extractor.extract(chat_id, hours=hours)

    print(f"\n抽取结果：{len(todos)} 条事项")
    for i, todo in enumerate(todos, 1):
        print(f"\n{i}. {todo.get('事项标题', 'N/A')}")
        print(f"   负责人: {todo.get('负责人', 'N/A')}")
        print(f"   截止时间: {todo.get('截止时间', 'N/A')}")
        print(f"   置信度: {todo.get('置信度', 'N/A')}")

    # Save to file
    output_file = "output_im_realtime.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")


def test_batch_mode():
    """Test batch extraction mode with preprocessing."""
    print("\n" + "=" * 80)
    print("测试批量模式（预处理 + 去重）")
    print("=" * 80)

    extractor = FeishuIMExtractor(mode="batch")

    # Test with a real chat ID (replace with your test chat ID)
    chat_id = "oc_9a79e9273b6328fd16f9aa55e89c923d"
    hours = 264  # Last 4 days

    todos = extractor.extract(chat_id, hours=hours)

    print(f"\n抽取结果：{len(todos)} 条事项")
    for i, todo in enumerate(todos, 1):
        print(f"\n{i}. {todo.get('事项标题', 'N/A')}")
        print(f"   负责人: {todo.get('负责人', 'N/A')}")
        print(f"   截止时间: {todo.get('截止时间', 'N/A')}")
        print(f"   置信度: {todo.get('置信度', 'N/A')}")

    # Save to file
    output_file = "output_im_batch.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")


def compare_modes():
    """Compare realtime vs batch mode."""
    print("\n" + "=" * 80)
    print("对比两种模式")
    print("=" * 80)

    chat_id = "oc_9a79e9273b6328fd16f9aa55e89c923d"
    hours = 264

    # Realtime mode
    print("\n[实时模式]")
    extractor_realtime = FeishuIMExtractor(mode="realtime")
    todos_realtime = extractor_realtime.extract(chat_id, hours=hours)

    # Batch mode
    print("\n[批量模式]")
    extractor_batch = FeishuIMExtractor(mode="batch")
    todos_batch = extractor_batch.extract(chat_id, hours=hours)

    # Compare
    print("\n" + "=" * 80)
    print("对比结果")
    print("=" * 80)
    print(f"实时模式: {len(todos_realtime)} 条事项")
    print(f"批量模式: {len(todos_batch)} 条事项")
    print(f"差异: {len(todos_realtime) - len(todos_batch)} 条")

    # Save comparison
    comparison = {
        "realtime": todos_realtime,
        "batch": todos_batch,
        "stats": {
            "realtime_count": len(todos_realtime),
            "batch_count": len(todos_batch),
            "difference": len(todos_realtime) - len(todos_batch)
        }
    }

    output_file = "output_im_comparison.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    print(f"\n对比结果已保存到: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test IM extraction")
    parser.add_argument("--mode", choices=["realtime", "batch", "compare"],
                       default="batch", help="Test mode")

    args = parser.parse_args()

    if args.mode == "realtime":
        test_realtime_mode()
    elif args.mode == "batch":
        test_batch_mode()
    else:
        compare_modes()
