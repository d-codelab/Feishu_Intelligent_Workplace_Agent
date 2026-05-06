"""Main entry point for running the Feishu Intelligent Workplace Agent.

Support multiple dimension triggers:
1. Long-living WebSocket connection for manual trigger (IM) and events (Docs/Comments).
2. Scheduled Cron job trigger using APScheduler for processing target docs.
"""

import logging
import re
import signal
import sys
import threading

import requests
import lark_oapi as lark
from apscheduler.schedulers.background import BackgroundScheduler
from lark_oapi.api.im.v1 import (
    P2ImMessageReceiveV1,
)
from lark_oapi.api.vc.v1 import P2VcMeetingMeetingEndedV1

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
    todos = []
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


def _async_handle_im_message(data: P2ImMessageReceiveV1) -> None:
    """Async worker for processing IM messages."""
    msg = data.event.message
    content = msg.content
    logger.info(f"[WebSocket] 收到用户消息: {content}")
    # Very simple parsing logic for demo:
    if "feishu.cn" in content or "文档" in content:
        logger.info("[WebSocket] 检测到文档链接/命令，触发解析与抽取...")
        doc_token = parse_token_from_url(content)
        process_doc_todos(doc_token)

def handle_im_message(data: P2ImMessageReceiveV1) -> None:
    """Handle receiving messages (manual trigger) via WebSocket."""
    # 将整个处理逻辑放入内部异步线程，确保最快速度（毫秒级）返回，彻底杜绝飞书 3s 超时重试问题
    threading.Thread(target=_async_handle_im_message, args=(data,)).start()
    return None

def _async_handle_meeting_ended(data: P2VcMeetingMeetingEndedV1) -> None:
    """Async worker for processing meeting ended events."""
    try:
        meeting = data.event.meeting
        # 根据飞书 SDK 数据结构提取 meeting_id
        meeting_id = getattr(meeting, "id", None)
        logger.info(f"[WebSocket] 收到会议结束事件, meeting_id={meeting_id}")

        # 调用纪要接口拿到document_token
        access_token = get_access_token()
        url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{meeting_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers)

        doc_token = None
        if resp.status_code == 200:
            resp_data = resp.json().get("data", {}).get("meeting", {})
            related_artifacts = resp_data.get("related_artifacts", {})
            doc_token = related_artifacts.get("note_doc_token")

        if not doc_token:
            # fallback 到已知可用的mock文档进行测试
            doc_token = config.doc_token
            logger.info("未获取到实际 doc_token，使用 mock document_token 进行演示")

        logger.info(f"[WebSocket] 获取到纪要文档 document_token={doc_token}，触发解析与抽取...")
        process_doc_todos(doc_token)
    except Exception as e:
        logger.error(f"处理 meeting_ended 事件失败: {e}")

def handle_meeting_ended(data: P2VcMeetingMeetingEndedV1) -> None:
    """Handle receiving meeting ended event via WebSocket."""
    threading.Thread(target=_async_handle_meeting_ended, args=(data,)).start()
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
        .register_p2_vc_meeting_meeting_ended_v1(handle_meeting_ended) \
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

    # 设定每天中午 12:00 和晚上 18:00 扫描一次群聊，触发抽取与同步流程
    # scheduler.add_job(handle_chat_scan, trigger='cron', hour=12, minute=0)
    # scheduler.add_job(handle_chat_scan, trigger='cron', hour=18, minute=0)
    scheduler.add_job(handle_chat_scan, trigger='interval', seconds=120)  # For demo, run every 30s

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
