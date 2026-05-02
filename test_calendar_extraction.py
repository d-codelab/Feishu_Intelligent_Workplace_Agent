"""
日历调取测试脚本
https://open.feishu.cn/document/server-docs/calendar-v4/calendar/get
需要用户权限
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json
from typing import Optional
from todo_extractor.extractors.feishu_calendar import FeishuCalendarExtractor
from todo_extractor.pipeline import extract_pipeline


def test_calendar_extraction(calendar_id: Optional[str] = None, days: int = 7, save_to_file: bool = True):
    """Test calendar extraction.

    Args:
        calendar_id: Calendar ID (uses primary calendar if not provided)
        days: Number of days to look ahead
        save_to_file: Whether to save results to JSON file
    """
    print("=" * 60)
    print("📅 飞书日历抽取测试")
    print("=" * 60)
    print(f"\n时间范围：接下来 {days} 天")
    if calendar_id:
        print(f"日历 ID: {calendar_id} (仅提取指定日历)")
    else:
        print("日历 ID: 未指定 (将遍历所有日历)")

    try:
        # Create extractor
        extractor = FeishuCalendarExtractor()

        # Run extraction
        result = extract_pipeline(extractor, calendar_id=calendar_id, days=days)

        if result["success"]:
            print(f"\n✅ 抽取成功：{result['count']} 条事项")
            print(f"数据源类型：{result['source_type']}")

            # Save to file
            if save_to_file and result["todos"]:
                output_file = f"output_calendar_{days}days.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result["todos"], f, ensure_ascii=False, indent=2)
                print(f"✅ 结果已保存到：{output_file}")

            # Show preview
            if result["todos"]:
                print("\n" + "=" * 60)
                print("📋 抽取结果预览")
                print("=" * 60)

                for idx, todo in enumerate(result["todos"], 1):
                    print(f"\n【事项 {idx}】")
                    print(f"  事项标题：{todo.get('事项标题', '无标题')}")
                    print(f"  事项描述：{todo.get('事项描述', '无描述')[:50]}...")
                    print(f"  负责人：{todo.get('负责人', '待确认')}")
                    print(f"  开始时间：{todo.get('开始时间', '待确认')}")
                    print(f"  截止时间：{todo.get('截止时间', '待确认')}")
                    print(f"  优先级：{todo.get('优先级', 'P2')}")
                    print(f"  当前状态：{todo.get('当前状态', '待开始')}")
                    print(f"  来源链接：{todo.get('来源链接', '')}")

                    # Show evidence (first 100 chars)
                    evidence = todo.get('原文依据', '')
                    if evidence:
                        print(f"  原文依据：{evidence[:100]}...")

                    if todo.get('待确认项'):
                        print(f"  ⚠️  待确认项：{', '.join(todo['待确认项'])}")

            else:
                print("\n⚠️  未抽取到任何事项")
                print("可能原因：")
                print("  1. 日历中没有明确的待办事项")
                print("  2. 时间范围内没有日程")

            # Show validation issues
            print("\n" + "=" * 60)
            print("🔍 数据验证")
            print("=" * 60)

            if result["validation_issues"]:
                print("⚠️  发现以下问题：")
                for issue in result["validation_issues"]:
                    print(f"  - {issue}")
            else:
                print("✅ 数据验证通过，所有必填字段完整")

            return result["todos"]

        else:
            print(f"\n❌ 抽取失败：{result.get('error', '未知错误')}")
            print("\n可能的原因：")
            print("  1. Tenant Token 不正确或已过期")
            print("  2. 应用没有读取日历的权限")
            print("  3. 日历 ID 不存在或无权访问")
            return []

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        print("\n" + "=" * 60)


if __name__ == "__main__":
    # Default values
    calendar_id = None  # Use primary calendar
    days = 7

    # Command line arguments
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    if len(sys.argv) > 2:
        calendar_id = sys.argv[2]

    print("\n提示：可以通过命令行参数指定时间范围和日历 ID")
    print(f"用法：python test_calendar_extraction.py [days] [calendar_id]\n")

    # Run test
    todos = test_calendar_extraction(calendar_id, days)

    # Summary
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"成功抽取：{len(todos)} 条事项")
    print("\n下一步：")
    print("1. 查看生成的 JSON 文件，确认数据格式")
    print("2. 如果数据正确，可以运行完整流程：")
    print("   from src.integration import extract_and_process_calendar")
    print(f"   extract_and_process_calendar(days={days})")
