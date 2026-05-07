# 飞书智能办公 Agent

一个基于 LLM 的智能待办事项提取系统，自动从飞书的多个数据源（文档、日历、聊天、妙记、任务）中提取待办事项，并写入飞书多维表格进行统一管理。

## 功能特性

- **多数据源支持**：支持从飞书文档、日历、群聊、妙记、任务中提取待办事项
- **智能提取**：基于 Claude LLM 的智能语义理解和结构化抽取
- **实时监听**：通过 WebSocket 长连接监听飞书事件，实时处理新增内容
- **定时扫描**：支持定时扫描指定文档和群聊，自动更新待办事项
- **自动去重**：基于语义相似度的智能去重，避免重复待办
- **多维表格集成**：自动写入飞书多维表格，支持字段映射和状态管理

## 项目结构

```
src/
├── main.py                  # 主入口文件
├── todo_extractor/          # TODO 抽取模块
│   ├── clients/            # 飞书 API 客户端
│   │   ├── feishu_api.py   # 文档 API（支持 blocks 解析）
│   │   ├── calendar_api.py # 日历 API
│   │   ├── task_api.py     # 任务 API
│   │   ├── minutes_api.py  # 妙记 API
│   │   └── auth.py         # 认证模块
│   ├── extractors/         # 各数据源的抽取器
│   │   ├── base.py         # 抽取器基类
│   │   ├── feishu_doc.py   # 文档抽取器
│   │   ├── feishu_calendar.py  # 日历抽取器
│   │   ├── feishu_im.py    # 聊天抽取器
│   │   ├── feishu_minutes.py   # 妙记抽取器
│   │   └── feishu_task.py  # 任务抽取器
│   ├── llm/                # LLM 抽取逻辑
│   │   ├── client.py       # LLM 客户端
│   │   └── prompts.py      # 抽取 Prompt 模板
│   ├── utils/              # 工具模块
│   │   ├── chunker.py      # 文本分块
│   │   ├── deduplicator.py # 去重逻辑
│   │   └── semantic_dedup.py   # 语义去重
│   └── pipeline.py         # 抽取流水线
└── todo_agent/             # TODO Agent 模块
    ├── clients/            # 多维表格、IM 客户端
    ├── services/           # 业务逻辑服务
    │   ├── bitable_writer.py   # 多维表格写入
    │   ├── todo_mapper.py      # 字段映射
    │   ├── pipeline.py         # 处理流水线
    │   └── summary_sender.py   # 消息发送
    └── scripts/            # 工具脚本
```

## 快速开始

### 环境要求

- Python 3.9+
- 飞书企业账号
- Claude API Key

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

配置项说明：

```env
# 飞书应用凭证
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# 多维表格配置
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token
FEISHU_BITABLE_TABLE_ID=your_table_id

# 用户访问令牌（用于访问日历、任务等）
FEISHU_USER_ACCESS_TOKEN=your_user_access_token

# 通知群聊 ID
FEISHU_CHAT_ID=your_chat_id

# Claude API Key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 运行

```bash
python src/main.py
```

## 使用方式

### 1. 实时监听模式

启动后，系统会通过 WebSocket 监听以下事件：

- **群聊消息**：在群聊中 @机器人 并发送文档链接，自动提取待办
- **文档评论**：在飞书文档中评论 @机器人，触发文档待办提取
- **会议结束**：会议结束后自动提取妙记中的待办事项

### 2. 定时扫描模式

系统会定时扫描配置的文档和群聊：

- 每天定时扫描指定文档夹中的文档
- 定时扫描配置的群聊历史消息

### 3. 手动触发

在群聊中发送以下命令：

```
@机器人 https://example.feishu.cn/docx/xxxxx  # 提取文档待办
@机器人 扫描群聊  # 扫描当前群聊历史消息
```

## 待办事项字段

提取的待办事项包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| 事项标题 | 简洁标题（10字以内） | "完成技术方案" |
| 事项描述 | 详细描述 | "完成618主会场的前端技术方案拆解" |
| 负责人 | 负责人姓名 | "张三" |
| 开始时间 | YYYY-MM-DD 格式 | "2026-05-07" |
| 截止时间 | YYYY-MM-DD 格式 | "2026-05-09" |
| 当前状态 | 待开始/进行中/已完成/有阻塞/已延期/待确认 | "进行中" |
| 优先级 | P0/P1/P2/P3 | "P0" |
| 置信度 | 0.0-1.0 | 0.95 |
| 来源类型 | 飞书文档/会议妙记/群聊消息/飞书任务/日历 | "飞书文档" |
| 来源链接 | 原始链接 | "https://..." |
| 原文依据 | 原文片段 | "技术方案deadline是5月9日" |
| 风险/阻塞 | 风险说明 | "后端排期受线上问题影响" |
| 待确认项 | 需确认的内容 | ["负责人缺失"] |

## 核心特性

### 智能抽取

- **严格验证**：只抽取明确的执行事项，避免误抽讨论、背景信息
- **上下文理解**：基于 LLM 理解会议纪要、文档结构和群聊上下文
- **多阶段抽取**：粗筛 + 精筛两阶段，提高准确率

### 语义去重

- 基于 embedding 的语义相似度计算
- 自动识别重复或相似的待办事项
- 支持跨数据源去重

### 灵活配置

- 支持自定义抽取 Prompt
- 可配置字段映射规则
- 灵活的触发方式（实时/定时/手动）

## 开发指南

详见 [CLAUDE.md](CLAUDE.md) 了解项目开发规范和模块说明。

## 技术栈

- **LLM**：Claude (Anthropic)
- **飞书 SDK**：lark-oapi
- **任务调度**：APScheduler
- **异步处理**：ThreadPoolExecutor
- **向量化**：sentence-transformers（语义去重）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请联系项目维护者。
