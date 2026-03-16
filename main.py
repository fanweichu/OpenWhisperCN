#!/usr/bin/env python3

"""
=== OpenWhisper ASR v3.0 (whisper.cpp) ===
操作方式：按住 F9 或 F5 录音，松开后自动识别并粘贴到光标位置。
平台：macOS / Linux
用法：
  python3 whisper_asr.py            # 正常启动
  python3 whisper_asr.py --select   # 重新选择模型
"""

import os
import sys
import subprocess
import time
import urllib.request
import platform
import shutil
import json
import re
from pathlib import Path

# ============================================================
#  1. 自动化依赖自检
# ============================================================
def ensure_dependencies():
    """检测并自动安装缺失的第三方库"""
    required_libs = {
        "pynput": "pynput",
        "pyperclip": "pyperclip"
    }
    
    missing = []
    for lib_name, pip_name in required_libs.items():
        try:
            __import__(lib_name)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        print(f"[!] 发现缺失组件: {', '.join(missing)}")
        print("[-] 正在为您自动安装，请稍候...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[+] 组件安装完成，正在重启脚本...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"[错误] 自动安装失败: {e}")
            print("请手动执行: pip3 install pynput pyperclip")
            sys.exit(1)

ensure_dependencies()

from pynput import keyboard
import pyperclip

# ============================================================
#  2. 平台配置与系统依赖检查
# ============================================================
OS_TYPE = platform.system()
BASE_DIR = Path(__file__).parent.absolute()
MODELS_DIR = BASE_DIR / "models"
CONFIG_FILE = BASE_DIR / ".whisper_config.json"
AUDIO_FILE = "/tmp/whisper_temp.wav"

if OS_TYPE == "Darwin":
    WHISPER_BIN = shutil.which("whisper-cli") or "/opt/homebrew/bin/whisper-cli"
    REC_BIN = shutil.which("rec") or "/opt/homebrew/bin/rec"
elif OS_TYPE == "Linux":
    WHISPER_BIN = shutil.which("whisper-cli") or "/usr/bin/whisper-cli"
    REC_BIN = shutil.which("rec") or "/usr/bin/rec"
else:
    print("[!] 致命错误: 暂不支持的操作系统 ->", OS_TYPE)
    sys.exit(1)

def check_system_deps():
    for bin_path in [WHISPER_BIN, REC_BIN]:
        if not os.path.exists(bin_path):
            print(f"\n[!] 警告: 未发现系统组件 {bin_path}")
            if OS_TYPE == "Darwin":
                if not shutil.which("brew"):
                    print("检测到未安装 Homebrew，请先安装:")
                    print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                print("\n请执行: brew install whisper.cpp sox")
            elif OS_TYPE == "Linux":
                print("\n请执行: sudo apt update && sudo apt install whisper.cpp sox xdotool xclip")
            sys.exit(1)

# ============================================================
#  3. 模型配置与读写记忆
# ============================================================
WHISPER_MODELS = {
    "1": {"name": "tiny", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin", "size": "75 MB", "desc": "速度极快，适合日常极短对话"},
    "2": {"name": "base", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", "size": "142 MB", "desc": "速度快，准确率平衡（推荐）"},
    "3": {"name": "small", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", "size": "466 MB", "desc": "准确率较高，占用适中"},
    "4": {"name": "medium", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin", "size": "1.5 GB", "desc": "高准确率，适合长句"},
    "5": {"name": "large-v3-turbo", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin", "size": "1.6 GB", "desc": "极致准确率，需较高配置"}
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[警告] 配置保存失败: {e}")

# ============================================================
#  4. 模型下载与选择机制
# ============================================================
def download_model(model_info):
    filename = f"ggml-{model_info['name']}.bin"
    save_path = MODELS_DIR / filename
    
    if save_path.exists():
        return str(save_path)
        
    print(f"\n[*] 需要下载 Whisper {model_info['name']} 模型 ({model_info['size']})")
    print(f"    保存至: {save_path}")
    
    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(parents=True)

    def progress_bar(count, block_size, total_size):
        progress = count * block_size
        percent = min(100, int(progress * 100 / total_size))
        bar_len = 40
        filled_len = int(bar_len * progress / total_size)
        bar = '█' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write(f"\r  [{bar}] {percent}% ({progress/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB)")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(model_info['url'], str(save_path), reporthook=progress_bar)
        print("\n[+] 模型下载完成！")
    except KeyboardInterrupt:
        print("\n[!] 下载已取消。")
        if save_path.exists(): os.remove(save_path)
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误]: 下载中断: {e}")
        if save_path.exists(): os.remove(save_path)
        sys.exit(1)
        
    return str(save_path)

def show_model_menu():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║          选择要加载的 Whisper 模型               ║")
    print("╠══════════════════════════════════════════════════╣")
    for k, v in WHISPER_MODELS.items():
        print(f"║  {k}. {v['name']} ({v['size']})")
        print(f"║     {v['desc']}")
        print("║")
    print("╚══════════════════════════════════════════════════╝")

    while True:
        choice = input("\n请选择序号 [1-5]: ").strip()
        if choice in WHISPER_MODELS:
            return choice
        print("[!] 无效选择，请重新输入。")

def setup_model(force_select: bool = False):
    config = load_config()
    saved_choice = config.get("model_choice")
    need_select = force_select or (saved_choice not in WHISPER_MODELS)

    if need_select:
        if force_select:
            print("\n[*] 重新选择模型（--select 模式）")
        else:
            print("\n[*] 首次运行，请选择要加载的模型。")

        choice = show_model_menu()
        config["model_choice"] = choice
        save_config(config)
    else:
        choice = saved_choice
        print(f"[状态]: 加载上次选择的模型 -> {WHISPER_MODELS[choice]['name']}")
        print(f"        （如需更换，请加 --select 参数重新运行）")

    selected = WHISPER_MODELS[choice]
    model_path = download_model(selected)
    return model_path, selected["name"]

# ============================================================
#  5. 核心逻辑：录音与识别
# ============================================================
is_recording = False
record_process = None
current_model_path = ""

def start_recording():
    global is_recording, record_process
    if is_recording:
        return
    
    is_recording = True
    if os.path.exists(AUDIO_FILE): 
        os.remove(AUDIO_FILE)
        
    print("\r🎙️  [录音中...] 松开按键停止          ", end="", flush=True)
    # 让 sox 自动重采样为 16k
    record_process = subprocess.Popen(
        [REC_BIN, "-q", "-c", "1", "-b", "16", AUDIO_FILE, "rate", "16k"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_recording_and_transcribe():
    global is_recording, record_process
    if not is_recording:
        return

    print("\r⏳ [正在识别...]                        ", end="", flush=True)
    is_recording = False
    
    if record_process:
        record_process.terminate()
        record_process.wait()
        record_process = None
    
    try:
        start_t = time.time()
        
        if not os.path.exists(AUDIO_FILE):
            print("\r[提示]: 未检测到音频文件。              ")
            return
            
        # 增加 --prompt 参数强制引导简体输出，屏蔽多余的时间戳输出
        result = subprocess.run(
            [WHISPER_BIN, "-m", current_model_path, "-f", AUDIO_FILE, "-l", "zh", "-nt", "--prompt", "简体中文。"],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        text = result.stdout.strip()
        
        # 净化文本：Whisper 经常输出 [音乐] (清嗓子) 等无用标签，利用正则去除
        clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', text)
        # 去掉多余空格和换行
        clean_text = " ".join([line.strip() for line in clean_text.split("\n") if line.strip()])
        
        elapsed = time.time() - start_t
        
        if clean_text:
            print(f"\r[结果]: {clean_text}")
            print(f"[耗时]: {elapsed:.2f} 秒")
            pyperclip.copy(clean_text)
            if OS_TYPE == "Darwin":
                subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'])
            elif OS_TYPE == "Linux":
                subprocess.run(['xdotool', 'key', 'ctrl+v'])
        else:
            print("\r[提示]: 未检测到有效语音。              ")
            
    except Exception as e:
        print(f"\n[错误]: {e}")
    finally:
        if os.path.exists(AUDIO_FILE):
            os.remove(AUDIO_FILE)

# ============================================================
#  6. 键盘监听与主函数
# ============================================================
def main():
    global current_model_path
    force_select = "--select" in sys.argv

    print("=" * 50)
    print("  OpenWhisper ASR v3.0 (whisper.cpp)")
    print(f"  平台: {OS_TYPE}")
    print("=" * 50)

    check_system_deps()
    current_model_path, model_name = setup_model(force_select=force_select)

    print()
    print("┌────────────────────────────────────────────────┐")
    print("│  ✅ 系统已就绪                                  │")
    print("│  🎙️  按住 F5 或 F9 录音，松开自动粘贴文本         │")
    print("│  🔄 换模型: python3 main.py --select      │")
    print("│  ❌ 退出: Ctrl+C                                │")
    print("└────────────────────────────────────────────────┘")
    print()

    def on_press(key):
        if key in (keyboard.Key.f5, keyboard.Key.f9): 
            start_recording()

    def on_release(key):
        if key in (keyboard.Key.f5, keyboard.Key.f9): 
            stop_recording_and_transcribe()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()