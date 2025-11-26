"""
证书安装模块
处理 CA 证书的系统安装和信任设置
"""

import os
import subprocess
import sys

from .process_utils import run_command
from .resource_manager import ResourceManager

PROCESS_PARTS_MIN = 3


def install_ca_cert_windows(ca_cert_file, log_func=print):
    """
    在 Windows 系统中安装 CA 证书

    参数:
        ca_cert_file: CA 证书文件路径
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("正在 Windows 系统中安装 CA 证书...")

    try:
        cmd = f'certutil -addstore -f "ROOT" "{ca_cert_file}"'
        log_func(f"执行命令: {cmd}")
        return_code, stdout, stderr = run_command(cmd, shell=True)

        if stdout:
            log_func(stdout)
        if stderr:
            log_func(stderr)

        if return_code == 0:
            log_func("CA 证书安装成功！")
            return True
        else:
            log_func(f"证书安装失败，返回码: {return_code}")
            return False

    except Exception as e:
        log_func(f"安装 CA 证书时发生错误: {e}")
        return False


def install_ca_cert_macos(ca_cert_file, log_func=print):  # noqa: PLR0912, PLR0915
    """
    在 macOS 系统中安装 CA 证书

    参数:
        ca_cert_file: CA 证书文件路径
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("正在 macOS 系统中安装 CA 证书...")

    # 检查是否在 AppleScript 环境下运行
    is_applescript_env = False

    try:
        # 检查环境变量
        if os.environ.get("_") and "osascript" in os.environ.get("_", ""):
            is_applescript_env = True
            log_func("通过环境变量检测到 AppleScript 环境")

        # 检查进程树中是否有 osascript
        if not is_applescript_env:
            try:
                current_pid = os.getpid()
                ps_output = subprocess.check_output(["ps", "-eo", "pid,ppid,comm"], text=True)
                log_func(f"当前进程 ID: {current_pid}")

                processes = {}
                for line in ps_output.strip().split("\\n")[1:]:
                    parts = line.strip().split(None, 2)
                    if len(parts) >= PROCESS_PARTS_MIN:
                        pid, ppid, comm = parts[0], parts[1], parts[2]
                        processes[pid] = {"ppid": ppid, "comm": comm}

                pid = str(current_pid)
                process_chain = []
                while pid in processes and pid != "1":
                    process_info = processes[pid]
                    process_chain.append(f"{pid}:{process_info['comm']}")
                    if "osascript" in processes[pid]["comm"]:
                        is_applescript_env = True
                        log_func(f"通过进程树检测到 AppleScript 环境: {' -> '.join(process_chain)}")
                        break
                    pid = processes[pid]["ppid"]

            except Exception as e:
                log_func(f"进程树检测失败: {str(e)}")

        # 检查是否通过 sudo 运行且没有 TTY
        if not is_applescript_env:
            try:
                # 仅在 Unix/Linux/macOS 系统上检查 geteuid
                if sys.platform != "win32" and hasattr(os, "geteuid"):
                    if os.geteuid() == 0 and not os.isatty(0):
                        is_applescript_env = True
                        log_func("通过 sudo+无TTY 检测到 AppleScript 环境")
            except Exception as e:
                log_func(f"sudo+TTY 检测失败: {str(e)}")

        log_func(f"AppleScript 环境检测结果: {is_applescript_env}")

        if is_applescript_env:
            # 在 AppleScript 环境下，尝试自动安装并设置信任
            log_func("检测到 AppleScript 环境，尝试自动安装并设置证书信任...")

            try:
                # 使用 security 命令添加证书到登录钥匙串
                cmd = (
                    "security add-certificates "
                    "-k ~/Library/Keychains/login.keychain-db "
                    f'"{ca_cert_file}"'
                )
                log_func(f"执行命令: {cmd}")
                return_code, stdout, stderr = run_command(cmd, shell=True)

                if return_code == 0:
                    log_func("✅ 证书已成功添加到登录钥匙串")
                elif "already in" in stderr:
                    log_func("✅ 证书已存在于钥匙串中，需要手动设置信任级别")
                else:
                    log_func(f"添加证书失败 (返回码: {return_code})")
                    if stderr:
                        log_func(f"错误信息: {stderr}")
                    raise Exception("添加证书失败，转为手动安装")

                # 提供手动设置信任的指导
                log_func("")
                log_func("=== 设置证书信任（重要步骤）===")
                log_func("1. 打开钥匙串访问应用")
                log_func("2. 选择'登录'钥匙串")
                log_func("3. 找到证书（名为'MyLocalCA'）")
                log_func("4. 双击证书打开详情窗口")
                log_func("5. 展开'信任'设置")
                log_func("6. 将'使用此证书时'设置为'始终信任'")
                log_func("7. 输入密码确认更改")
                log_func("✅ 完成后证书将被完全信任")

                # 尝试打开钥匙串访问应用
                try:
                    subprocess.run(["open", "-a", "Keychain Access"], check=False)
                    log_func("已尝试自动打开钥匙串访问应用")
                except Exception:
                    log_func("无法自动打开钥匙串访问应用，请手动打开")

                return True

            except Exception as e:
                log_func(f"自动安装证书失败: {str(e)}")
                log_func("转为手动安装模式...")

                # 提供详细的手动安装指导
                log_func("")
                log_func("=== CA证书手动安装步骤 ===")
                log_func(f"1. 证书文件位置: {ca_cert_file}")
                log_func("2. 双击证书文件，系统会自动打开钥匙串访问应用")
                log_func("3. 证书会被添加到'登录'钥匙串中（此时显示为不被信任）")
                log_func("")
                log_func("=== 设置证书信任（重要步骤）===")
                log_func("4. 在钥匙串访问中，确保选择了'登录'钥匙串")
                log_func("5. 在'种类'中选择'证书'")
                log_func("6. 找到刚添加的证书（通常名为'MyLocalCA'或类似名称）")
                log_func("7. 双击该证书打开详情窗口")
                log_func("8. 点击'信任'旁边的三角形展开信任设置")
                log_func("9. 在'使用此证书时'下拉菜单中选择'始终信任'")
                log_func("10. 关闭证书窗口，系统会提示输入密码")
                log_func("11. 输入您的macOS登录密码确认更改")
                log_func("")
                log_func("✅ 完成后，证书图标会显示蓝色加号，表示已被信任")
                log_func("✅ 此时HTTPS代理将能够正常工作，浏览器不会显示安全警告")

                # 尝试使用 open 命令打开证书文件
                try:
                    subprocess.run(["open", ca_cert_file], check=False)
                    log_func(f"已尝试自动打开证书文件: {ca_cert_file}")
                except Exception:
                    log_func("无法自动打开证书文件，请手动打开")

                return True
        else:
            # 在 GUI 环境下，直接添加到登录钥匙串
            log_func("将证书添加到登录钥匙串...")

            try:
                # 添加到登录钥匙串（不需要管理员权限）
                cmd = ["security", "add-certificates", "-k", "login.keychain", ca_cert_file]
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)

                if result.returncode == 0:
                    log_func("✅ 证书已成功添加到登录钥匙串")
                elif "already exists" in result.stderr:
                    log_func("证书已存在于登录钥匙串中")
                else:
                    log_func(f"添加失败: {result.stderr}")
                    return False

                # 打开钥匙串访问应用
                subprocess.run(
                    ["open", "/System/Applications/Utilities/Keychain Access.app"], check=False
                )

                # 尝试打开证书文件（会自动定位到证书）
                subprocess.run(["open", ca_cert_file], check=False)

                log_func("")
                log_func("=== 请手动设置证书信任（重要步骤）===")
                log_func("1. 钥匙串访问已打开")
                log_func("2. 在左侧选择'登录'钥匙串")
                log_func("3. 在证书列表中找到刚添加的证书")
                log_func("4. 双击证书打开详情")
                log_func("5. 展开'信任'部分")
                log_func("6. 将'使用此证书时'设为'始终信任'")
                log_func("7. 关闭窗口并输入密码确认")
                log_func("")
                log_func("完成后，证书将被系统信任，HTTPS代理可正常工作")

                return True

            except Exception as e:
                log_func(f"证书安装操作失败: {e}")
                return False

    except Exception as e:
        log_func(f"安装 CA 证书时发生错误: {e}")
        return False


