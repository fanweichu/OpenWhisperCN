import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path

# === 1. 自动化依赖自检 (Bootstrapping) ===
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
        print(f"[!] 发现缺失战术组件: {', '.join(missing)}")
        print("[-] 正在为您自动安装，请稍候...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[+] 组件安装完成。")
            # 重新启动脚本以应用新安装的库
            os.execv(sys.executable, ['python3'] + sys.argv)
        except Exception as e:
            print(f"[错误] 自动安装失败: {e}")
            print("请手动执行: pip3 install pynput pyperclip")
            sys.exit(1)

# 执行自检
ensure_dependencies()

# 成功通过自检后导入
from pynput import keyboard
import pyperclip

# === 2. 配置与路径 ===
import platform
import shutil

BASE_DIR = Path(__file__).parent.absolute()
MODELS_DIR = BASE_DIR / "models"
AUDIO_FILE = "/tmp/whisper_temp.wav"

OS_TYPE = platform.system()

if OS_TYPE == "Darwin":
    WHISPER_BIN = shutil.which("whisper-cli") or "/opt/homebrew/bin/whisper-cli"
    REC_BIN = shutil.which("rec") or "/opt/homebrew/bin/rec"
elif OS_TYPE == "Linux":
    WHISPER_BIN = shutil.which("whisper-cli") or "/usr/bin/whisper-cli"
    REC_BIN = shutil.which("rec") or "/usr/bin/rec"
else:
    print("[!] 致命错误: 暂不支持的操作系统 ->", OS_TYPE)
    sys.exit(1)

WHISPER_MODELS = {
    "1": {"name": "tiny", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin", "size": "75 MB"},
    "2": {"name": "base", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", "size": "142 MB"},
    "3": {"name": "small", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", "size": "466 MB"},
    "4": {"name": "medium", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin", "size": "1.5 GB"},
    "5": {"name": "large-v3-turbo", "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin", "size": "1.6 GB"}
}

is_recording = False
record_process = None
current_model_path = ""

# === 3. 内置进度条下载器 (标准库实现) ===
def download_model(model_info):
    filename = f"ggml-{model_info['name']}.bin"
    save_path = MODELS_DIR / filename
    
    print(f"\n[目标]: {filename} ({model_info['size']})")
    print(f"[下载中] -> {save_path}")

    def progress_bar(count, block_size, total_size):
        progress = count * block_size
        percent = min(100, int(progress * 100 / total_size))
        bar_len = 40
        filled_len = int(bar_len * progress / total_size)
        bar = '█' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write(f"\r  [{bar}] {percent}% ({progress/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB)")
        sys.stdout.flush()

    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(parents=True)

    try:
        urllib.request.urlretrieve(model_info['url'], str(save_path), reporthook=progress_bar)
        print(f"\n[成功]: 模型已就绪。")
    except Exception as e:
        print(f"\n[错误]: 下载中断: {e}")
        if save_path.exists(): os.remove(save_path)
        sys.exit(1)
        
    return str(save_path)

def setup():
    global current_model_path
    
    # 检查系统依赖
    for bin_path in [WHISPER_BIN, REC_BIN]:
        if not os.path.exists(bin_path):
            print(f"[!] 警告: 未发现系统组件 {bin_path}")
            if OS_TYPE == "Darwin":
                if not shutil.which("brew"):
                    print("检测到未安装 Homebrew，请先在终端执行以下指令安装:")
                    print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                    print("\n安装完成后，再执行:")
                print("请执行: brew install whisper.cpp sox")
            elif OS_TYPE == "Linux":
                print("请执行: sudo apt install whisper.cpp sox xdotool xclip")
            sys.exit(1)

    # 检查本地模型
    if not MODELS_DIR.exists(): MODELS_DIR.mkdir()
    existing = list(MODELS_DIR.glob("*.bin"))
    
    if existing:
        current_model_path = str(existing[0])
        print(f"[状态]: 激活模型 -> {existing[0].name}")
    else:
        print("\n=== OpenWhisper 模型管理 ===")
        for k, v in WHISPER_MODELS.items():
            print(f"  {k}. {v['name']} ({v['size']})")
        
        choice = input("\n请选择要下载的模型序号 (1-5): ").strip()
        if choice in WHISPER_MODELS:
            current_model_path = download_model(WHISPER_MODELS[choice])
        else:
            print("[错误]: 指令无效，战术撤退。")
            sys.exit(1)

# === 4. 核心逻辑 ===
def start_recording():
    global is_recording, record_process
    if not is_recording:
        print("\r[正在监听...] (松开 F5 结束)          ", end="", flush=True)
        is_recording = True
        if os.path.exists(AUDIO_FILE): os.remove(AUDIO_FILE)
        # 优化战术：不再强制硬件采样率，而是让 sox 自动重采样为 16k
        record_process = subprocess.Popen([REC_BIN, "-q", "-c", "1", "-b", "16", AUDIO_FILE, "rate", "16k"])

def stop_recording_and_transcribe():
    global is_recording, record_process
    if is_recording:
        print("\r[正在识别...]                        ", end="", flush=True)
        is_recording = False
        if record_process:
            record_process.terminate()
            record_process.wait()
        
        try:
            # 增加 --prompt 参数强制引导简体输出
            result = subprocess.run(
                [WHISPER_BIN, "-m", current_model_path, "-f", AUDIO_FILE, "-l", "zh", "-nt", "--prompt", "简体中文。"],
                capture_output=True, text=True, encoding='utf-8'
            )
            
            text = result.stdout.strip()
            clean_text = " ".join([l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[")])
            
            if clean_text:
                print(f"\r[结果]: {clean_text}               ")
                pyperclip.copy(clean_text)
                if OS_TYPE == "Darwin":
                    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'])
                elif OS_TYPE == "Linux":
                    subprocess.run(['xdotool', 'key', 'ctrl+v'])
            else:
                print("\r[提示]: 未检测到有效语音。           ")
        except Exception as e:
            print(f"\n[错误]: {e}")

def on_press(key):
    if key == keyboard.Key.f5: start_recording()

def on_release(key):
    if key == keyboard.Key.f5: stop_recording_and_transcribe()

if __name__ == "__main__":
    print("=== OpenWhisper v3.0 (Standalone) ===")
    setup()
    print("\n[系统已就绪] 按住 F5 录音，松开自动粘贴文本。")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
