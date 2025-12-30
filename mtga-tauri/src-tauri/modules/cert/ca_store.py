from __future__ import annotations

import shlex

from modules.cert.cert_utils import filter_certs_by_name, log_lines, parse_certutil_store
from modules.platform.macos_privileged_helper import get_mac_privileged_session
from modules.platform.system import is_macos, is_posix, is_windows
from modules.runtime.operation_result import OperationResult
from modules.runtime.process_utils import run_command

MAC_KEYCHAIN_ITEM_NOT_FOUND = 44


def check_ca_cert(ca_common_name: str, log_func=print) -> OperationResult:
    """检查系统信任存储中是否存在指定 CA。"""
    if is_macos():
        return _check_ca_on_macos(ca_common_name, log_func=log_func)
    if is_windows():
        return _check_ca_on_windows(ca_common_name, log_func=log_func)

    log_func("?? 当前平台不支持自动检查系统CA证书")
    return OperationResult.failure(
        "当前平台不支持自动检查系统CA证书",
        exists=False,
    )


def install_ca_cert_file(ca_cert_file: str, log_func=print) -> OperationResult:
    """将指定 CA 证书安装到系统信任存储。"""
    if not ca_cert_file:
        return OperationResult.failure("证书路径为空")

    if is_windows():
        return _install_ca_on_windows(ca_cert_file, log_func=log_func)
    if is_macos():
        return _install_ca_on_macos(ca_cert_file, log_func=log_func)
    if is_posix():
        return _install_ca_on_linux(ca_cert_file, log_func=log_func)

    log_func("错误: 不支持的操作系统")
    return OperationResult.failure("不支持的操作系统")


def clear_ca_cert_store(ca_common_name: str, log_func=print) -> OperationResult:
    """从系统信任存储中清除指定 CA。"""
    if is_macos():
        return _clear_ca_on_macos(ca_common_name, log_func=log_func)
    if is_windows():
        return _clear_ca_on_windows(ca_common_name, log_func=log_func)

    log_func("⚠️ 当前平台不支持自动清除CA证书")
    return OperationResult.failure("当前平台不支持自动清除CA证书")


def _check_ca_on_windows(ca_common_name: str, log_func=print) -> OperationResult:
    log_func("检查 Windows 受信任根证书存储中的 CA 证书...")
    list_cmd = ["cmd", "/d", "/s", "/c", "certutil -store Root"]
    return_code, stdout, stderr = run_command(list_cmd)

    log_lines(stderr, log_func)
    if return_code != 0:
        log_func(f"? 读取证书存储失败 (返回码: {return_code})")
        return OperationResult.failure(
            "读取证书存储失败",
            exists=False,
            returncode=return_code,
        )

    entries = parse_certutil_store(stdout)
    targets = filter_certs_by_name(entries, ca_common_name)
    if targets:
        log_func(f"检测到 {len(targets)} 个匹配的 CA 证书")
        return OperationResult.success(
            exists=True,
            match_count=len(targets),
        )

    log_func("未找到匹配的 CA 证书")
    return OperationResult.success(exists=False, match_count=0)


def _check_ca_on_macos(ca_common_name: str, log_func=print) -> OperationResult:
    log_func("检查 macOS 系统钥匙串中的 CA 证书...")
    cmd = [
        "security",
        "find-certificate",
        "-a",
        "-c",
        ca_common_name,
        "-Z",
        "/Library/Keychains/System.keychain",
    ]
    return_code, stdout, stderr = run_command(cmd)

    if (
        return_code == MAC_KEYCHAIN_ITEM_NOT_FOUND
        and stderr
        and "could not be found" in stderr.lower()
    ):
        log_func("未在系统钥匙串中找到匹配的 CA 证书")
        return OperationResult.success(exists=False)

    if return_code not in (0, MAC_KEYCHAIN_ITEM_NOT_FOUND):
        log_func(f"? 检查系统钥匙串失败 (返回码: {return_code})")
        log_lines(stderr, log_func)
        return OperationResult.failure(
            "检查系统钥匙串失败",
            exists=False,
            returncode=return_code,
        )

    if stdout.strip():
        log_func("检测到系统钥匙串中存在匹配的 CA 证书")
        return OperationResult.success(exists=True)

    log_func("未在系统钥匙串中找到匹配的 CA 证书")
    return OperationResult.success(exists=False)


def _install_ca_on_windows(ca_cert_file: str, log_func=print) -> OperationResult:
    log_func("正在 Windows 系统中安装 CA 证书...")
    cmd = f'certutil -addstore -f "ROOT" "{ca_cert_file}"'
    log_func(f"执行命令: {cmd}")
    return_code, stdout, stderr = run_command(cmd, shell=True)

    log_lines(stdout, log_func)
    log_lines(stderr, log_func)

    if return_code == 0:
        log_func("CA 证书安装成功！")
        return OperationResult.success()

    log_func(f"证书安装失败，返回码: {return_code}")
    return OperationResult.failure(
        "证书安装失败",
        returncode=return_code,
        stderr=stderr,
        stdout=stdout,
    )