def install_ca_cert_linux(ca_cert_file, log_func=print):
    """
    在 Linux 系统中安装 CA 证书

    参数:
        ca_cert_file: CA 证书文件路径
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("正在 Linux 系统中安装 CA 证书...")

    try:
        # 复制证书到系统目录
        cmd = f'sudo cp "{ca_cert_file}" /usr/local/share/ca-certificates/'
        log_func(f"执行命令: {cmd}")
        return_code, stdout, stderr = run_command(cmd, shell=True)

        if stdout:
            log_func(stdout)
        if stderr:
            log_func(stderr)

        if return_code != 0:
            log_func(f"复制证书失败，返回码: {return_code}")
            return False

        # 更新 CA 证书
        cmd = "sudo update-ca-certificates"
        log_func(f"执行命令: {cmd}")
        return_code, stdout, stderr = run_command(cmd, shell=True)

        if stdout:
            log_func(stdout)
        if stderr:
            log_func(stderr)

        if return_code == 0:
            log_func("CA 证书安装成功！")
            return True
        else:
            log_func(f"更新证书失败，返回码: {return_code}")
            return False

    except Exception as e:
        log_func(f"安装 CA 证书时发生错误: {e}")
        return False


def install_ca_cert(log_func=print):
    """
    根据操作系统安装 CA 证书

    参数:
        log_func: 日志输出函数

    返回:
        成功返回 True，失败返回 False
    """
    log_func("开始安装 CA 证书...")

    # 初始化资源管理器
    resource_manager = ResourceManager()

    # 检查可能的 CA 证书文件名
    possible_cert_files = [
        resource_manager.get_ca_cert_file(),
        os.path.join(resource_manager.ca_path, "rootCA.crt"),
        os.path.join(resource_manager.ca_path, "ca.cer"),
        os.path.join(resource_manager.ca_path, "rootCA.cer"),
    ]

    ca_cert_file = None
    for cert_file in possible_cert_files:
        if os.path.exists(cert_file):
            ca_cert_file = cert_file
            log_func(f"找到 CA 证书文件: {ca_cert_file}")
            break

    if ca_cert_file is None:
        log_func(f"错误: 未找到 CA 证书文件，已检查以下路径: {', '.join(possible_cert_files)}")
        return False

    try:
        if os.name == "nt":  # Windows
            return install_ca_cert_windows(ca_cert_file, log_func)
        elif sys.platform == "darwin":  # macOS
            return install_ca_cert_macos(ca_cert_file, log_func)
        elif os.name == "posix":  # Linux
            return install_ca_cert_linux(ca_cert_file, log_func)
        else:
            log_func("错误: 不支持的操作系统")
            return False

    except Exception as e:
        log_func(f"安装 CA 证书失败: {e}")
        return False
