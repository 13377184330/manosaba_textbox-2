"""QQ / 微信 聊天软件适配层。"""

from __future__ import annotations

import os
import time
from typing import Literal

ChatApp = Literal["qq", "wechat", "qqwechat", "global"]

APP_PROFILES = {
    "qq": {
        "name": "QQ",
        "delay": 0.1,
        "paste_sleep": 0.3,
        "use_copy_for_text": True,
        "focus_window": True,
        "window_titles": ("QQ",),
    },
    "wechat": {
        "name": "微信",
        "delay": 0.15,
        "paste_sleep": 0.35,
        "use_copy_for_text": True,
        "focus_window": True,
        "window_titles": ("微信", "WeChat", "Weixin"),
    },
    "qqwechat": {
        "name": "QQ微信",
        "delay": 0.12,
        "paste_sleep": 0.32,
        "use_copy_for_text": True,
        "focus_window": True,
        "window_titles": ("QQ", "微信", "WeChat", "Weixin"),
    },
    "global": {
        "name": "全局",
        "delay": 0.15,
        "paste_sleep": 0.35,
        "use_copy_for_text": True,
        "focus_window": False,
        "window_titles": (),
    },
}


def get_chat_app() -> ChatApp:
    value = os.environ.get("MOUSHEN_APP", "qq").strip().lower()
    if value in ("wechat", "wx", "微信"):
        return "wechat"
    if value in ("qqwechat", "qq_wx", "qq_wechat", "qqandwechat", "qq_and_wechat", "qq微信"):
        return "qqwechat"
    if value in ("global", "all", "全局"):
        return "global"
    return "qq"


def get_profile(app: ChatApp | None = None) -> dict:
    return APP_PROFILES[app or get_chat_app()]


def focus_chat_window(app: ChatApp | None = None) -> bool:
    profile = get_profile(app)
    if not profile["focus_window"]:
        return True

    try:
        import win32con
        import win32gui
        import win32api
        import win32process
    except ImportError:
        print("微信模式需要 pywin32，请运行: pip install pywin32")
        return False

    titles = profile["window_titles"]
    matches: list[int] = []

    def _enum(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if title and any(key in title for key in titles):
            matches.append(hwnd)

    win32gui.EnumWindows(_enum, None)
    if not matches:
        print(f"未找到{profile['name']}窗口，请先打开{profile['name']}。")
        return False

    hwnd = matches[0]

    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        win32process.AllowSetForegroundWindow(pid)
    except Exception:
        pass

    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        time.sleep(0.1)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass

    time.sleep(profile["delay"])
    return True


def is_active_window_matching(app: ChatApp | None = None) -> bool:
    """判断当前前台活跃窗口是否属于当前模式允许的应用。
    global 模式总是返回 True（任何窗口都触发）。
    """
    profile = get_profile(app)
    if not profile["focus_window"]:
        return True

    try:
        import win32gui
    except ImportError:
        return False

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or ""
    except Exception:
        return False

    if not title:
        return False

    return any(key in title for key in profile["window_titles"])
