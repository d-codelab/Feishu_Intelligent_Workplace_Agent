"""
任务调取测试脚本  
https://open.feishu.cn/document/task-v2/task/get?appId=cli_a97ac4e3d9781cc2
需要用户进行授权
"""

import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json
from typing import Optional
from todo_extractor.extractors.feishu_task import FeishuTaskExtractor
from todo_extractor.pipeline import extract_pipeline


def test_task_extraction(max_count: int = 200, save_to_file: bool = True):
    """Test task extraction.

    Args:
        max_count: Maximum number of tasks to fetch
        save_to_file: Whether to save results to JSON file
    """
    print("=" * 60)
    print("📋 飞书任务抽取测试")
    print("=" * 60)
    print(f"\n最大任务数: {max_count}")

    try:
        # Create extractor
        extractor = FeishuTaskExtractor()

        # Run extraction
        result = extract_pipeline(extractor, max_count=max_count)

        if result["success"]:
            print(f"\n✅ 抽取成功：{result['count']} 条事项")
            print(f"数据源类型：{result['source_type']}")

            # Save to file
            if save_to_file and result["todos"]:
                output_file = f"output_tasks_{max_count}.json"
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
                print("  1. 任务列表为空")
                print("  2. 任务中没有明确的待办事项")

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
            print("  1. User Token 不正确或已过期")
            print("  2. 应用没有读取任务的权限")
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
    max_count = 200

    # Command line arguments
    if len(sys.argv) > 1:
        max_count = int(sys.argv[1])

    print("\n提示：可以通过命令行参数指定最大任务数")
    print(f"用法：python test_task_extraction.py [max_count]\n")

    # Run test
    todos = test_task_extraction(max_count)

    # Summary
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"成功抽取：{len(todos)} 条事项")
    print("\n下一步：")
    print("1. 查看生成的 JSON 文件，确认数据格式")
    print("2. 如果数据正确，可以运行完整流程：")
    print("   from src.integration import extract_and_process_task")
    print(f"   extract_and_process_task(max_count={max_count})")
