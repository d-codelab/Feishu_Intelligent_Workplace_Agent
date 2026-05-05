# Claude Code 项目说明

## 项目概述

这是一个飞书智能办公 Agent 项目，用于从飞书的多个数据源（文档、日历、聊天、妙记、任务）中自动提取待办事项，并写入飞书多维表格。

## 项目结构

```
src/
├── todo_extractor/          # TODO 抽取模块（可修改）
│   ├── clients/            # 飞书 API 客户端
│   ├── extractors/         # 各数据源的抽取器
│   └── llm/                # LLM 抽取逻辑
├── todo_agent/             # TODO Agent 模块  (⚠️ 不可修改)
│   ├── clients/            # 多维表格、IM 客户端
│   ├── services/           # 业务逻辑服务
│   └── scripts/            # 工具脚本
├── bitable_writer.py       # ⚠️ 不可修改
├── bot_sender.py           # ⚠️ 不可修改
└── feishu_client.py        # ⚠️ 不可修改
```

## ⚠️ 不可修改的文件和模块

以下文件和模块由队友负责维护，**请勿修改**：

### 1. `src/todo_agent/` 目录（整个目录不可修改）
TODO Agent 模块，负责将抽取的待办事项写入多维表格并发送通知。
- `clients/` - 多维表格、IM 客户端
- `services/` - 业务逻辑服务
- `scripts/` - 工具脚本

### 2. 根目录下的核心文件
- **`src/bitable_writer.py`** - 多维表格写入逻辑
- **`src/bot_sender.py`** - 飞书机器人消息发送
- **`src/feishu_client.py`** - 飞书 API 基础客户端

## ✅ 可修改的模块

### `src/todo_extractor/` 目录
这是你负责的模块，可以自由修改和新增文件。

**核心文件：**
- `clients/feishu_api.py` - 飞书文档 API，支持 blocks 解析
- `clients/calendar_api.py` - 日历 API
- `clients/task_api.py` - 任务 API
- `clients/minutes_api.py` - 妙记 API
- `extractors/feishu_doc.py` - 文档抽取器
- `extractors/feishu_calendar.py` - 日历抽取器
- `extractors/feishu_im.py` - 聊天抽取器
- `extractors/feishu_minutes.py` - 妙记抽取器
- `extractors/feishu_task.py` - 任务抽取器
- `llm/client.py` - LLM 抽取客户端
- `llm/prompts.py` - 抽取 Prompt 模板

**可以新增文件**：在 `src/todo_extractor/` 目录下可以自由创建新文件和子目录

## 开发指南

### 修改 TODO 抽取逻辑
如果需要修改抽取逻辑，请编辑：
- `src/todo_extractor/llm/prompts.py` - 修改 Prompt
- `src/todo_extractor/extractors/*.py` - 修改特定数据源的抽取逻辑

### 修改文档解析
如果需要修改飞书文档解析（blocks API）：
- `src/todo_extractor/clients/feishu_api.py` - 修改 blocks 解析逻辑

### 添加新的数据源
1. 在 `src/todo_extractor/extractors/` 创建新的抽取器
2. 继承 `BaseExtractor` 类
3. 实现 `extract()` 方法

### 测试
项目根目录下的测试文件：
- `test_doc_extraction.py` - 文档抽取测试
- `test_calendar_extraction.py` - 日历抽取测试
- `test_chat_extraction.py` - 聊天抽取测试
- `test_minutes_extraction.py` - 妙记抽取测试
- `test_task_extraction.py` - 任务抽取测试

## 注意事项

1. **不要修改不可修改的文件**：`bitable_writer.py`, `bot_sender.py`, `feishu_client.py`
2. **保持 API 兼容性**：修改时确保不破坏现有接口
3. **添加测试**：新功能需要添加对应的测试文件
4. **文档更新**：重大修改需要更新此文档

## 环境配置

需要配置以下环境变量：
- `FEISHU_APP_ID` - 飞书应用 ID
- `FEISHU_APP_SECRET` - 飞书应用密钥
- `ANTHROPIC_API_KEY` - Claude API 密钥（用于 LLM 抽取）

## 联系方式

如有问题，请联系项目维护者。
