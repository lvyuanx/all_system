#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@File    : async_plugin_manager.py
@Author  : lvyuanxiang
@Time    : 2025-12-25
@Desc    :
    异步插件管理器(单利模式)
"""
import logging
import asyncio
from collections import defaultdict
import time
from typing import Any, Awaitable, Dict, List, Set

from core.utils.common_util import SingletonBase
from .async_plugin import AsyncPluginBase

logger = logging.getLogger(__name__)

banner = """
   ___ _             _                           
  / _ \ |_   _  __ _(_)_ __     /\/\   __ _ _ __ 
 / /_)/ | | | |/ _` | | '_ \   /    \ / _` | '__|
/ ___/| | |_| | (_| | | | | | / /\/\ \ (_| | |   
\/    |_|\__,_|\__, |_|_| |_| \/    \/\__, |_|   
               |___/                  |___/      
"""


class PluginManager(SingletonBase):

    def _init(self):
        self.running: bool = True
        self._shutdown_event = asyncio.Event()
        self._tasks: Set[asyncio.Task] = set()
        self._plugins: Dict[str, AsyncPluginBase] = {}

    async def shutdown_wait(self):
        await self._shutdown_event.wait()

    # ------------------------
    # 插件管理
    # ------------------------
    def register(self, plugin: AsyncPluginBase):
        self._plugins[plugin.plugin_name] = plugin
        plugin.set_plugin_manager(self)

    # ------------------------
    # spawn（你给的核心逻辑）
    # ------------------------
    def spawn(self, coro: Awaitable[Any], name: str) -> asyncio.Task | None:
        """创建任务并登记，关停时统一取消"""
        if not self.running or self._shutdown_event.is_set():
            logger.debug(f"跳过任务创建（应用正在关闭）: {name}")
            return None

        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)

        def _done(t: asyncio.Task):
            self._tasks.discard(t)
            if not t.cancelled() and t.exception():
                logger.error(
                    f"任务 {name} 异常结束: {t.exception()}",
                    exc_info=True,
                )

        task.add_done_callback(_done)
        return task

    # ------------------------
    # 权重分组
    # ------------------------
    def _group_by_weight(self, plugins: List[AsyncPluginBase] = None) -> List[List[AsyncPluginBase]]:
        """
        按 weight 分组，并按 weight 从大到小排序
        """
        plugins = plugins or list(self._plugins.values())
        groups = defaultdict(list)
        for plugin in plugins:
            groups[plugin.weight].append(plugin)

        sorted_groups = sorted(
            groups.items(),
            key=lambda x: x[0],
            reverse=True,
        )
        return [gplugins for _, gplugins in sorted_groups]

    # ------------------------
    # start_all / stop_all
    # ------------------------
    async def start_all(self):
        """
        启动所有插件，按权重调度：
        - 同权重：并行
        - 不同权重：高权重先
        """
        logger.info(banner)
        logger.info(f"{'*' * 15}启动所有插件{'*' * 15}")
        start_time = time.time()
        plugin_group = self._group_by_weight()
        ready_tasks = []
        for plugins in plugin_group:
            tasks = []
            for plugin in plugins:
                plugin_name = plugin.plugin_name
                logger.info(f"启动插件 [{plugin_name}] ...")
                task = self.spawn(plugin.start(), f"start:{plugin_name}")
                if task:
                    tasks.append(task)
                ready_task = self.spawn(
                    plugin.wait_ready(),
                    f"wait_ready:{plugin_name}",
                )
                if ready_task:
                    ready_tasks.append(ready_task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(0)  # 让出事件循环

        if ready_tasks:  # 等待所有插件就绪
            await asyncio.gather(*ready_tasks, return_exceptions=True)

        logger.info(f"{'*' * 15}所有插件启动完成 (总耗时：{time.time() - start_time:.3f}){'*' * 15}")

    async def stop_all(self):
        """
        停止所有插件，按权重调度
        """
        logger.info(f"{'*' * 15}停止所有插件{'*' * 15}")
        for plugins in self._group_by_weight().reverse():
            tasks = []
            for plugin in plugins:
                plugin_name = plugin.plugin_name
                logger.info(f"停止插件: {plugin_name} ...")
                task = self.spawn(plugin.stop(), f"stop:{plugin_name}")
                if task:
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(0)
        logger.info(f"{'*' * 15}所有启动插件停止完成{'*' * 15}")

    # ------------------------
    # 按权重广播（组内消息）
    # ------------------------
    async def send_broadcast_by_weight(self, provider: str, action: str, data: Any = None):
        """
        广播规则：
        - 同权重：并行
        - 不同权重：权重大先
        """
        for plugins in self._group_by_weight():
            tasks = set()
            for plugin in plugins:
                task = self.spawn(
                    plugin._receive_broadcast(provider, action, data),
                    f"broadcast:{provider}->{plugin.plugin_name}",
                )
                if task:
                    tasks.add(task)
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0)

    # ------------------------
    # 普通广播（无权重）
    # ------------------------
    def send_broadcast(self, provider: str, action: str, data: Any = None):
        for name, plugin in self._plugins.items():
            if name == provider:
                continue
            self.spawn(
                plugin._receive_broadcast(provider, action, data),
                f"broadcast:{provider}->{name}",
            )
    
    # ------------------------
    # 通知指定插件
    # ------------------------
    async def send_to(self,  provider: str, names: list[str], action: str, data: Any = None):
        plugins = [self._plugins[name] for name in names if name in self._plugins]

        len_plugins = len(plugins)
        if not len_plugins:
            logger.error("无插件可通知!")
            return
        
        if len_plugins != len(names):
            logger.warning(f"找不到指定插件: {[name for name in names if name not in self._plugins]}")

        group = self._group_by_weight(plugins)
        for gplugins in group:
            tasks = set()
            for plugin in gplugins:
                task = self.spawn(
                    plugin._receive_broadcast(provider, action, data),
                    f"broadcast:{provider}->{plugin.plugin_name}",
                )
                if task:
                    tasks.add(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(0)

    # ------------------------
    # shutdown
    # ------------------------
    async def shutdown(self):
        self.running = False
        self._shutdown_event.set()

        for task in list(self._tasks):
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()



class AsyncPluginBase:

    weight = 50  # 0~100，越大越先执行
    name = None  # 插件名称

    def __init__(self):
        self._plugin_manager = None
        self._start_time = None

    def set_plugin_manager(self, plugin_manager):
        self._plugin_manager = plugin_manager

    @property
    def plugin_name(self):
        return self.name or self.__class__.__name__

    async def _receive_broadcast(self, provider: str, action: str, data: Any = None):
        """收到广播"""
        func_name = f"action_{action}"
        if hasattr(self, func_name):
           action_func = getattr(self, func_name)
           if callable(action_func): 
                try:
                    await action_func(provider, data)
                except Exception as e:
                    logger.exception(f"插件[{self.plugin_name}]执行方法[{func_name}]异常：{e}")

    def send_broadcast(self, action: str, data: Any = None):
        """发送广播"""
        logger.info(f"插件[{self.plugin_name}]发送广播 -> {action}")
        self._plugin_manager.send_broadcast(self.plugin_name, action, data)

    def send_broadcast_by_weight(self, action: str, data: Any = None):
        """按权重发送广播"""
        logger.info(f"插件[{self.plugin_name}]发送广播(权重) -> {action}")
        self._plugin_manager.spawn(
            self._plugin_manager.send_broadcast_by_weight(
                self.plugin_name, action, data
            ),
            f"{self.plugin_name}:send_broadcast_by_weight:{action}"
        )

    def send_to(self, names: list[str], action: str, data: Any = None):
        """指定插件发送广播"""
        logger.info(f"插件[{self.plugin_name}]发送广播(指定插件) -> {action}")
        self._plugin_manager.spawn(
            self._plugin_manager.send_to(self.plugin_name, names, action, data),
            f"{self.plugin_name}:send_to:{action}"
        )

    async def _start(self):
        """插件启动入口"""

    async def start(self):
        self.start_time = time.time()
        self._plugin_manager.spawn(self._start(), self.plugin_name)

    async def _wait_ready(self):
        """等待插件就绪"""

    async def wait_ready(self):
        """等待插件就绪"""
        await self._wait_ready()
        logger.info(
            f"插件 [{self.plugin_name}] 准备就绪！耗时：{time.time() - self.start_time:.3f}s"
        )

    async def _stop(self):
        """插件停止入口"""

    async def stop(self):
        plugin_name = self.plugin_name
        logger.info(f"插件 {plugin_name} 关闭中...")
        self._plugin_manager.spawn(self._stop(), plugin_name)
