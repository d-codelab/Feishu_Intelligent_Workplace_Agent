"""测试语义去重功能"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from todo_extractor.utils.semantic_dedup import semantic_dedup_todos


def test_semantic_dedup():
    """测试语义去重"""

    # 构造测试数据（包含语义相似但表述不同的 TODO）
    test_todos = [
        {
            "事项标题": "完成用户登录功能开发",
            "事项描述": "实现用户名密码登录，包括前端表单和后端API",
            "负责人": "张三",
            "截止日期": "2024-03-15",
            "置信度": 0.9
        },
        {
            "事项标题": "开发用户登录模块",
            "事项描述": "需要实现登录接口和前端页面",
            "负责人": "张三",
            "截止日期": "2024-03-15",
            "置信度": 0.85
        },
        {
            "事项标题": "优化数据库查询性能",
            "事项描述": "分析慢查询日志，添加索引",
            "负责人": "李四",
            "截止日期": "2024-03-20",
            "置信度": 0.8
        },
        {
            "事项标题": "提升数据库查询效率",
            "事项描述": "优化SQL语句，建立合适的索引",
            "负责人": "李四",
            "截止日期": "2024-03-20",
            "置信度": 0.75
        },
        {
            "事项标题": "编写API文档",
            "事项描述": "使用Swagger生成接口文档",
            "负责人": "王五",
            "截止日期": "2024-03-18",
            "置信度": 0.7
        },
        {
            "事项标题": "修复支付模块bug",
            "事项描述": "解决支付回调失败的问题",
            "负责人": "赵六",
            "截止日期": "2024-03-12",
            "置信度": 0.95
        }
    ]

    print("=" * 80)
    print("测试语义去重功能")
    print("=" * 80)
    print(f"\n原始 TODO 数量: {len(test_todos)}")
    print("\n原始 TODO 列表:")
    for i, todo in enumerate(test_todos, 1):
        print(f"{i}. {todo['事项标题']} (负责人: {todo['负责人']}, 置信度: {todo['置信度']})")

    print("\n" + "-" * 80)

    # 执行语义去重
    result = semantic_dedup_todos(test_todos, threshold=0.85)

    print("\n" + "-" * 80)
    print(f"\n去重后 TODO 数量: {len(result)}")
    print("\n去重后 TODO 列表:")
    for i, todo in enumerate(result, 1):
        print(f"{i}. {todo['事项标题']} (负责人: {todo['负责人']}, 置信度: {todo['置信度']})")

    print("\n" + "=" * 80)
    print(f"去重效果: {len(test_todos)} -> {len(result)} 条 (合并 {len(test_todos) - len(result)} 条)")
    print("=" * 80)


if __name__ == "__main__":
    test_semantic_dedup()
