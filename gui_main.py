"""
魔审galgame聊天器
支持 QQ / 微信 / 全局模式
"""

from __future__ import annotations

import argparse
import getpass
import io
import os
import random
import sys
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGroupBox, QTextEdit, QStatusBar,
    QProgressBar, QFrame, QGridLayout, QMessageBox, QCheckBox, QScrollArea,
    QSizePolicy, QSlider, QStackedWidget, QLineEdit, QFileDialog, QButtonGroup
)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "_internal")

import pyperclip
import win32clipboard
from PIL import Image

from chat_adapter import focus_chat_window, get_profile, is_active_window_matching
from config import HELP_TEXT, WECHAT_HELP_EXTRA, mahoshojo, mahoshojo_over, mahoshojo_postion, text_configs_dict
from image_fit_paste import paste_image_auto
from text_fit_draw import draw_text_auto

character_list = list(mahoshojo.keys())

# 角色中文名映射
character_names = {
    "ema": "樱羽艾玛",
    "hiro": "二阶堂希罗",
    "sherri": "橘雪莉",
    "hanna": "远野汉娜",
    "anan": "夏目安安",
    "yuki": "月代雪",
    "meruru": "冰上梅露露",
    "noa": "城崎诺亚",
    "reia": "莲见蕾雅",
    "miria": "佐伯米莉亚",
    "nanoka": "黑部奈叶香",
    "mago": "宝生玛格",
    "alisa": "紫藤亚里沙",
    "coco": "泽渡可可",
}

if os.name == "nt":
    user_documents = os.path.join("C:\\", "Users", getpass.getuser(), "Documents")
else:
    user_documents = os.path.expanduser("~/Documents")

magic_cut_folder = os.path.join(user_documents, "魔裁")
os.makedirs(magic_cut_folder, exist_ok=True)


# =========================================================
# 全局样式常量
# =========================================================
COLOR_BG_WINDOW = "#F7F9FC"
COLOR_BG_CARD = "#FFFFFF"
COLOR_BG_SUB = "#F2F5FA"
COLOR_BORDER = "#E6EAF0"
COLOR_TEXT_PRIMARY = "#1F2D3D"
COLOR_TEXT_SECONDARY = "#6B7A8B"
COLOR_TEXT_MUTED = "#A3AFBE"
COLOR_ACCENT = "#5B8DEF"
COLOR_ACCENT_HOVER = "#4A7BD9"
COLOR_ACCENT_DOWN = "#3C6BC0"
COLOR_ACCENT_GREEN = "#5CB85C"
COLOR_ACCENT_GREEN_HOVER = "#47A44A"
COLOR_ACCENT_PINK = "#F08BA8"
COLOR_ACCENT_ORANGE = "#F0AD4E"
COLOR_ACCENT_ORANGE_HOVER = "#E0993E"

RADIUS_CARD = 10
RADIUS_BTN = 6
RADIUS_INPUT = 6
RADIUS_TAG = 14

