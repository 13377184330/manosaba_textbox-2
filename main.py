"""
魔裁图片生成工具 - 支持 QQ / 微信

用法:
  python main.py           # 默认 QQ 模式
  python main.py --wechat  # 微信模式
  set MOUSHEN_APP=wechat && python main.py
"""

from __future__ import annotations

import argparse
import getpass
import io
import os
import random
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "_internal")

import keyboard
import pyperclip
import win32clipboard
from PIL import Image

from chat_adapter import focus_chat_window, get_profile
from config import HELP_TEXT, WECHAT_HELP_EXTRA, mahoshojo, mahoshojo_over, mahoshojo_postion, text_configs_dict
from image_fit_paste import paste_image_auto
from text_fit_draw import draw_text_auto

current_character_index = 3
value_1 = -1
expression = None

HOTKEY = "enter"
SELECT_ALL_HOTKEY = "ctrl+a"
CUT_HOTKEY = "ctrl+x"
COPY_HOTKEY = "ctrl+c"
PASTE_HOTKEY = "ctrl+v"
SEND_HOTKEY = "enter"
BLOCK_HOTKEY = False
AUTO_PASTE_IMAGE = True
AUTO_SEND_IMAGE = True

character_list = list(mahoshojo.keys())

if os.name == "nt":
    user_documents = os.path.join("C:\\", "Users", getpass.getuser(), "Documents")
else:
    user_documents = os.path.expanduser("~/Documents")

magic_cut_folder = os.path.join(user_documents, "魔裁")
os.makedirs(magic_cut_folder, exist_ok=True)


def _apply_profile():
    global DELAY, PASTE_SLEEP
    profile = get_profile()
    DELAY = profile["delay"]
    PASTE_SLEEP = profile["paste_sleep"]


_apply_profile()


def switch_app_mode(mode: str) -> None:
    os.environ["MOUSHEN_APP"] = mode
    _apply_profile()
    profile = get_profile()
    print(f"\n已切换到{profile['name']}模式")


def get_current_character() -> str:
    return character_list[current_character_index]


def get_current_font() -> str:
    font_name = mahoshojo[get_current_character()]["font"]
    return os.path.join(RESOURCE_DIR, font_name)


def get_current_emotion_count() -> int:
    return mahoshojo[get_current_character()]["emotion_count"]


def delate(folder_path: str = magic_cut_folder, quality: int = 85) -> None:
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".jpg"):
            os.remove(os.path.join(folder_path, filename))


def generate_and_save_images(character_name: str) -> None:
    now_file = RESOURCE_DIR
    emotion_count = mahoshojo[character_name]["emotion_count"]

    for filename in os.listdir(magic_cut_folder):
        if filename.startswith(character_name):
            return

    print("正在加载")
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
    print("加载完成")


def switch_character(new_index: int) -> None:
    global current_character_index
    if 0 <= new_index < len(character_list):
        current_character_index = new_index
        character_name = get_current_character()
        print(f"已切换到角色: {character_name}")
        generate_and_save_images(character_name)


def show_current_character() -> None:
    print(f"当前角色: {get_current_character()}")


def get_expression(i: int) -> None:
    global expression
    character_name = get_current_character()
    if i <= mahoshojo[character_name]["emotion_count"]:
        print(f"已切换至第{i}个表情")
        expression = i


def get_random_value() -> str:
    global expression, value_1
    character_name = get_current_character()
    emotion_count = get_current_emotion_count()
    total_images = 16 * emotion_count

    if expression:
        i = random.randint((expression - 1) * 16 + 1, expression * 16)
        expression = None
        return f"{character_name} ({i})"

    max_attempts = 100
    attempts = 0
    while attempts < max_attempts:
        i = random.randint(1, total_images)
        current_emotion = (i - 1) // 16
        if value_1 == -1:
            value_1 = i
            return f"{character_name} ({i})"
        if current_emotion != (value_1 - 1) // 16:
            value_1 = i
            return f"{character_name} ({i})"
        attempts += 1

    value_1 = i
    return f"{character_name} ({i})"


def copy_png_bytes_to_clipboard(png_bytes: bytes) -> None:
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


def get_input_text() -> str:
    """从当前焦点的聊天输入框读取文字。"""
    profile = get_profile()
    if profile["focus_window"]:
        focus_chat_window()

    old_clip = pyperclip.paste()
    pyperclip.copy("")
    
    keyboard.release("ctrl")
    keyboard.release("alt")
    keyboard.release("shift")
    time.sleep(0.05)
    
    keyboard.send(SELECT_ALL_HOTKEY)
    time.sleep(DELAY)

    if profile["use_copy_for_text"]:
        keyboard.send(COPY_HOTKEY)
    else:
        keyboard.send(CUT_HOTKEY)
    time.sleep(DELAY)

    new_clip = pyperclip.paste()

    # 微信模式用复制，尽量恢复原剪贴板；QQ 模式保持原版剪切行为
    if profile["use_copy_for_text"] and old_clip:
        pyperclip.copy(old_clip)
    return new_clip


