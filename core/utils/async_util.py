import asyncio
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    在同步上下文中运行协程，兼容有/无事件循环两种情况。

    - 已有事件循环（Django 异步视图）：创建 Task 异步执行，绑定 done_callback 记录异常。
    - 无事件循环（同步视图 / 信号 / on_commit 回调）：直接 asyncio.run() 阻塞执行。
    """
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(coro)
        task.add_done_callback(_log_task_exception)
    except RuntimeError:
        asyncio.run(coro)


def _log_task_exception(task: asyncio.Task):
    if not task.cancelled() and task.exception() is not None:
        logger.error(
            "Async task %r raised an unhandled exception",
            task.get_name(),
            exc_info=task.exception(),
        )
