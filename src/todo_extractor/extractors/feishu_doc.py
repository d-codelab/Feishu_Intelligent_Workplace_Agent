"""Feishu document extractor."""

from typing import Any

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.feishu_api import read_feishu_doc, Document
from todo_extractor.llm.client import extract_todos_by_llm


class FeishuDocExtractor(BaseExtractor):
    """Extract todo items from Feishu documents."""

    def extract(self, doc_token: str) -> list[dict[str, Any]]:
        """Extract todos from a Feishu document.

        Args:
            doc_token: Feishu document token

        Returns:
            List of extracted todo items
        """
        print(f"📄 开始从飞书文档抽取：{doc_token}")

        # Step 1: Read document content with structured parsing using blocks API
        doc = read_feishu_doc(doc_token, return_structured=True, use_blocks_api=True)

        if not isinstance(doc, Document):
            raise RuntimeError("Expected Document object from read_feishu_doc")

        print(f"✅ 文档读取成功：{doc.title}")
        print(f"   - Markdown 长度：{len(doc.markdown)} 字符")
        print(f"   - 图片：{len(doc.elements.get('images', []))} 个")
        print(f"   - 电子表格：{len(doc.elements.get('sheets', []))} 个")
        print(f"   - 多维表格：{len(doc.elements.get('bitables', []))} 个")
        print(f"   - 待办事项：{len(doc.elements.get('todos', []))} 个")
        print(f"   - 任务：{len(doc.elements.get('tasks', []))} 个")
        print(f"   - 高亮块：{len(doc.elements.get('callouts', []))} 个")

        # Step 2: Use markdown text for LLM extraction
        text = doc.markdown

        if not text.strip():
            print("⚠️  文档内容为空")
            return []

        # Step 3: Extract todos using LLM
        todos = extract_todos_by_llm(text, source_type=self.source_type)

        # Step 4: Add source_link to each todo
        source_link = f"https://feishu.cn/docx/{doc_token}"
        for todo in todos:
            todo["source_link"] = source_link

        print(f"✅ 文档抽取完成：{len(todos)} 条事项")
        return todos

    @property
    def source_type(self) -> str:
        return "飞书文档"
