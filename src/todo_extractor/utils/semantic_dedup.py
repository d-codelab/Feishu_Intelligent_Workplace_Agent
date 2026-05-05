"""语义去重模块：使用中文 Embedding 模型进行语义相似度计算"""

from typing import Any, List, Dict, Optional
import numpy as np


class SemanticDeduplicator:
    """语义去重器：使用 Embedding 模型计算语义相似度"""

    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese", threshold: float = 0.85):
        """初始化语义去重器

        Args:
            model_name: Embedding 模型名称，支持：
                - "shibing624/text2vec-base-chinese" (推荐，中文优化)
                - "BAAI/bge-small-zh-v1.5" (百度出品，轻量级)
                - "paraphrase-multilingual-MiniLM-L12-v2" (多语言)
            threshold: 相似度阈值（0-1），超过此值视为重复
        """
        self.model_name = model_name
        self.threshold = threshold
        self.model = None
        self._init_model()

    def _init_model(self):
        """延迟加载模型"""
        try:
            if "text2vec" in self.model_name:
                # 使用 text2vec 库
                from text2vec import SentenceModel
                print(f"[加载模型] 正在加载 text2vec 模型: {self.model_name}")
                self.model = SentenceModel(self.model_name)
                self.model_type = "text2vec"
            else:
                # 使用 sentence-transformers 库
                from sentence_transformers import SentenceTransformer
                print(f"[加载模型] 正在加载 sentence-transformers 模型: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                self.model_type = "sentence_transformers"

            print(f"[成功] 模型加载完成")

        except ImportError as e:
            print(f"[错误] 缺少依赖库: {e}")
            print("请安装: pip install text2vec 或 pip install sentence-transformers")
            self.model = None

        except Exception as e:
            print(f"[错误] 模型加载失败: {e}")
            self.model = None

    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量数组 (n_texts, embedding_dim)，失败返回 None
        """
        if self.model is None:
            return None

        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return np.array(embeddings)
        except Exception as e:
            print(f"[错误] 文本编码失败: {e}")
            return None

    def compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """计算余弦相似度矩阵

        Args:
            embeddings: 向量数组 (n, dim)

        Returns:
            相似度矩阵 (n, n)
        """
        # 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-8)

        # 计算余弦相似度
        similarity_matrix = np.dot(normalized, normalized.T)
        return similarity_matrix

    def deduplicate(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对 TODO 列表进行语义去重

        Args:
            todos: TODO 事项列表

        Returns:
            去重后的 TODO 列表
        """
        if len(todos) <= 1:
            return todos

        if self.model is None:
            print("[警告] 模型未加载，跳过语义去重")
            return todos

        try:
            # 构建文本（标题 + 描述）
            texts = []
            for item in todos:
                title = item.get('事项标题', '')
                desc = item.get('事项描述', '')
                text = f"{title} {desc}".strip()
                texts.append(text)

            print(f"[去重] 正在生成 {len(texts)} 条事项的语义向量...")

            # 生成 embeddings
            embeddings = self.encode(texts)
            if embeddings is None:
                print("[警告] Embedding 生成失败，跳过语义去重")
                return todos

            # 计算相似度矩阵
            similarity_matrix = self.compute_similarity_matrix(embeddings)

            # 查找重复项
            keep_indices = set(range(len(todos)))
            merged_count = 0

            for i in range(len(todos)):
                if i not in keep_indices:
                    continue

                for j in range(i + 1, len(todos)):
                    if j not in keep_indices:
                        continue

                    # 检查语义相似度
                    if similarity_matrix[i, j] >= self.threshold:
                        # 额外检查：负责人是否相同（提高精确度）
                        owner_i = todos[i].get('负责人', '')
                        owner_j = todos[j].get('负责人', '')
                        same_owner = (owner_i == owner_j and owner_i not in ['待确认', '', None])

                        # 如果语义相似度很高（>0.9）或者负责人相同，则判定为重复
                        if similarity_matrix[i, j] >= 0.9 or same_owner:
                            # 保留置信度更高的
                            conf_i = todos[i].get('置信度', 0.5)
                            conf_j = todos[j].get('置信度', 0.5)

                            if conf_j > conf_i:
                                keep_indices.discard(i)
                                merged_count += 1
                                break
                            else:
                                keep_indices.discard(j)
                                merged_count += 1

            result = [todos[i] for i in sorted(keep_indices)]
            print(f"[成功] 语义去重完成: {len(todos)} -> {len(result)} 条（合并 {merged_count} 条重复）")
            print(f"   相似度阈值: {self.threshold}")

            return result

        except Exception as e:
            print(f"[错误] 语义去重失败: {e}")
            return todos


# 全局单例（避免重复加载模型）
_global_deduplicator: Optional[SemanticDeduplicator] = None


def get_deduplicator(
    model_name: str = "shibing624/text2vec-base-chinese",
    threshold: float = 0.85
) -> SemanticDeduplicator:
    """获取全局去重器实例（单例模式）

    Args:
        model_name: 模型名称
        threshold: 相似度阈值

    Returns:
        SemanticDeduplicator 实例
    """
    global _global_deduplicator

    if _global_deduplicator is None:
        _global_deduplicator = SemanticDeduplicator(model_name, threshold)

    return _global_deduplicator


def semantic_dedup_todos(
    todos: List[Dict[str, Any]],
    model_name: str = "shibing624/text2vec-base-chinese",
    threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """便捷函数：对 TODO 列表进行语义去重

    Args:
        todos: TODO 事项列表
        model_name: Embedding 模型名称
        threshold: 相似度阈值

    Returns:
        去重后的 TODO 列表
    """
    deduplicator = get_deduplicator(model_name, threshold)
    return deduplicator.deduplicate(todos)