# 全局 QSS（卡片/GroupBox/按钮/输入框/进度条/下拉框/复选框/状态栏）
GLOBAL_QSS = f"""
/* 窗口/背景 */
QMainWindow, QWidget {{
    background-color: {COLOR_BG_WINDOW};
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
}}

/* 卡片式 GroupBox */
QGroupBox {{
    background-color: {COLOR_BG_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    margin-top: 14px;
    padding: 14px 14px 14px 14px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 4px;
    padding: 2px 10px;
    color: {COLOR_TEXT_PRIMARY};
    font-size: 12px;
    font-weight: bold;
    background-color: {COLOR_BG_CARD};
    border-radius: 4px;
}}

/* 主按钮（发送/生成） */
QPushButton#btnPrimary {{
    background-color: {COLOR_ACCENT};
    color: white;
    border: none;
    border-radius: {RADIUS_BTN}px;
    padding: 9px 22px;
    font-weight: bold;
}}
QPushButton#btnPrimary:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}
QPushButton#btnPrimary:pressed {{
    background-color: {COLOR_ACCENT_DOWN};
}}
QPushButton#btnPrimary:disabled {{
    background-color: #C7D0DB;
    color: #F0F3F8;
}}

/* 次按钮 */
QPushButton#btnSecondary {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BTN}px;
    padding: 7px 16px;
}}
QPushButton#btnSecondary:hover {{
    background-color: {COLOR_BG_SUB};
    border-color: #D4DAE4;
}}

/* 危险按钮 */
QPushButton#btnDanger {{
    background-color: {COLOR_ACCENT_ORANGE};
    color: white;
    border: none;
    border-radius: {RADIUS_BTN}px;
    padding: 8px 18px;
}}
QPushButton#btnDanger:hover {{
    background-color: {COLOR_ACCENT_ORANGE_HOVER};
}}

/* 模式按钮（可选中胶囊） */
QPushButton#btnMode {{
    background-color: {COLOR_BG_SUB};
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_TAG}px;
    padding: 7px 18px;
    font-weight: 600;
}}
QPushButton#btnMode:hover {{
    background-color: #EAF0FA;
    color: {COLOR_TEXT_PRIMARY};
}}
QPushButton#btnMode:checked {{
    background-color: {COLOR_ACCENT};
    color: white;
    border-color: {COLOR_ACCENT};
}}

/* 角色按钮（网格选中） */
QPushButton#btnChar {{
    background-color: {COLOR_BG_SUB};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 7px 10px;
    min-width: 84px;
}}
QPushButton#btnChar:hover {{
    background-color: #EAF0FA;
    border-color: #D4DAE4;
}}
QPushButton#btnChar:checked {{
    background-color: {COLOR_ACCENT_PINK};
    color: white;
    border-color: {COLOR_ACCENT_PINK};
}}

/* 输入框 / 文本域 */
QTextEdit, QLineEdit {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    padding: 8px 10px;
    selection-background-color: {COLOR_ACCENT};
}}
QTextEdit:focus, QLineEdit:focus {{
    border-color: {COLOR_ACCENT};
}}
QTextEdit#historyLog {{
    background-color: {COLOR_BG_CARD};
}}

/* 下拉框 */
QComboBox {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    padding: 6px 10px;
    min-width: 160px;
}}
QComboBox:hover {{
    border-color: #D4DAE4;
}}
QComboBox:focus {{
    border-color: {COLOR_ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    selection-background-color: {COLOR_ACCENT};
    selection-color: white;
}}

/* 复选框 */
QCheckBox {{
    spacing: 8px;
    color: {COLOR_TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: {COLOR_BG_CARD};
}}
QCheckBox::indicator:hover {{
    border-color: {COLOR_ACCENT};
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

/* 进度条 */
QProgressBar {{
    background-color: {COLOR_BG_SUB};
    border: none;
    border-radius: 8px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 8px;
}}

/* 状态栏 */
QStatusBar {{
    background-color: {COLOR_BG_CARD};
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_SECONDARY};
    font-size: 12px;
}}

/* 滚动条（细一点） */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #CFD6E0;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #B5BDCD;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* 标题标签 */
QLabel#titleMain {{
    font-size: 18px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}
QLabel#titleSub {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 12px;
}}
QLabel#previewPlaceholder {{
    color: {COLOR_TEXT_MUTED};
    font-size: 13px;
}}

/* 文字大小滑块 */
QSlider#fontSizeSlider {{
    height: 20px;
}}
QSlider#fontSizeSlider::groove:horizontal {{
    height: 6px;
    background-color: {COLOR_BG_SUB};
    border-radius: 3px;
}}
QSlider#fontSizeSlider::handle:horizontal {{
    width: 16px;
    height: 16px;
    background-color: {COLOR_ACCENT};
    border-radius: 8px;
    margin: -5px 0;
}}
/* 下拉选择框 */
QComboBox#charCombo {{
    padding: 6px 30px 6px 10px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BTN}px;
    background-color: {COLOR_BG_CARD};
    min-width: 150px;
}}
QComboBox#charCombo:hover {{
    border-color: {COLOR_ACCENT};
}}
QComboBox#charCombo:focus {{
    border-color: {COLOR_ACCENT};
    outline: none;
}}
QComboBox#charCombo::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left-width: 1px;
    border-left-color: {COLOR_BORDER};
    border-left-style: solid;
    border-top-right-radius: {RADIUS_BTN}px;
    border-bottom-right-radius: {RADIUS_BTN}px;
    background-color: {COLOR_BG_SUB};
}}
QComboBox#charCombo::down-arrow {{
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='{COLOR_TEXT_SECONDARY}' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}}
QComboBox#charCombo QAbstractItemView {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    background-color: {COLOR_BG_CARD};
    selection-background-color: {COLOR_ACCENT};
    padding: 4px;
}}
QLabel#fontSizeLabel {{
    min-width: 40px;
    text-align: center;
    font-weight: bold;
    color: {COLOR_ACCENT};
}}

/* 页面选择下拉框 */
QComboBox#pageCombo {{
    padding: 4px 24px 4px 10px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BTN}px;
    background-color: {COLOR_BG_CARD};
    min-width: 100px;
}}
QComboBox#pageCombo:hover {{
    border-color: {COLOR_ACCENT};
}}
QComboBox#pageCombo:focus {{
    border-color: {COLOR_ACCENT};
    outline: none;
}}
QComboBox#pageCombo::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left-width: 1px;
    border-left-color: {COLOR_BORDER};
    border-left-style: solid;
    border-top-right-radius: {RADIUS_BTN}px;
    border-bottom-right-radius: {RADIUS_BTN}px;
    background-color: {COLOR_BG_SUB};
}}
QComboBox#pageCombo QAbstractItemView {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    background-color: {COLOR_BG_CARD};
    selection-background-color: {COLOR_ACCENT};
    padding: 4px;
}}

/* 角色管理输入框 */
QLineEdit#charNameInput, QLineEdit#charKeyInput, QLineEdit#charExprInput {{
    padding: 8px 12px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BTN}px;
    background-color: {COLOR_BG_CARD};
    font-size: 13px;
}}
QLineEdit#charNameInput:focus, QLineEdit#charKeyInput:focus, QLineEdit#charExprInput:focus {{
    border-color: {COLOR_ACCENT};
    outline: none;
}}

/* 角色列表 */
QTextEdit#charListText {{
    background-color: {COLOR_BG_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    padding: 12px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 12px;
}}

/* 上传角色下拉框 */
QComboBox#uploadCharCombo {{
    padding: 6px 30px 6px 10px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BTN}px;
    background-color: {COLOR_BG_CARD};
    min-width: 200px;
}}
QComboBox#uploadCharCombo:hover {{
    border-color: {COLOR_ACCENT};
}}
QComboBox#uploadCharCombo:focus {{
    border-color: {COLOR_ACCENT};
    outline: none;
}}

/* 上传状态标签 */
QLabel#uploadStatus {{
    font-size: 12px;
    color: {COLOR_ACCENT};
    padding: 4px;
}}
"""