def _install_ca_on_macos(ca_cert_file: str, log_func=print) -> OperationResult:
    log_func("正在 macOS 系统中安装 CA 证书...")
    session = get_mac_privileged_session(log_func=log_func)
    if not session:
        log_func("❌ 无法获取管理员权限，证书未安装")
        return OperationResult.failure("无法获取管理员权限")

    log_func("请求以管理员权限将证书安装到系统钥匙串并设为信任...")
    success, data = session.install_trusted_cert(
        ca_cert_file,
        keychain="/Library/Keychains/System.keychain",
        log_func=log_func,
    )
    stdout = data.get("stdout") if isinstance(data, dict) else None
    stderr = data.get("stderr") if isinstance(data, dict) else None
    log_lines(stdout, log_func)
    log_lines(stderr, log_func)

    if success:
        log_func("✅ CA 证书已添加到系统钥匙串并设为信任")
        return OperationResult.success()

    return_code = data.get("returncode") if isinstance(data, dict) else None
    error_msg = ""
    if isinstance(data, dict):
        error_msg = stderr or data.get("error") or ""
    log_func(
        f"❌ 证书安装失败 (返回码: {return_code if return_code is not None else '未知'})"
    )
    if error_msg:
        log_func(f"错误信息: {error_msg}")
    return OperationResult.failure(
        "证书安装失败",
        returncode=return_code,
        stderr=stderr,
        stdout=stdout,
    )


def _install_ca_on_linux(ca_cert_file: str, log_func=print) -> OperationResult:
    log_func("正在 Linux 系统中安装 CA 证书...")
    cmd = f'sudo cp "{ca_cert_file}" /usr/local/share/ca-certificates/'
    log_func(f"执行命令: {cmd}")
    return_code, stdout, stderr = run_command(cmd, shell=True)

    log_lines(stdout, log_func)
    log_lines(stderr, log_func)

    if return_code != 0:
        log_func(f"复制证书失败，返回码: {return_code}")
        return OperationResult.failure(
            "复制证书失败",
            returncode=return_code,
            stderr=stderr,
            stdout=stdout,
        )

    cmd = "sudo update-ca-certificates"
    log_func(f"执行命令: {cmd}")
    return_code, stdout, stderr = run_command(cmd, shell=True)

    log_lines(stdout, log_func)
    log_lines(stderr, log_func)

    if return_code == 0:
        log_func("CA 证书安装成功！")
        return OperationResult.success()

    log_func(f"更新证书失败，返回码: {return_code}")
    return OperationResult.failure(
        "更新证书失败",
        returncode=return_code,
        stderr=stderr,
        stdout=stdout,
    )


def _clear_ca_on_windows(ca_common_name: str, log_func=print) -> OperationResult:
    log_func("开始清除 Windows 受信任根中的CA证书...")
    list_cmd = ["cmd", "/d", "/s", "/c", "certutil -store Root"]
    return_code, stdout, stderr = run_command(list_cmd)

    log_lines(stderr, log_func)
    if return_code != 0:
        log_func(f"❌ 读取证书存储失败 (返回码: {return_code})")
        return OperationResult.failure(
            "读取证书存储失败",
            returncode=return_code,
        )

    entries = parse_certutil_store(stdout)
    targets = filter_certs_by_name(entries, ca_common_name)
    if not targets:
        log_func(f"未找到匹配证书: {ca_common_name}")
        return OperationResult.success()

    log_func(f"找到 {len(targets)} 个匹配证书，准备删除...")
    any_failed = False

    for cert in targets:
        thumbprint = cert.get("thumbprint")
        subject = cert.get("subject", "")
        if not thumbprint:
            any_failed = True
            log_func(f"⚠️ 跳过缺少哈希的证书: {subject or '[未知证书]'}")
            continue

        log_func(f"Deleting from Root store: {thumbprint}")
        if subject:
            log_func(f"Subject: {subject}")

        delete_cmd = ["cmd", "/d", "/s", "/c", f"certutil -delstore Root {thumbprint}"]
        rc, del_stdout, del_stderr = run_command(delete_cmd)
        log_lines(del_stdout, log_func)
        log_lines(del_stderr, log_func)
        if rc != 0:
            any_failed = True
            log_func(f"❌ 删除失败 (返回码: {rc})")

    if any_failed:
        log_func("❌ CA证书清除失败 (部分证书未能删除)")
        return OperationResult.failure("部分证书未能删除")

    log_func("✅ CA证书清除完成")
    return OperationResult.success()


def _clear_ca_on_macos(ca_common_name: str, log_func=print) -> OperationResult:
    session = get_mac_privileged_session(log_func=log_func)
    if not session:
        log_func("❌ 无法获取管理员权限，无法清除CA证书")
        return OperationResult.failure("无法获取管理员权限")

    log_func("开始清除系统钥匙串中的CA证书...")
    command = (
        f"security find-certificate -a -c {shlex.quote(ca_common_name)} "
        "-Z /Library/Keychains/System.keychain "
        "| awk '/SHA-1 hash:/ {print $3}' "
        "| while read -r hash; do "
        'echo \"Deleting from System.keychain: $hash\"; '
        'sudo security delete-certificate -Z \"$hash\" /Library/Keychains/System.keychain; '
        "done"
    )
    success, data = session.run_command(["bash", "-lc", command], log_func=log_func)
    if not isinstance(data, dict):
        data = {}
    log_lines(data.get("stdout"), log_func)
    log_lines(data.get("stderr"), log_func)
    if success:
        log_func("✅ CA证书清除完成")
        return OperationResult.success()

    return_code = data.get("returncode")
    rc_text = return_code if return_code is not None else "未知"
    log_func(f"❌ CA证书清除失败 (返回码: {rc_text})")
    return OperationResult.failure(
        "CA证书清除失败",
        returncode=return_code,
    )


__all__ = ["check_ca_cert", "clear_ca_cert_store", "install_ca_cert_file"]
