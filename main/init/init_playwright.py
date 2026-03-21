# -*-coding:utf-8 -*-
"""
# File       : init_playwright.py
# Description: 初始化 Playwright 浏览器内核（跨 Win/Linux）
"""
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _browser_root() -> Path:
    # 优先使用环境变量 PLAYWRIGHT_BROWSERS_PATH
    env_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
    if env_path:
        return Path(env_path)

    system = platform.system().lower()
    if system == "windows":
        return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "ms-playwright"
    # Linux / macOS 默认缓存目录
    return Path.home() / ".cache" / "ms-playwright"


def _chromium_exists() -> bool:
    root = _browser_root()
    if not root.exists():
        return False
    # 常见目录：chromium-xxxx, chromium_headless_shell-xxxx
    for pattern in ("chromium*", "chromium_headless_shell*"):
        for p in root.glob(pattern):
            if p.is_dir() and any(p.rglob("chrome")):
                return True
    return False


def init_playwright():
    """确保 Playwright Chromium 已安装（幂等，可多次执行）。"""
    if _chromium_exists():
        logger.info("Playwright Chromium 已存在，跳过下载。")
        return

    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    # Linux 推荐携带依赖
    if platform.system().lower() == "linux":
        cmd.append("--with-deps")

    logger.info("未检测到 Playwright Chromium，正在执行：%s", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        logger.info("Playwright Chromium 安装完成。")
    except Exception as e:
        logger.error("Playwright Chromium 安装失败：%s", e, exc_info=True)
        # 不抛出，避免阻断其他初始化脚本


__all__ = ["init_playwright"]