class WorkerThread(QThread):
    """后台工作线程，用于生成图片"""
    progress_update = pyqtSignal(int)
    task_complete = pyqtSignal(bool, str)
    image_ready = pyqtSignal(bytes)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_name = ""
        self.expression = None
        self.text = ""
        self.image_data = None
        self.auto_paste = False
        self.auto_send = False
        self.font_size = 145

    def set_params(self, character_name: str, expression: int | None, text: str, 
                   image_data: bytes | None, auto_paste: bool, auto_send: bool,
                   font_size: int = 145):
        self.character_name = character_name
        self.expression = expression
        self.text = text
        self.image_data = image_data
        self.auto_paste = auto_paste
        self.auto_send = auto_send
        self.font_size = font_size

    def run(self):
        try:
            self.progress_update.emit(20)
            png_bytes = self.generate_image()
            self.progress_update.emit(80)
            
            if png_bytes:
                copy_png_bytes_to_clipboard(png_bytes)
                self.image_ready.emit(png_bytes)
                
                if self.auto_paste:
                    if get_profile()["focus_window"]:
                        focus_chat_window()
                    import keyboard
                    keyboard.send("ctrl+v")
                    time.sleep(get_profile()["paste_sleep"])
                
                if self.auto_send:
                    import keyboard
                    keyboard.send("enter")
                
                self.task_complete.emit(True, "图片生成成功！")
            else:
                self.task_complete.emit(False, "生成图片失败")
        except Exception as e:
            self.task_complete.emit(False, f"生成失败: {str(e)}")

    def generate_image(self) -> bytes | None:
        """生成图片"""
        emotion_count = mahoshojo[self.character_name]["emotion_count"]
        total_images = 16 * emotion_count
        
        if self.expression and 1 <= self.expression <= emotion_count:
            i = random.randint((self.expression - 1) * 16 + 1, self.expression * 16)
        else:
            i = random.randint(1, total_images)
        
        address = os.path.join(magic_cut_folder, f"{self.character_name} ({i}).jpg")
        
        if not os.path.exists(address):
            return None
        
        text_box_topleft = (mahoshojo_postion[0], mahoshojo_postion[1])
        image_box_bottomright = (mahoshojo_over[0], mahoshojo_over[1])
        
        png_bytes = None
        
        if self.image_data:
            image = Image.open(io.BytesIO(self.image_data)).convert("RGBA")
            png_bytes = paste_image_auto(
                image_source=address,
                image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                content_image=image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,
                role_name=self.character_name,
                text_configs_dict=text_configs_dict,
            )
        elif self.text:
            font_path = os.path.join(RESOURCE_DIR, mahoshojo[self.character_name]["font"])
            png_bytes = draw_text_auto(
                image_source=address,
                image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                text=self.text,
                align="left",
                valign="top",
                color=(255, 255, 255),
                font_size=self.font_size,
                font_path=font_path,
                role_name=self.character_name,
                text_configs_dict=text_configs_dict,
            )
        
        return png_bytes


def copy_png_bytes_to_clipboard(png_bytes: bytes) -> None:
    """将PNG字节复制到剪贴板"""
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    output = io.BytesIO()
    image.save(output, "BMP")
    bmp_data = output.getvalue()[14:]
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    finally:
        win32clipboard.CloseClipboard()


def generate_and_save_images(character_name: str) -> None:
    """预生成角色图片"""
    now_file = RESOURCE_DIR
    emotion_count = mahoshojo[character_name]["emotion_count"]

    for filename in os.listdir(magic_cut_folder):
        if filename.startswith(character_name):
            return

    for i in range(16):
        for j in range(emotion_count):
            background_path = os.path.join(now_file, "background", f"c{i + 1}.png")
            overlay_path = os.path.join(
                now_file, character_name, f"{character_name} ({j + 1}).png"
            )
            background = Image.open(background_path).convert("RGBA")
            overlay = Image.open(overlay_path).convert("RGBA")
            img_num = j * 16 + i + 1
            result = background.copy()
            result.paste(overlay, (0, 134), overlay)
            save_path = os.path.join(
                magic_cut_folder, f"{character_name} ({img_num}).jpg"
            )
            result.convert("RGB").save(save_path)


def try_get_image_from_clipboard() -> Optional[bytes]:
    """尝试从剪贴板获取图片"""
    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            return None
        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
        if len(data) < 14:
            return None
        header = b"BM" + len(data).to_bytes(4, "little") + b"\x00\x00\x00\x006\x00\x00\x00"
        image = Image.open(io.BytesIO(header + data))
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


# 外部输入获取相关的快捷键常量
SELECT_ALL_HOTKEY = "ctrl+a"
CUT_HOTKEY = "ctrl+x"
COPY_HOTKEY = "ctrl+c"


