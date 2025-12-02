#!/usr/bin/env python3
# ruff: noqa: E402,I001

# 在最早阶段设置 UTF-8 编码环境变量 - 必须在任何导入之前
import ctypes
import glob
import io
import locale
import logging
import os
import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Literal, cast
from types import ModuleType
import requests
import yaml


try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from modules.markdown_renderer import convert_markdown_to_html

if sys.platform == "darwin":
    try:
        import Cocoa  # pyright: ignore[reportMissingImports]
        import Foundation  # pyright: ignore[reportMissingImports]
        import objc  # pyright: ignore[reportMissingImports]
    except ImportError:
        Cocoa = None
        Foundation = None
        objc = None
    NSDistributedNotificationCenter = (
        getattr(Cocoa, "NSDistributedNotificationCenter", None) if Cocoa else None
    )
    NSObject = getattr(Foundation, "NSObject", None) if Foundation else None
else:  # 非 macOS 平台仅作占位
    Cocoa = None
    Foundation = None
    objc = None
    NSDistributedNotificationCenter = None
    NSObject = None

os.environ.setdefault("LANG", "zh_CN.UTF-8")
os.environ.setdefault("LC_ALL", "zh_CN.UTF-8")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if sys.platform == "darwin":
    try:
        locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8")
    except Exception:
        with suppress(Exception):
            locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

"""
MTGA GUI - 重构版本
采用单进程模块化架构，解决 Nuitka 打包兼容性问题

功能:
1. 一键生成证书（模块化调用）
2. 导入证书到系统信任存储
3. 修改 hosts 文件
4. 启动代理服务器（线程模式）
"""


# Setup environment (fixes macOS Tkinter functionality)
def setup_environment():
    """Prepare Tkinter environment variables for macOS builds."""
    if sys.platform != "darwin":  # Not macOS, return directly
        return

    # Check if in packaged environment
    if not (getattr(sys, "frozen", False) or "MTGA_GUI" in sys.executable):
        return  # Development environment doesn't need special handling

    # Nuitka packaged environment
    executable_dir = os.path.dirname(sys.executable)

    # Switch working directory - this is critical
    # When launched from Finder on macOS, working directory is "/", must switch
    if os.getcwd() == "/":
        # Prefer switching to user home directory (safer)
        home_dir = os.path.expanduser("~")
        try:
            os.chdir(home_dir)
        except OSError:
            with suppress(OSError):
                os.chdir(executable_dir)

    # Set TCL/TK library paths (if they exist)
    tcl_library = os.path.join(executable_dir, "tcl-files")
    tk_library = os.path.join(executable_dir, "tk-files")

    if os.path.exists(tcl_library):
        os.environ["TCL_LIBRARY"] = tcl_library

    if os.path.exists(tk_library):
        os.environ["TK_LIBRARY"] = tk_library



# Call setup_environment before importing other modules
setup_environment()


