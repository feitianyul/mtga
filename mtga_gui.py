#!/usr/bin/env python3
# ruff: noqa: E402,I001

# 在最早阶段设置 UTF-8 编码环境变量 - 必须在任何导入之前
import ctypes
import io
import locale
import logging
import os
import sys
import tkinter as tk
from contextlib import suppress
from functools import partial
from pathlib import Path
from tkinter import messagebox, ttk


try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from modules.ui_helpers import (
    build_tk_error_handler,
    center_window,
    create_tooltip,
)
from modules.macos_theme import detect_macos_dark_mode
from modules.network_utils import is_port_in_use

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
    from modules.cert_checker import has_existing_ca_cert
    from modules.cert_installer import install_ca_cert
    from modules.file_operability import check_file_operability
    from modules.hosts_manager import (
        ALLOW_UNSAFE_HOSTS_FLAG,
        configure_hosts_modify_block,
        get_hosts_file_path,
        get_hosts_modify_block_report,
        is_hosts_modify_blocked,
        modify_hosts_file,
        open_hosts_file,
    )
    from modules.network_environment import check_network_environment
    from modules.proxy_server import ProxyServer
    from modules.resource_manager import (
        ResourceManager,
        copy_template_files,
        get_user_data_dir,
        is_packaged,
    )
    from modules.tkhtml_compat import create_tkinterweb_html_widget
    from modules.thread_manager import ThreadManager
    from modules import macos_privileged_helper
    from modules.actions import hosts_actions, model_tests, proxy_actions
    from modules.services.config_service import ConfigStore
    from modules.services import update_service
    from modules.ui import (
        config_group_panel,
        global_config_panel,
        layout_builders,
        runtime_options_panel,
        tab_builders,
        update_dialog,
        window_setup,
    )
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

API_KEY_VISIBLE_CHARS = 4
APP_DISPLAY_NAME = "MTGA GUI"
GITHUB_REPO = "BiFangKNT/mtga"
ERROR_LOG_FILENAME = "mtga_gui_error.log"
CA_COMMON_NAME = "MTGA_CA"


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

HOSTS_PREFLIGHT_REPORT = None
NETWORK_ENV_REPORT = None


def _startup_hosts_preflight():
    """程序启动时预检 hosts 文件，必要时启用受限 hosts 模式。"""
    logger = logging.getLogger("mtga_gui")

    def warn(message: str):
        logger.warning(message)

    hosts_file = get_hosts_file_path(log_func=print)
    report = check_file_operability(hosts_file, log_func=warn)

    if report.ok:
        return report

    if ALLOW_UNSAFE_HOSTS_FLAG in sys.argv:
        warn(
            f"⚠️ hosts 预检未通过（status={report.status.value}），但已使用启动参数 "
            f"{ALLOW_UNSAFE_HOSTS_FLAG} 覆盖；后续自动修改可能失败。"
        )
        return report

    configure_hosts_modify_block(
        True,
        reason=report.status.value,
        report=report,
    )
    warn(
        f"⚠️ hosts 预检未通过（status={report.status.value}），已启用受限 hosts 模式："
        "添加将回退为追加写入（无法保证原子性增删/去重），自动移除/还原将被禁用。"
    )
    return report


HOSTS_PREFLIGHT_REPORT = _startup_hosts_preflight()


def _startup_network_environment_preflight():
    """程序启动时检查网络环境（显式代理），用于提示 hosts 导流可能被绕过。"""
    logger = logging.getLogger("mtga_gui")

    def warn(message: str):
        logger.warning(message)

    return check_network_environment(log_func=warn, emit_logs=True)


NETWORK_ENV_REPORT = _startup_network_environment_preflight()


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
config_store = ConfigStore(CONFIG_FILE)


