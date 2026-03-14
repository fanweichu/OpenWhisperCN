# OpenWhisperCN 🎙️⚡️

A zero-dependency, cross-platform push-to-talk whisper client **optimized for Mandarin Chinese**. Hold `F5` to record, release to auto-paste anywhere.

[中文说明](#中文说明) | [English](#english)

---

<h2 id="中文说明">中文说明</h2>

OpenWhisperCN 是一个专为**中文环境**深度优化的本地语音输入工具。纯离线运行，保护隐私。按住快捷键说话，松开后文字将自动粘贴到当前的光标位置。

### ✨ 核心特性
* **中文语境优化**: 代码内置了简繁体引导词与中文语料对齐机制，专为高频中文打字环境设计。
* **全局对讲机模式**: 按住 `F5` 键开始录音，松开自动转写并强制粘贴，支持所有软件输入框。
* **绝对隐私安全**: 基于 `whisper.cpp` 本地推理，声音永远不会被上传到云端。
* **智能自举部署**: 脚本内置操作系统嗅探，自动通过 pip 补齐缺失的 Python 库，真正的“一键运行”。
* **跨平台自适应**: 完美兼容 macOS 与 Linux 环境。

### 🛠 环境依赖
Python 库脚本会自己搞定，但你需要保证系统底层有音频和转写工具：

**macOS 用户:**
```bash
# 如果没装，脚本运行时也会智能提醒你
brew install whisper.cpp sox
```

**Linux 用户:**
```bash
sudo apt install whisper.cpp sox xdotool xclip
```

### 🚀 如何使用

1. 下载项目到本地:
```bash
git clone https://github.com/fanweichu/OpenWhisperCN.git
cd OpenWhisperCN
```

2. 启动程序:
```bash
python3 main.py
```
* **首次运行:** 终端会弹出菜单，请根据提示选择并下载 Whisper 模型（推荐下载 `large-v3-turbo` 获得最佳中文体验）。
* **日常使用:** 保持终端在后台运行。在任意输入框中按住 `F5` 说话，松开后文字将自动粘贴。

### ⚠️ 常见问题 (Troubleshooting)
* **Mac 粘贴失败？** 请前往 `系统设置 -> 隐私与安全性 -> 辅助功能`，把你用来运行脚本的终端（如 iTerm2 或 Terminal）打勾，允许其控制电脑。
* **Linux 录音失败？** 请确保当前用户对麦克风设备 `/dev/snd` 有读取权限。

---

<h2 id="english">English</h2>

OpenWhisperCN is a universal dictation machine **built and optimized for the Chinese language**. It runs completely offline using `whisper.cpp`, ensuring 100% privacy. Just press a key, speak, and your text appears at your cursor.

### ✨ Features
* **Mandarin Optimized**: Uses targeted prompts to ensure accurate Simplified Chinese output.
* **Global Hotkey**: Hold `F5` to record, release to transcribe and paste. Works in any application.
* **100% Offline**: Powered by local GGML models. Your voice never goes to the cloud.
* **Zero-Dependency Bootstrapper**: Detects your OS and auto-installs missing Python packages.
* **Cross-Platform**: Fully supports macOS and Linux (Ubuntu/Debian).

### 🛠 Requirements
The script will install Python dependencies automatically, but you need the core system binaries:

**macOS:**
```bash
brew install whisper.cpp sox
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install whisper.cpp sox xdotool xclip
```

### 🚀 Usage

1. Clone the repository:
```bash
git clone https://github.com/fanweichu/OpenWhisperCN.git
cd OpenWhisperCN
```

2. Run the tool:
```bash
python3 main.py
```