def ensure_utf8_stdio():
    """Ensure stdout/stderr can emit UTF-8 even when Finder starts the app."""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if not stream:
            continue
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower().startswith("utf-8"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            buffer = getattr(stream, "buffer", None)
            if buffer is None:
                continue
            try:
                new_stream = io.TextIOWrapper(
                    buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
            except Exception:
                continue
            setattr(sys, name, new_stream)
        except Exception:
            pass


ensure_utf8_stdio()

# 导入自定义模块
try:
    from modules.cert_generator import generate_certificates
    from modules.cert_cleaner import clear_ca_cert
    from modules.cert_installer import install_ca_cert
    from modules.hosts_manager import modify_hosts_file, open_hosts_file
    from modules.proxy_server import ProxyServer
    from modules.resource_manager import (
        ResourceManager,
        copy_template_files,
        get_user_data_dir,
        is_packaged,
    )
    from modules.thread_manager import ThreadManager
    from modules import macos_privileged_helper, update_checker
    from modules import resource_manager as resource_manager_module
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 modules 目录及其模块文件存在")
    sys.exit(1)

# 处理 macOS 持久化 helper CLI 调用
if macos_privileged_helper.HELPER_FLAG in sys.argv:
    macos_privileged_helper.main()
    sys.exit(0)

# 全局变量
proxy_server_instance = None
resource_manager = ResourceManager()
thread_manager = ThreadManager()

HTTP_OK = 200
CONTENT_PREVIEW_LEN = 50
API_KEY_VISIBLE_CHARS = 4
APP_DISPLAY_NAME = "MTGA GUI"
GITHUB_REPO = "BiFangKNT/mtga"
ERROR_LOG_FILENAME = "mtga_gui_error.log"
CA_COMMON_NAME = "MTGA_CA"
THEME_OBSERVER_CLASS = None


def setup_logging():
    """配置全局日志，将 ERROR 级别写入用户数据目录并带时间戳。"""
    user_dir = get_user_data_dir()
    log_path = os.path.join(user_dir, ERROR_LOG_FILENAME)
    os.makedirs(user_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", None) == os.path.abspath(log_path)
        for handler in root_logger.handlers
    ):
        root_logger.addHandler(file_handler)

    return log_path


ERROR_LOG_PATH = setup_logging()


def log_error(message: str, exc_info=None):
    """统一的错误日志入口，写入文件并附带时间戳。"""
    logging.getLogger("mtga_gui").error(message, exc_info=exc_info)


def install_global_exception_hook():
    """将未捕获异常写入错误日志。"""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log_error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


install_global_exception_hook()


def resolve_app_version():
    """从构建期注入的版本信息或 pyproject.toml 解析应用版本。"""

    def normalize_version(raw_value: str | None) -> str | None:
        if not raw_value:
            return None
        raw_value = raw_value.strip()
        if not raw_value:
            return None
        return raw_value if raw_value.startswith("v") else f"v{raw_value}"

    env_version = normalize_version(os.getenv("MTGA_VERSION"))
    if env_version:
        return env_version

    baked_version: str | None = None
    try:
        from modules import _build_version as build_version_module  # type: ignore  # noqa: PLC0415

        baked_version = normalize_version(
            getattr(build_version_module, "BUILT_APP_VERSION", None)
        )
    except Exception:
        baked_version = None

    if baked_version:
        return baked_version

    if tomllib is None:
        return "v0.0.0"

    project_root = Path(__file__).resolve().parent
    pyproject_path = project_root / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        version = normalize_version(data.get("project", {}).get("version"))
        if not version:
            return "v0.0.0"
        return version
    except Exception:
        return "v0.0.0"


APP_VERSION = resolve_app_version()



def get_proxy_instance():
    """读取当前代理实例"""
    return globals().get("proxy_server_instance")


def set_proxy_instance(instance):
    """更新当前代理实例"""
    globals()["proxy_server_instance"] = instance


def check_is_admin():
    """检查是否具有管理员权限"""
    try:
        if os.name == "nt":  # Windows
            return ctypes.windll.shell32.IsUserAnAdmin()
        elif os.name == "posix":  # Unix/Linux/macOS
            return os.geteuid() == 0
        else:
            return False
    except Exception:
        return False


def run_as_admin():
    """请求管理员权限并重启脚本"""
    if not check_is_admin():
        if os.name == "nt":  # Windows
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        elif os.name == "posix":  # Unix/Linux/macOS
            print("此程序需要管理员权限才能运行。")
            print("请使用以下命令重新运行：")
            print(f"sudo {sys.executable} {' '.join(sys.argv)}")
            sys.exit(1)
        else:
            print("不支持的操作系统")
            sys.exit(1)


def check_environment():
    """检查运行环境"""
    missing_resources = resource_manager.check_resources()

    if missing_resources:
        error_msg = "环境检查失败，缺少以下资源:\n" + "\n".join(missing_resources)
        return False, error_msg

    return True, "环境检查通过"


# 配置文件路径（持久化到用户数据目录）
CONFIG_FILE = resource_manager.get_user_config_file()


def load_config_groups():
    """从配置文件加载配置组"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "config_groups" in config:
                    config_groups = config["config_groups"]
                    current_index = config.get("current_config_index", 0)
                    return config_groups, current_index
    except Exception:
        pass
    return [], 0


def load_global_config():
    """从配置文件加载全局配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config:
                    mapped_model_id = config.get("mapped_model_id", "")
                    mtga_auth_key = config.get("mtga_auth_key", "")
                    return mapped_model_id, mtga_auth_key
    except Exception:
        pass
    return "", ""


def save_config_groups(config_groups, current_index=0, mapped_model_id=None, mtga_auth_key=None):
    """保存配置组和全局配置到配置文件"""
    try:
        # 首先读取现有配置，保留其他字段
        config_data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

        # 更新配置组和索引
        config_data["config_groups"] = config_groups
        config_data["current_config_index"] = current_index

        # 更新全局配置（如果提供）
        if mapped_model_id is not None:
            config_data["mapped_model_id"] = mapped_model_id
        if mtga_auth_key is not None:
            config_data["mtga_auth_key"] = mtga_auth_key

        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(
                config_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False,
            )
        return True
    except Exception:
        return False


def get_current_config():
    """获取当前选中的配置"""
    config_groups, current_index = load_config_groups()
    if config_groups and 0 <= current_index < len(config_groups):
        return config_groups[current_index]
    return {}


def test_model_connection(config_group, log_func=print):
    """测试模型连接（GET /v1/models/{模型id}）"""

    def run_test():
        model_id = "未知模型"  # 提前初始化，避免未绑定问题
        try:
            api_url = config_group.get("api_url", "").rstrip("/")
            model_id = config_group.get("model_id", "")
            api_key = config_group.get("api_key", "")

            if not api_url or not model_id:
                log_func("测试失败: API URL或模型ID为空")
                return

            # 构建测试URL
            test_url = f"{api_url}/v1/models/{model_id}"

            # 准备请求头
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            log_func(f"正在测试模型连接: {test_url}")

            # 发送GET请求测试模型
            response = requests.get(test_url, headers=headers, timeout=10)

            if response.status_code == HTTP_OK:
                log_func(f"✅ 模型测试成功: {model_id}")
                try:
                    model_info = response.json()
                    if "id" in model_info:
                        log_func(f"   模型ID: {model_info['id']}")
                    if "object" in model_info:
                        log_func(f"   对象类型: {model_info['object']}")
                except Exception:
                    log_func("   (响应解析成功，但无法获取详细信息)")
            else:
                log_func(f"❌ 模型测试失败: HTTP {response.status_code}")
                try:
                    error_info = response.text[:200]
                    log_func(f"   错误信息: {error_info}")
                except Exception:
                    log_func("   (无法获取错误详情)")

        except requests.exceptions.Timeout:
            log_func(f"❌ 模型测试超时: {model_id}")
        except requests.exceptions.RequestException as e:
            log_func(f"❌ 模型测试网络错误: {str(e)}")
        except Exception as e:
            log_func(f"❌ 模型测试意外错误: {str(e)}")

    # 交给统一线程管理器调度，避免阻塞UI且保留状态
    thread_manager.run("test_model_connection", run_test)


def test_chat_completion(config_group, log_func=print):
    """测试聊天补全连接（POST /v1/chat/completions）"""

    def run_test():
        model_id = "未知模型"  # 提前初始化，避免未绑定问题
        try:
            api_url = config_group.get("api_url", "").rstrip("/")
            model_id = config_group.get("model_id", "")
            api_key = config_group.get("api_key", "")

            if not api_url or not model_id:
                log_func("测活失败: API URL或模型ID为空")
                return

            # 构建测试URL
            test_url = f"{api_url}/v1/chat/completions"

            # 准备请求头
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # 准备测试数据（最小输入）
            test_data = {
                "model": model_id,
                "messages": [{"role": "user", "content": "1"}],
                "max_tokens": 1,
                "temperature": 0,
            }

            log_func(f"正在测活模型: {model_id} (会消耗少量tokens)")

            # 发送POST请求测试聊天补全
            response = requests.post(test_url, json=test_data, headers=headers, timeout=30)

            if response.status_code == HTTP_OK:
                log_func(f"✅ 模型测活成功: {model_id}")
                try:
                    completion_info = response.json()
                    if "choices" in completion_info and completion_info["choices"]:
                        content = (
                            completion_info["choices"][0]
                            .get("message", {})
                            .get("content", "")
                            .strip()
                        )
                        preview = content[:CONTENT_PREVIEW_LEN]
                        suffix = "..." if len(content) > CONTENT_PREVIEW_LEN else ""
                        log_func(f"   响应内容: {preview}{suffix}")
                    if "usage" in completion_info:
                        usage = completion_info["usage"]
                        log_func(f"   消耗tokens: {usage.get('total_tokens', '未知')}")
                except Exception:
                    log_func("   (响应成功，但无法解析详细信息)")
            else:
                log_func(f"❌ 模型测活失败: HTTP {response.status_code}")
                try:
                    error_info = response.text[:200]
                    log_func(f"   错误信息: {error_info}")
                except Exception:
                    log_func("   (无法获取错误详情)")

        except requests.exceptions.Timeout:
            log_func(f"❌ 模型测活超时: {model_id}")
        except requests.exceptions.RequestException as e:
            log_func(f"❌ 模型测活网络错误: {str(e)}")
        except Exception as e:
            log_func(f"❌ 模型测活意外错误: {str(e)}")

    # 使用线程管理器调度任务
    thread_manager.run("test_chat_completion", run_test)


def create_main_window() -> tk.Tk | None:  # noqa: PLR0915
    """创建主窗口"""
    # 在 macOS 上，确保工作目录不是根目录
    if sys.platform == "darwin" and os.getcwd() == "/":
        with suppress(OSError):
            os.chdir(os.path.expanduser("~"))

    window = tk.Tk()
    window.title("MTGA GUI")
    window.geometry("1250x750")
    window.resizable(True, True)

    if sys.platform == "darwin":
        try:
            # Retina 屏幕上 Tk 默认按 72 DPI 渲染，字号偏小，这里按实际 DPI 调整缩放
            scaling = window.winfo_fpixels("1i") / 72.0
            if scaling > 0:
                window.tk.call("tk", "scaling", scaling)
        except tk.TclError:
            pass

    def tk_error_handler(exc, val, tb):
        log_error("Tkinter 回调异常", exc_info=(exc, val, tb))

    window.report_callback_exception = tk_error_handler

    font_cache = {}

    def get_preferred_font(
        size: int = 10,
        weight: Literal["normal", "bold"] = "normal",
    ) -> tkfont.Font:
        """返回跨平台首选字体对象，缺失时回退到默认字体。"""
        effective_size = size
        if sys.platform == "darwin":
            # macOS 上字号普遍偏小，整体放大约 15%
            effective_size = max(size + 1, round(size * 1.15))

        key = (effective_size, weight)
        if key in font_cache:
            font_obj = font_cache[key]
            print(
                f"[字体] 使用缓存字体: {font_obj.cget('family')} "
                f"size={font_obj.cget('size')} weight={font_obj.cget('weight')}",
            )
            return font_obj

        available = {name.lower(): name for name in tkfont.families()}
        candidates = [
            "Maple Mono NF CN",
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "PingFang SC",
            "Hiragino Sans GB",
            "Segoe UI",
            "Arial",
        ]

        chosen = None
        for name in candidates:
            matched = available.get(name.lower())
            if matched:
                chosen = matched
                break

        if chosen is None:
            font_obj = tkfont.nametofont("TkDefaultFont").copy()
            font_obj.configure(size=effective_size, weight=weight)
        else:
            font_obj = tkfont.Font(family=chosen, size=effective_size, weight=weight)

        font_cache[key] = font_obj
        print(
            f"[字体] 选用字体: {font_obj.cget('family')} "
            f"size={font_obj.cget('size')} weight={font_obj.cget('weight')}",
        )
        return font_obj

    # 全局字体覆盖，避免 ttk 控件仍然使用系统默认字体
    default_font = get_preferred_font()
    window.option_add("*Font", default_font)
    ttk.Style().configure(".", font=default_font)

    # 设置窗口图标
    try:
        if os.name == "nt":
            icon_path = resource_manager.get_icon_file("f0bb32_bg-black.ico")
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
    except Exception:
        pass

    # 创建主框架
    main_frame = ttk.Frame(window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 添加标题
    title_label = ttk.Label(
        main_frame,
        text="MTGA - 代理服务器管理工具",
        font=get_preferred_font(size=16, weight="bold"),
    )
    title_label.pack(pady=10)

    # 创建左右分栏
    main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    main_paned.pack(fill=tk.BOTH, expand=True, pady=5)

    # 左侧功能区域
    left_frame = ttk.Frame(main_paned, width=1)
    main_paned.add(left_frame, weight=1)

    left_frame.grid_rowconfigure(0, weight=1)
    left_frame.grid_columnconfigure(0, weight=1)
    left_content = ttk.Frame(left_frame)
    left_content.grid(row=0, column=0, sticky="nsew")

    # 右侧日志区域
    right_frame = ttk.Frame(main_paned, width=1)
    main_paned.add(right_frame, weight=1)

    # 创建日志文本框
    log_frame = ttk.LabelFrame(right_frame, text="日志")
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_text = scrolledtext.ScrolledText(log_frame, height=10, width=1)
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def log(message):
        """日志输出函数"""
        # 将 \\n 替换为真正的换行符
        formatted_message = message.replace("\\n", "\n")
        log_text.insert(tk.END, f"{formatted_message}\n")
        log_text.see(tk.END)
        log_text.update()  # 强制更新显示
        try:
            print(formatted_message)  # 同时输出到控制台
        except UnicodeEncodeError:
            fallback = formatted_message.encode("unicode_escape").decode("ascii", errors="replace")
            print(fallback)

    def detect_macos_dark_mode():
        """检测 macOS 是否处于深色模式"""
        if sys.platform != "darwin":
            return False

        apple_script = (
            'tell application "System Events" to tell appearance preferences to get dark mode'
        )
        commands = [
            (["osascript", "-e", apple_script], {"true"}),
            (["defaults", "read", "-g", "AppleInterfaceStyle"], {"dark"}),
        ]
        for cmd, expected in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except (FileNotFoundError, OSError):
                continue
            output = (result.stdout or "").strip().lower()
            if result.returncode == 0 and output in expected:
                return True
        return False

    macos_dark_mode = detect_macos_dark_mode()

    def register_macos_theme_observer(callback):
        """监听 macOS 主题切换通知并返回 (center, observer)。"""
        if (
            sys.platform != "darwin"
            or NSDistributedNotificationCenter is None
            or NSObject is None
            or objc is None
        ):
            return None, None

        global THEME_OBSERVER_CLASS  # noqa: PLW0603
        if THEME_OBSERVER_CLASS is None:

            class ThemeObserver(NSObject):  # type: ignore[misc]
                """在 macOS 上监听主题切换通知。"""

                def initWithCallback_(self, cb):
                    obj = objc.super(ThemeObserver, self).init()  # type: ignore[attr-defined]
                    if obj is None:
                        return None
                    obj._callback = cb
                    return obj

                def themeChanged_(self, _notification):
                    if getattr(self, "_callback", None):
                        self._callback()

            THEME_OBSERVER_CLASS = ThemeObserver

        observer = THEME_OBSERVER_CLASS.alloc().initWithCallback_(callback)  # type: ignore[call-arg]
        center = NSDistributedNotificationCenter.defaultCenter()
        selector_factory: Any = objc.selector  # type: ignore[attr-defined]
        selector = selector_factory(  # type: ignore[call-arg]
            THEME_OBSERVER_CLASS.themeChanged_, signature=b"v@:@"
        )
        center.addObserver_selector_name_object_(
            observer,
            selector,
            "AppleInterfaceThemeChangedNotification",
            None,
        )
        return center, observer

    def create_tooltip(widget, text, wraplength=300):
        """为控件创建可复用悬浮提示"""
        tooltip_window = None
        bg_color = "#2C2C2E" if macos_dark_mode else "lightyellow"
        fg_color = "#F5F5F7" if macos_dark_mode else "black"

        def on_enter(event):
            nonlocal tooltip_window
            tooltip_window = tk.Toplevel()
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip_window.configure(bg=bg_color, relief="solid", bd=1, highlightthickness=0)
            label = tk.Label(
                tooltip_window,
                text=text,
                bg=bg_color,
                fg=fg_color,
                font=get_preferred_font(size=9),
                wraplength=wraplength,
            )
            label.pack()

        def on_leave(event):
            nonlocal tooltip_window
            if tooltip_window:
                tooltip_window.destroy()
                tooltip_window = None

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    proxy_start_task_id = None
    proxy_stop_task_id = None
    hosts_task_id = None
    shutdown_task_id = None

    def build_proxy_config():
        """根据当前 UI 状态生成代理配置"""
        current_config = get_current_config()
        if not current_config:
            log("❌ 错误: 没有可用的配置组")
            return None
        config = current_config.copy()
        config["debug_mode"] = debug_mode_var.get()
        config["stream_mode"] = stream_mode_combo.get() if stream_mode_var.get() else None
        return config

    def stop_proxy_instance(reason="stop", show_idle_message=False):
        """统一停止代理实例，返回是否存在运行中的服务。"""
        instance = get_proxy_instance()
        if instance and instance.is_running():
            if reason == "restart":
                log("检测到代理服务器正在运行，正在停止旧实例...")
            else:
                log("正在停止代理服务器...")
            try:
                instance.stop()
                log("✅ 代理服务器已停止")
            except Exception as exc:  # noqa: BLE001
                log(f"停止代理服务器时出错: {exc}")
            finally:
                set_proxy_instance(None)
            return True
        if show_idle_message:
            log("代理服务器未运行")
        return False

    def start_proxy_instance(
        config, success_message="✅ 代理服务器启动成功", *, hosts_modified=False
    ):
        """启动代理实例并输出统一日志。

        hosts_modified=True 表示已在外部完成 hosts 更新，可跳过内置步骤。
        """
        if not hosts_modified:
            log("正在修改hosts文件...")
            if not modify_hosts_file(log_func=log):
                log("❌ 修改hosts文件失败，代理服务器未启动")
                return False
        log("开始启动代理服务器...")
        instance = ProxyServer(config, log_func=log, thread_manager=thread_manager)
        set_proxy_instance(instance)
        if instance.start():
            log(success_message)
            return True
        log("❌ 代理服务器启动失败")
        set_proxy_instance(None)
        return False

    def stop_proxy_and_restore(show_idle_message=False, *, block_hosts_cleanup=False):
        """停止代理并移除模块写入的 hosts 记录。

        block_hosts_cleanup=True 时会同步等待 hosts 操作完成，避免程序退出前记录未清理。
        """
        stopped = stop_proxy_instance(show_idle_message=show_idle_message)
        modify_hosts_task("remove", block=block_hosts_cleanup)
        return stopped

    # 显示环境检查结果
    env_ok, env_msg = check_environment()
    if env_ok:
        log(f"✅ {env_msg}")
        if is_packaged():
            log("📦 运行在 Nuitka 打包环境中")
        else:
            log("🔧 运行在开发环境中")
    else:
        log(f"❌ {env_msg}")

    # 配置组管理界面
    config_groups = []
    current_config_index = 0
    config_frame = ttk.LabelFrame(left_content, text="代理服务器配置组")
    config_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    config_paned = ttk.PanedWindow(config_frame, orient=tk.HORIZONTAL)
    config_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 配置组列表
    config_list_frame = ttk.Frame(config_paned)
    config_paned.add(config_list_frame, weight=3)

    # 配置组列表标题和刷新按钮
    list_header_frame = ttk.Frame(config_list_frame)
    list_header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

    ttk.Label(list_header_frame, text="配置组列表:").pack(side=tk.LEFT)

    def refresh_config_list():
        """刷新配置组列表"""
        refresh_config_tree()
        log("已刷新配置组列表")

    # 测活按钮功能
    def test_selected_config():
        """测活选中的配置组"""
        selected_index = get_selected_index()
        if selected_index < 0:
            log("请先选择要测活的配置组")
            return

        config_group = config_groups[selected_index]
        test_chat_completion(config_group, log)

    # 测活按钮
    test_btn = ttk.Button(list_header_frame, text="测活", command=test_selected_config, width=6)
    test_btn.pack(side=tk.RIGHT, padx=5)

    create_tooltip(
        test_btn,
        "测试选中配置组的实际对话功能\n会发送最小请求并消耗少量tokens\n请确保配置正确后使用",
        wraplength=250,
    )

    refresh_btn = ttk.Button(list_header_frame, text="刷新", command=refresh_config_list, width=6)
    refresh_btn.pack(side=tk.RIGHT, padx=16)

    create_tooltip(
        refresh_btn,
        "重新加载配置文件中的配置组\n用于同步外部修改或恢复意外更改",
        wraplength=250,
    )

    tree_frame = ttk.Frame(config_list_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    columns = ("序号", "API URL", "实际模型ID", "API Key")
    config_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)

    # 滚动条
    v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=config_tree.yview)
    config_tree.configure(yscrollcommand=v_scrollbar.set)
    h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=config_tree.xview)
    config_tree.configure(xscrollcommand=h_scrollbar.set)

    # 设置列
    config_tree.heading("序号", text="序号")
    config_tree.heading("API URL", text="API URL")
    config_tree.heading("实际模型ID", text="实际模型ID")
    config_tree.heading("API Key", text="API Key")

    config_tree.column("序号", width=30, anchor=tk.CENTER)
    config_tree.column("API URL", width=200)
    config_tree.column("实际模型ID", width=120)
    config_tree.column("API Key", width=120)

    config_tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # 配置组操作按钮
    config_buttons_frame = ttk.Frame(config_paned)
    config_paned.add(config_buttons_frame, weight=1)

    ttk.Label(config_buttons_frame, text="操作:").pack(anchor=tk.W, padx=5, pady=(5, 0))

    def refresh_config_tree():
        """刷新配置组列表"""
        nonlocal config_groups, current_config_index
        config_groups, current_config_index = load_config_groups()

        for item in config_tree.get_children():
            config_tree.delete(item)

        for i, group in enumerate(config_groups):
            # 向下兼容：如果是旧配置还有target_model_id，显示它；否则显示API key的掩码版本
            if "target_model_id" in group:
                # 旧配置兼容模式
                fourth_col = group.get("target_model_id", "") or "(无)"
            else:
                # 新配置：显示API key的掩码版本
                api_key = group.get("api_key", "")
                if api_key:
                    if len(api_key) > API_KEY_VISIBLE_CHARS:
                        mask = "*" * (len(api_key) - API_KEY_VISIBLE_CHARS)
                        suffix = api_key[-API_KEY_VISIBLE_CHARS:]
                        fourth_col = f"{mask}{suffix}"
                    else:
                        fourth_col = "***"
                else:
                    fourth_col = "(无)"

            config_tree.insert(
                "",
                "end",
                values=(i + 1, group.get("api_url", ""), group.get("model_id", ""), fourth_col),
            )

        if config_groups and 0 <= current_config_index < len(config_groups):
            children = config_tree.get_children()
            if current_config_index < len(children):
                config_tree.selection_set(children[current_config_index])
                config_tree.focus(children[current_config_index])

    def get_selected_index():
        """获取选中的配置组索引"""
        selection = config_tree.selection()
        if selection:
            item = selection[0]
            return config_tree.index(item)
        return -1

    def on_config_select(event):
        """配置组选择事件"""
        nonlocal current_config_index
        selected_index = get_selected_index()
        if selected_index >= 0:
            current_config_index = selected_index
            save_config_groups(config_groups, current_config_index)

    config_tree.bind("<<TreeviewSelect>>", on_config_select)

    # 配置组管理函数（简化版）
    def add_config_group():  # noqa: PLR0915
        """新增配置组"""

        def save_new_config():
            name = name_var.get().strip()
            api_url = api_url_var.get().strip()
            model_id = model_id_var.get().strip()
            api_key = api_key_var.get().strip()

            # 调整验证逻辑：API URL、实际模型ID、API Key是必填的
            if not api_url or not model_id or not api_key:
                log("错误: API URL、实际模型ID和API Key都是必填项")
                return

            new_group = {
                "name": name,  # 配置组名称改为可选
                "api_url": api_url,
                "model_id": model_id,  # 这是实际调用的模型ID
                "api_key": api_key,  # 新增API key字段
            }

            config_groups.append(new_group)
            if save_config_groups(config_groups, current_config_index):
                display_name = name if name else f"配置组 {len(config_groups)}"
                log(f"已添加配置组: {display_name}")
                refresh_config_list()
                add_window.destroy()

                # 保存后测试模型
                test_model_connection(new_group, log)
            else:
                log("保存配置组失败")

        add_window = tk.Toplevel(window)
        add_window.title("新增配置组")
        add_window.geometry("450x300")  # 调整窗口大小以容纳新字段
        add_window.resizable(False, False)
        add_window.transient(window)
        add_window.grab_set()

        # 居中显示
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - (add_window.winfo_width() // 2)
        y = (add_window.winfo_screenheight() // 2) - (add_window.winfo_height() // 2)
        add_window.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(add_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置组名称（可选）
        ttk.Label(main_frame, text="配置组名称 (可选):").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=35)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # API URL（必填）
        ttk.Label(main_frame, text="* API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_url_var = tk.StringVar()
        api_url_entry = ttk.Entry(main_frame, textvariable=api_url_var, width=35)
        api_url_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # 实际模型ID（必填）
        ttk.Label(main_frame, text="* 实际模型ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_id_var = tk.StringVar()
        model_id_entry = ttk.Entry(main_frame, textvariable=model_id_var, width=35)
        model_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # API Key（必填）
        ttk.Label(main_frame, text="* API Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(main_frame, textvariable=api_key_var, width=35, show="*")
        api_key_entry.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # 添加说明标签
        info_label = ttk.Label(
            main_frame,
            text="* 为必填项",
            font=get_preferred_font(size=8),
            foreground="gray",
        )
        info_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=save_new_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=add_window.destroy).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)
        name_entry.focus()

    # 配置组操作按钮
    ttk.Button(config_buttons_frame, text="新增", command=add_config_group).pack(
        fill=tk.X, padx=5, pady=2
    )

    def edit_config_group():  # noqa: PLR0915
        """修改配置组"""
        selected_index = get_selected_index()
        if selected_index < 0:
            log("请先选择要修改的配置组")
            return

        current_group = config_groups[selected_index]

        def save_edited_config():
            name = name_var.get().strip()
            api_url = api_url_var.get().strip()
            model_id = model_id_var.get().strip()
            api_key = api_key_var.get().strip()

            # 调整验证逻辑：API URL、实际模型ID、API Key是必填的
            if not api_url or not model_id or not api_key:
                log("错误: API URL、实际模型ID和API Key都是必填项")
                return

            # 更新配置组
            config_groups[selected_index] = {
                "name": name,  # 配置组名称改为可选
                "api_url": api_url,
                "model_id": model_id,  # 这是实际调用的模型ID
                "api_key": api_key,  # API key字段
            }

            if save_config_groups(config_groups, current_config_index):
                display_name = name if name else f"配置组 {selected_index + 1}"
                log(f"已修改配置组: {display_name}")
                refresh_config_list()
                edit_window.destroy()

                # 保存后测试模型
                test_model_connection(config_groups[selected_index], log)
            else:
                log("保存配置组失败")

        # 创建修改窗口
        edit_window = tk.Toplevel(window)
        edit_window.title("修改配置组")
        edit_window.geometry("450x300")  # 调整窗口大小
        edit_window.resizable(False, False)
        edit_window.transient(window)
        edit_window.grab_set()

        # 居中显示
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(edit_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置组名称（可选）
        ttk.Label(main_frame, text="配置组名称 (可选):").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=current_group.get("name", ""))
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=35)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # API URL（必填）
        ttk.Label(main_frame, text="* API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_url_var = tk.StringVar(value=current_group.get("api_url", ""))
        api_url_entry = ttk.Entry(main_frame, textvariable=api_url_var, width=35)
        api_url_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # 实际模型ID（必填）
        ttk.Label(main_frame, text="* 实际模型ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_id_var = tk.StringVar(value=current_group.get("model_id", ""))
        model_id_entry = ttk.Entry(main_frame, textvariable=model_id_var, width=35)
        model_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # API Key（必填）
        ttk.Label(main_frame, text="* API Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar(value=current_group.get("api_key", ""))
        api_key_entry = ttk.Entry(main_frame, textvariable=api_key_var, width=35, show="*")
        api_key_entry.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # 添加说明标签
        info_label = ttk.Label(
            main_frame,
            text="* 为必填项",
            font=get_preferred_font(size=8),
            foreground="gray",
        )
        info_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=save_edited_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=edit_window.destroy).pack(
            side=tk.LEFT, padx=5
        )

        main_frame.columnconfigure(1, weight=1)
        name_entry.focus()

    def delete_config_group():
        """删除配置组"""
        selected_index = get_selected_index()
        if selected_index < 0:
            log("请先选择要删除的配置组")
            return

        if len(config_groups) <= 1:
            log("至少需要保留一个配置组")
            return

        group_name = config_groups[selected_index].get("name", f"配置组{selected_index + 1}")

        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除配置组 '{group_name}' 吗？"):
            del config_groups[selected_index]

            # 调整当前选中索引
            nonlocal current_config_index
            if current_config_index >= len(config_groups):
                current_config_index = len(config_groups) - 1
            elif current_config_index > selected_index:
                current_config_index -= 1

            if save_config_groups(config_groups, current_config_index):
                log(f"已删除配置组: {group_name}")
                refresh_config_list()
            else:
                log("保存配置组失败")

    def move_config_up():
        """上移配置组"""
        selected_index = get_selected_index()
        if selected_index <= 0:
            return

        # 交换位置
        config_groups[selected_index], config_groups[selected_index - 1] = (
            config_groups[selected_index - 1],
            config_groups[selected_index],
        )

        # 更新当前选中索引
        nonlocal current_config_index
        if current_config_index == selected_index:
            current_config_index = selected_index - 1
        elif current_config_index == selected_index - 1:
            current_config_index = selected_index

        if save_config_groups(config_groups, current_config_index):
            refresh_config_list()
            # 保持选中状态
            children = config_tree.get_children()
            if selected_index - 1 < len(children):
                config_tree.selection_set(children[selected_index - 1])
                config_tree.focus(children[selected_index - 1])
        else:
            log("保存配置组失败")

    def move_config_down():
        """下移配置组"""
        selected_index = get_selected_index()
        if selected_index < 0 or selected_index >= len(config_groups) - 1:
            return

        # 交换位置
        config_groups[selected_index], config_groups[selected_index + 1] = (
            config_groups[selected_index + 1],
            config_groups[selected_index],
        )

        # 更新当前选中索引
        nonlocal current_config_index
        if current_config_index == selected_index:
            current_config_index = selected_index + 1
        elif current_config_index == selected_index + 1:
            current_config_index = selected_index

        if save_config_groups(config_groups, current_config_index):
            refresh_config_list()
            # 保持选中状态
            children = config_tree.get_children()
            if selected_index + 1 < len(children):
                config_tree.selection_set(children[selected_index + 1])
                config_tree.focus(children[selected_index + 1])
        else:
            log("保存配置组失败")

    ttk.Button(config_buttons_frame, text="修改", command=edit_config_group).pack(
        fill=tk.X, padx=5, pady=2
    )
    ttk.Button(config_buttons_frame, text="删除", command=delete_config_group).pack(
        fill=tk.X, padx=5, pady=2
    )
    ttk.Button(config_buttons_frame, text="上移", command=move_config_up).pack(
        fill=tk.X, padx=5, pady=2
    )
    ttk.Button(config_buttons_frame, text="下移", command=move_config_down).pack(
        fill=tk.X, padx=5, pady=2
    )

    # 初始化配置组列表
    refresh_config_list()

    # 全局配置框架
    global_config_frame = ttk.LabelFrame(left_content, text="全局配置")
    global_config_frame.pack(fill=tk.X, padx=5, pady=5)

    # 映射模型ID配置
    mapped_model_frame = ttk.Frame(global_config_frame)
    mapped_model_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(mapped_model_frame, text="映射模型ID:", width=12).pack(side=tk.LEFT)
    mapped_model_var = tk.StringVar()
    mapped_model_entry = ttk.Entry(mapped_model_frame, textvariable=mapped_model_var, width=25)
    mapped_model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    # MTGA鉴权key配置
    mtga_auth_frame = ttk.Frame(global_config_frame)
    mtga_auth_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(mtga_auth_frame, text="MTGA鉴权Key:", width=12).pack(side=tk.LEFT)
    mtga_auth_var = tk.StringVar()
    mtga_auth_entry = ttk.Entry(mtga_auth_frame, textvariable=mtga_auth_var, width=25, show="*")
    mtga_auth_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    # 加载并初始化全局配置
    def load_global_config_values():
        """加载并设置全局配置值到GUI"""
        mapped_model_id, mtga_auth_key = load_global_config()
        mapped_model_var.set(mapped_model_id)
        mtga_auth_var.set(mtga_auth_key)

    def save_global_config_values():
        """保存全局配置值"""
        mapped_model_id = mapped_model_var.get().strip()
        mtga_auth_key = mtga_auth_var.get().strip()

        # 验证必填字段
        if not mapped_model_id or not mtga_auth_key:
            log("错误: 映射模型ID和MTGA鉴权Key都是必填项")
            return False

        # 获取当前配置组信息
        config_groups, current_config_index = load_config_groups()

        # 保存全局配置
        if save_config_groups(config_groups, current_config_index, mapped_model_id, mtga_auth_key):
            log("全局配置已保存")
            return True
        else:
            log("保存全局配置失败")
            return False

    # 初始化全局配置值
    load_global_config_values()

    # 为全局配置添加保存按钮
    global_save_btn = ttk.Button(
        global_config_frame, text="保存全局配置", command=save_global_config_values
    )
    global_save_btn.pack(pady=5)

    # 调试模式复选框
    debug_mode_var = tk.BooleanVar(value=False)
    debug_mode_check = ttk.Checkbutton(left_content, text="开启调试模式", variable=debug_mode_var)
    debug_mode_check.pack(fill=tk.X, padx=5, pady=2)

    # 强制流模式选项
    stream_mode_frame = ttk.Frame(left_content)
    stream_mode_frame.pack(fill=tk.X, padx=5, pady=2)
    stream_mode_var = tk.BooleanVar(value=False)
    stream_mode_check = ttk.Checkbutton(
        stream_mode_frame,
        text="强制流模式:",
        variable=stream_mode_var,
        command=lambda: stream_mode_combo.config(
            state="readonly" if stream_mode_var.get() else "disabled"
        ),
    )
    stream_mode_check.pack(side=tk.LEFT)
    stream_mode_combo = ttk.Combobox(
        stream_mode_frame, values=["true", "false"], state="disabled", width=10
    )
    stream_mode_combo.pack(side=tk.LEFT, padx=(10, 0))  # 改为左对齐，减小间距
    stream_mode_combo.set("true")  # 默认值

    # 功能标签页
    notebook = ttk.Notebook(left_content)
    notebook.pack(fill=tk.BOTH, expand=True, pady=0)

    # 证书管理标签页
    cert_tab = ttk.Frame(notebook)
    notebook.add(cert_tab, text="证书管理")

    def generate_certs_task():
        """生成证书任务"""

        def task():  # noqa: PLR0912
            log("开始生成证书...")
            if generate_certificates(log_func=log, ca_common_name=CA_COMMON_NAME):
                log("✅ 证书生成完成")
            else:
                log("❌ 证书生成失败")

        thread_manager.run("cert_generate", task)

    def install_certs_task():
        """安装证书任务"""

        def task():  # noqa: PLR0912
            log("开始安装CA证书...")
            # install_ca_cert 内部会处理权限请求
            if install_ca_cert(log_func=log):
                log("✅ CA证书安装完成")
            else:
                log("❌ CA证书安装失败")

        thread_manager.run("cert_install", task)

    def clear_ca_cert_task():
        """清除系统钥匙串中的 CA 证书"""

        def task():
            clear_ca_cert(ca_common_name=CA_COMMON_NAME, log_func=log)

        thread_manager.run("cert_clear", task)

    ttk.Button(cert_tab, text="生成CA和服务器证书", command=generate_certs_task).pack(
        fill=tk.X, padx=5, pady=5
    )
    ttk.Button(cert_tab, text="安装CA证书", command=install_certs_task).pack(
        fill=tk.X, padx=5, pady=5
    )
    clear_ca_btn = ttk.Button(cert_tab, text="清除系统CA证书", command=clear_ca_cert_task)
    clear_ca_btn.pack(fill=tk.X, padx=5, pady=5)
    create_tooltip(
        clear_ca_btn,
        "macOS: 删除系统钥匙串中匹配的CA证书；"
        "Windows: 删除本地计算机/Root 中匹配的CA证书\n"
        f"Common Name: {CA_COMMON_NAME}\n"
        "需要管理员权限，建议仅在需要重置证书时使用",
        wraplength=280,
    )

    # hosts文件管理标签页
    hosts_tab = ttk.Frame(notebook)
    notebook.add(hosts_tab, text="hosts文件管理")

    def modify_hosts_task(action="add", *, block=False):
        """修改hosts文件任务"""
        nonlocal hosts_task_id

        def task():
            # 使用字典获取动作名称
            action_names = {"add": "修改", "remove": "移除", "backup": "备份", "restore": "还原"}
            action_name = action_names.get(action, action)
            log(f"开始{action_name} hosts文件...")
            ip_tuple = ("127.0.0.1", "::1")
            if modify_hosts_file(action=action, ip=ip_tuple, log_func=log):
                log(f"✅ hosts文件{action_name}完成")
            else:
                log(f"❌ hosts文件{action_name}失败")

        if block:
            thread_manager.wait(hosts_task_id)
            hosts_task_id = None
            task()
            return None

        wait_targets = [hosts_task_id] if hosts_task_id else None
        hosts_task_id = thread_manager.run(
            "hosts_manage",
            task,
            wait_for=wait_targets,
        )
        return hosts_task_id

    def open_hosts_task():
        """打开hosts文件任务"""

        def task():
            log("正在打开hosts文件...")
            if open_hosts_file(log_func=log):
                log("✅ hosts文件已打开")
            else:
                log("❌ 打开hosts文件失败")

        thread_manager.run("hosts_open", task)

    ttk.Button(hosts_tab, text="修改hosts文件", command=lambda: modify_hosts_task("add")).pack(
        fill=tk.X, padx=5, pady=5
    )

    hosts_buttons_frame = ttk.Frame(hosts_tab)
    hosts_buttons_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Button(
        hosts_buttons_frame, text="备份hosts", command=lambda: modify_hosts_task("backup")
    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    ttk.Button(
        hosts_buttons_frame, text="还原hosts", command=lambda: modify_hosts_task("restore")
    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    ttk.Button(hosts_tab, text="打开hosts文件", command=open_hosts_task).pack(
        fill=tk.X, padx=5, pady=5
    )

    # 代理服务器标签页
    proxy_tab = ttk.Frame(notebook)
    notebook.add(proxy_tab, text="代理服务器操作")

    def start_proxy_task():
        """启动代理服务器任务"""
        nonlocal proxy_start_task_id, proxy_stop_task_id

        def task():
            config = build_proxy_config()
            if not config:
                return
            stream_mode_value = config.get("stream_mode")
            if stream_mode_value is not None:
                log(f"启用强制流模式: {stream_mode_value}")
            stop_proxy_instance(reason="restart")
            start_proxy_instance(config)

        wait_targets = [proxy_stop_task_id] if proxy_stop_task_id else None
        proxy_start_task_id = thread_manager.run(
            "proxy_start",
            task,
            wait_for=wait_targets,
        )

    def stop_proxy_task():
        """停止代理服务器任务"""
        nonlocal proxy_stop_task_id, proxy_start_task_id

        def task():
            stop_proxy_and_restore(show_idle_message=True)

        wait_targets = [proxy_start_task_id] if proxy_start_task_id else None
        proxy_stop_task_id = thread_manager.run(
            "proxy_stop",
            task,
            wait_for=wait_targets,
        )

    ttk.Button(proxy_tab, text="启动代理服务器", command=start_proxy_task).pack(
        fill=tk.X, padx=5, pady=5
    )
    ttk.Button(proxy_tab, text="停止代理服务器", command=stop_proxy_task).pack(
        fill=tk.X, padx=5, pady=5
    )

    # 用户数据管理标签页（仅在单文件模式下显示）
    if is_packaged():
        data_mgmt_tab = ttk.Frame(notebook)
        notebook.add(data_mgmt_tab, text="用户数据管理")

        def open_user_data_directory():
            """打开用户数据目录"""
            try:
                user_data_dir = get_user_data_dir()
                if os.name == "nt":  # Windows
                    os.startfile(user_data_dir)
                elif sys.platform == "darwin":  # macOS
                    os.system(f'open "{user_data_dir}"')
                else:  # Linux
                    os.system(f'xdg-open "{user_data_dir}"')
                log(f"已打开用户数据目录: {user_data_dir}")
            except Exception as e:
                log(f"打开用户数据目录失败: {e}")

        def backup_user_data():
            """备份用户数据"""
            try:
                user_data_dir = get_user_data_dir()
                backup_base_dir = os.path.join(user_data_dir, "backups")

                # 创建备份基础目录
                os.makedirs(backup_base_dir, exist_ok=True)

                # 生成时间戳文件夹名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(backup_base_dir, f"backup_{timestamp}")

                # 复制除备份文件夹外的所有文件和文件夹
                items_to_backup = []
                for item in os.listdir(user_data_dir):
                    item_path = os.path.join(user_data_dir, item)
                    if item not in {"backups", ERROR_LOG_FILENAME}:  # 排除备份文件夹和日志
                        items_to_backup.append((item, item_path))

                if items_to_backup:
                    os.makedirs(backup_dir, exist_ok=True)

                    for item_name, item_path in items_to_backup:
                        dest_path = os.path.join(backup_dir, item_name)
                        if os.path.isfile(item_path):
                            shutil.copy2(item_path, dest_path)
                        elif os.path.isdir(item_path):
                            shutil.copytree(item_path, dest_path)

                    log(f"✅ 用户数据备份成功: {backup_dir}")
                    log(f"备份了 {len(items_to_backup)} 个项目")
                else:
                    log("没有需要备份的用户数据")

            except Exception as e:
                log(f"❌ 备份用户数据失败: {e}")

        def clear_user_data():
            """清除用户数据（保留备份文件夹）"""
            try:
                # 确认对话框
                result = messagebox.askyesno(
                    "确认清除",
                    "此操作将删除所有用户数据（配置文件、证书等），但保留备份文件夹。\n\n确定要继续吗？",
                    icon="warning",
                )

                if not result:
                    log("用户取消了清除操作")
                    return

                user_data_dir = get_user_data_dir()

                # 删除除备份文件夹外的所有文件和文件夹
                items_to_remove = []
                for item in os.listdir(user_data_dir):
                    if item not in {"backups", ERROR_LOG_FILENAME}:  # 保留备份文件夹与日志
                        item_path = os.path.join(user_data_dir, item)
                        items_to_remove.append((item, item_path))

                if items_to_remove:
                    for _item_name, item_path in items_to_remove:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)

                    log(f"✅ 用户数据清除成功，删除了 {len(items_to_remove)} 个项目")
                    log("备份文件夹已保留")

                    # 清除数据后复制模板文件
                    log("正在复制模板文件...")
                    copied_files = copy_template_files()
                    if copied_files:
                        log(f"✅ 已复制 {len(copied_files)} 个模板文件")
                    else:
                        log("模板文件已存在或复制完成")
                else:
                    log("没有需要清除的用户数据")

            except Exception as e:
                log(f"❌ 清除用户数据失败: {e}")

        def restore_user_data():
            """从最新备份还原用户数据"""
            try:
                user_data_dir = get_user_data_dir()
                backup_base_dir = os.path.join(user_data_dir, "backups")

                # 检查是否存在备份
                if not os.path.exists(backup_base_dir):
                    log("❌ 没有找到备份文件夹")
                    messagebox.showwarning("无备份", "没有找到备份文件夹，无法执行还原操作。")
                    return

                # 查找所有备份文件夹
                backup_pattern = os.path.join(backup_base_dir, "backup_*")
                backup_folders = glob.glob(backup_pattern)

                if not backup_folders:
                    log("❌ 没有找到任何备份")
                    messagebox.showwarning("无备份", "没有找到任何备份文件，无法执行还原操作。")
                    return

                # 找到最新的备份（按文件夹名排序，时间戳格式保证了字典序就是时间序）
                latest_backup = max(backup_folders, key=lambda x: os.path.basename(x))
                backup_name = os.path.basename(latest_backup)

                # 确认对话框
                result = messagebox.askyesno(
                    "确认还原",
                    f"将从最新备份还原数据：\n{backup_name}\n\n此操作将覆盖当前的配置文件、证书等数据。\n\n确定要继续吗？",
                    icon="question",
                )

                if not result:
                    log("用户取消了还原操作")
                    return

                # 执行还原操作
                restored_count = 0
                for item in os.listdir(latest_backup):
                    src_path = os.path.join(latest_backup, item)
                    dest_path = os.path.join(user_data_dir, item)

                    # 如果目标已存在，先删除
                    if os.path.exists(dest_path):
                        if os.path.isfile(dest_path):
                            os.remove(dest_path)
                        elif os.path.isdir(dest_path):
                            shutil.rmtree(dest_path)

                    # 复制文件或目录
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)
                    elif os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)

                    restored_count += 1

                log(f"✅ 数据还原成功，从备份 {backup_name} 还原了 {restored_count} 个项目")
                messagebox.showinfo(
                    "还原成功",
                    f"数据还原完成！\n\n从备份：{backup_name}\n还原项目：{restored_count} 个",
                )

            except Exception as e:
                log(f"❌ 还原用户数据失败: {e}")
                messagebox.showerror("还原失败", f"还原操作失败：\n{e}")

        # 按钮区域（仅包含按钮）
        button_frame = ttk.Frame(data_mgmt_tab)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        # 创建按钮并添加提示
        btn_open = ttk.Button(button_frame, text="打开目录", command=open_user_data_directory)
        btn_open.pack(fill=tk.X, pady=2)
        create_tooltip(
            btn_open,
            "使用系统文件管理器打开用户数据目录\nWindows: %APPDATA%\\MTGA\\\nmacOS/Linux: ~/.mtga/",
        )

        btn_backup = ttk.Button(button_frame, text="备份数据", command=backup_user_data)
        btn_backup.pack(fill=tk.X, pady=2)
        create_tooltip(
            btn_backup,
            "创建带时间戳的完整数据备份\n备份内容：配置文件、SSL证书、hosts备份\n备份位置：用户数据目录/backups/backup_时间戳/",
        )

        btn_restore = ttk.Button(button_frame, text="还原数据", command=restore_user_data)
        btn_restore.pack(fill=tk.X, pady=2)
        create_tooltip(
            btn_restore,
            "从最新备份恢复用户数据（覆盖现有数据）\n自动选择最新时间戳的备份进行还原\n注意：此操作会覆盖当前的配置和证书",
        )

        btn_clear = ttk.Button(button_frame, text="清除数据", command=clear_user_data)
        btn_clear.pack(fill=tk.X, pady=2)
        create_tooltip(
            btn_clear,
            "删除所有用户数据（保留历史备份）\n清除内容：配置文件、SSL证书、hosts备份\n保留内容：backups文件夹及其历史备份",
        )

    check_updates_button = None

    def show_release_notes_dialog(version_label, notes, release_url):  # noqa: PLR0915
        """显示包含 Markdown 说明的新版本弹窗。"""
        current_dark_mode = detect_macos_dark_mode()
        markdown_text = notes or "该版本暂无更新说明。"
        dialog = tk.Toplevel(window)
        dialog.title(f"发现新版本：{version_label}")
        dialog.geometry("520x420")
        dialog.minsize(480, 360)
        dialog.transient(window)
        dialog.grab_set()

        heading_font = tkfont.nametofont("TkDefaultFont").copy()
        heading_font.configure(weight="bold", size=heading_font.cget("size") + 1)

        ttk.Label(
            dialog,
            text=f"发现新版本：{version_label}",
            anchor="w",
            font=heading_font,
        ).pack(fill=tk.X, padx=12, pady=(12, 6))

        def _init_tkhtml_dir():
            base_dir = Path(resource_manager_module.get_program_resource_dir())
            pkg_dir = base_dir / "tkinterweb_tkhtml"
            candidate = pkg_dir / "tkhtml"

            if not candidate.exists():
                return None

            # DLL 搜索路径
            os.environ["PATH"] = f"{candidate}{os.pathsep}{os.environ.get('PATH', '')}"

            # 伪造 tkinterweb_tkhtml 模块，强制指向解压目录
            sys.modules.pop("tkinterweb_tkhtml", None)
            binaries = sorted([f for f in os.listdir(candidate) if "libTkhtml" in f])

            fake_mod = ModuleType("tkinterweb_tkhtml")
            fake_mod.__file__ = str(pkg_dir / "__init__.py")
            fake_mod.__path__ = [str(pkg_dir)]
            cast(Any, fake_mod).TKHTML_ROOT_DIR = str(candidate)
            cast(Any, fake_mod).ALL_TKHTML_BINARIES = binaries

            def _get_tkhtml_file(version=None, index=-1, experimental=False):
                files = sorted(cast(Any, fake_mod).ALL_TKHTML_BINARIES)
                if not files:
                    raise OSError("No Tkhtml binaries found in packaged root")
                chosen = files[index]
                exp = experimental or ("exp" in chosen)
                ver = chosen.replace("libTkhtml", "").replace("exp", "").replace(".dll", "")
                return os.path.join(cast(Any, fake_mod).TKHTML_ROOT_DIR, chosen), ver, exp

            def _load_tkhtml_file(master, file):
                master.tk.call("load", file)

            def _load_tkhtml(master):
                path, ver, exp = _get_tkhtml_file()
                _load_tkhtml_file(master, path)
                with suppress(Exception):
                    master.tk.call("package", "provide", "Tkhtml", ver or "0")

            def _get_loaded_tkhtml_version(master):
                try:
                    return master.tk.call("package", "present", "Tkhtml")
                except Exception:
                    return ""

            cast(Any, fake_mod).get_tkhtml_file = _get_tkhtml_file
            cast(Any, fake_mod).load_tkhtml_file = _load_tkhtml_file
            cast(Any, fake_mod).load_tkhtml = _load_tkhtml
            cast(Any, fake_mod).get_loaded_tkhtml_version = _get_loaded_tkhtml_version

            sys.modules["tkinterweb_tkhtml"] = fake_mod

            return candidate


        _TKHTML_DIR = _init_tkhtml_dir()
        if _TKHTML_DIR:
            with suppress(Exception):
                import tkinterweb_tkhtml as tkhtml_mod  # type: ignore  # noqa: PLC0415

                load_fn = getattr(tkhtml_mod, "load_tkhtml", None)
                if callable(load_fn):
                    load_fn(dialog)

        try:
            from tkinterweb import HtmlFrame  # noqa: PLC0415
            html_frame_cls: Any | None = HtmlFrame
            notes_widget = HtmlFrame(
                dialog,
                horizontal_scrollbar="auto",
                vertical_scrollbar="auto",
                relief="solid",
                borderwidth=1,
                messages_enabled=False,
            )
        except Exception:
            html_frame_cls = None
            notes_widget = ttk.Label(
                dialog,
                text="该版本暂无更新说明。",
                anchor="w",
                font=tkfont.nametofont("TkDefaultFont"),
            )
        notes_widget.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        if html_frame_cls and isinstance(notes_widget, html_frame_cls):
            frame_widget = cast(Any, notes_widget)
            def render_markdown(dark_mode):
                notes_html = convert_markdown_to_html(
                    markdown_text,
                    dark_mode=dark_mode,
                    font_family=default_font.cget("family"),
                    font_size=int(default_font.cget("size")),
                    font_weight=default_font.cget("weight"),
                )
                frame_widget.load_html(notes_html)

            render_markdown(current_dark_mode)

            default_link_handler = frame_widget.html.on_link_click

            def handle_link_click(url, decode=None, force=False):
                if url.startswith(("http://", "https://")):
                    webbrowser.open(url)
                else:
                    default_link_handler(url, decode=decode, force=force)

            frame_widget.html.on_link_click = handle_link_click

        theme_center = None
        theme_observer = None

        def handle_theme_change():
            if not (html_frame_cls and isinstance(notes_widget, html_frame_cls)):
                return
            nonlocal current_dark_mode
            new_mode = detect_macos_dark_mode()
            if new_mode != current_dark_mode:
                current_dark_mode = new_mode
                render_markdown(current_dark_mode)

        if sys.platform == "darwin":
            theme_center, theme_observer = register_macos_theme_observer(
                lambda: window.after(0, handle_theme_change)
            )

        def on_close():
            if theme_center and theme_observer:
                with suppress(Exception):
                    theme_center.removeObserver_(theme_observer)
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        if release_url:
            ttk.Button(
                button_frame,
                text="打开发布页",
                command=lambda: webbrowser.open(release_url),
            ).pack(side=tk.LEFT)

        ttk.Button(button_frame, text="关闭", command=on_close).pack(side=tk.RIGHT)

    update_check_task_id = None

    def check_for_updates():
        """后台检查 GitHub 最新发行版，并在主线程更新 UI。"""
        nonlocal check_updates_button, update_check_task_id
        if check_updates_button:
            check_updates_button.state(["disabled"])

        def finalize(callback):
            def _finish():
                if check_updates_button:
                    check_updates_button.state(["!disabled"])
                callback()

            window.after(0, _finish)

        def worker():
            try:
                release_info = update_checker.fetch_latest_release(
                    GITHUB_REPO,
                    timeout=10,
                    user_agent=f"{APP_DISPLAY_NAME}/{APP_VERSION}",
                )
            except requests.RequestException as exc:
                error_msg = f"检查更新失败：网络异常 {exc}"
                finalize(lambda: (messagebox.showerror("检查更新失败", error_msg), log(error_msg)))
                return
            except (ValueError, RuntimeError) as exc:
                error_msg = f"检查更新失败：{exc}"
                finalize(lambda: (messagebox.showerror("检查更新失败", error_msg), log(error_msg)))
                return

            latest_version = release_info.version_label
            if not latest_version:
                finalize(
                    lambda: (
                        messagebox.showwarning("检查更新", "未能解析最新版本号，请稍后再试。"),
                        log("检查更新失败：未解析到版本号"),
                    )
                )
                return

            if not update_checker.is_remote_version_newer(latest_version, APP_VERSION):
                finalize(
                    lambda: (
                        messagebox.showinfo("检查更新", f"当前版本 {APP_VERSION} 已是最新。"),
                        log("检查更新：当前已是最新版本"),
                    )
                )
                return

            release_notes = release_info.release_notes or "该版本暂无更新说明。"
            release_url = release_info.release_url

            def _show_new_version():
                show_release_notes_dialog(latest_version, release_notes, release_url)
                log(f"发现新版本：{latest_version}")

            finalize(_show_new_version)

        update_check_task_id = thread_manager.run("check_updates", worker)

    # 关于标签页
    style = ttk.Style()
    style.configure("About.TFrame", background="#f0f0f0")
    style.configure(
        "AboutTitle.TLabel",
        background="#f0f0f0",
        font=get_preferred_font(size=11, weight="bold"),
    )
    style.configure(
        "AboutFooter.TLabel",
        background="#f0f0f0",
        foreground="#666666",
        font=get_preferred_font(size=9),
    )
    about_tab = ttk.Frame(notebook, style="About.TFrame")
    notebook.add(about_tab, text="关于")

    version_label = ttk.Label(
        about_tab,
        text=f"{APP_DISPLAY_NAME} {APP_VERSION}",
        style="AboutTitle.TLabel",
        anchor="w",
    )
    version_label.pack(anchor="w", fill=tk.X, padx=8, pady=(8, 4))

    check_updates_button = ttk.Button(about_tab, text="检查更新", command=check_for_updates)
    check_updates_button.pack(anchor="w", padx=8, pady=(0, 8))

    about_footer = ttk.Label(
        about_tab,
        text="powered by BiFangKNT",
        style="AboutFooter.TLabel",
        anchor="center",
        justify="center",
    )
    about_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(0, 8))

    # 一键启动按钮
    def start_all_task():
        """一键启动全部服务"""
        nonlocal proxy_start_task_id, proxy_stop_task_id

        def task():
            thread_manager.wait(proxy_start_task_id)
            thread_manager.wait(proxy_stop_task_id)

            current_config = get_current_config()
            if not current_config:
                log("❌ 错误: 没有可用的配置组")
                return

            log("=== 开始一键启动全部服务 ===")

            # 1. 生成证书
            log("步骤 1/4: 生成证书")
            if not generate_certificates(log_func=log, ca_common_name=CA_COMMON_NAME):
                log("❌ 生成证书失败，无法继续")
                return

            # 2. 安装CA证书
            log("步骤 2/4: 安装CA证书")
            if not install_ca_cert(log_func=log):
                log("❌ 安装CA证书失败，无法继续")
                return

            # 3. 修改hosts文件
            log("步骤 3/4: 修改hosts文件")
            hosts_modified = modify_hosts_file(log_func=log)
            if not hosts_modified:
                log("❌ 修改hosts文件失败，无法继续")
                return

            # 4. 启动代理服务器
            log("步骤 4/4: 启动代理服务器")
            config = build_proxy_config()
            if not config:
                return
            stream_mode_value = config.get("stream_mode")
            if stream_mode_value is not None:
                log(f"启用强制流模式: {stream_mode_value}")
            stop_proxy_instance(reason="restart")
            if start_proxy_instance(
                config,
                success_message="✅ 全部服务启动成功",
                hosts_modified=hosts_modified,
            ):
                return
            log("❌ 全部服务启动失败：代理服务器未能启动")

        thread_manager.run("start_all", task)

    start_button = ttk.Button(left_frame, text="一键启动全部服务", command=start_all_task)
    start_button.grid(row=1, column=0, sticky="ew", padx=5, pady=0)

    first_layout_done = False

    def on_main_paned_configure(_event):
        nonlocal first_layout_done
        if first_layout_done:
            return
        window.update_idletasks()
        total_width = main_paned.winfo_width() or main_frame.winfo_width() or window.winfo_width()
        if total_width > 0:
            main_paned.sashpos(0, total_width // 2)
            first_layout_done = True
            main_paned.unbind("<Configure>")

    main_paned.bind("<Configure>", on_main_paned_configure)

    # 窗口关闭处理
    def on_closing():
        nonlocal proxy_start_task_id, proxy_stop_task_id, shutdown_task_id
        if shutdown_task_id:
            log("⌛ 正在退出程序，请稍候...")
            return

        log("正在退出程序，请稍候...")

        def cleanup():
            nonlocal shutdown_task_id
            try:
                thread_manager.wait(proxy_start_task_id, timeout=5)
                thread_manager.wait(proxy_stop_task_id, timeout=5)
                stopped = stop_proxy_and_restore(block_hosts_cleanup=True)
                if stopped:
                    log("代理服务器已停止，程序即将退出")
            finally:
                shutdown_task_id = None
                window.after(0, window.destroy)

        shutdown_task_id = thread_manager.run(
            "app_shutdown",
            cleanup,
            allow_parallel=False,
        )

    window.protocol("WM_DELETE_WINDOW", on_closing)

    log("MTGA GUI 已启动")
    log("请选择操作或直接使用一键启动...")

    return window


def main():
    """主函数"""
    # 不再在启动时检查管理员权限
    # 只在需要时（安装证书）请求权限

    try:
        # 创建并运行GUI
        root = create_main_window()
        if root is None:
            log_error("GUI initialization returned None; aborting.")
            sys.exit(1)
        root.mainloop()
    except Exception as e:
        # 如果 GUI 创建失败，至少尝试记录错误
        error_msg = f"GUI initialization failed: {e}"
        log_error(error_msg, exc_info=True)

        # 在 macOS 上，如果是从 Finder 启动，显示错误对话框并指明日志路径
        if sys.platform == "darwin":
            with suppress(Exception):
                messagebox.showerror(
                    "MTGA GUI Error",
                    f"{error_msg}\n\n详细日志: {ERROR_LOG_PATH}",
                )

        # 退出程序
        sys.exit(1)


if __name__ == "__main__":
    main()
