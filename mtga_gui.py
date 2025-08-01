#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTGA GUI - 图形界面工具
集成证书生成和代理服务器功能，自动获取管理员权限

功能:
1. 一键生成证书
2. 导入证书到系统信任存储
3. 修改hosts文件
4. 启动代理服务器
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
import re # 确保导入 re 模块
from tkinter import ttk, scrolledtext
import ctypes
import shutil
import io
import contextlib
from pathlib import Path
import json
import time
from queue import Queue, Empty
import yaml # 添加yaml导入

# 获取当前脚本的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# OpenSSL 路径
OPENSSL_DIR = os.path.join(SCRIPT_DIR, "openssl")
OPENSSL_EXE = os.path.join(OPENSSL_DIR, "openssl.exe")
# 虚拟环境路径
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")
# 根据操作系统选择正确的Python可执行文件路径
if os.name == 'nt':  # Windows
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
else:  # Unix/Linux/macOS
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")

# 其他脚本路径

DOMAIN = "api.openai.com"
# DOMAIN = "generativelanguage.googleapis.com"

GENERATE_CERTS_PY = os.path.join(SCRIPT_DIR, "generate_certs.py")
# GENERATE_CERTS_PY = os.path.join(SCRIPT_DIR, "generate_google_certs.py")

DOMAIN_CNF = f"{DOMAIN}.crt"
DOMAIN_KEY = f"{DOMAIN}.key"
HOSTS_CONTENT = f"127.0.0.1 {DOMAIN}"


TRAE_PROXY_PY = os.path.join(SCRIPT_DIR, "trae_proxy.py")
# hosts文件路径
HOSTS_FILE = r"C:\Windows\System32\drivers\etc\hosts" if os.name == 'nt' else "/etc/hosts"
# 证书目录
CA_DIR = os.path.join(SCRIPT_DIR, "ca")

# 定义配置文件路径
CONFIG_FILE = os.path.join(SCRIPT_DIR, "mtga_config.yaml") # 修改文件名后缀

# 全局变量，用于存储代理服务器进程
proxy_process = None

# 检查是否具有管理员权限
def is_admin():
    try:
        if os.name == 'nt':  # Windows
            return ctypes.windll.shell32.IsUserAnAdmin()
        elif os.name == 'posix':  # Unix/Linux/macOS
            return os.geteuid() == 0
        else:
            return False
    except:
        return False

# 请求管理员权限并重启脚本
def run_as_admin():
    if not is_admin():
        if os.name == 'nt':  # Windows
            # 使用 sys.executable 获取当前 Python 解释器的路径
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        elif os.name == 'posix':  # Unix/Linux/macOS
            # 在 Unix/Linux/macOS 上，提示用户使用 sudo 运行
            print("此程序需要管理员权限才能运行。")
            print(f"请使用以下命令重新运行：")
            print(f"sudo {sys.executable} {' '.join(sys.argv)}")
            sys.exit(1)
        else:
            print("不支持的操作系统")
            sys.exit(1)

# 捕获输出的上下文管理器
@contextlib.contextmanager
def capture_output():
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    new_stdout = io.StringIO()
    new_stderr = io.StringIO()
    sys.stdout = new_stdout
    sys.stderr = new_stderr
    try:
        yield new_stdout, new_stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

# 运行命令并返回输出
def run_command(cmd, shell=False):
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            shell=shell
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, "", str(e)

# 检查环境
def check_environment():
    # 检查OpenSSL
    if not os.path.exists(OPENSSL_EXE):
        return False, f"OpenSSL不存在: {OPENSSL_EXE}"
    
    # 检查虚拟环境
    if not os.path.exists(VENV_PYTHON):
        return False, f"虚拟环境不存在: {VENV_PYTHON}"
    
    # 检查脚本文件
    if not os.path.exists(GENERATE_CERTS_PY):
        return False, f"证书生成脚本不存在: {GENERATE_CERTS_PY}"
    
    if not os.path.exists(TRAE_PROXY_PY):
        return False, f"代理服务器脚本不存在: {TRAE_PROXY_PY}"
    
    return True, "环境检查通过"