def create_main_window() -> tk.Tk | None:  # noqa: PLR0912, PLR0915
    """创建主窗口"""
    # 在 macOS 上，确保工作目录不是根目录
    if sys.platform == "darwin" and os.getcwd() == "/":
        with suppress(OSError):
            os.chdir(os.path.expanduser("~"))

    window = tk.Tk()

    window.report_callback_exception = build_tk_error_handler(log_error, "Tkinter 回调异常")

    window_setup_result = window_setup.setup_main_window(
        window,
        get_icon_file=resource_manager.get_icon_file,
    )
    get_preferred_font = window_setup_result.get_preferred_font
    default_font = get_preferred_font()

    layout = layout_builders.build_main_layout(
        window,
        get_preferred_font=get_preferred_font,
    )
    main_frame = layout.main_frame
    main_paned = layout.main_paned
    left_frame = layout.left_frame
    left_content = layout.left_content
    log = layout.log
    hosts_runner = hosts_actions.HostsTaskRunner(
        log_func=log,
        thread_manager=thread_manager,
        modify_hosts_file=modify_hosts_file,
        open_hosts_file=open_hosts_file,
    )

    macos_dark_mode = detect_macos_dark_mode()
    tooltip = partial(
        create_tooltip,
        font_getter=get_preferred_font,
        is_dark_mode=macos_dark_mode,
    )

    shutdown_task_id = None
    network_env_precheck_enabled = False

    def ensure_global_config_ready():
        """检查全局配置文件中的必填项。"""
        mapped_model_id, mtga_auth_key = config_store.load_global_config()
        mapped_model_id = (mapped_model_id or "").strip()
        mtga_auth_key = (mtga_auth_key or "").strip()

        missing_fields = []
        if not mapped_model_id:
            missing_fields.append("映射模型ID")
        if not mtga_auth_key:
            missing_fields.append("MTGA鉴权Key")

        if missing_fields:
            missing_display = "、".join(missing_fields)
            log(
                f"⚠️ 全局配置缺失: {missing_display} 不能为空，请在左侧“全局配置”中填写后再试。"
            )
            return False

        return True

    def build_proxy_config():
        """根据当前 UI 状态生成代理配置"""
        current_config = config_store.get_current_config()
        if not current_config:
            log("❌ 错误: 没有可用的配置组")
            return None
        config = current_config.copy()
        config["debug_mode"] = runtime_options.debug_mode_var.get()
        config["disable_ssl_strict_mode"] = runtime_options.disable_ssl_strict_var.get()
        config["stream_mode"] = (
            runtime_options.stream_mode_combo.get()
            if runtime_options.stream_mode_var.get()
            else None
        )
        return config

    def restart_proxy(
        config,
        *,
        success_message="✅ 代理服务器启动成功",
        hosts_modified=False,
    ) -> bool:
        """统一代理重启逻辑：输出 stream_mode 日志、停止旧实例并启动新实例。"""
        stream_mode_value = config.get("stream_mode")
        if stream_mode_value is not None:
            log(f"启用强制流模式: {stream_mode_value}")
        stop_proxy_instance(reason="restart")
        return start_proxy_instance(
            config,
            success_message=success_message,
            hosts_modified=hosts_modified,
        )

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
        if network_env_precheck_enabled:
            check_network_environment(log_func=log, emit_logs=True)

        if is_port_in_use(443):
            log("⚠️ 端口 443 已被其他进程占用，代理服务器未启动。请释放该端口后重试。")
            return False

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
        hosts_runner.modify_hosts("remove", block=block_hosts_cleanup)
        return stopped

    proxy_runner = proxy_actions.ProxyTaskRunner(
        log_func=log,
        thread_manager=thread_manager,
        deps=proxy_actions.ProxyTaskDependencies(
            ensure_global_config_ready=ensure_global_config_ready,
            build_proxy_config=build_proxy_config,
            get_current_config=config_store.get_current_config,
            restart_proxy=restart_proxy,
            stop_proxy_and_restore=stop_proxy_and_restore,
            has_existing_ca_cert=has_existing_ca_cert,
            generate_certificates=generate_certificates,
            install_ca_cert=install_ca_cert,
            modify_hosts_file=modify_hosts_file,
            ca_common_name=CA_COMMON_NAME,
        ),
    )

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

    if is_hosts_modify_blocked():
        report = get_hosts_modify_block_report()
        status = report.status.value if report else "unknown"
        log(
            f"⚠️ 检测到 hosts 文件写入受限（status={status}），已启用受限 hosts 模式："
            "添加将回退为追加写入（无法保证原子性增删/去重），自动移除/还原将被禁用。"
        )
        log(
            f"⚠️ 你可以点击「打开hosts文件」手动修改；或使用启动参数 "
            f"{ALLOW_UNSAFE_HOSTS_FLAG} 覆盖此检查以强制尝试原子写入（风险自负）。"
        )
    elif HOSTS_PREFLIGHT_REPORT is not None and not HOSTS_PREFLIGHT_REPORT.ok:
        log(
            f"⚠️ hosts 预检未通过（status={HOSTS_PREFLIGHT_REPORT.status.value}），"
            f"但已使用启动参数 {ALLOW_UNSAFE_HOSTS_FLAG} 覆盖；后续自动修改可能失败。"
        )

    if NETWORK_ENV_REPORT is not None and NETWORK_ENV_REPORT.explicit_proxy_detected:
        log("⚠️" * 20 + "\n检测到显式代理配置：部分应用可能优先走代理，从而绕过 hosts 导流。")
        log("建议：1. 关闭显式代理（如clash的系统代理），或改用 TUN/VPN")
        log("      2. 检查 Trae 的代理设置。\n" + "⚠️" * 20)

    config_group_panel.build_config_group_panel(
        config_group_panel.ConfigGroupPanelDeps(
            parent=left_content,
            window=window,
            log=log,
            tooltip=tooltip,
            center_window=center_window,
            get_preferred_font=get_preferred_font,
            config_store=config_store,
            thread_manager=thread_manager,
            api_key_visible_chars=API_KEY_VISIBLE_CHARS,
            test_chat_completion=model_tests.test_chat_completion,
            test_model_in_list=model_tests.test_model_in_list,
        )
    )

    global_config_panel.build_global_config_panel(
        global_config_panel.GlobalConfigPanelDeps(
            parent=left_content,
            log=log,
            tooltip=tooltip,
            config_store=config_store,
        )
    )

    def on_debug_mode_toggle():
        nonlocal network_env_precheck_enabled
        enabled = bool(runtime_options.debug_mode_var.get())
        network_env_precheck_enabled = enabled

    runtime_options = runtime_options_panel.build_runtime_options_panel(
        runtime_options_panel.RuntimeOptionsPanelDeps(
            parent=left_content,
            tooltip=tooltip,
            on_debug_mode_toggle=on_debug_mode_toggle,
        )
    )

    # 功能标签页
    notebook = ttk.Notebook(left_content)
    notebook.pack(fill=tk.BOTH, expand=True, pady=0)
    tab_builders.build_cert_tab(
        tab_builders.CertTabDeps(
            notebook=notebook,
            window=window,
            log=log,
            tooltip=tooltip,
            center_window=center_window,
            ca_common_name=CA_COMMON_NAME,
            thread_manager=thread_manager,
        )
    )
    tab_builders.build_hosts_tab(
        tab_builders.HostsTabDeps(
            notebook=notebook,
            hosts_runner=hosts_runner,
        )
    )
    tab_builders.build_proxy_tab(
        tab_builders.ProxyTabDeps(
            notebook=notebook,
            proxy_runner=proxy_runner,
            log=log,
            thread_manager=thread_manager,
        )
    )

    if is_packaged():
        tab_builders.build_data_management_tab(
            tab_builders.DataManagementTabDeps(
                notebook=notebook,
                log=log,
                tooltip=tooltip,
                get_user_data_dir=get_user_data_dir,
                copy_template_files=copy_template_files,
                error_log_filename=ERROR_LOG_FILENAME,
            )
        )

    check_updates_button = None

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
            result = update_service.check_for_updates(
                repo=GITHUB_REPO,
                app_version=APP_VERSION,
                timeout=10,
                user_agent=f"{APP_DISPLAY_NAME}/{APP_VERSION}",
                font=update_service.UpdateFontOptions(
                    family=default_font.cget("family"),
                    size=int(default_font.cget("size")),
                    weight=default_font.cget("weight"),
                ),
            )

            if result.status == "network_error":
                error_msg = result.error_message or "检查更新失败：网络异常"
                finalize(lambda: (messagebox.showerror("检查更新失败", error_msg), log(error_msg)))
                return
            if result.status == "remote_error":
                error_msg = result.error_message or "检查更新失败"
                finalize(lambda: (messagebox.showerror("检查更新失败", error_msg), log(error_msg)))
                return
            if result.status == "no_version":
                finalize(
                    lambda: (
                        messagebox.showwarning("检查更新", "未能解析最新版本号，请稍后再试。"),
                        log("检查更新失败：未解析到版本号"),
                    )
                )
                return
            if result.status == "up_to_date":
                finalize(
                    lambda: (
                        messagebox.showinfo("检查更新", f"当前版本 {APP_VERSION} 已是最新。"),
                        log("检查更新：当前已是最新版本"),
                    )
                )
                return

            latest_version = result.latest_version or "未知版本"
            release_notes = result.release_notes or "该版本暂无更新说明。"
            release_url = result.release_url or ""

            def _show_new_version():
                update_dialog.show_release_notes_dialog(
                    update_dialog.UpdateDialogDeps(
                        window=window,
                        notes_html=release_notes,
                        release_url=release_url,
                        version_label=latest_version,
                        create_tkinterweb_html_widget=create_tkinterweb_html_widget,
                        program_resource_dir=resource_manager_module.get_program_resource_dir(),
                        log=log,
                    )
                )
                log(f"发现新版本：{latest_version}")

            finalize(_show_new_version)

        update_check_task_id = thread_manager.run("check_updates", worker)

    _, check_updates_button = tab_builders.build_about_tab(
        tab_builders.AboutTabDeps(
            notebook=notebook,
            app_display_name=APP_DISPLAY_NAME,
            app_version=APP_VERSION,
            get_preferred_font=get_preferred_font,
            on_check_updates=check_for_updates,
        )
    )

    # 一键启动按钮
    def start_all_task():
        """一键启动全部服务"""
        proxy_runner.start_all()

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

    layout_builders.init_paned_layout(main_paned, main_frame, window)

    # 窗口关闭处理
    def on_closing():
        nonlocal shutdown_task_id
        if shutdown_task_id:
            log("⌛ 正在退出程序，请稍候...")
            return

        log("正在退出程序，请稍候...")

        def cleanup():
            nonlocal shutdown_task_id
            try:
                thread_manager.wait(proxy_runner.proxy_start_task_id, timeout=5)
                thread_manager.wait(proxy_runner.proxy_stop_task_id, timeout=5)
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
    # GUI 启动后自动检查一次更新
    window.after(200, check_for_updates)

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
