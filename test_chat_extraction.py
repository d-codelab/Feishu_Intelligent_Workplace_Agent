"""
群消息调取测试脚本
https://open.feishu.cn/document/server-docs/im-v1/message/list?appId=cli_a97ac4e3d9781cc2&lang=zh-CN
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json
from todo_extractor.extractors.feishu_im import FeishuIMExtractor
from todo_extractor.pipeline import extract_pipeline


def test_chat_extraction(chat_id: str, hours: int = 24, save_to_file: bool = True):
    """Test group chat extraction.

    Args:
        chat_id: Feishu chat ID
        hours: Number of hours to look back
        save_to_file: Whether to save results to JSON file
    """

    print(f"群聊 ID: {chat_id}")
    print(f"时间范围：最近 {hours} 小时")

    try:
        # Create extractor
        extractor = FeishuIMExtractor()

        # Run extraction
        result = extract_pipeline(extractor, chat_id=chat_id, hours=hours)

        if result["success"]:

            # Save to file
            if save_to_file and result["todos"]:
                output_file = f"output_chat_{chat_id[:10]}_{hours}h.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result["todos"], f, ensure_ascii=False, indent=2)
                print(f"结果已保存到：{output_file}")

            # Show preview
            if result["todos"]:
                print("\n" + "=" * 60)
                print("抽取成功")
                print("=" * 60)

                # for idx, todo in enumerate(result["todos"], 1):
                #     print(f"\n【事项 {idx}】")
                #     print(f"  事项标题：{todo.get('事项标题', '无标题')}")
                #     print(f"  事项描述：{todo.get('事项描述', '无描述')[:50]}...")
                #     print(f"  负责人：{todo.get('负责人', '待确认')}")
                #     print(f"  开始时间：{todo.get('开始时间', '待确认')}")
                #     print(f"  截止时间：{todo.get('截止时间', '待确认')}")
                #     print(f"  优先级：{todo.get('优先级', 'P2')}")
                #     print(f"  当前状态：{todo.get('当前状态', '待开始')}")
                #     print(f"  来源链接：{todo.get('来源链接', '')}")

                #     # Show evidence (first 100 chars)
                #     evidence = todo.get('原文依据', '')
                #     if evidence:
                #         print(f"  原文依据：{evidence[:100]}...")

                #     if todo.get('待确认项'):
                #         print(f" 待确认项：{', '.join(todo['待确认项'])}")

            else:
                print("\n未抽取到任何事项")
                print("可能原因：")
                print("  1. 群聊中没有明确的待办事项")
                print("  2. 时间范围内没有消息")
                print("  3. 机器人未加入该群聊")

            # Show validation issues
            print("\n" + "=" * 60)
            print("数据验证")
            print("=" * 60)

            if result["validation_issues"]:
                print("发现以下问题：")
                for issue in result["validation_issues"]:
                    print(f"  - {issue}")
            else:
                print("数据验证通过，所有必填字段完整")

            return result["todos"]

        else:
            print(f"\n抽取失败：{result.get('error', '未知错误')}")
            print("\n可能的原因：")
            print("  1. chat_id 不正确")
            print("  2. 应用没有读取群消息的权限")
            print("  3. 机器人未加入该群聊")
            return []

    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        print("\n" + "=" * 60)





if __name__ == "__main__":
    # Default values
    chat_id = 'oc_9a79e9273b6328fd16f9aa55e89c923d'
    hours = 96

    # Command line arguments
    if len(sys.argv) > 1:
        chat_id = sys.argv[1]
    if len(sys.argv) > 2:
        hours = int(sys.argv[2])

    # Run test
    todos = test_chat_extraction(chat_id, hours)

    # Summary
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"成功抽取：{len(todos)} 条事项")
    print("\n下一步：")
    print("1. 查看生成的 JSON 文件，确认数据格式")
    print("2. 如果数据正确，可以运行完整流程：")
    print("   from src.integration import extract_and_process_chat")
    print(f"   extract_and_process_chat(chat_id='{chat_id}', hours={hours})")
