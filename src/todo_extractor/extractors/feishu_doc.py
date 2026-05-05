"""Feishu document extractor."""

from typing import Any, List, Dict

from todo_extractor.extractors.base import BaseExtractor
from todo_extractor.clients.feishu_api import read_feishu_doc, Document
from todo_extractor.llm.client import (
    coarse_extract_todos,
    extract_todos_by_llm,
    refine_todos_batch,
    semantic_dedup,
)
from todo_extractor.utils.chunker import chunk_document, get_chunk_summary, estimate_tokens
from todo_extractor.utils.deduplicator import deduplicate_todos


class FeishuDocExtractor(BaseExtractor):
    """Extract todo items from Feishu documents."""

    def __init__(self, mode: str = "batch"):
        """
        Args:
            mode: 抽取模式
                - "batch": 批量模式（多阶段抽取 + 语义去重，适合定时任务）
                - "realtime": 实时模式（单阶段抽取，适合事件响应）
        """
        self.mode = mode

    def extract(self, doc_token: str) -> list[dict[str, Any]]:
        """Extract todos from a Feishu document.

        Args:
            doc_token: Feishu document token

        Returns:
            List of extracted todo items
        """
        print(f"[文档抽取] 开始从飞书文档抽取：{doc_token} (模式: {self.mode})")

        # Step 1: Read document content with structured parsing using blocks API
        doc = read_feishu_doc(doc_token, return_structured=True, use_blocks_api=True)

        if not isinstance(doc, Document):
            raise RuntimeError("Expected Document object from read_feishu_doc")

        print(f"[成功] 文档读取成功：{doc.title}")
        print(f"   - Markdown 长度：{len(doc.markdown)} 字符")
        print(f"   - 图片：{len(doc.elements.get('images', []))} 个")
        print(f"   - 电子表格：{len(doc.elements.get('sheets', []))} 个")
        print(f"   - 多维表格：{len(doc.elements.get('bitables', []))} 个")
        print(f"   - 待办事项：{len(doc.elements.get('todos', []))} 个")
        print(f"   - 任务：{len(doc.elements.get('tasks', []))} 个")
        print(f"   - 高亮块：{len(doc.elements.get('callouts', []))} 个")

        if not doc.markdown.strip():
            print("[警告] 文档内容为空")
            return []

        # Step 2: 根据模式选择抽取策略
        if self.mode == "batch":
            todos = self._batch_extract(doc)
        else:
            todos = self._realtime_extract(doc)

        # Step 3: Add source_link to each todo
        source_link = f"https://feishu.cn/docx/{doc_token}"
        for todo in todos:
            todo["source_link"] = source_link

        print(f"[成功] 文档抽取完成：{len(todos)} 条事项")
        return todos

    def _realtime_extract(self, doc: Document) -> List[Dict[str, Any]]:
        """实时模式：单阶段抽取（快速响应）"""
        print("\n[实时模式] 启动实时模式（单阶段抽取）")
        enhanced_text = self._build_enhanced_text(doc)
        todos = extract_todos_by_llm(enhanced_text, source_type=self.source_type)

        # 规则去重（轻量级）
        if len(todos) > 1:
            print(f"[去重] 规则去重中...")
            deduped = deduplicate_todos(todos)
            print(f"   [成功] 去重完成: {len(todos)} -> {len(deduped)} 条")
            return deduped

        return todos

    def _batch_extract(self, doc: Document) -> List[Dict[str, Any]]:
        """批量模式：多阶段抽取（高准确率）

        Pipeline:
        1. 智能分块（长文档）
        2. 粗抽取（宽松模式，提高召回率）
        3. 精筛选（严格判断，过滤误报）
        4. 语义去重（文本相似度算法）
        """
        print("\n" + "="*60)
        print("[批量模式] 启动批量模式 Pipeline")
        print("="*60)

        # 估算文档 token 数
        doc_tokens = estimate_tokens(doc.markdown)
        print(f"\n[阶段 0] 文档分析")
        print(f"   - 文档标题: {doc.title}")
        print(f"   - 估算 tokens: {doc_tokens}")
        print(f"   - 待办事项: {len(doc.elements.get('todos', []))} 个")
        print(f"   - 任务块: {len(doc.elements.get('tasks', []))} 个")
        print(f"   - 表格: {len(doc.elements.get('tables', []))} 个")

        # ========== 阶段 1: 智能分块 ==========
        print(f"\n[阶段 1] 智能分块")
        if doc_tokens <= 6000:
            # 短文档：不需要分块
            print("   [成功] 文档较短，无需分块")
            chunks_text = [self._build_enhanced_text(doc)]
        else:
            # 长文档：智能分块
            print("   [处理] 文档较长，启动智能分块...")
            chunks = chunk_document(
                doc.markdown,
                max_tokens=6000,
                overlap_tokens=500,
                min_chunk_tokens=500
            )

            summary = get_chunk_summary(chunks)
            print(f"   [成功] 分块完成: {summary['total_chunks']} 块")
            print(f"     - 平均每块: {summary['avg_tokens_per_chunk']} tokens")
            print(f"     - 重叠块数: {summary['chunks_with_overlap']}")

            # 为每个块添加结构化提示
            chunks_text = [self._add_structured_hints(chunk.content, doc) for chunk in chunks]

        # ========== 阶段 2: 粗抽取 ==========
        print(f"\n[阶段 2] 粗抽取（宽松模式）")
        all_raw_todos = []
        for i, chunk_text in enumerate(chunks_text, 1):
            print(f"   - 处理块 {i}/{len(chunks_text)}...")
            chunk_todos = coarse_extract_todos(chunk_text, source_type=self.source_type)
            all_raw_todos.extend(chunk_todos)

        print(f"   [成功] 粗抽取完成: {len(all_raw_todos)} 条候选事项")

        if not all_raw_todos:
            print("\n[警告] 未抽取到任何事项")
            return []

        # ========== 阶段 3: 精筛选 ==========
        print(f"\n[阶段 3] 精筛选（严格判断）")
        refined_todos = refine_todos_batch(all_raw_todos, batch_size=20)
        print(f"   [成功] 精筛选完成: {len(all_raw_todos)} -> {len(refined_todos)} 条")

        if not refined_todos:
            print("\n[警告] 精筛选后无有效事项")
            return []

        # ========== 阶段 4: 语义去重 ==========
        print(f"\n[阶段 4] 语义去重")
        final_todos = semantic_dedup(refined_todos, threshold=0.85)
        print(f"   [成功] 语义去重完成: {len(refined_todos)} -> {len(final_todos)} 条")

        # ========== Pipeline 总结 ==========
        print("\n" + "="*60)
        print("[总结] Pipeline 执行总结")
        print("="*60)
        print(f"   分块数量: {len(chunks_text)}")
        print(f"   粗抽取:   {len(all_raw_todos)} 条候选")
        print(f"   精筛选:   {len(refined_todos)} 条有效")
        print(f"   语义去重: {len(final_todos)} 条最终")
        print(f"   过滤率:   {(1 - len(final_todos)/len(all_raw_todos))*100:.1f}%")
        print("="*60 + "\n")

        return final_todos

    def _add_structured_hints(self, chunk_text: str, doc: Document) -> str:
        """为分块添加结构化提示"""
        hints = []

        # 添加文档级别的统计信息
        todos_count = len(doc.elements.get('todos', []))
        tasks_count = len(doc.elements.get('tasks', []))
        tables_count = len(doc.elements.get('tables', []))

        if todos_count > 0:
            hints.append(f"💡 提示：文档包含 {todos_count} 个待办事项")
        if tasks_count > 0:
            hints.append(f"💡 提示：文档包含 {tasks_count} 个任务块")
        if tables_count > 0:
            hints.append(f"💡 提示：文档包含 {tables_count} 个表格，注意表格中的任务信息")

        if hints:
            return "\n".join(hints) + "\n\n---\n\n" + chunk_text
        return chunk_text

    def _build_enhanced_text(self, doc: Document) -> str:
        """构建增强的文本输入，优先展示结构化的 TODO 信息"""
        parts = []

        # 1. 文档标题
        parts.append(f"# 文档标题：{doc.title}\n")

        # 2. 如果有待办事项列表，优先展示
        todos = doc.elements.get('todos', [])
        if todos:
            parts.append("\n## 📋 文档中的待办事项列表（优先识别）：")
            for idx, todo in enumerate(todos, 1):
                status = "✓ 已完成" if todo['checked'] else "○ 未完成"
                parts.append(f"{idx}. [{status}] {todo['text']}")
            parts.append("")  # 空行

        # 3. 如果有任务块，展示任务
        tasks = doc.elements.get('tasks', [])
        if tasks:
            parts.append("\n## 📌 文档中的任务块（优先识别）：")
            for idx, task in enumerate(tasks, 1):
                parts.append(f"{idx}. [ ] {task['text']} (task_id: {task['task_id']})")
            parts.append("")

        # 4. 如果有高亮块，展示重要内容
        callouts = doc.elements.get('callouts', [])
        if callouts:
            parts.append("\n## 💡 文档中的高亮块（可能包含重要事项）：")
            for idx, callout in enumerate(callouts, 1):
                parts.append(f"{idx}. {callout['raw']}")
            parts.append("")

        # 5. 如果有表格，提示 LLM 注意表格内容
        tables = doc.elements.get('tables', [])
        if tables:
            parts.append(f"\n## 📊 文档包含 {len(tables)} 个表格，请注意表格中的任务信息")
            parts.append("")

        # 6. 完整的 Markdown 内容
        parts.append("\n## 📄 完整文档内容：\n")
        parts.append(doc.markdown)

        # 7. 添加抽取提示
        parts.append("\n\n---")
        parts.append("**抽取指引：**")
        parts.append("1. 优先从「待办事项列表」和「任务块」中提取明确的 TODO")
        parts.append("2. 注意「高亮块」中可能包含重要的行动项")
        parts.append("3. 检查表格中是否有任务分配信息（列名包含：待办、任务、负责人、截止时间等）")
        parts.append("4. 忽略已完成的任务（标记为 ✓ 或 [x]）")
        parts.append("5. 忽略历史记录、示例说明等非执行性内容")

        return "\n".join(parts)

    @property
    def source_type(self) -> str:
        return "飞书文档"
