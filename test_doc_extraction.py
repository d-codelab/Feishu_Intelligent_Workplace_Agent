"""
云文档内容调取测试脚本
"""

import sys
import io
from pathlib import Path

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json
from todo_extractor.extractors.feishu_doc import FeishuDocExtractor
from todo_extractor.pipeline import extract_pipeline


def test_doc_extraction(doc_token: str, save_to_file: bool = True):
    """Test document extraction.

    Args:
        doc_token: Feishu document token
        save_to_file: Whether to save results to JSON file
    """
    print("=" * 60)
    print("📄 飞书文档抽取测试")
    print("=" * 60)
    print(f"\n文档 Token: {doc_token}")

    try:
        # Create extractor
        extractor = FeishuDocExtractor()

        # Run extraction
        result = extract_pipeline(extractor, doc_token=doc_token)

        if result["success"]:
            print(f"\n✅ 抽取成功：{result['count']} 条事项")
            print(f"数据源类型：{result['source_type']}")

            # Save to file
            if save_to_file and result["todos"]:
                output_file = f"output_doc_{doc_token[:10]}.json"
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

                    if todo.get('待确认项'):
                        print(f"  ⚠️  待确认项：{', '.join(todo['待确认项'])}")

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
            return []

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        print("\n" + "=" * 60)


if __name__ == "__main__":
    # Default doc token
    doc_token = "FVsKw2E0xiEOGwkTezhcvyHEnNc"

    # You can also pass doc_token as command line argument
    if len(sys.argv) > 1:
        doc_token = sys.argv[1]

    print("\n提示：可以通过命令行参数指定文档 Token")
    print(f"用法：python test_doc_extraction.py <doc_token>\n")

    # Run test
    todos = test_doc_extraction(doc_token)

    # Summary
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"成功抽取：{len(todos)} 条事项")
    print("\n下一步：")
    print("1. 查看生成的 JSON 文件，确认数据格式")
    print("2. 如果数据正确，可以运行完整流程：")
    print("   python src/integration.py")
