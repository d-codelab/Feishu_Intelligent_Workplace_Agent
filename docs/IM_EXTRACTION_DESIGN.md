# 群聊消息 TODO 抽取设计方案

## 业务场景

**定时任务**：每天早上 9:00 抽取前 24 小时的群聊消息，识别待办事项

## 核心挑战

1. **上下文依赖**：群聊是对话形式，单条消息可能缺少完整信息
   ```
   张三: "明天的需求评审会"
   李四: "几点开始？"
   张三: "下午2点，记得准备PPT"  ← 需要结合前面的消息才能理解
   ```

2. **噪声过滤**：群聊包含大量闲聊、表情、无关信息
   ```
   "哈哈哈"
   "收到"
   "[图片]"
   "👍"
   ```

3. **任务分散**：同一个任务可能在多条消息中讨论
   ```
   消息1: "下周要上线支付功能"
   消息5: "支付功能的测试用例谁来写？"
   消息10: "我来写，周五前完成"
   ```

## 设计方案

### 方案 A：轻量级方案（推荐）

**适用场景**：24小时消息量 < 500条

**Pipeline：**
```
1. 获取消息（24小时）
   ↓
2. 预处理（过滤噪声）
   - 移除纯表情消息
   - 移除"收到"、"好的"等无效回复
   - 保留图片/文件的描述信息
   ↓
3. 时间排序（保持对话连贯性）
   ↓
4. 上下文增强
   - 为每条消息添加"对话窗口"（前后3条消息）
   - 标注发言人和时间
   ↓
5. LLM 抽取（单阶段）
   - 使用专门的"群聊 Prompt"
   - 要求 LLM 识别：谁、做什么、什么时候
   ↓
6. 后处理
   - 置信度过滤（< 0.6 丢弃）
   - 规则去重（标题相似度）
   - 补充来源链接
```

**优势：**
- ✅ 简单高效，成本低
- ✅ 适合中小规模群聊
- ✅ 保持对话上下文

**实现复杂度：** ⭐⭐ (1-2小时)

---

### 方案 B：话题分段方案（高级）

**适用场景**：消息量大（> 500条）或需要展示技术深度

**Pipeline：**
```
1. 获取消息（24小时）
   ↓
2. 预处理（同方案A）
   ↓
3. 话题分段（使用 LLM 或规则）
   - 识别话题切换点
   - 将消息分成多个"对话段"
   例如：
     段1: 讨论需求评审会（消息1-15）
     段2: 讨论支付功能上线（消息16-30）
     段3: 讨论测试用例（消息31-45）
   ↓
4. 分段抽取
   - 每个话题独立抽取 TODO
   - 保留话题上下文
   ↓
5. 跨段去重
   - 合并不同话题中的相同任务
   ↓
6. 时间线重建
   - 按讨论顺序展示 TODO
```

**优势：**
- ✅ 更精确（话题隔离）
- ✅ 展示 AI 能力（话题识别）
- ✅ 适合大规模群聊

**实现复杂度：** ⭐⭐⭐⭐ (3-4小时)

---

## 推荐方案：方案 A + 亮点优化

### 核心改进点

#### 1. 专门的"群聊 Prompt"

```python
CHAT_EXTRACTION_PROMPT = """
你是一个专业的任务识别助手，负责从群聊记录中识别待办事项。

# 群聊特点
- 对话形式，需要结合上下文理解
- 包含多人讨论，注意识别负责人
- 时间信息可能分散在多条消息中

# 识别规则
1. 明确的任务分配：
   - "张三，你来负责..."
   - "这个任务交给李四"
   
2. 承诺性表述：
   - "我明天完成"
   - "周五前提交"
   
3. 待办事项标记：
   - "TODO: ..."
   - "记得..."
   - "别忘了..."

# 输出要求
- 事项标题：简洁明确（10字以内）
- 负责人：从对话中识别（如果无法确定，标注"待确认"）
- 截止日期：相对时间转换为绝对日期（"明天" → 2024-03-15）
- 置信度：0-1，表示识别的确定性

# 群聊记录
{chat_history}

# 输出格式（JSON）
[
  {
    "事项标题": "...",
    "事项描述": "...",
    "负责人": "...",
    "截止日期": "YYYY-MM-DD",
    "置信度": 0.0-1.0
  }
]
"""
```