def get_input_text_from_external() -> str:
    """从外部聊天窗口获取输入文字"""
    profile = get_profile()
    if profile["focus_window"]:
        focus_chat_window()
    
    import keyboard
    
    old_clip = pyperclip.paste()
    pyperclip.copy("")
    
    keyboard.release("ctrl")
    keyboard.release("alt")
    keyboard.release("shift")
    time.sleep(0.05)
    
    keyboard.send(SELECT_ALL_HOTKEY)
    time.sleep(profile["delay"])
    
    if profile["use_copy_for_text"]:
        keyboard.send(COPY_HOTKEY)
    else:
        keyboard.send(CUT_HOTKEY)
    time.sleep(profile["delay"])
    
    new_clip = pyperclip.paste()
    
    if profile["use_copy_for_text"] and old_clip:
        pyperclip.copy(old_clip)
    
    return new_clip


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.current_character_index = 3
        self.current_expression = None
        self.worker_thread = WorkerThread()
        self.worker_thread.progress_update.connect(self.on_progress_update)
        self.worker_thread.task_complete.connect(self.on_task_complete)
        self.worker_thread.image_ready.connect(self.on_image_ready)
        
        # 后台监控线程
        self.monitor_thread = None
        self.monitoring_active = False
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面（左右分栏 + 卡片式）"""
        self.setWindowTitle("魔审galgame聊天器")
        self.setGeometry(100, 80, 880, 620)
        self.setMinimumSize(780, 560)
        self.setStyleSheet(GLOBAL_QSS)

        # ---- 主容器 ----
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root = QVBoxLayout(central_widget)
        root.setSpacing(12)
        root.setContentsMargins(18, 16, 18, 10)

        # ---- 顶部标题条 ----
        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel("✦ 魔审galgame聊天器")
        title.setObjectName("titleMain")
        header.addWidget(title)
        header.addStretch(1)
        
        self.page_combo = QComboBox()
        self.page_combo.setObjectName("pageCombo")
        self.page_combo.addItem("主界面")
        self.page_combo.addItem("角色管理")
        self.page_combo.currentIndexChanged.connect(self.switch_page)
        header.addWidget(self.page_combo)
        
        self.mode_pill_label = QLabel()
        self.mode_pill_label.setObjectName("titleSub")
        header.addWidget(self.mode_pill_label)
        root.addLayout(header)

        # ---- 页面切换容器 ----
        self.stacked_widget = QStackedWidget()
        root.addWidget(self.stacked_widget)

        # ---- 主页面 ----
        self.main_page = QWidget()
        self.init_main_page()
        self.stacked_widget.addWidget(self.main_page)

        # ---- 角色管理页面 ----
        self.char_manager_page = QWidget()
        self.init_char_manager_page()
        self.stacked_widget.addWidget(self.char_manager_page)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 · 勾选「后台监控」后可直接在 QQ/微信 聊天框按 Enter 使用")

        self._update_mode_pill()
        self.preload_current_character()
    
    def init_main_page(self):
        """初始化主页面（左右分栏 + 卡片式）"""
        body = QHBoxLayout(self.main_page)
        body.setSpacing(14)

        # =========================
        # 左侧：操作面板
        # =========================
        left = QVBoxLayout()
        left.setSpacing(10)

        # 运行模式
        mode_group = QGroupBox("运行模式")
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(12, 24, 12, 12)
        mode_layout.setSpacing(8)
        self.mode_buttons = []
        for name, mode in [("QQ", "qq"), ("微信", "wechat"), ("QQ微信", "qqwechat"), ("全局", "global")]:
            btn = QPushButton(name)
            btn.setObjectName("btnMode")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self.switch_mode(m))
            self.mode_buttons.append(btn)
            mode_layout.addWidget(btn)
        mode_layout.addStretch(1)
        left.addWidget(mode_group)

        if os.environ.get("MOUSHEN_APP") == "wechat":
            self.mode_buttons[1].setChecked(True)
        elif os.environ.get("MOUSHEN_APP") == "qqwechat":
            self.mode_buttons[2].setChecked(True)
        elif os.environ.get("MOUSHEN_APP") == "global":
            self.mode_buttons[3].setChecked(True)
        else:
            self.mode_buttons[0].setChecked(True)

        # 角色选择（下拉框 + 预览图）
        char_group = QGroupBox("角色选择")
        char_layout = QHBoxLayout(char_group)
        char_layout.setContentsMargins(12, 24, 12, 12)
        char_layout.setSpacing(10)
        
        self.char_combo = QComboBox()
        self.char_combo.setObjectName("charCombo")
        self.char_combo.setMinimumWidth(150)
        
        for i, char_key in enumerate(character_list):
            char_name = character_names[char_key]
            image_path = os.path.join(magic_cut_folder, f"{char_key} (1).png")
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon = QIcon(pixmap)
                self.char_combo.addItem(icon, char_name, i)
            else:
                self.char_combo.addItem(char_name, i)
        
        self.char_combo.setCurrentIndex(3)
        self.char_combo.currentIndexChanged.connect(self.select_character)
        char_layout.addWidget(self.char_combo)
        char_layout.addStretch(1)
        left.addWidget(char_group)

        # 表情选择
        expr_group = QGroupBox("表情选择")
        expr_layout = QHBoxLayout(expr_group)
        expr_layout.setContentsMargins(12, 24, 12, 12)
        expr_layout.setSpacing(10)
        self.expr_combo = QComboBox()
        self.expr_combo.addItem("随机表情")
        self.expr_combo.currentIndexChanged.connect(self.select_expression)
        expr_layout.addWidget(self.expr_combo)
        expr_layout.addStretch(1)
        self.update_expression_list()
        left.addWidget(expr_group)

        # 文字大小滑块
        font_group = QGroupBox("文字大小")
        font_layout = QHBoxLayout(font_group)
        font_layout.setContentsMargins(12, 24, 12, 12)
        font_layout.setSpacing(8)
        
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(0, 200)
        self.font_size_slider.setValue(0)
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_size_slider.setTickInterval(20)
        self.font_size_slider.setObjectName("fontSizeSlider")
        font_layout.addWidget(self.font_size_slider)
        
        self.font_size_label = QLabel("自动")
        self.font_size_label.setObjectName("fontSizeLabel")
        font_layout.addWidget(self.font_size_label)
        
        self.font_auto_btn = QPushButton("自动")
        self.font_auto_btn.setObjectName("btnFontAuto")
        self.font_auto_btn.setCheckable(True)
        self.font_auto_btn.setChecked(True)
        self.font_auto_btn.setFixedWidth(60)
        self.font_auto_btn.clicked.connect(self.set_font_auto)
        font_layout.addWidget(self.font_auto_btn)
        
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        left.addWidget(font_group)

        # 输入 + 发送
        chat_group = QGroupBox("输入消息")
        chat_layout = QVBoxLayout(chat_group)
        chat_layout.setContentsMargins(12, 24, 12, 12)
        chat_layout.setSpacing(8)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("输入文字 (Enter发送，Ctrl+Enter换行)")
        self.text_edit.setMinimumHeight(70)
        self.text_edit.setMaximumHeight(110)
        self.text_edit.installEventFilter(self)
        chat_layout.addWidget(self.text_edit)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        send_btn = QPushButton("发送")
        send_btn.setObjectName("btnPrimary")
        send_btn.clicked.connect(self.send_message)
        btn_row.addWidget(send_btn)
        paste_btn = QPushButton("从剪贴板粘贴")
        paste_btn.setObjectName("btnSecondary")
        paste_btn.clicked.connect(self.paste_from_clipboard)
        btn_row.addWidget(paste_btn)
        chat_layout.addLayout(btn_row)
        left.addWidget(chat_group)

        # 选项复选框
        opt_group = QGroupBox("选项")
        opt_layout = QHBoxLayout(opt_group)
        opt_layout.setContentsMargins(12, 24, 12, 12)
        opt_layout.setSpacing(14)
        self.auto_paste_check = QCheckBox("自动粘贴")
        self.auto_paste_check.setChecked(True)
        opt_layout.addWidget(self.auto_paste_check)
        self.auto_send_check = QCheckBox("自动发送")
        self.auto_send_check.setChecked(True)
        opt_layout.addWidget(self.auto_send_check)
        self.monitor_check = QCheckBox("后台监控")
        self.monitor_check.setToolTip("勾选后在QQ/微信聊天框按Enter即可触发")
        self.monitor_check.stateChanged.connect(self.toggle_monitoring)
        opt_layout.addWidget(self.monitor_check)
        opt_layout.addStretch(1)
        left.addWidget(opt_group)

        # 底部操作按钮
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.generate_btn = QPushButton("生成图片")
        self.generate_btn.setObjectName("btnPrimary")
        self.generate_btn.clicked.connect(self.generate_image)
        action_row.addWidget(self.generate_btn)
        clear_btn = QPushButton("清除缓存")
        clear_btn.setObjectName("btnDanger")
        clear_btn.clicked.connect(self.clear_cache)
        action_row.addWidget(clear_btn)
        left.addLayout(action_row)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(10)
        left.addWidget(self.progress_bar)

        # 左侧面板撑满
        left_wrap = QWidget()
        left_wrap.setLayout(left)
        body.addWidget(left_wrap, 3)

        # =========================
        # 右侧：消息历史 + 预览
        # =========================
        right = QVBoxLayout()
        right.setSpacing(10)

        # 消息历史
        hist_group = QGroupBox("消息历史")
        hist_layout = QVBoxLayout(hist_group)
        hist_layout.setContentsMargins(12, 24, 12, 12)
        self.message_history = QTextEdit()
        self.message_history.setObjectName("historyLog")
        self.message_history.setReadOnly(True)
        self.message_history.setMinimumHeight(180)
        hist_layout.addWidget(self.message_history)
        right.addWidget(hist_group, 2)

        # 图片预览
        prev_group = QGroupBox("图片预览")
        prev_layout = QVBoxLayout(prev_group)
        prev_layout.setContentsMargins(12, 24, 12, 12)
        prev_frame = QFrame()
        prev_frame.setStyleSheet(
            f"background-color: {COLOR_BG_SUB};"
            f"border: 1px dashed {COLOR_BORDER};"
            f"border-radius: 8px;"
        )
        prev_inner = QVBoxLayout(prev_frame)
        prev_inner.setContentsMargins(8, 8, 8, 8)
        self.preview_label = QLabel("图片将在这里预览")
        self.preview_label.setObjectName("previewPlaceholder")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        prev_inner.addWidget(self.preview_label)
        prev_layout.addWidget(prev_frame)
        right.addWidget(prev_group, 3)

        right_wrap = QWidget()
        right_wrap.setLayout(right)
        body.addWidget(right_wrap, 2)
    
    def init_char_manager_page(self):
        """初始化角色管理页面"""
        layout = QVBoxLayout(self.char_manager_page)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("✦ 角色管理")
        title.setObjectName("titleMain")
        layout.addWidget(title)

        # 添加角色区域
        add_group = QGroupBox("添加新角色")
        add_layout = QVBoxLayout(add_group)
        add_layout.setContentsMargins(16, 24, 16, 16)
        add_layout.setSpacing(14)

        # 角色名字输入
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_label = QLabel("角色名字:")
        name_label.setFixedWidth(80)
        self.char_name_input = QLineEdit()
        self.char_name_input.setPlaceholderText("请输入角色中文名（如：樱羽艾玛）")
        self.char_name_input.setObjectName("charNameInput")
        name_row.addWidget(name_label)
        name_row.addWidget(self.char_name_input)
        add_layout.addLayout(name_row)

        # 角色英文名（key）输入
        key_row = QHBoxLayout()
        key_row.setSpacing(10)
        key_label = QLabel("角色标识:")
        key_label.setFixedWidth(80)
        self.char_key_input = QLineEdit()
        self.char_key_input.setPlaceholderText("请输入角色标识（英文小写，如：ema）")
        self.char_key_input.setObjectName("charKeyInput")
        key_row.addWidget(key_label)
        key_row.addWidget(self.char_key_input)
        add_layout.addLayout(key_row)

        # 表情数量输入
        expr_row = QHBoxLayout()
        expr_row.setSpacing(10)
        expr_label = QLabel("表情数量:")
        expr_label.setFixedWidth(80)
        self.char_expr_input = QLineEdit()
        self.char_expr_input.setPlaceholderText("请输入表情数量（数字，如：8）")
        self.char_expr_input.setObjectName("charExprInput")
        expr_row.addWidget(expr_label)
        expr_row.addWidget(self.char_expr_input)
        add_layout.addLayout(expr_row)

        # 添加按钮
        add_btn = QPushButton("添加角色")
        add_btn.setObjectName("btnPrimary")
        add_btn.clicked.connect(self.add_new_character)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_group)

        # 上传表情图片区域
        img_group = QGroupBox("上传表情图片")
        img_layout = QVBoxLayout(img_group)
        img_layout.setContentsMargins(16, 24, 16, 16)
        img_layout.setSpacing(12)

        # 角色选择
        char_select_row = QHBoxLayout()
        char_select_row.setSpacing(10)
        char_select_label = QLabel("选择角色:")
        char_select_label.setFixedWidth(80)
        self.upload_char_combo = QComboBox()
        self.upload_char_combo.setObjectName("uploadCharCombo")
        char_select_row.addWidget(char_select_label)
        char_select_row.addWidget(self.upload_char_combo)
        img_layout.addLayout(char_select_row)

        # 图片选择按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        upload_single_btn = QPushButton("上传单张图片")
        upload_single_btn.setObjectName("btnSecondary")
        upload_single_btn.clicked.connect(self.upload_single_image)
        btn_row.addWidget(upload_single_btn)
        
        upload_multi_btn = QPushButton("批量上传图片")
        upload_multi_btn.setObjectName("btnSecondary")
        upload_multi_btn.clicked.connect(self.upload_multi_images)
        btn_row.addWidget(upload_multi_btn)
        
        img_layout.addLayout(btn_row)

        # 提示信息
        self.upload_status_label = QLabel("")
        self.upload_status_label.setObjectName("uploadStatus")
        self.upload_status_label.setWordWrap(True)
        img_layout.addWidget(self.upload_status_label)

        layout.addWidget(img_group)

        # 角色列表显示
        list_group = QGroupBox("已添加角色")
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(16, 24, 16, 16)
        
        self.char_list_text = QTextEdit()
        self.char_list_text.setReadOnly(True)
        self.char_list_text.setObjectName("charListText")
        self.char_list_text.setMinimumHeight(200)
        list_layout.addWidget(self.char_list_text)
        
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setObjectName("btnSecondary")
        refresh_btn.clicked.connect(self.refresh_char_list)
        list_layout.addWidget(refresh_btn)
        
        layout.addWidget(list_group, 1)

        self.refresh_char_list()
    
    def switch_page(self, index: int):
        """切换页面"""
        self.stacked_widget.setCurrentIndex(index)
    
    def refresh_char_list(self):
        """刷新角色列表"""
        text = "当前已加载角色列表：\n\n"
        for key, info in mahoshojo.items():
            name = character_names.get(key, key)
            text += f"• {name} ({key}) - 表情数量: {info['emotion_count']}\n"
        self.char_list_text.setPlainText(text)
        
        if hasattr(self, 'upload_char_combo'):
            self.upload_char_combo.clear()
            for key in character_list:
                name = character_names.get(key, key)
                self.upload_char_combo.addItem(f"{name} ({key})", key)
    
    def add_new_character(self):
        """添加新角色"""
        char_name = self.char_name_input.text().strip()
        char_key = self.char_key_input.text().strip()
        expr_count = self.char_expr_input.text().strip()

        if not char_name:
            QMessageBox.warning(self, "提示", "请输入角色名字！")
            return
        
        if not char_key:
            QMessageBox.warning(self, "提示", "请输入角色标识！")
            return
        
        if not char_key.islower() or not char_key.isalnum():
            QMessageBox.warning(self, "提示", "角色标识必须是小写字母和数字的组合！")
            return
        
        if not expr_count.isdigit():
            QMessageBox.warning(self, "提示", "表情数量必须是数字！")
            return
        
        expr_count = int(expr_count)
        if expr_count < 1 or expr_count > 99:
            QMessageBox.warning(self, "提示", "表情数量必须在 1-99 之间！")
            return
        
        if char_key in mahoshojo:
            QMessageBox.warning(self, "提示", f"角色标识 '{char_key}' 已存在！")
            return
        
        mahoshojo[char_key] = {"emotion_count": expr_count, "font": "font3.ttf"}
        character_names[char_key] = char_name
        character_list.append(char_key)
        
        text_configs_dict[char_key] = [
            {"text": char_name[0] if len(char_name) > 0 else "", "position": (759, 73), "font_color": (180, 180, 180), "font_size": 186},
            {"text": char_name[1] if len(char_name) > 1 else "", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
            {"text": char_name[2] if len(char_name) > 2 else "", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
            {"text": char_name[3:] if len(char_name) > 3 else "", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92},
        ]
        
        self.char_name_input.clear()
        self.char_key_input.clear()
        self.char_expr_input.clear()
        
        self.refresh_char_list()
        
        self.update_char_combo()
        
        QMessageBox.information(self, "成功", f"角色 '{char_name}' 添加成功！\n\n注意：需要将角色图片放入 _internal/magic_cut 目录，命名格式为 '{char_key} (1).png', '{char_key} (2).png'...")
    
    def update_char_combo(self):
        """更新主界面角色下拉框"""
        if hasattr(self, 'char_combo'):
            current_index = self.char_combo.currentIndex()
            current_char_key = None
            if current_index >= 0 and current_index < len(character_list):
                current_char_key = character_list[current_index]
            
            self.char_combo.clear()
            for i, char_key in enumerate(character_list):
                char_name = character_names[char_key]
                image_path = os.path.join(magic_cut_folder, f"{char_key} (1).png")
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon = QIcon(pixmap)
                    self.char_combo.addItem(icon, char_name, i)
                else:
                    self.char_combo.addItem(char_name, i)
            
            if current_char_key and current_char_key in character_list:
                self.char_combo.setCurrentIndex(character_list.index(current_char_key))
    
    def upload_single_image(self):
        """上传单张表情图片"""
        if self.upload_char_combo.currentIndex() < 0:
            QMessageBox.warning(self, "提示", "请先选择角色！")
            return
        
        char_key = self.upload_char_combo.currentData()
        char_name = character_names.get(char_key, char_key)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择表情图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if not file_path:
            return
        
        try:
            import glob
            
            existing_files = glob.glob(os.path.join(magic_cut_folder, f"{char_key} (*).png"))
            next_num = len(existing_files) + 1
            
            new_file_name = f"{char_key} ({next_num}).png"
            new_file_path = os.path.join(magic_cut_folder, new_file_name)
            
            from PIL import Image
            img = Image.open(file_path)
            img.save(new_file_path, "PNG")
            
            self.upload_status_label.setText(f"✓ 已上传第 {next_num} 张表情图片：{new_file_name}")
            self.status_bar.showMessage(f"已为角色 {char_name} 上传第 {next_num} 张表情图片")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"上传失败：{str(e)}")
            self.upload_status_label.setText(f"✗ 上传失败：{str(e)}")
    
    def upload_multi_images(self):
        """批量上传表情图片"""
        if self.upload_char_combo.currentIndex() < 0:
            QMessageBox.warning(self, "提示", "请先选择角色！")
            return
        
        char_key = self.upload_char_combo.currentData()
        char_name = character_names.get(char_key, char_key)
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择表情图片（可多选）",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if not file_paths:
            return
        
        try:
            import glob
            
            existing_files = glob.glob(os.path.join(magic_cut_folder, f"{char_key} (*).png"))
            next_num = len(existing_files) + 1
            
            success_count = 0
            from PIL import Image
            
            for file_path in file_paths:
                try:
                    new_file_name = f"{char_key} ({next_num}).png"
                    new_file_path = os.path.join(magic_cut_folder, new_file_name)
                    
                    img = Image.open(file_path)
                    img.save(new_file_path, "PNG")
                    
                    next_num += 1
                    success_count += 1
                except Exception as e:
                    self.upload_status_label.setText(f"✗ 部分图片上传失败：{str(e)}")
            
            self.upload_status_label.setText(f"✓ 批量上传完成，成功上传 {success_count} 张图片")
            self.status_bar.showMessage(f"已为角色 {char_name} 批量上传 {success_count} 张表情图片")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"上传失败：{str(e)}")
            self.upload_status_label.setText(f"✗ 上传失败：{str(e)}")

    def _update_mode_pill(self):
        profile = get_profile()
        self.mode_pill_label.setText(f"当前模式：{profile['name']}")
    
    def switch_mode(self, mode: str):
        """切换运行模式"""
        os.environ["MOUSHEN_APP"] = mode
        profile = get_profile()
        
        modes = [("qq", "qq"), ("wechat", "wechat"), ("qqwechat", "qqwechat"), ("global", "global")]
        for i, (_, m) in enumerate(modes):
            self.mode_buttons[i].setChecked(m == mode)
        
        self._update_mode_pill()
        self.status_bar.showMessage(f"已切换到 {profile['name']} 模式")
    
    def select_character(self, index: int):
        """选择角色"""
        if 0 <= index < len(character_list):
            self.current_character_index = index
            
            self.update_expression_list()
            
            self.preload_current_character()
            
            char_name = character_names[character_list[index]]
            self.status_bar.showMessage(f"已选择角色: {char_name}")
    
    def select_expression(self, index: int):
        """选择表情"""
        if index == 0:
            self.current_expression = None
        else:
            self.current_expression = index
    
    def on_font_size_changed(self, value: int):
        if value == 0:
            self.font_size_label.setText("自动")
            self.font_auto_btn.setChecked(True)
        else:
            self.font_size_label.setText(str(value))
            self.font_auto_btn.setChecked(False)
    
    def set_font_auto(self, checked: bool):
        if checked:
            self.font_size_slider.setValue(0)
            self.font_size_label.setText("自动")
        else:
            if self.font_size_slider.value() == 0:
                self.font_size_slider.setValue(145)
                self.font_size_label.setText("145")
    
    def get_font_size(self) -> int | None:
        val = self.font_size_slider.value()
        return None if val == 0 else val
    
    def update_expression_list(self):
        """更新表情列表"""
        current_char = character_list[self.current_character_index]
        emotion_count = mahoshojo[current_char]["emotion_count"]
        
        self.expr_combo.clear()
        self.expr_combo.addItem("随机表情")
        for i in range(1, emotion_count + 1):
            self.expr_combo.addItem(f"表情 {i}")
        
        self.current_expression = None
        self.expr_combo.setCurrentIndex(0)
    
    def paste_from_clipboard(self):
        """从剪贴板粘贴文字"""
        try:
            text = pyperclip.paste()
            if text:
                self.text_edit.setPlainText(text)
                self.status_bar.showMessage("已从剪贴板粘贴")
        except Exception as e:
            self.status_bar.showMessage(f"粘贴失败: {str(e)}")
    
    def preload_current_character(self):
        """预加载当前角色图片"""
        try:
            char_name = character_list[self.current_character_index]
            generate_and_save_images(char_name)
        except Exception as e:
            self.status_bar.showMessage(f"预加载失败: {str(e)}")
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理Enter键发送"""
        from PyQt6.QtGui import QKeyEvent
        
        if obj == self.text_edit and event.type() == event.Type.KeyPress:
            # Ctrl+Enter 换行
            if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    # Ctrl+Enter 允许换行
                    return False
                else:
                    # Enter 发送消息
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
    
    def send_message(self):
        """发送消息（生成图片）"""
        text = self.text_edit.toPlainText().strip()
        
        # 输入验证
        if not text:
            # 检查剪贴板是否有图片
            image_data = try_get_image_from_clipboard()
            if not image_data:
                QMessageBox.warning(self, "输入验证", "请输入文字或从剪贴板复制图片")
                return
        
        # 添加到消息历史
        char_name = character_names[character_list[self.current_character_index]]
        self.add_message_to_history(text, char_name, is_user=True)
        
        # 禁用发送按钮，显示处理状态
        self.status_bar.showMessage("正在处理消息...")
        
        # 生成图片
        self.generate_image()
    
    def add_message_to_history(self, text: str, character_name: str, is_user: bool = False):
        """添加消息到历史记录（气泡样式，左右对齐）"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        safe_text = self.escape_html(text)
        
        if is_user:
            bubble = f"""
            <table style="width:100%; margin: 4px 0;" cellspacing="0" cellpadding="0">
              <tr>
                <td style="width:100%; vertical-align:top; padding-right:8px;">
                  <div style="display:flex; justify-content:flex-end;">
                    <div style="max-width:70%; background:{COLOR_ACCENT}; color:white;
                                padding:8px 12px; border-radius:12px 12px 2px 12px;
                                font-size:13px; line-height:1.5; word-break:break-all;
                                box-sizing:border-box;">
                      {safe_text}
                    </div>
                  </div>
                  <div style="text-align:right; color:{COLOR_TEXT_MUTED}; font-size:11px; margin-top:2px;">
                    {timestamp}
                  </div>
                </td>
              </tr>
            </table>"""
        else:
            bubble = f"""
            <table style="width:100%; margin: 4px 0;" cellspacing="0" cellpadding="0">
              <tr>
                <td style="vertical-align:top; padding-left:8px;">
                  <div style="color:{COLOR_TEXT_MUTED}; font-size:11px; margin-bottom:2px;">
                    {character_name} · {timestamp}
                  </div>
                  <div style="display:flex; justify-content:flex-start;">
                    <div style="max-width:70%; background:{COLOR_BG_SUB}; color:{COLOR_TEXT_PRIMARY};
                                padding:8px 12px; border-radius:12px 12px 12px 2px;
                                font-size:13px; line-height:1.5; word-break:break-all;
                                box-sizing:border-box;">
                      {safe_text}
                    </div>
                  </div>
                </td>
              </tr>
            </table>"""
        
        self.message_history.append(bubble)
        cursor = self.message_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.message_history.setTextCursor(cursor)
    
    def escape_html(self, text: str) -> str:
        """HTML转义"""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") \
                   .replace('"', "&quot;").replace("'", "&#39;")
    
    def generate_image(self):
        """生成图片"""
        text = self.text_edit.toPlainText().strip()
        image_data = try_get_image_from_clipboard() if not text else None
        
        # 禁用按钮，显示进度
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("正在生成图片...")
        
        # 启动工作线程
        char_name = character_list[self.current_character_index]
        self.worker_thread.set_params(
            character_name=char_name,
            expression=self.current_expression,
            text=text,
            image_data=image_data,
            auto_paste=self.auto_paste_check.isChecked(),
            auto_send=self.auto_send_check.isChecked(),
            font_size=self.get_font_size()
        )
        self.worker_thread.start()
    
    def on_progress_update(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def on_task_complete(self, success: bool, message: str):
        """任务完成处理"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        char_name = character_names[character_list[self.current_character_index]]
        
        if success:
            # 清空输入框
            self.text_edit.clear()
            
            # 添加成功消息到历史记录
            self.add_message_to_history(message, char_name, is_user=False)
            
            self.status_bar.showMessage(message)
        else:
            # 添加错误消息到历史记录
            self.add_message_to_history(f"错误: {message}", char_name, is_user=False)
            
            QMessageBox.error(self, "错误", message)
            self.status_bar.showMessage(message)
    
    def on_image_ready(self, png_bytes: bytes):
        """显示生成的图片预览"""
        try:
            image = QImage.fromData(png_bytes)
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setStyleSheet("")
        except Exception as e:
            self.status_bar.showMessage(f"预览失败: {str(e)}")
    
    def clear_cache(self):
        """清除缓存图片"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有生成的图片缓存吗？清除后需要重新加载角色。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for filename in os.listdir(magic_cut_folder):
                    if filename.lower().endswith(".jpg"):
                        os.remove(os.path.join(magic_cut_folder, filename))
                self.status_bar.showMessage("缓存已清除")
                self.preview_label.clear()
                self.preview_label.setText("生成的图片将在这里显示")
                self.preview_label.setStyleSheet("color: #999;")
            except Exception as e:
                QMessageBox.error(self, "错误", f"清除失败: {str(e)}")
    
    def toggle_monitoring(self, state):
        """切换后台监控"""
        if state:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """启动后台监控"""
        try:
            import keyboard
            
            # 取消之前的所有热键注册
            keyboard.unhook_all()
            
            # 注册Enter键监听
            keyboard.on_press_key("enter", self.on_external_enter, suppress=True)
            
            self.monitoring_active = True
            self.status_bar.showMessage("后台监控已启动 - 在QQ/微信聊天框按Enter键将自动发送")
            
        except Exception as e:
            QMessageBox.warning(self, "监控启动失败", f"无法启动后台监控：{str(e)}\n请确保程序有足够的权限。")
            self.monitor_check.setChecked(False)
    
    def stop_monitoring(self):
        """停止后台监控"""
        try:
            import keyboard
            keyboard.unhook_all()
            
            self.monitoring_active = False
            self.status_bar.showMessage("后台监控已停止")
            
        except Exception as e:
            self.status_bar.showMessage(f"停止监控时出错: {str(e)}")
    
    def on_external_enter(self, event):
        """外部应用按Enter键时的处理。
        suppress=True 注册后 Enter 总会被拦截，所以：
        - 窗口匹配当前模式 → 拦截有效，生成图片+粘贴发送
        - 窗口不匹配 → 手动再发一个 Enter 还给原应用，模拟"未拦截"
        """
        if not is_active_window_matching():
            try:
                import keyboard
                keyboard.send("enter")
            except Exception:
                pass
            return

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self.process_external_input)
    
    def process_external_input(self):
        """处理外部应用的输入"""
        try:
            # 获取聊天窗口的输入文字
            text = get_input_text_from_external()
            image_data = None
            
            if text:
                self.status_bar.showMessage(f"检测到输入: {text[:20]}...")
                
                # 添加到消息历史
                char_name = character_names[character_list[self.current_character_index]]
                self.add_message_to_history(text, char_name, is_user=True)
                
                # 生成图片
                self.generate_image_from_external(text, image_data)
            else:
                # 没有文字，检查剪贴板是否有图片
                image_data = try_get_image_from_clipboard()
                if image_data:
                    self.status_bar.showMessage("检测到图片输入...")
                    char_name = character_names[character_list[self.current_character_index]]
                    self.add_message_to_history("[图片]", char_name, is_user=True)
                    self.generate_image_from_external("", image_data)
                else:
                    self.status_bar.showMessage("未检测到文字或图片输入")
                    
        except Exception as e:
            self.status_bar.showMessage(f"处理输入时出错: {str(e)}")
    
    def generate_image_from_external(self, text: str, image_data: Optional[bytes] = None):
        """从外部输入生成图片"""
        # 禁用按钮，显示进度
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("正在生成图片...")
        
        # 启动工作线程
        char_name = character_list[self.current_character_index]
        self.worker_thread.set_params(
            character_name=char_name,
            expression=self.current_expression,
            text=text,
            image_data=image_data,
            auto_paste=self.auto_paste_check.isChecked(),
            auto_send=self.auto_send_check.isChecked(),
            font_size=self.get_font_size()
        )
        self.worker_thread.start()
    
    def closeEvent(self, event):
        """关闭窗口时停止线程"""
        # 停止后台监控
        if self.monitoring_active:
            self.stop_monitoring()
        
        # 停止工作线程
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
        
        event.accept()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="魔审galgame聊天器 - 可视化版本")
    parser.add_argument("--wechat", action="store_true", help="启用微信模式")
    parser.add_argument("--qq", action="store_true", help="启用QQ模式（默认）")
    parser.add_argument("--global-mode", action="store_true", help="启用全局模式")
    args = parser.parse_args()
    
    if args.wechat:
        os.environ["MOUSHEN_APP"] = "wechat"
    elif args.global_mode:
        os.environ["MOUSHEN_APP"] = "global"
    elif args.qq:
        os.environ["MOUSHEN_APP"] = "qq"
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()