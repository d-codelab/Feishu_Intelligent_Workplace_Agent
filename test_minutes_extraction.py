"""
飞书妙记测试脚本
https://open.feishu.cn/document/minutes-v1/minute-transcript/get
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from todo_extractor.extractors.feishu_minutes import FeishuMinutesExtractor

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ========== 配置 ==========
# 妙记 token（从妙记链接中获取）
# 例如: https://jcneyh7qlo8i.feishu.cn/minutes/obcnb4r7575w2m39416cvaj3
# minute_token 就是: obcnb4r7575w2m39416cvaj3
DEFAULT_MINUTE_TOKEN = "obcnb4r7575w2m39416cvaj3"
# ==========================


def main():
    """Test minutes extraction."""
    print("=" * 60)
    print("飞书妙记 Todo 抽取测试")
    print("=" * 60)

    # Get minute token from command line or use default
    minute_token = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MINUTE_TOKEN

    # Create extractor
    extractor = FeishuMinutesExtractor()

    # Extract todos
    try:
        todos = extractor.extract(minute_token)

        # Display results
        print(f"\n{'='*60}")
        print(f"抽取结果")
        print(f"{'='*60}")
        print(f"共抽取 {len(todos)} 条事项\n")

        # Save to file
        output_file = f"output_minutes_{minute_token}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {output_file}")

    except Exception as e:
        print(f"抽取失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