#### 2. 消息预处理（过滤噪声）

```python
def preprocess_messages(messages: list[dict]) -> list[dict]:
    """过滤无效消息"""
    
    # 无效消息模式
    NOISE_PATTERNS = [
        r'^[哈嘿呵嗯啊哦]+$',  # 纯语气词
        r'^[👍😄😊🙏💪]+$',    # 纯表情
        r'^(收到|好的|OK|ok|知道了)$',  # 简单确认
        r'^\[图片\]$',  # 纯图片
        r'^\[文件\]$',  # 纯文件
    ]
    
    filtered = []
    for msg in messages:
        content = msg['content'].strip()
        
        # 跳过空消息
        if not content:
            continue
            
        # 跳过噪声消息
        is_noise = any(re.match(pattern, content) for pattern in NOISE_PATTERNS)
        if is_noise:
            continue
            
        filtered.append(msg)
    
    return filtered
```

#### 3. 相对时间转换

```python
def resolve_relative_time(text: str, base_date: datetime) -> str:
    """将相对时间转换为绝对日期
    
    例如：
    - "明天" → "2024-03-15"
    - "下周五" → "2024-03-22"
    - "本月底" → "2024-03-31"
    """
    
    # 明天/后天
    if "明天" in text or "明日" in text:
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if "后天" in text:
        return (base_date + timedelta(days=2)).strftime("%Y-%m-%d")
    
    # 下周X
    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6}
    for day_name, day_num in weekday_map.items():
        if f"下周{day_name}" in text:
            days_ahead = day_num - base_date.weekday() + 7
            return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # 本周X
    for day_name, day_num in weekday_map.items():
        if f"本周{day_name}" in text or f"周{day_name}" in text:
            days_ahead = day_num - base_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    return "待确认"
```

---

## 实现计划

### Phase 1: 基础功能（1小时）
- [x] 消息预处理（过滤噪声）
- [ ] 群聊专用 Prompt
- [ ] 相对时间转换

### Phase 2: 优化（1小时）
- [ ] 上下文窗口增强
- [ ] 置信度过滤
- [ ] 规则去重

### Phase 3: 测试（30分钟）
- [ ] 真实群聊数据测试
- [ ] 边界情况验证
- [ ] 性能优化

---

## 定时任务配置

```python
# 每天早上 9:00 执行
SCHEDULE = "0 9 * * *"

def daily_chat_extraction():
    """定时任务：抽取前24小时群聊消息"""
    
    # 1. 获取需要监控的群聊列表
    chat_ids = get_monitored_chats()
    
    # 2. 逐个群聊抽取
    all_todos = []
    for chat_id in chat_ids:
        extractor = FeishuIMExtractor(mode="batch")
        todos = extractor.extract(chat_id, hours=24)
        all_todos.extend(todos)
    
    # 3. 写入多维表格
    write_to_bitable(all_todos)
    
    # 4. 发送通知
    send_notification(f"今日待办：{len(all_todos)} 条")
```

---

## 对比：文档 vs 群聊

| 维度 | 文档抽取 | 群聊抽取 |
|------|---------|---------|
| **数据特点** | 结构化、长文本 | 对话式、碎片化 |
| **上下文** | 完整、独立 | 分散、依赖前后文 |
| **噪声** | 少 | 多（闲聊、表情） |
| **重复率** | 高（反复提同一任务） | 低（讨论即时性强） |
| **Pipeline** | 多阶段（分块→粗抽→精筛→去重） | 单阶段（预处理→抽取→过滤） |
| **技术重点** | 智能分块、语义去重 | 上下文理解、时间解析 |

---

## 总结

**推荐方案：方案 A（轻量级）+ 3个亮点优化**

1. ✅ **群聊专用 Prompt**：针对对话特点设计
2. ✅ **消息预处理**：过滤噪声，提高信噪比
3. ✅ **相对时间转换**：自动解析"明天"、"下周五"

**实现时间：** 2-3 小时
**技术亮点：** 中等（足够展示 AI 能力，不过度复杂）
**实用性：** 高（真正解决用户痛点）
