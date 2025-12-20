from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from modules.hosts_manager import (
    ALLOW_UNSAFE_HOSTS_FLAG,
    get_hosts_modify_block_report,
    is_hosts_modify_blocked,
)


@dataclass(frozen=True)
class StartupReport:
    env_ok: bool
    env_message: str


def emit_startup_logs(
    *,
    log: Callable[[str], None],
    check_environment: Callable[[], tuple[bool, str]],
    is_packaged: Callable[[], bool],
    hosts_preflight_report,
    network_env_report,
) -> StartupReport:
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
    elif hosts_preflight_report is not None and not hosts_preflight_report.ok:
        log(
            f"⚠️ hosts 预检未通过（status={hosts_preflight_report.status.value}），"
            f"但已使用启动参数 {ALLOW_UNSAFE_HOSTS_FLAG} 覆盖；后续自动修改可能失败。"
        )

    if network_env_report is not None and network_env_report.explicit_proxy_detected:
        log("⚠️" * 20 + "\n检测到显式代理配置：部分应用可能优先走代理，从而绕过 hosts 导流。")
        log("建议：1. 关闭显式代理（如clash的系统代理），或改用 TUN/VPN")
        log("      2. 检查 Trae 的代理设置。\n" + "⚠️" * 20)

    return StartupReport(env_ok=env_ok, env_message=env_msg)
