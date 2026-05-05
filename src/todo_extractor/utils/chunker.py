"""文档智能分块模块，用于处理长文档的分块策略"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Chunk:
    """文档块"""
    content: str  # 块内容
    start_line: int  # 起始行号
    end_line: int  # 结束行号
    context: Dict[str, str]  # 全局上下文（标题、章节等）
    has_overlap: bool = False  # 是否包含重叠内容


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量（粗略估计：中文 1 字 ≈ 1.5 tokens，英文 1 词 ≈ 1.3 tokens）"""
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    other_chars = len(text) - chinese_chars - english_words

    # 粗略估算
    return int(chinese_chars * 1.5 + english_words * 1.3 + other_chars * 0.5)


def extract_document_context(markdown: str) -> Dict[str, str]:
    """提取文档的全局上下文信息（标题、作者等）"""
    lines = markdown.split('\n')
    context = {}

    # 提取第一个一级标题作为文档标题
    for line in lines[:20]:  # 只看前 20 行
        if line.strip().startswith('# '):
            context['title'] = line.strip()[2:].strip()
            break

    return context


def find_semantic_boundaries(lines: List[str]) -> List[int]:
    """找到语义边界（标题位置），返回行号列表"""
    boundaries = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 标题（# 开头）
        if stripped.startswith('#'):
            boundaries.append(i)
        # 分割线
        elif stripped in ['---', '***', '___']:
            boundaries.append(i)

    return boundaries


def split_at_boundary(lines: List[str], start: int, max_tokens: int, boundaries: List[int]) -> Tuple[int, bool]:
    """
    从 start 开始，找到最佳切分点

    Returns:
        (切分点行号, 是否在语义边界处切分)
    """
    current_tokens = 0
    last_boundary = start
    found_boundary = False

    for i in range(start, len(lines)):
        line = lines[i]
        line_tokens = estimate_tokens(line)

        # 如果加上这一行会超出限制
        if current_tokens + line_tokens > max_tokens:
            # 如果找到了语义边界，在边界处切分
            if found_boundary and last_boundary > start:
                return last_boundary, True
            # 否则在当前位置强制切分
            return max(i, start + 1), False

        current_tokens += line_tokens

        # 记录语义边界
        if i in boundaries and i > start:
            last_boundary = i
            found_boundary = True

    # 到达文档末尾
    return len(lines), True


def chunk_document(
    markdown: str,
    max_tokens: int = 3000,
    overlap_tokens: int = 500,
    min_chunk_tokens: int = 500
) -> List[Chunk]:
    """
    智能分块文档

    Args:
        markdown: 文档的 markdown 文本
        max_tokens: 每块最大 token 数
        overlap_tokens: 重叠区域的 token 数
        min_chunk_tokens: 最小块大小（避免产生过小的块）

    Returns:
        文档块列表
    """
    lines = markdown.split('\n')
    total_tokens = estimate_tokens(markdown)

    # 如果文档很短，不需要分块
    if total_tokens <= max_tokens:
        context = extract_document_context(markdown)
        return [Chunk(
            content=markdown,
            start_line=0,
            end_line=len(lines),
            context=context,
            has_overlap=False
        )]

    # 提取全局上下文
    context = extract_document_context(markdown)

    # 找到所有语义边界
    boundaries = find_semantic_boundaries(lines)
    boundaries_set = set(boundaries)

    chunks = []
    current_line = 0

    while current_line < len(lines):
        # 找到切分点
        end_line, at_boundary = split_at_boundary(
            lines, current_line, max_tokens, boundaries_set
        )

        # 提取块内容
        chunk_lines = lines[current_line:end_line]
        chunk_content = '\n'.join(chunk_lines)

        # 如果块太小且不是最后一块，合并到下一块
        chunk_tokens = estimate_tokens(chunk_content)
        if chunk_tokens < min_chunk_tokens and end_line < len(lines):
            # 扩展到下一个边界或固定大小
            end_line, _ = split_at_boundary(
                lines, current_line, max_tokens + overlap_tokens, boundaries_set
            )
            chunk_lines = lines[current_line:end_line]
            chunk_content = '\n'.join(chunk_lines)

        # 添加全局上下文到块内容开头
        if context.get('title'):
            chunk_content = f"# 文档标题：{context['title']}\n\n{chunk_content}"

        chunks.append(Chunk(
            content=chunk_content,
            start_line=current_line,
            end_line=end_line,
            context=context,
            has_overlap=len(chunks) > 0  # 除了第一块，其他都有重叠
        ))

        # 计算下一块的起始位置（带重叠）
        if end_line >= len(lines):
            break

        # 回退 overlap_tokens 的内容
        overlap_lines = 0
        overlap_tokens_count = 0
        for i in range(end_line - 1, current_line, -1):
            line_tokens = estimate_tokens(lines[i])
            if overlap_tokens_count + line_tokens > overlap_tokens:
                break
            overlap_tokens_count += line_tokens
            overlap_lines += 1

        # 确保重叠区域至少从一个完整的段落或标题开始
        overlap_start = end_line - overlap_lines
        # 向前找到最近的语义边界
        for boundary in reversed([b for b in boundaries if b < end_line and b >= overlap_start]):
            overlap_start = boundary
            break

        current_line = max(overlap_start, end_line - overlap_lines)

        # 避免无限循环
        if current_line >= end_line:
            current_line = end_line

    return chunks


def get_chunk_summary(chunks: List[Chunk]) -> Dict:
    """获取分块统计信息"""
    if not chunks:
        return {
            "total_chunks": 0,
            "total_tokens": 0,
            "avg_tokens_per_chunk": 0,
            "chunks_with_overlap": 0
        }

    total_tokens = sum(estimate_tokens(c.content) for c in chunks)
    chunks_with_overlap = sum(1 for c in chunks if c.has_overlap)

    return {
        "total_chunks": len(chunks),
        "total_tokens": total_tokens,
        "avg_tokens_per_chunk": total_tokens // len(chunks),
        "chunks_with_overlap": chunks_with_overlap
    }
