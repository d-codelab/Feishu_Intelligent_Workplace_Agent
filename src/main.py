"""Main entry point for running the Feishu Intelligent Workplace Agent.

Support multiple dimension triggers:
1. Long-living WebSocket connection for manual trigger (IM) and events (Docs/Comments).
2. Scheduled Cron job trigger using APScheduler for processing target docs.
"""

import logging
import re
import signal
import sys

import lark_oapi as lark
from apscheduler.schedulers.background import BackgroundScheduler
from lark_oapi.api.im.v1 import (
    P2ImMessageReceiveV1,
)

from todo_agent.clients.auth import get_access_token
from todo_agent.clients.drive import list_files_in_folder
from todo_agent.clients.im import list_chats
from todo_agent.config import config
from todo_agent.services.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_doc_todos(doc_token: str):
    """Placeholder: Call the LLM extraction logic and trigger pipeline."""
    logger.info(f"[*] 触发抽取链路: doc_token={doc_token}")

    # 队友负责抽取功能
    # ... extract Logic ...

    # 获取抽取结果后，这里负责写入和同步链路
    logger.info("[*] (Mock) 根据抽取结果执行写入同步")
    # For now, optionally just log or run a mocked version:
    todos = [
        {
          "title": "测试演示闭环",
          "description": "两天内测试最小可演示闭环，完成技术可行性验证，确认核心链路可测试",
          "owner_open_id": "ou_5861fdd8ba230b2a2ae9254b4e52df2a",
          "deadline": "1777647368627",
          "status": "待开始",
          "priority": "",
          "source_type": "飞书任务",
          "evidence": "两天内测试一个最小可演示闭环：模拟办公数据 → OpenClaw/CLI 抽取事项 → 输出结构化 JSON → API 写入飞书多维表格 → 机器人发送整理结果",
          "source_link": "https://xxx.feishu.cn/doc/FVsKw2E0xiEOGwkTezhcvyHEnNc"
        }
      ]
    run_pipeline(todos)

def process_chat_todos(chat_id: str):
    """Placeholder: Call the LLM extraction logic for chats and trigger pipeline."""
    logger.info(f"[*] 触发群聊抽取链路: chat_id={chat_id}")
    # 这里可以添加提取群聊记录并喂给LLM的逻辑


def handle_scheduled_scan():
    """Triggered by APScheduler every morning at 9:00"""
    logger.info(f"==== 开始执行定时巡检任务 ====")
    folder_token = "IHTzf0VO4lILOYd75z3cV09AnKe"
    try:
        files = list_files_in_folder(folder_token)
        for f in files:
            file_token = f.get("token")
            file_name = f.get("name")
            logger.info(f"-> 扫描文档: {file_name} ({file_token})")
            try:
                process_doc_todos(file_token)
            except Exception as e:
                logger.error(f"处理文档 {file_name} 失败: {e}")
    except Exception as e:
        logger.error(f"获取文件夹列表失败: {e}")
    logger.info(f"==== 定时巡检任务完成 ====")


def handle_chat_scan():
    """Triggered by APScheduler every day at 18:00"""
    logger.info(f"==== 开始执行群聊定时巡检任务 ====")
    try:
        chats = list_chats()
        for c in chats:
            chat_id = c.get("chat_id")
            chat_name = c.get("name")
            logger.info(f"-> 扫描群聊: {chat_name} ({chat_id})")
            try:
                process_chat_todos(chat_id)
            except Exception as e:
                logger.error(f"处理群聊 {chat_name} 失败: {e}")
    except Exception as e:
        logger.error(f"获取群聊列表失败: {e}")
    logger.info(f"==== 群聊定时巡检任务完成 ====")


def handle_im_message(data: P2ImMessageReceiveV1) -> None:
    """Handle receiving messages (manual trigger) via WebSocket."""
    msg = data.event.message
    content = msg.content
    logger.info(f"[WebSocket] 收到用户消息: {content}")
    # Very simple parsing logic for demo:
    if "feishu.cn" in content or "文档" in content:
        logger.info("[WebSocket] 检测到文档链接/命令，触发解析与抽取...")
        doc_token = parse_token_from_url(content)
        process_doc_todos(doc_token)
    return None

def parse_token_from_url(content: str) -> str:
    """从输入内容或飞书链接中解析出文档 token。"""
    match = re.search(r'/(?:doc|docx|wiki)/([a-zA-Z0-9]+)', content)
    if match:
        print(f"解析到文档 token: {match.group(1)}")
        return match.group(1)
    # 如果未匹配到 URL 格式，假设传入的就是 token 文本
    return content.strip()

def refresh_access_token_job() -> None:
    """Refresh tenant access token on a fixed schedule."""
    try:
        get_access_token(force_refresh=True)
        logger.info("✅ 已定时刷新 tenant access token")
    except Exception as e:
        logger.error(f"❌ 定时刷新 token 失败: {e}")


def main():
    app_id, app_secret = config.require_app_credentials()

    # 1. 建立长连接监听器 (WebSocket)
    # Handles manual messaging and event subscriptions
    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_im_message) \
        .build()

    cli = lark.ws.Client(
        app_id=app_id,
        app_secret=app_secret,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO
    )

    # 2. 定时任务配置
    scheduler = BackgroundScheduler()
    # 设定每天早上 9:00 扫描一次共享文件夹列表，触发抽取与同步流程
    # scheduler.add_job(handle_scheduled_scan, trigger='cron', hour=9, minute=0)
    scheduler.add_job(handle_scheduled_scan, trigger='interval', seconds=60)  # For demo, run every 60s

    # 设定每天晚上 18:00 扫描一次群聊，触发抽取与同步流程
    # scheduler.add_job(handle_chat_scan, trigger='cron', hour=18, minute=0)
    # scheduler.add_job(handle_chat_scan, trigger='interval', seconds=30)  # For demo, run every 30s

    # 定时刷新 token，确保长连接稳定
    scheduler.add_job(refresh_access_token_job, trigger='interval', minutes=60)
    scheduler.start()
    logger.info("已启动定时任务调度器 (每天9:00)")

    # 3. 启动并阻塞
    logger.info("正在建立与飞书服务器的 WebSocket 长连接...")

    def signal_handler(sig, frame):
        logger.info("收到中止信号，正在关闭服务...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        cli.start()
    except KeyboardInterrupt:
        logger.info("服务关闭...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
