"""Main entry point for running the Feishu Intelligent Workplace Agent.

Support multiple dimension triggers:
1. Long-living WebSocket connection for manual trigger (IM) and events (Docs/Comments).
2. Scheduled Cron job trigger using APScheduler for processing target docs.
"""

import logging
import os
import signal
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    P2ImMessageReceiveV1,
)

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
    # todos = mock_extract(doc_token)
    # result = run_pipeline(todos)


def handle_scheduled_scan():
    """Triggered by APScheduler every morning at 9:00"""
    logger.info(f"==== 开始执行定时巡检任务 ====")
    docs = getattr(config, 'target_docs', [])
    for doc in docs:
        logger.info(f"-> 扫描文档: {doc['title']} ({doc['token']})")
        process_doc_todos(doc['token'])
    logger.info(f"==== 定时巡检任务完成 ====")


def handle_im_message(data: P2ImMessageReceiveV1) -> None:
    """Handle receiving messages (manual trigger) via WebSocket."""
    msg = data.event.message
    content = msg.content
    logger.info(f"[WebSocket] 收到用户消息: {content}")
    # Very simple parsing logic for demo:
    if "feishu.cn" in content or "文档" in content:
        logger.info("[WebSocket] 检测到文档链接/命令，触发解析与抽取...")
        # doc_token = parse_token_from_url(content)
        # process_doc_todos(doc_token)
    return None


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
    # 设定每天早上 9:00 扫描。Demo阶段可改为每分钟等用于测试 (e.g., trigger='cron', hour=9, minute=0)
    scheduler.add_job(handle_scheduled_scan, trigger='cron', hour=9, minute=0)
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