# 生成证书
def generate_certificates(log_func=print):
    log_func("开始生成证书...")
    
    # 设置环境变量，确保使用正确的OpenSSL
    env = os.environ.copy()
    env["PATH"] = OPENSSL_DIR + os.pathsep + env["PATH"]
    
    # 运行证书生成脚本
    if os.name == 'nt':  # Windows
        cmd = [VENV_PYTHON, GENERATE_CERTS_PY]
    elif os.name == 'posix':  # Unix/Linux/macOS
        cmd = ['/bin/zsh', '-c', f'source {VENV_DIR}/bin/activate && python {GENERATE_CERTS_PY}']
    else:  # Linux
        print("不支持的操作系统")
    log_func(f"执行命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )
        
        # 使用communicate获取输出
        stdout, _ = process.communicate()
        
        # 输出结果
        for line in stdout.splitlines():
            log_func(line)
        
        return_code = process.returncode
        
        if return_code == 0:
            log_func("证书生成成功！")
            return True
        else:
            log_func(f"证书生成失败，返回码: {return_code}")
            return False
    except Exception as e:
        log_func(f"执行证书生成脚本时出错: {e}")
        return False

# 导入证书到系统信任存储
def import_certificate(log_func=print):
    log_func("开始导入CA证书到系统信任存储...")
    
    ca_cert_path = os.path.join(CA_DIR, "ca.crt")
    if not os.path.exists(ca_cert_path):
        log_func(f"错误: CA证书不存在: {ca_cert_path}")
        return False
    
    # 使用certutil导入证书
    cmd = ["certutil", "-addstore", "ROOT", ca_cert_path]
    log_func(f"执行命令: {' '.join(cmd)}")
    
    return_code, stdout, stderr = run_command(cmd)
    log_func(stdout)
    if stderr:
        log_func(stderr)
    
    if return_code == 0:
        log_func("CA证书导入成功！")
        return True
    else:
        log_func(f"CA证书导入失败，返回码: {return_code}")
        return False

# 安装CA证书
def install_ca_cert(log_func=print):
    """
    安装CA证书
    
    参数:
    - log_func: 日志记录函数
    
    返回值:
    - 成功返回True，失败返回False
    """
    log_func("开始安装CA证书...")
    
    # 检查可能的CA证书文件名
    possible_cert_files = [
        os.path.join(CA_DIR, "rootCA.crt"),
        os.path.join(CA_DIR, "ca.crt"),
        os.path.join(CA_DIR, "ca.cer"),
        os.path.join(CA_DIR, "rootCA.cer")
    ]
    
    ca_cert_file = None
    for cert_file in possible_cert_files:
        if os.path.exists(cert_file):
            ca_cert_file = cert_file
            log_func(f"找到CA证书文件: {ca_cert_file}")
            break
    
    if ca_cert_file is None:
        log_func(f"错误: 未找到CA证书文件，已检查以下路径: {', '.join(possible_cert_files)}")
        return False
    
    # 安装CA证书
    try:
        # Windows系统
        if os.name == 'nt':
            cmd = f'certutil -addstore -f "ROOT" "{ca_cert_file}"'
            log_func(f"执行命令: {cmd}")
            return_code, stdout, stderr = run_command(cmd, shell=True)
            log_func(stdout)
            if stderr:
                log_func(stderr)
            
            if return_code != 0:
                log_func(f"证书安装失败，返回码: {return_code}")
                return False
        # Mac系统 - 需要优先于posix检查，因为macOS也是posix系统
        elif sys.platform == 'darwin':
            # 检查是否在AppleScript环境下运行（通过检查环境变量和进程树）
            is_applescript_env = False
            
            # 调试信息
            log_func("开始检测AppleScript环境...")
            log_func(f"当前用户ID: {os.geteuid()}")
            log_func(f"是否有TTY: {os.isatty(0)}")
            log_func(f"环境变量_: {os.environ.get('_', 'None')}")
            
            # 方法1：检查环境变量
            if os.environ.get('_') and 'osascript' in os.environ.get('_', ''):
                is_applescript_env = True
                log_func("通过环境变量检测到AppleScript环境")
            
            # 方法2：检查进程树中是否有osascript
            if not is_applescript_env:
                try:
                    # 获取当前进程的完整进程树
                    current_pid = os.getpid()
                    ps_output = subprocess.check_output(['ps', '-eo', 'pid,ppid,comm'], text=True)
                    log_func(f"当前进程ID: {current_pid}")
                    
                    # 构建进程树
                    processes = {}
                    for line in ps_output.strip().split('\n')[1:]:  # 跳过标题行
                        parts = line.strip().split(None, 2)
                        if len(parts) >= 3:
                            pid, ppid, comm = parts[0], parts[1], parts[2]
                            processes[pid] = {'ppid': ppid, 'comm': comm}
                    
                    # 向上遍历进程树查找osascript
                    pid = str(current_pid)
                    process_chain = []
                    while pid in processes and pid != '1':
                        process_info = processes[pid]
                        process_chain.append(f"{pid}:{process_info['comm']}")
                        if 'osascript' in processes[pid]['comm']:
                            is_applescript_env = True
                            log_func(f"通过进程树检测到AppleScript环境: {' -> '.join(process_chain)}")
                            break
                        pid = processes[pid]['ppid']
                    
                    if not is_applescript_env:
                        log_func(f"进程链: {' -> '.join(process_chain)}")
                except Exception as e:
                    log_func(f"进程树检测失败: {str(e)}")
            
            # 方法3：检查是否通过sudo运行且没有TTY（AppleScript特征）
            if not is_applescript_env:
                try:
                    if os.geteuid() == 0 and not os.isatty(0):  # root用户且没有终端
                        is_applescript_env = True
                        log_func("通过sudo+无TTY检测到AppleScript环境")
                except Exception as e:
                    log_func(f"sudo+TTY检测失败: {str(e)}")
            
            log_func(f"AppleScript环境检测结果: {is_applescript_env}")
            
            if is_applescript_env:
                # 在AppleScript环境下，尝试自动安装并设置信任
                log_func("检测到AppleScript环境，尝试自动安装并设置证书信任...")
                
                # 在AppleScript环境下，先尝试简单添加证书到登录钥匙串
                try:
                    # 使用security命令添加证书到登录钥匙串（不设置信任级别）
                    cmd = f'security add-certificates -k ~/Library/Keychains/login.keychain-db "{ca_cert_file}"'
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
                        # 如果添加失败，提供手动安装指导
                        raise Exception("添加证书失败，转为手动安装")
                    
                    # 如果到这里，说明需要手动设置信任
                    log_func("")
                    log_func("=== 设置证书信任（重要步骤）===")
                    log_func("1. 打开钥匙串访问应用")
                    log_func("2. 选择'登录'钥匙串")
                    log_func("3. 找到证书（名为'MTGA CA'）")
                    log_func("4. 双击证书打开详情窗口")
                    log_func("5. 展开'信任'设置")
                    log_func("6. 将'使用此证书时'设置为'始终信任'")
                    log_func("7. 输入密码确认更改")
                    log_func("✅ 完成后证书将被完全信任")
                    
                    # 尝试打开钥匙串访问应用
                    try:
                        subprocess.run(['open', '-a', 'Keychain Access'], check=False)
                        log_func("已尝试自动打开钥匙串访问应用")
                    except:
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
                    log_func("6. 找到刚添加的证书（通常名为'MTGA CA'或类似名称）")
                    log_func("7. 双击该证书打开详情窗口")
                    log_func("8. 点击'信任'旁边的三角形展开信任设置")
                    log_func("9. 在'使用此证书时'下拉菜单中选择'始终信任'")
                    log_func("10. 关闭证书窗口，系统会提示输入密码")
                    log_func("11. 输入您的macOS登录密码确认更改")
                    log_func("")
                    log_func("✅ 完成后，证书图标会显示蓝色加号，表示已被信任")
                    log_func("✅ 此时HTTPS代理将能够正常工作，浏览器不会显示安全警告")
                    
                    # 尝试使用open命令打开证书文件
                    try:
                        subprocess.run(['open', ca_cert_file], check=False)
                        log_func(f"已尝试自动打开证书文件: {ca_cert_file}")
                    except:
                        log_func("无法自动打开证书文件，请手动打开")
                    
                    return True
            else:
                # 在终端环境下，使用传统的sudo方法
                cmd = f'sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "{ca_cert_file}"'
                log_func(f"执行命令: {cmd}")
                return_code, stdout, stderr = run_command(cmd, shell=True)
                log_func(stdout)
                if stderr:
                    log_func(stderr)
                
                if return_code != 0:
                    log_func(f"证书安装失败，返回码: {return_code}")
                    return False
        # Linux系统
        elif os.name == 'posix':
            # 复制证书到系统目录
            cmd = f'sudo cp "{ca_cert_file}" /usr/local/share/ca-certificates/'
            log_func(f"执行命令: {cmd}")
            return_code, stdout, stderr = run_command(cmd, shell=True)
            log_func(stdout)
            if stderr:
                log_func(stderr)
            
            if return_code != 0:
                log_func(f"复制证书失败，返回码: {return_code}")
                return False
            
            # 更新CA证书
            cmd = 'sudo update-ca-certificates'
            log_func(f"执行命令: {cmd}")
            return_code, stdout, stderr = run_command(cmd, shell=True)
            log_func(stdout)
            if stderr:
                log_func(stderr)
            
            if return_code != 0:
                log_func(f"更新证书失败，返回码: {return_code}")
                return False
        else:
            log_func("错误: 不支持的操作系统")
            return False
        
        log_func("CA证书安装成功！")
        return True
    except Exception as e:
        log_func(f"安装CA证书失败: {e}")
        return False

# 修改hosts文件
def modify_hosts_file(log_func=print, action="add"):
    """
    修改hosts文件
    
    参数:
    - log_func: 日志记录函数
    - action: 操作类型，可选值: "add"(添加), "backup"(备份), "restore"(还原), "reset"(重置)
    
    返回值:
    - 成功返回True，失败返回False
    """
    log_func(f"开始{{'add': '修改', 'backup': '备份', 'restore': '还原', 'reset': '重置'}}[action] hosts文件...")
    
    if not os.path.exists(HOSTS_FILE):
        log_func(f"错误: hosts文件不存在: {HOSTS_FILE}")
        return False
    
    # 备份文件路径
    backup_file = os.path.join(SCRIPT_DIR, "hosts.backup")
    
    # 尝试确定文件编码
    def detect_encoding(file_path):
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'utf-16']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    f.read()
                return enc
            except UnicodeDecodeError:
                continue
        # 如果所有编码都失败，返回一个安全的默认值
        return 'utf-8'
    
    # 根据不同操作类型执行不同操作
    if action == "backup":
        # 备份hosts文件
        try:
            shutil.copy2(HOSTS_FILE, backup_file)
            log_func(f"hosts文件已备份到: {backup_file}")
            return True
        except Exception as e:
            log_func(f"备份hosts文件失败: {e}")
            return False
            
    elif action == "restore":
        # 还原hosts文件
        if not os.path.exists(backup_file):
            log_func(f"错误: 备份文件不存在: {backup_file}")
            return False
        
        try:
            shutil.copy2(backup_file, HOSTS_FILE)
            log_func("hosts文件已还原")
            return True
        except Exception as e:
            log_func(f"还原hosts文件失败: {e}")
            return False
            
    elif action == "reset":
        # 重置hosts文件 (删除 域名 条目)
        try:
            # 检测文件编码
            encoding = detect_encoding(HOSTS_FILE)
            log_func(f"检测到hosts文件编码: {encoding}")
            
            with open(HOSTS_FILE, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                
            # 查找并删除包含 域名 的行
            lines = content.splitlines()
            new_lines = []
            skip_next = False
            
            for line in lines:
                if "Added by MTGA GUI" in line:
                    skip_next = True
                    continue
                if skip_next and DOMAIN in line:
                    skip_next = False
                    continue
                new_lines.append(line)
                
            # 写回文件
            with open(HOSTS_FILE, 'w', encoding=encoding) as f:
                f.write('\n'.join(new_lines))
                
            log_func("hosts文件已重置，删除了 域名 条目")
            return True
        except Exception as e:
            log_func(f"重置hosts文件失败: {e}")
            return False
            
    else:  # action == "add"
        # 添加 域名 条目
        try:
            # 先备份
            if not os.path.exists(backup_file):
                shutil.copy2(HOSTS_FILE, backup_file)
                log_func(f"hosts文件已自动备份到: {backup_file}")
            
            # 检测文件编码
            encoding = detect_encoding(HOSTS_FILE)
            log_func(f"检测到hosts文件编码: {encoding}")
            
            # 读取hosts文件内容
            with open(HOSTS_FILE, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            
            # 检查是否已经包含 域名 
            if HOSTS_CONTENT in content:
                log_func("hosts文件已包含 域名 条目，无需修改")
                return True
            
            # 添加 域名 条目
            with open(HOSTS_FILE, 'a', encoding=encoding) as f:
                f.write(f"\n# Added by MTGA GUI\n{HOSTS_CONTENT}\n")
            log_func("hosts文件修改成功！")
            return True
        except Exception as e:
            log_func(f"修改hosts文件失败: {e}")
            return False

# 保存配置
def save_config(api_url=None, model_id=None, target_model_id=None, stream_mode=None, log_func=print):
    """
    保存配置到配置文件，兼容配置组格式。
    如果文件不存在，则创建新文件。

    参数:
    - api_url: API基础URL (可选)
    - model_id: 模型ID (可选)
    - target_model_id: 实际模型ID (可选)
    - stream_mode: 强制流模式 (可选)
    - log_func: 日志记录函数

    返回值:
    - 成功返回True，失败返回False
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # 尝试加载现有配置
        config_data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                log_func(f"YAML格式错误，将重新创建配置文件: {e}")
                config_data = {}
            except Exception as e:
                log_func(f"读取配置文件失败，将重新创建: {e}")
                config_data = {}
        
        # 更新配置值
        if api_url is not None:
            config_data['api_url'] = api_url
            log_func(f"已设置 api_url: {api_url}")
        if model_id is not None:
            config_data['model_id'] = model_id
            log_func(f"已设置 model_id: {model_id}")
        if target_model_id is not None:
            config_data['target_model_id'] = target_model_id
            log_func(f"已设置 target_model_id: {target_model_id}")
        if stream_mode is not None:
            config_data['stream_mode'] = stream_mode
            log_func(f"已设置 stream_mode: {stream_mode}")
        
        # 创建临时文件，避免在写入过程中损坏原文件
        temp_config_file = CONFIG_FILE + '.tmp'
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            # 使用与save_config_groups相同的YAML格式设置
            yaml.dump(config_data, f, 
                     default_flow_style=False, 
                     allow_unicode=True, 
                     indent=2,
                     sort_keys=False,
                     width=float('inf'),  # 避免自动换行
                     default_style=None,
                     line_break=None,  # 使用系统默认换行符
                     encoding='utf-8')
        
        # 原子性替换：只有在临时文件写入成功后才替换原文件
        if os.path.exists(temp_config_file):
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            os.rename(temp_config_file, CONFIG_FILE)
        
        log_func(f"配置已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        log_func(f"保存配置失败: {e}")
        # 清理临时文件
        temp_config_file = CONFIG_FILE + '.tmp'
        if os.path.exists(temp_config_file):
            try:
                os.remove(temp_config_file)
            except:
                pass
        return False

# 加载配置
def load_config(log_func=print):
    """
    从配置文件加载配置
    
    参数:
    - log_func: 日志记录函数
    
    返回值:
    - 成功返回配置字典，失败返回空字典
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) # 使用 yaml.safe_load
                log_func(f"已加载配置: {CONFIG_FILE}")
                return config if config else {} # 返回空字典如果文件为空
        else:
            log_func(f"配置文件不存在: {CONFIG_FILE}，将使用默认配置")
            return {}
    except yaml.YAMLError as e: # 捕获YAML解析错误
        log_func(f"加载配置失败: YAML格式错误 - {e}")
        return {}
    except Exception as e:
        log_func(f"加载配置失败: {e}")
        return {}

# 配置组管理函数
def load_config_groups(log_func=print):
    """
    从配置文件加载配置组
    
    参数:
    - log_func: 日志记录函数
    
    返回值:
    - 成功返回(配置组列表, 当前选中索引)，失败返回([], 0)
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'config_groups' in config:
                    config_groups = config['config_groups']
                    current_index = config.get('current_config_index', 0)
                    log_func(f"已加载 {len(config_groups)} 个配置组")
                    return config_groups, current_index
                else:
                    log_func("配置文件格式不正确，使用默认配置")
                    return [], 0
        else:
            log_func(f"配置文件不存在: {CONFIG_FILE}，将使用默认配置")
            return [], 0
    except yaml.YAMLError as e:
        log_func(f"加载配置失败: YAML格式错误 - {e}")
        return [], 0
    except Exception as e:
        log_func(f"加载配置失败: {e}")
        return [], 0

def save_config_groups(config_groups, current_index=0, log_func=print):
    """
    保存配置组到配置文件
    
    参数:
    - config_groups: 配置组列表
    - current_index: 当前选中的配置组索引
    - log_func: 日志记录函数
    
    返回值:
    - 成功返回True，失败返回False
    """
    try:
        config_data = {
            'config_groups': config_groups,
            'current_config_index': current_index
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # 创建临时文件，避免在写入过程中损坏原文件
        temp_config_file = CONFIG_FILE + '.tmp'
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            # 使用更保守的YAML格式设置，确保格式稳定
            yaml.dump(config_data, f, 
                     default_flow_style=False, 
                     allow_unicode=True, 
                     indent=2,
                     sort_keys=False,
                     width=float('inf'),  # 避免自动换行
                     default_style=None,
                     line_break=None,  # 使用系统默认换行符
                     encoding='utf-8')
        
        # 原子性替换：只有在临时文件写入成功后才替换原文件
        if os.path.exists(temp_config_file):
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            os.rename(temp_config_file, CONFIG_FILE)
        
        log_func(f"配置组已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        log_func(f"保存配置组失败: {e}")
        # 清理临时文件
        temp_config_file = CONFIG_FILE + '.tmp'
        if os.path.exists(temp_config_file):
            try:
                os.remove(temp_config_file)
            except:
                pass
        return False

def get_current_config(log_func=print):
    """
    获取当前选中的配置
    
    参数:
    - log_func: 日志记录函数
    
    返回值:
    - 成功返回配置字典，失败返回空字典
    """
    config_groups, current_index = load_config_groups(log_func)
    if config_groups and 0 <= current_index < len(config_groups):
        return config_groups[current_index]
    return {}

# 启动代理服务器
def start_proxy_server(log_func=print, api_url=None, model_id=None, target_model_id=None, stream_mode=None, debug_mode=False):
    """
    启动代理服务器
    
    参数:
    - log_func: 日志记录函数
    - api_url: API基础URL，如果为None则使用配置文件中的值
    - model_id: 模型ID，如果为None则使用配置文件中的值
    - target_model_id: 实际模型ID，如果为None则不修改
    - stream_mode: 强制流模式，如果为None则不修改
    - debug_mode: 是否开启调试模式 (布尔值)
    
    返回值:
    - 成功返回进程对象，失败返回None
    """
    global proxy_process
    
    log_func("开始启动代理服务器...")
    
    # 如果已经有代理服务器在运行，先停止它
    if proxy_process:
        try:
            log_func("检测到代理服务器已在运行，先停止它...")
            proxy_process.terminate()
            proxy_process = None
            # 等待一段时间确保端口释放
            time.sleep(1)
        except Exception as e:
            log_func(f"停止现有代理服务器时出错: {e}")
    
    # 检查证书文件
    possible_cert_files = [
        os.path.join(CA_DIR, DOMAIN_CNF),
        os.path.join(CA_DIR, "server.crt")
    ]
    possible_key_files = [
        os.path.join(CA_DIR, DOMAIN_KEY),
        os.path.join(CA_DIR, "server.key")
    ]
    
    cert_file = None
    for f in possible_cert_files:
        if os.path.exists(f):
            cert_file = f
            log_func(f"找到服务器证书文件: {cert_file}")
            break
    
    key_file = None
    for f in possible_key_files:
        if os.path.exists(f):
            key_file = f
            log_func(f"找到服务器密钥文件: {key_file}")
            break
    
    if cert_file is None or key_file is None:
        log_func(f"错误: 未找到服务器证书或密钥文件")
        log_func(f"已检查的证书文件: {', '.join(possible_cert_files)}")
        log_func(f"已检查的密钥文件: {', '.join(possible_key_files)}")
        return None
    
    # 注意：不再在启动代理服务器时保存配置到文件，避免与配置组格式冲突
    # 配置参数仅用于临时修改代理脚本，不会持久化到配置文件
    
    # 创建临时代理脚本
    temp_proxy_file = os.path.join(SCRIPT_DIR, "temp_proxy.py")
    try:
        # 读取原始文件内容
        with open(TRAE_PROXY_PY, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修改证书文件路径
        if os.path.basename(cert_file) != DOMAIN_CNF:
            content = content.replace(
                f"CERT_FILE = os.path.join(CERT_DIR, {DOMAIN_CNF})",
                f"CERT_FILE = os.path.join(CERT_DIR, '{os.path.basename(cert_file)}')"
            )
        
        if os.path.basename(key_file) != DOMAIN_KEY:
            content = content.replace(
                f"KEY_FILE = os.path.join(CERT_DIR, {DOMAIN_KEY})",
                f"KEY_FILE = os.path.join(CERT_DIR, '{os.path.basename(key_file)}')"
            )
        
        # 如果提供了API URL，替换它
        if api_url:
            # 替换常见的API URL模式
            patterns = [
                'TARGET_API_BASE_URL = "YOUR_REVERSE_ENGINEERED_API_ENDPOINT_BASE_URL"',
                'TARGET_API_BASE_URL = "https://api.example.com/v1"'
            ]
            
            for pattern in patterns:
                if pattern in content:
                    content = content.replace(pattern, f'TARGET_API_BASE_URL = "{api_url}"')
                    log_func(f"已设置API URL: {api_url}")
                    break
        
        # 如果提供了模型ID，替换它
        if model_id:
            # 替换常见的模型ID模式
            patterns = [
                'CUSTOM_MODEL_ID = "CUSTOM_MODEL_ID"',
                'CUSTOM_MODEL_ID = "glm-4-flash-250414"',
                'CUSTOM_MODEL_ID = "gpt-3.5-turbo"'
            ]
            
            for pattern in patterns:
                if pattern in content:
                    content = content.replace(pattern, f'CUSTOM_MODEL_ID = "{model_id}"')
                    log_func(f"已设置模型ID: {model_id}")
                    break
        
        # 如果提供了实际模型ID，替换它
        if target_model_id:
            # 替换TARGET_MODEL_ID的赋值
            patterns = [
                'TARGET_MODEL_ID = CUSTOM_MODEL_ID # 默认和 CUSTOM_MODEL_ID 相同',
                'TARGET_MODEL_ID = CUSTOM_MODEL_ID',
                'TARGET_MODEL_ID = "gpt-4o"'
            ]
            
            for pattern in patterns:
                if pattern in content:
                    content = content.replace(pattern, f'TARGET_MODEL_ID = "{target_model_id}"')
                    log_func(f"已设置实际模型ID: {target_model_id}")
                    break
        
        # 如果提供了流模式设置，替换它
        if stream_mode:
            # 替换STREAM_MODE的赋值
            patterns = [
                'STREAM_MODE = None # None为不修改，\'true\'为开启流式，\'false\'为关闭流式',
                'STREAM_MODE = None',
                'STREAM_MODE = \'true\'',
                'STREAM_MODE = \'false\''
            ]
            
            for pattern in patterns:
                if pattern in content:
                    content = content.replace(pattern, f'STREAM_MODE = \'{stream_mode}\'')
                    log_func(f"已设置强制流模式: {stream_mode}")
                    break
        
        # 修改脚本，确保输出使用UTF-8编码
        if "# -*- coding: utf-8 -*-" not in content:
            content = "# -*- coding: utf-8 -*-\n" + content
        
        # 写入临时文件
        with open(temp_proxy_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log_func(f"已创建临时代理脚本: {temp_proxy_file}")
        
        # 删除可能存在的旧批处理文件
        run_proxy_bat = os.path.join(SCRIPT_DIR, "run_proxy.bat")
        if os.path.exists(run_proxy_bat):
            try:
                os.remove(run_proxy_bat)
                log_func("已删除旧的批处理文件")
            except Exception as e:
                log_func(f"删除旧批处理文件失败: {e}")
    except Exception as e:
        log_func(f"创建临时代理脚本失败: {e}")
        return None
    
    # 启动代理服务器，将输出重定向到日志
    try:
        log_func("正在启动代理服务器...")
        
        # 创建一个队列用于存储输出
        output_queue = Queue()
        
        # 定义一个尝试多种编码解码文本的函数
        def decode_with_fallback(byte_str):
            encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin1']
            for encoding in encodings:
                try:
                    return byte_str.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # 如果所有编码都失败，使用latin1（它不会失败，但可能有乱码）
            return byte_str.decode('latin1', errors='replace')
        
        # 定义一个读取输出的函数
        def enqueue_output(out, queue):
            for line in iter(out.readline, b''):
                queue.put(decode_with_fallback(line).strip())
            out.close()
        
        # 设置环境变量，确保子进程使用UTF-8编码
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # 构建启动命令
        cmd = [VENV_PYTHON, temp_proxy_file]
        if debug_mode:
            cmd.append("--debug")
            log_func("调试模式已启用")
        
        # 创建子进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=False,
            env=env
        )
        
        # 保存到全局变量
        proxy_process = process
        
        # 创建线程来读取输出
        output_thread = threading.Thread(
            target=enqueue_output,
            args=(process.stdout, output_queue)
        )
        output_thread.daemon = True
        output_thread.start()
        
        # 创建线程来处理输出
        def process_output():
            global proxy_process
            while True:
                try:
                    # 检查进程是否还在运行
                    if process.poll() is not None:
                        # 进程已结束
                        returncode = process.poll()
                        log_func(f"代理服务器已停止，返回码: {returncode}")
                        if proxy_process == process:
                            proxy_process = None
                        break
                    
                    # 尝试从队列获取输出
                    try:
                        line = output_queue.get_nowait()
                        log_func(f"[代理] {line}")
                    except Empty:
                        # 队列为空，等待一段时间
                        time.sleep(0.1)
                        continue
                except Exception as e:
                    log_func(f"处理代理服务器输出时出错: {e}")
                    break
        
        # 启动处理输出的线程
        threading.Thread(target=process_output, daemon=True).start()
        
        log_func("代理服务器已启动！")
        return process
    except Exception as e:
        log_func(f"启动代理服务器失败: {e}")
        return None

# 检查并安装依赖
def check_and_install_dependencies(log_func=print):
    log_func("检查并安装依赖...")
    
    # 使用uv安装Flask和requests
    cmd = ["uv", "pip", "install", "Flask", "requests"]
    log_func(f"执行命令: {' '.join(cmd)}")
    
    return_code, stdout, stderr = run_command(cmd)
    log_func(stdout)
    if stderr:
        log_func(stderr)
    
    if return_code == 0:
        log_func("依赖安装成功！")
        return True
    else:
        log_func(f"依赖安装失败，返回码: {return_code}")
        return False

# 创建主窗口
def create_main_window():
    window = tk.Tk()
    window.title("MTGA GUI")
    window.geometry("1250x700")  # 将宽度从1000增加五分之一到1200像素
    window.resizable(True, True)
    
    # 设置窗口图标
    try:
        if os.name == 'nt':  # Windows
            icon_path = os.path.join(SCRIPT_DIR, "icon.ico")
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
        else:  # macOS/Linux
            icon_path = os.path.join(SCRIPT_DIR, "icon.png")
            if os.path.exists(icon_path):
                # 在macOS和Linux上使用PhotoImage
                icon_image = tk.PhotoImage(file=icon_path)
                window.iconphoto(True, icon_image)
    except Exception as e:
        print(f"设置图标失败: {e}")
        pass
    
    # 创建主框架
    main_frame = ttk.Frame(window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 添加标题
    title_label = ttk.Label(
        main_frame, 
        text="MTGA GUI - 代理服务器管理工具", 
        font=("Arial", 16, "bold")
    )
    title_label.pack(pady=10)
    
    # 创建左右分栏的主容器
    main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    main_paned.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # 左侧功能区域
    left_frame = ttk.Frame(main_paned)
    main_paned.add(left_frame, weight=1000)
    
    # 右侧日志区域
    right_frame = ttk.Frame(main_paned)
    main_paned.add(right_frame, weight=1)
    
    # 设置初始sash位置，确保左侧占大部分空间（75%）
    def set_sash_position():
        """设置分栏位置为左侧75%，右侧25%"""
        window.update_idletasks()  # 确保窗口已完全渲染
        total_width = main_paned.winfo_width()
        if total_width > 1:  # 确保窗口已经有实际宽度
            left_width = int(total_width * 0.5)  # 左侧占75%
            main_paned.sashpos(0, left_width)
    
    window.after(100, set_sash_position)
    
    # 创建日志文本框 - 放在右侧独占整个高度
    log_frame = ttk.LabelFrame(right_frame, text="日志")
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_text = scrolledtext.ScrolledText(log_frame, height=10)
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 自定义日志函数
    def log(message):
        log_text.insert(tk.END, f"{message}\n")
        log_text.see(tk.END)
        print(message)
    
    # 加载启动日志文件（如果存在）
    startup_log_file = os.path.join(SCRIPT_DIR, "startup.log")
    if os.path.exists(startup_log_file):
        try:
            with open(startup_log_file, 'r', encoding='utf-8') as f:
                startup_content = f.read().strip()
                if startup_content:
                    log("=== 启动日志 ===")
                    for line in startup_content.split('\n'):
                        if line.strip():
                            log_text.insert(tk.END, f"{line}\n")
                    log("=== 启动日志结束 ===")
                    log_text.see(tk.END)
        except Exception as e:
            log(f"读取启动日志失败: {e}")
    
    # 配置组管理界面 - 放在左侧框架中
    # 注意：配置组将在refresh_config_list()中加载，避免重复加载
    config_groups = []
    current_config_index = 0
    config_frame = ttk.LabelFrame(left_frame, text="代理服务器配置组")
    config_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # 创建左右分栏
    config_paned = ttk.PanedWindow(config_frame, orient=tk.HORIZONTAL)
    config_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 左侧配置组列表
    config_list_frame = ttk.Frame(config_paned)
    config_paned.add(config_list_frame, weight=3)
    
    ttk.Label(config_list_frame, text="配置组列表:").pack(anchor=tk.W, padx=5, pady=(5, 0))
    
    # 创建Treeview显示配置组，并添加滚动条
    tree_frame = ttk.Frame(config_list_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    columns = ('序号', 'API URL', '模型ID', '实际模型ID')
    config_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=6)
    
    # 创建垂直滚动条
    v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=config_tree.yview)
    config_tree.configure(yscrollcommand=v_scrollbar.set)
    
    # 创建水平滚动条
    h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=config_tree.xview)
    config_tree.configure(xscrollcommand=h_scrollbar.set)
    
    # 设置列标题
    config_tree.heading('序号', text='序号')
    config_tree.heading('API URL', text='API URL')
    config_tree.heading('模型ID', text='模型ID')
    config_tree.heading('实际模型ID', text='实际模型ID')
    
    # 设置列宽
    config_tree.column('序号', width=30, anchor=tk.CENTER)
    config_tree.column('API URL', width=200)
    config_tree.column('模型ID', width=120)
    config_tree.column('实际模型ID', width=120)
    
    # 布局Treeview和滚动条
    config_tree.grid(row=0, column=0, sticky='nsew')
    v_scrollbar.grid(row=0, column=1, sticky='ns')
    h_scrollbar.grid(row=1, column=0, sticky='ew')
    
    # 配置grid权重
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    # 右侧按钮区域
    config_buttons_frame = ttk.Frame(config_paned)
    config_paned.add(config_buttons_frame, weight=1)
    
    ttk.Label(config_buttons_frame, text="操作:").pack(anchor=tk.W, padx=5, pady=(5, 0))
    
    # 配置组操作函数
    def refresh_config_list():
        """刷新配置组列表显示"""
        nonlocal config_groups, current_config_index
        config_groups, current_config_index = load_config_groups(log)
        
        # 清空现有项目
        for item in config_tree.get_children():
            config_tree.delete(item)
        
        # 添加配置组到列表
        for i, group in enumerate(config_groups):
            target_model = group.get('target_model_id', '') or '(无)'
            config_tree.insert('', 'end', values=(
                i + 1,
                group.get('api_url', ''),
                group.get('model_id', ''),
                target_model
            ))
        
        # 选中当前配置组
        if config_groups and 0 <= current_config_index < len(config_groups):
            children = config_tree.get_children()
            if current_config_index < len(children):
                config_tree.selection_set(children[current_config_index])
                config_tree.focus(children[current_config_index])
    
    def get_selected_index():
        """获取当前选中的配置组索引"""
        selection = config_tree.selection()
        if selection:
            item = selection[0]
            return config_tree.index(item)
        return -1
    
    def on_config_select(event):
        """配置组选择事件处理"""
        nonlocal current_config_index
        selected_index = get_selected_index()
        if selected_index >= 0:
            current_config_index = selected_index
            # 保存当前选中的配置组索引
            save_config_groups(config_groups, current_config_index, log)
    
    def add_config_group():
        """新增配置组"""
        def save_new_config():
            name = name_var.get().strip()
            api_url = api_url_var.get().strip()
            model_id = model_id_var.get().strip()
            target_model_id = target_model_var.get().strip()
            
            if not api_url or not model_id:
                log("错误: API URL和模型ID不能为空")
                return
            
            new_group = {
                'name': name,
                'api_url': api_url,
                'model_id': model_id,
                'target_model_id': target_model_id
            }
            
            config_groups.append(new_group)
            if save_config_groups(config_groups, current_config_index, log):
                log(f"已添加配置组: {name}")
                refresh_config_list()
                add_window.destroy()
            else:
                log("保存配置组失败")
        
        # 创建新增窗口
        add_window = tk.Toplevel(window)
        add_window.title("新增配置组")
        add_window.geometry("400x250")
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
        
        # 配置组名称
        ttk.Label(main_frame, text="配置组名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # API URL
        ttk.Label(main_frame, text="API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_url_var = tk.StringVar()
        api_url_entry = ttk.Entry(main_frame, textvariable=api_url_var, width=30)
        api_url_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # 模型ID
        ttk.Label(main_frame, text="模型ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_id_var = tk.StringVar()
        model_id_entry = ttk.Entry(main_frame, textvariable=model_id_var, width=30)
        model_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # 实际模型ID（可选）
        ttk.Label(main_frame, text="实际模型ID (可选):").grid(row=3, column=0, sticky=tk.W, pady=5)
        target_model_var = tk.StringVar()
        target_model_entry = ttk.Entry(main_frame, textvariable=target_model_var, width=30)
        target_model_entry.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="保存", command=save_new_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=add_window.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
        name_entry.focus()
    
    def edit_config_group():
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
            target_model_id = target_model_var.get().strip()
            
            if not api_url or not model_id:
                log("错误: API URL和模型ID不能为空")
                return
            
            # 更新配置组
            config_groups[selected_index] = {
                'name': name,
                'api_url': api_url,
                'model_id': model_id,
                'target_model_id': target_model_id
            }
            
            if save_config_groups(config_groups, current_config_index, log):
                log(f"已修改配置组: {name}")
                refresh_config_list()
                edit_window.destroy()
            else:
                log("保存配置组失败")
        
        # 创建修改窗口
        edit_window = tk.Toplevel(window)
        edit_window.title("修改配置组")
        edit_window.geometry("400x250")
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
        
        # 配置组名称
        ttk.Label(main_frame, text="配置组名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=current_group.get('name', ''))
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # API URL
        ttk.Label(main_frame, text="API URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_url_var = tk.StringVar(value=current_group.get('api_url', ''))
        api_url_entry = ttk.Entry(main_frame, textvariable=api_url_var, width=30)
        api_url_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # 模型ID
        ttk.Label(main_frame, text="模型ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_id_var = tk.StringVar(value=current_group.get('model_id', ''))
        model_id_entry = ttk.Entry(main_frame, textvariable=model_id_var, width=30)
        model_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # 实际模型ID（可选）
        ttk.Label(main_frame, text="实际模型ID (可选):").grid(row=3, column=0, sticky=tk.W, pady=5)
        target_model_var = tk.StringVar(value=current_group.get('target_model_id', ''))
        target_model_entry = ttk.Entry(main_frame, textvariable=target_model_var, width=30)
        target_model_entry.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="保存", command=save_edited_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
        
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
        
        group_name = config_groups[selected_index].get('name', f'配置组{selected_index + 1}')
        
        # 确认删除
        import tkinter.messagebox as msgbox
        if msgbox.askyesno("确认删除", f"确定要删除配置组 '{group_name}' 吗？"):
            del config_groups[selected_index]
            
            # 调整当前选中索引
            nonlocal current_config_index
            if current_config_index >= len(config_groups):
                current_config_index = len(config_groups) - 1
            elif current_config_index > selected_index:
                current_config_index -= 1
            
            if save_config_groups(config_groups, current_config_index, log):
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
        config_groups[selected_index], config_groups[selected_index - 1] = \
            config_groups[selected_index - 1], config_groups[selected_index]
        
        # 更新当前选中索引
        nonlocal current_config_index
        if current_config_index == selected_index:
            current_config_index = selected_index - 1
        elif current_config_index == selected_index - 1:
            current_config_index = selected_index
        
        if save_config_groups(config_groups, current_config_index, log):
            refresh_config_list()
        else:
            log("保存配置组失败")
    
    def move_config_down():
        """下移配置组"""
        selected_index = get_selected_index()
        if selected_index < 0 or selected_index >= len(config_groups) - 1:
            return
        
        # 交换位置
        config_groups[selected_index], config_groups[selected_index + 1] = \
            config_groups[selected_index + 1], config_groups[selected_index]
        
        # 更新当前选中索引
        nonlocal current_config_index
        if current_config_index == selected_index:
            current_config_index = selected_index + 1
        elif current_config_index == selected_index + 1:
            current_config_index = selected_index
        
        if save_config_groups(config_groups, current_config_index, log):
            refresh_config_list()
        else:
            log("保存配置组失败")
    
    # 绑定选择事件
    config_tree.bind('<<TreeviewSelect>>', on_config_select)
    
    # 操作按钮
    ttk.Button(config_buttons_frame, text="新增", command=add_config_group).pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(config_buttons_frame, text="修改", command=edit_config_group).pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(config_buttons_frame, text="删除", command=delete_config_group).pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(config_buttons_frame, text="上移", command=move_config_up).pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(config_buttons_frame, text="下移", command=move_config_down).pack(fill=tk.X, padx=5, pady=2)
    
    # 初始化配置组列表
    refresh_config_list()
    
    # 强制流模式下拉框（带勾选框）- 放在left_frame中
    stream_mode_frame = ttk.Frame(left_frame)
    stream_mode_frame.pack(fill=tk.X, padx=5, pady=2)
    stream_mode_var = tk.BooleanVar(value=False)
    stream_mode_check = ttk.Checkbutton(stream_mode_frame, text="强制流模式:", variable=stream_mode_var, command=lambda: stream_mode_combo.config(state='readonly' if stream_mode_var.get() else 'disabled'))
    stream_mode_check.pack(side=tk.LEFT)
    stream_mode_combo = ttk.Combobox(stream_mode_frame, values=["true", "false"], state='disabled')
    stream_mode_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
    stream_mode_combo.set("true")  # 默认值

    # 添加调试模式复选框 - 放在left_frame中
    debug_mode_var = tk.BooleanVar(value=False) # 默认为关闭
    debug_mode_check = ttk.Checkbutton(left_frame, text="开启调试模式", variable=debug_mode_var)
    debug_mode_check.pack(fill=tk.X, padx=5, pady=2)
    
    # 创建标签页控件 - 放在左侧框架中
    notebook = ttk.Notebook(left_frame)
    notebook.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # --------- 标签页1: 证书管理 ---------
    cert_tab = ttk.Frame(notebook)
    notebook.add(cert_tab, text="证书管理")
    
    # 创建证书管理按钮
    cert_button = ttk.Button(
        cert_tab, 
        text="生成CA和服务器证书", 
        command=lambda: threading.Thread(target=lambda: generate_certificates(log)).start()
    )
    cert_button.pack(fill=tk.X, padx=5, pady=5)
    
    install_cert_button = ttk.Button(
        cert_tab, 
        text="安装CA证书", 
        command=lambda: threading.Thread(target=lambda: install_ca_cert(log)).start()
    )
    install_cert_button.pack(fill=tk.X, padx=5, pady=5)
    
    # --------- 标签页2: hosts文件管理 ---------
    hosts_tab = ttk.Frame(notebook)
    notebook.add(hosts_tab, text="hosts文件管理")
    
    # 创建hosts文件管理按钮
    hosts_button = ttk.Button(
        hosts_tab, 
        text="修改hosts文件", 
        command=lambda: threading.Thread(target=lambda: modify_hosts_file(log)).start()
    )
    hosts_button.pack(fill=tk.X, padx=5, pady=5)
    
    # 添加hosts文件备份、还原和重置按钮
    hosts_buttons_frame = ttk.Frame(hosts_tab)
    hosts_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
    
    hosts_backup_button = ttk.Button(
        hosts_buttons_frame, 
        text="备份hosts", 
        command=lambda: threading.Thread(target=lambda: modify_hosts_file(log, action="backup")).start()
    )
    hosts_backup_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    
    hosts_restore_button = ttk.Button(
        hosts_buttons_frame, 
        text="还原hosts", 
        command=lambda: threading.Thread(target=lambda: modify_hosts_file(log, action="restore")).start()
    )
    hosts_restore_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    
    hosts_reset_button = ttk.Button(
        hosts_buttons_frame, 
        text="重置hosts", 
        command=lambda: threading.Thread(target=lambda: modify_hosts_file(log, action="reset")).start()
    )
    hosts_reset_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    
    # 添加打开hosts文件按钮
    def open_hosts_file():
        """根据平台打开hosts文件"""
        try:
            if os.name == 'nt':  # Windows
                # Windows使用notepad打开
                subprocess.run(['notepad', HOSTS_FILE], check=True)
                log("已使用记事本打开hosts文件")
            elif sys.platform == 'darwin':  # macOS
                # macOS使用默认文本编辑器打开
                subprocess.run(['open', '-t', HOSTS_FILE], check=True)
                log("已使用默认文本编辑器打开hosts文件")
            else:  # Linux
                # Linux尝试使用常见的文本编辑器
                editors = ['gedit', 'nano', 'vim']
                for editor in editors:
                    try:
                        subprocess.run([editor, HOSTS_FILE], check=True)
                        log(f"已使用{editor}打开hosts文件")
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    log("未找到合适的文本编辑器")
        except Exception as e:
            log(f"打开hosts文件失败: {e}")
    
    hosts_open_button = ttk.Button(
        hosts_tab, 
        text="打开hosts文件", 
        command=lambda: threading.Thread(target=open_hosts_file).start()
    )
    hosts_open_button.pack(fill=tk.X, padx=5, pady=5)
    
    # --------- 标签页3: 代理服务器操作 ---------
    proxy_tab = ttk.Frame(notebook)
    notebook.add(proxy_tab, text="代理服务器操作")
    
    # 创建代理服务器按钮
    def start_proxy_with_current_config():
        """使用当前选中的配置组启动代理服务器"""
        current_config = get_current_config()
        if not current_config:
            log("错误: 没有可用的配置组")
            return
        
        start_proxy_server(
            log, 
            api_url=current_config.get('api_url'),
            model_id=current_config.get('model_id'),
            target_model_id=current_config.get('target_model_id') if current_config.get('target_model_id') else None,
            stream_mode=stream_mode_combo.get() if stream_mode_var.get() else None,
            debug_mode=debug_mode_var.get()
        )
    
    proxy_button = ttk.Button(
        proxy_tab, 
        text="启动代理服务器", 
        command=lambda: threading.Thread(target=start_proxy_with_current_config).start()
    )
    proxy_button.pack(fill=tk.X, padx=5, pady=5)
    
    # 添加停止代理服务器按钮
    proxy_stop_button = ttk.Button(
        proxy_tab, 
        text="停止代理服务器", 
        command=lambda: threading.Thread(target=lambda: stop_proxy_server(log)).start()
    )
    proxy_stop_button.pack(fill=tk.X, padx=5, pady=5)
    
    # --------- 标签页4: 关于 ---------
    about_tab = ttk.Frame(notebook)
    notebook.add(about_tab, text="关于")
    
    # 创建关于标签
    about_text = "MTGA GUI v1.0\n\n"
    about_text += "本工具用于自动生成CA和服务器证书，修改hosts文件，启动代理服务器。\n\n"
    about_text += "使用方法：\n"
    about_text += "1. 在\"证书管理\"标签页中生成并安装CA证书\n"
    about_text += "2. 在\"hosts文件管理\"标签页中修改hosts文件\n"
    about_text += "3. 在上方配置区域设置API URL和模型ID，点击\"保存配置\"保存\n"
    about_text += "4. 在\"代理服务器操作\"标签页中启动代理服务器\n"
    about_text += "5. 或者直接点击下方的\"一键启动全部服务\"按钮，一键完成以上所有操作\n"
    
    about_label = ttk.Label(about_tab, text=about_text, justify=tk.LEFT, wraplength=550)
    about_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 创建一键启动按钮（放在标签页外面）
    def start_all_with_current_config():
        """使用当前选中的配置组一键启动全部服务"""
        current_config = get_current_config()
        if not current_config:
            log("错误: 没有可用的配置组")
            return
        
        start_all_services(
            log,
            api_url=current_config.get('api_url'),
            model_id=current_config.get('model_id'),
            target_model_id=current_config.get('target_model_id') if current_config.get('target_model_id') else None,
            stream_mode=stream_mode_combo.get() if stream_mode_var.get() else None
        )
    
    start_button = ttk.Button(
        left_frame, 
        text="一键启动全部服务", 
        command=lambda: threading.Thread(target=start_all_with_current_config).start()
    )
    start_button.pack(fill=tk.X, pady=10)
    
    # 停止代理服务器函数
    def stop_proxy_server(log_func=print):
        global proxy_process
        if proxy_process:
            try:
                log_func("正在停止代理服务器...")
                proxy_process.terminate()
                proxy_process = None
                log_func("代理服务器已停止")
            except Exception as e:
                log_func(f"停止代理服务器时出错: {e}")
        else:
            log_func("代理服务器未运行")
    
    # 初始日志
    log("MTGA GUI已启动，请选择操作...")
    
    # 窗口关闭时停止代理服务器
    def on_closing():
        global proxy_process
        if proxy_process:
            try:
                log("正在停止代理服务器...")
                proxy_process.terminate()
                proxy_process = None
            except:
                pass
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", on_closing)
    
    return window, log

# 一键启动全部服务
def start_all_services(log_func=print, api_url=None, model_id=None, target_model_id=None, stream_mode=None):
    log_func("开始一键启动全部服务...")
    
    # 生成证书
    if not generate_certificates(log_func):
        log_func("生成证书失败，无法继续！")
        return False
    
    # 安装CA证书
    if not install_ca_cert(log_func):
        log_func("安装CA证书失败，无法继续！")
        return False
    
    # 修改hosts文件
    if not modify_hosts_file(log_func):
        log_func("修改hosts文件失败，无法继续！")
        return False
    
    # 如果提供了API URL或模型ID，保存到配置文件
    if api_url or model_id or target_model_id or stream_mode:
        if not save_config(api_url, model_id, target_model_id, stream_mode, log_func):
            log_func("保存配置失败，但将继续启动代理服务器")
    
    # macOS平台特殊处理：在证书安装后停止，不启动代理服务器
    if sys.platform == 'darwin':
        log_func("")
        log_func("=" * 60)
        log_func("🍎 macOS 平台检测到")
        log_func("=" * 60)
        log_func("")
        log_func("✅ 证书生成和安装已完成")
        log_func("✅ hosts文件修改已完成")
        log_func("✅ 配置文件保存已完成")
        log_func("")
        log_func("⚠️  由于macOS系统的安全机制，证书安装后需要用户手动确认信任设置。")
        log_func("⚠️  请确保上面的证书信任设置已完成，再启动代理服务器。")
        log_func("")
        log_func("📋  证书信任设置完成后，点击下方的 '启动代理服务器' 按钮")
        log_func("")
        log_func("💡 提示：如果找不到证书，请重新运行一键启动")
        log_func("")
        log_func("=" * 60)
        log_func("🔧 准备工作已完成，等待用户手动启动代理服务器")
        log_func("=" * 60)
        return True
    
    # 非macOS平台继续原有流程
    # 启动代理服务器
    process = start_proxy_server(log_func, api_url, model_id, target_model_id, stream_mode)
    if not process:
        log_func("启动代理服务器失败，无法继续！")
        return False
    
    log_func("全部服务启动成功！")
    return True

def main():
    # 检查管理员权限，如果没有则请求
    if not is_admin():
        run_as_admin()
        return
    
    # 创建GUI
    root, log = create_main_window()
    root.mainloop()

if __name__ == "__main__":
    main()