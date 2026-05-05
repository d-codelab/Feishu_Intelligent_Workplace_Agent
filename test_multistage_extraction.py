"""测试多阶段文档抽取流程"""

import sys
import json
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from todo_extractor.extractors.feishu_doc import FeishuDocExtractor

def test_batch_mode():
    """测试批量模式（多阶段抽取）"""
    print("="*80)
    print("测试批量模式（多阶段抽取 + 语义去重）")
    print("="*80)

    # 使用之前的测试文档
    doc_token = "FVsKw2E0xiEOGwkTezhcvyHEnNc"

    # 创建批量模式的抽取器
    extractor = FeishuDocExtractor(mode="batch")

    try:
        # 执行抽取
        todos = extractor.extract(doc_token)

        # 输出结果
        print("\n" + "="*80)
        print("📋 最终抽取结果")
        print("="*80)
        print(f"共抽取 {len(todos)} 条待办事项\n")

        for i, todo in enumerate(todos, 1):
            print(f"\n【事项 {i}】")
            print(f"  标题: {todo.get('事项标题', 'N/A')}")
            print(f"  描述: {todo.get('事项描述', 'N/A')}")
            print(f"  负责人: {todo.get('负责人', 'N/A')}")
            print(f"  截止时间: {todo.get('截止时间', 'N/A')}")
            print(f"  优先级: {todo.get('优先级', 'N/A')}")
            print(f"  置信度: {todo.get('置信度', 'N/A')}")
            print(f"  状态: {todo.get('当前状态', 'N/A')}")
            if todo.get('待确认项'):
                print(f"  待确认: {', '.join(todo['待确认项'])}")

        # 保存到文件
        output_file = "output_multistage_extraction.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存到: {output_file}")

        return todos

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_realtime_mode():
    """测试实时模式（单阶段抽取）"""
    print("\n\n" + "="*80)
    print("测试实时模式（单阶段抽取 + 规则去重）")
    print("="*80)

    doc_token = "FVsKw2E0xiEOGwkTezhcvyHEnNc"

    # 创建实时模式的抽取器
    extractor = FeishuDocExtractor(mode="realtime")

    try:
        # 执行抽取
        todos = extractor.extract(doc_token)

        # 输出结果
        print("\n" + "="*80)
        print("📋 最终抽取结果")
        print("="*80)
        print(f"共抽取 {len(todos)} 条待办事项\n")

        for i, todo in enumerate(todos, 1):
            print(f"\n【事项 {i}】")
            print(f"  标题: {todo.get('事项标题', 'N/A')}")
            print(f"  负责人: {todo.get('负责人', 'N/A')}")
            print(f"  截止时间: {todo.get('截止时间', 'N/A')}")
            print(f"  置信度: {todo.get('置信度', 'N/A')}")

        return todos

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_modes(batch_todos, realtime_todos):
    """对比两种模式的结果"""
    if not batch_todos or not realtime_todos:
        print("\n⚠️  无法对比，某个模式执行失败")
        return

    print("\n\n" + "="*80)
    print("📊 模式对比")
    print("="*80)
    print(f"批量模式: {len(batch_todos)} 条")
    print(f"实时模式: {len(realtime_todos)} 条")
    print(f"差异: {abs(len(batch_todos) - len(realtime_todos))} 条")

    # 计算平均置信度
    batch_avg_conf = sum(t.get('置信度', 0) for t in batch_todos) / len(batch_todos) if batch_todos else 0
    realtime_avg_conf = sum(t.get('置信度', 0) for t in realtime_todos) / len(realtime_todos) if realtime_todos else 0

    print(f"\n平均置信度:")
    print(f"  批量模式: {batch_avg_conf:.2f}")
    print(f"  实时模式: {realtime_avg_conf:.2f}")


if __name__ == "__main__":
    # 测试批量模式
    batch_todos = test_batch_mode()

    # 测试实时模式
    realtime_todos = test_realtime_mode()

    # 对比结果
    compare_modes(batch_todos, realtime_todos)

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)

# 我是想做多智能体协作（高级）的，但是目前基本流程还没有跑通，我觉得精筛需要改一下，你看我现在抽取出来的todo，感觉有点太细碎了，你觉得呢，我就是可能很多事情它是包含在一个任务下面的：  {
#     "事项标题": "接入抽取结果写入",
#     "事项描述": "接入Agent输出的JSON结构，将抽取的事项批量写入飞书多维表格",
#     "负责人": "待确认",
#     "开始时间": "2026-04-27",
#     "截止时间": "2026-04-28",
#     "当前状态": "待开始",
#     "优先级": "P0",
#     "来源类型": "飞书文档",
#     "来源链接": "",
#     "原文依据": "角色C：飞书 API / 多维表格 / 机器人负责人 负责的任务：第四，接入 B 同学输出的 JSON。将 Agent 输出的 items 批量写入多维表格。",
#     "风险/阻塞": "依赖Agent侧输出的JSON结构稳定性",
#     "待确认项": [
#       "负责人"
#     ],
#     "source_link": "https://feishu.cn/docx/FVsKw2E0xiEOGwkTezhcvyHEnNc"
#   },
#   {
#     "事项标题": "测试机器人发消息",
#     "事项描述": "实现机器人消息推送功能，最小版本支持纯文本推送，两天内不强制要求卡片形式",
#     "负责人": "待确认",
#     "开始时间": "2026-04-26",
#     "截止时间": "2026-04-26",
#     "当前状态": "待开始",
#     "优先级": "P0",
#     "来源类型": "飞书文档",
#     "来源链接": "",
#     "原文依据": "角色C：飞书 API / 多维表格 / 机器人负责人 负责的任务：第五，测试机器人发消息。最小版本可以发送纯文本，进阶一点可以发卡片，但两天内不强求。第一天晚上的验收标准：机器人能发一条测试消息",
#     "风险/阻塞": "",
#     "待确认项": [
#       "负责人"
#     ],
#     "source_link": "https://feishu.cn/docx/FVsKw2E0xiEOGwkTezhcvyHEnNc"
#   },
#   {
#     "事项标题": "跑通演示闭环",
#     "事项描述": "两天内跑通最小可演示闭环，完成技术可行性验证，实现办公数据抽取→结构化输出→写入多维表→机器人推送的完整链路",
#     "负责人": "全体成员",
#     "开始时间": "2026-04-26",
#     "截止时间": "2026-04-28",
#     "当前状态": "待开始",
#     "优先级": "P0",
#     "来源类型": "飞书文档",
#     "来源链接": "",
#     "原文依据": "总目标 两天内跑通一个最小可演示闭环：模拟办公数据 → OpenClaw/CLI 抽取事项 → 输出结构化 JSON → API 写入飞书多维表格 → 机器人发送整理结果；可以把这两天定义为一个“技术可行性验证 Sprint”，目标不是把最终产品做完，而是确认核心链路是否能跑通",
#     "风险/阻塞": "各模块字段不对齐会导致联调阻塞",
#     "待确认项": [],
#     "source_link": "https://feishu.cn/docx/FVsKw2E0xiEOGwkTezhcvyHEnNc"
#   }
# ]