def try_get_image() -> Image.Image | None:
    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            return None
        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
        if len(data) < 14:
            return None
        header = b"BM" + len(data).to_bytes(4, "little") + b"\x00\x00\x00\x006\x00\x00\x00"
        return Image.open(io.BytesIO(header + data))
    except Exception as exc:
        print(f"无法从剪贴板获取图像：{exc}")
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def Start() -> None:
    print("Start generate...")
    character_name = get_current_character()
    address = os.path.join(magic_cut_folder, get_random_value() + ".jpg")
    print(address)

    text_box_topleft = (mahoshojo_postion[0], mahoshojo_postion[1])
    image_box_bottomright = (mahoshojo_over[0], mahoshojo_over[1])

    text = get_input_text()
    image = try_get_image()

    if text == "" and image is None:
        print("no text or image")
        return

    png_bytes = None
    if image is not None:
        try:
            print("Get image")
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
                role_name=character_name,
                text_configs_dict=text_configs_dict,
            )
        except Exception as exc:
            print(f"Generate image failed: {exc}")
    elif text != "":
        print("Get text: " + text)
        try:
            png_bytes = draw_text_auto(
                image_source=address,
                image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                text=text,
                align="left",
                valign="top",
                color=(255, 255, 255),
                max_font_height=145,
                font_path=get_current_font(),
                role_name=character_name,
                text_configs_dict=text_configs_dict,
            )
        except Exception as exc:
            print(f"Generate image failed: {exc}")

    if png_bytes is None:
        print("Generate image failed!")
        return

    copy_png_bytes_to_clipboard(png_bytes)

    if AUTO_PASTE_IMAGE:
        if get_profile()["focus_window"]:
            focus_chat_window()
        keyboard.send(PASTE_HOTKEY)
        time.sleep(PASTE_SLEEP)

    if AUTO_SEND_IMAGE:
        keyboard.send(SEND_HOTKEY)


def register_hotkeys() -> None:
    for i in range(1, 10):
        keyboard.add_hotkey(f"ctrl+{i}", lambda idx=i: switch_character(idx))

    keyboard.add_hotkey("ctrl+q", lambda: switch_character(10))
    keyboard.add_hotkey("ctrl+w", lambda: switch_character(11))
    keyboard.add_hotkey("ctrl+e", lambda: switch_character(12))
    keyboard.add_hotkey("ctrl+r", lambda: switch_character(13))
    keyboard.add_hotkey("ctrl+t", lambda: switch_character(14))
    keyboard.add_hotkey("ctrl+y", lambda: switch_character(0))
    keyboard.add_hotkey("Tab", lambda: delate(magic_cut_folder))

    for i in range(1, 10):
        keyboard.add_hotkey(f"alt+{i}", lambda idx=i: get_expression(idx))

    keyboard.add_hotkey(
        HOTKEY,
        Start,
        suppress=BLOCK_HOTKEY or HOTKEY == SEND_HOTKEY,
    )
    keyboard.add_hotkey("ctrl+0", show_current_character)
    
    keyboard.add_hotkey("ctrl+shift+q", lambda: switch_app_mode("qq"))
    keyboard.add_hotkey("ctrl+shift+w", lambda: switch_app_mode("wechat"))
    keyboard.add_hotkey("ctrl+shift+g", lambda: switch_app_mode("global"))


def main() -> None:
    parser = argparse.ArgumentParser(description="魔裁图片生成工具")
    parser.add_argument(
        "--wechat",
        action="store_true",
        help="启用微信模式",
    )
    parser.add_argument(
        "--qq",
        action="store_true",
        help="启用 QQ 模式（默认）",
    )
    parser.add_argument(
        "--global-mode",
        action="store_true",
        help="启用全局模式（适用于任何聊天软件）",
    )
    args = parser.parse_args()

    if args.wechat:
        os.environ["MOUSHEN_APP"] = "wechat"
    elif args.global_mode:
        os.environ["MOUSHEN_APP"] = "global"
    elif args.qq:
        os.environ["MOUSHEN_APP"] = "qq"

    _apply_profile()
    profile = get_profile()

    print(HELP_TEXT)
    print(f"\n当前运行模式: {profile['name']}\n")
    print("模式切换快捷键:")
    print("  Ctrl+Shift+Q  - 切换到QQ模式")
    print("  Ctrl+Shift+W  - 切换到微信模式")
    print("  Ctrl+Shift+G  - 切换到全局模式")

    show_current_character()
    generate_and_save_images(get_current_character())
    register_hotkeys()
    keyboard.wait("Esc")


if __name__ == "__main__":
    main()
