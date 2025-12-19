from __future__ import annotations

from collections.abc import Callable

from modules.cert_cleaner import clear_ca_cert
from modules.cert_generator import generate_certificates
from modules.cert_installer import install_ca_cert


def run_generate_certificates(
    *,
    ca_common_name: str,
    log_func: Callable[[str], None],
    thread_manager,
) -> None:
    def task():
        log_func("开始生成证书...")
        if generate_certificates(log_func=log_func, ca_common_name=ca_common_name):
            log_func("✅ 证书生成完成")
        else:
            log_func("❌ 证书生成失败")

    thread_manager.run("cert_generate", task)


def run_install_ca_cert(
    *,
    log_func: Callable[[str], None],
    thread_manager,
) -> None:
    def task():
        log_func("开始安装CA证书...")
        if install_ca_cert(log_func=log_func):
            log_func("✅ CA证书安装完成")
        else:
            log_func("❌ CA证书安装失败")

    thread_manager.run("cert_install", task)


def run_clear_ca_cert(
    *,
    ca_common_name: str,
    log_func: Callable[[str], None],
    thread_manager,
) -> None:
    def task():
        clear_ca_cert(ca_common_name=ca_common_name, log_func=log_func)

    thread_manager.run("cert_clear", task)
