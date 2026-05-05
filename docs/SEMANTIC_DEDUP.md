# 语义去重功能说明

## 📦 支持的模型

### 1. text2vec-base-chinese（推荐）
- **优势**：专门针对中文优化，轻量级（~400MB）
- **安装**：`pip install text2vec`
- **使用**：默认模型，无需配置

### 2. bge-small-zh-v1.5（百度出品）
- **优势**：百度智能云开源，small 版本只有 ~100MB
- **安装**：`pip install sentence-transformers`
- **使用**：在代码中指定 `model_name="BAAI/bge-small-zh-v1.5"`

### 3. paraphrase-multilingual-MiniLM（多语言）
- **优势**：支持 50+ 语言，非常轻量（~420MB）
- **安装**：`pip install sentence-transformers`
- **使用**：在代码中指定 `model_name="paraphrase-multilingual-MiniLM-L12-v2"`

## 🚀 快速开始

### 安装依赖

```bash
# 方案 1：使用 text2vec（推荐）
pip install text2vec

# 方案 2：使用 sentence-transformers
pip install sentence-transformers
```

### 基本使用

```python
from todo_extractor.utils.semantic_dedup import semantic_dedup_todos

# TODO 列表
todos = [
    {"事项标题": "完成用户登录功能", "事项描述": "...", "负责人": "张三", "置信度": 0.9},
    {"事项标题": "开发用户登录模块", "事项描述": "...", "负责人": "张三", "置信度": 0.85},
    # ...
]

# 执行语义去重（使用默认模型）
result = semantic_dedup_todos(todos, threshold=0.85)

# 使用指定模型
result = semantic_dedup_todos(
    todos,
    model_name="BAAI/bge-small-zh-v1.5",  # 或其他模型
    threshold=0.85
)
```

### 在 Pipeline 中使用

语义去重已集成到文档抽取 Pipeline 中：

```python
from todo_extractor.extractors.feishu_doc import FeishuDocExtractor

# 批量模式会自动使用语义去重
extractor = FeishuDocExtractor(mode="batch")
todos = extractor.extract(doc_token)
```

## ⚙️ 配置说明

### 相似度阈值（threshold）

- **0.9-1.0**：非常严格，只合并几乎完全相同的事项
- **0.85-0.9**：推荐值，合并语义高度相似的事项
- **0.7-0.85**：宽松，可能会误合并一些不同的事项

### 去重规则

1. **语义相似度 >= threshold**：基于 Embedding 向量的余弦相似度
2. **负责人相同**：提高精确度，避免误合并不同人的任务
3. **置信度优先**：保留置信度更高的事项

### 降级策略

如果 Embedding 模型不可用（未安装依赖或加载失败），会自动降级为规则去重：

- 标题完全相同 + 负责人相同
- 标题高度相似（> 0.85）+ 负责人相同
- 标题和描述都相似（> 0.7）+ 负责人相同

## 🧪 测试

运行测试脚本验证功能：

```bash
python test_semantic_dedup.py
```

## 📊 性能对比

| 模型 | 大小 | 速度 | 中文效果 | 推荐场景 |
|------|------|------|----------|----------|
| text2vec-base-chinese | ~400MB | 快 | ⭐⭐⭐⭐⭐ | 中文项目（推荐） |
| bge-small-zh-v1.5 | ~100MB | 很快 | ⭐⭐⭐⭐⭐ | 资源受限环境 |
| paraphrase-multilingual | ~420MB | 快 | ⭐⭐⭐ | 多语言项目 |
| 规则去重（降级） | 0 | 极快 | ⭐⭐ | 无依赖环境 |

## 💡 最佳实践

1. **首次使用**：模型会自动下载到 `~/.cache/` 目录，需要网络连接
2. **离线部署**：提前下载模型文件，设置 `TRANSFORMERS_CACHE` 环境变量
3. **性能优化**：使用单例模式避免重复加载模型（已内置）
4. **批量处理**：一次性处理多个文档时，模型只加载一次

## 🔧 故障排查

### 问题 1：模型下载失败

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
pip install text2vec
```

### 问题 2：内存不足

使用更小的模型：

```python
result = semantic_dedup_todos(todos, model_name="BAAI/bge-small-zh-v1.5")
```

### 问题 3：依赖冲突

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install text2vec
```

## 📈 效果示例

**输入（6 条）：**
1. 完成用户登录功能开发
2. 开发用户登录模块（语义相似）
3. 优化数据库查询性能
4. 提升数据库查询效率（语义相似）
5. 编写API文档
6. 修复支付模块bug

**输出（4 条）：**
1. 完成用户登录功能开发（合并了第2条）
2. 优化数据库查询性能（合并了第4条）
3. 编写API文档
4. 修复支付模块bug

**去重率：33%**
