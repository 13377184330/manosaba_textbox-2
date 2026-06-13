# 魔审galgame聊天器

一个基于 PyQt6 的可视化聊天工具，可以在 QQ/微信聊天窗口中输入文字，按 Enter 键自动生成带有角色表情的图片并发送。

本项目借鉴了 [manosaba_text_box](https://github.com/oplivilqo/manosaba_text_box/tree/lite) 的设计思路。

## 功能特点

- 🎨 **可视化界面**：基于 PyQt6 开发的现代化图形界面
- 💬 **聊天集成**：支持 QQ、微信、QQ微信、全局四种模式
- 🎭 **角色系统**：支持多个角色切换，每个角色有不同的表情
- ✏️ **文字大小调整**：支持手动调整和自动适配两种模式
- 📤 **一键发送**：在聊天窗口输入文字后按 Enter 键即可生成图片并发送
- 📁 **角色管理**：支持添加新角色和上传表情图片
- 效果如图

<img width="565" height="188" alt="image" src="https://github.com/user-attachments/assets/4934e4d6-fe3a-4258-b58d-712615ba537d" />



## 快速开始

### 直接运行

下载 `dist/魔审galgame聊天器.exe` 并双击运行。

### 开发环境

```bash
# 克隆项目
git clone <repository-url>
cd 魔审galgame聊天器

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python gui_main.py
```

## 使用方法

### 基本操作

1. **选择模式**：在顶部选择工作模式（QQ/微信/QQ微信/全局）
2. **选择角色**：从下拉框中选择一个角色
3. **选择表情**：点击表情按钮选择角色表情
4. **输入文字**：在输入框中输入要生成的文字
5. **按 Enter 发送**：在 QQ/微信聊天窗口输入文字后按 Enter 键

### 模式说明

| 模式 | 说明 |
|------|------|
| QQ | 仅在 QQ 窗口按 Enter 触发图片生成 |
| 微信 | 仅在微信窗口按 Enter 触发图片生成 |
| QQ微信 | 在 QQ 或微信窗口按 Enter 都可触发 |
| 全局 | 在任何窗口按 Enter 都会触发 |

### 文字大小调整

- **自动模式**：点击"自动"按钮，文字大小会根据内容自动适配
- **手动模式**：拖动滑块调整文字大小（20-200）

### 添加角色

1. 切换到"角色管理"页面
2. 输入角色名字和标识（英文小写字母）
3. 输入表情数量
4. 点击"添加角色"
5. 上传角色表情图片

### 上传表情图片

1. 切换到"角色管理"页面
2. 在"上传表情图片"区域选择角色
3. 点击"上传单张图片"或"批量上传图片"
4. 选择图片文件（支持 PNG、JPG、BMP、GIF 等格式）

## 项目结构

```
├── gui_main.py          # 主界面程序
├── main.py              # 原始命令行程序
├── chat_adapter.py      # 聊天适配器（窗口匹配、模式切换）
├── config.py            # 配置文件
├── image_fit_paste.py   # 图片处理工具
├── text_fit_draw.py     # 文字绘制工具
├── build.spec           # PyInstaller 打包配置
├── requirements.txt     # 依赖列表
└── _internal/           # 资源目录
    ├── magic_cut/       # 角色表情图片
    ├── background/      # 背景图片
    └── font*.ttf        # 字体文件
```

## 技术栈

- Python 3.12
- PyQt6
- Pillow (PIL)
- PyAutoGUI
- PyWin32
- Pyperclip
- Keyboard

## 打包

```bash
# 使用 PyInstaller 打包
.venv\Scripts\pyinstaller.exe build.spec --noconfirm
```

打包后的 EXE 文件位于 `dist/魔审galgame聊天器.exe`。

## 注意事项

1. 程序需要管理员权限才能正常监听全局键盘事件
2. 首次使用时请确保 QQ/微信已打开
3. 角色图片需要放在 `_internal/magic_cut/<角色标识>/` 目录下
4. 建议使用 1080p 或更高分辨率的显示器

## License

MIT License

## 致谢

- [manosaba_text_box](https://github.com/oplivilqo/manosaba_text_box/tree/lite) - 项目设计灵感来源
