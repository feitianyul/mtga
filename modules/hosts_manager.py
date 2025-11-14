# -*- coding: utf-8 -*-
"""
hosts 文件管理模块
处理 hosts 文件的备份、修改、还原等操作
"""

import os
import sys
import shutil
import subprocess
from .resource_manager import ResourceManager


def get_hosts_file_path():
    """获取 hosts 文件路径"""
    if os.name == 'nt':  # Windows
        return r"C:\Windows\System32\drivers\etc\hosts"
    else:  # Unix/Linux/macOS
        return "/etc/hosts"


def get_backup_file_path():
    """获取备份文件路径（持久化到用户数据目录）"""
    resource_manager = ResourceManager()
    return resource_manager.get_hosts_backup_file()


def detect_file_encoding(file_path):
    """检测文件编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'utf-16']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8'  # 默认编码


def backup_hosts_file(log_func=print):
    """
    备份 hosts 文件
    
    参数:
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    hosts_file = get_hosts_file_path()
    backup_file = get_backup_file_path()
    
    log_func("开始备份 hosts 文件...")
    
    if not os.path.exists(hosts_file):
        log_func(f"错误: hosts 文件不存在: {hosts_file}")
        return False
    
    try:
        shutil.copy2(hosts_file, backup_file)
        log_func(f"hosts 文件已备份到: {backup_file}")
        return True
    except Exception as e:
        log_func(f"备份 hosts 文件失败: {e}")
        return False


def restore_hosts_file(log_func=print):
    """
    还原 hosts 文件
    
    参数:
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    hosts_file = get_hosts_file_path()
    backup_file = get_backup_file_path()
    
    log_func("开始还原 hosts 文件...")
    
    if not os.path.exists(backup_file):
        log_func(f"错误: 备份文件不存在: {backup_file}")
        return False
    
    try:
        shutil.copy2(backup_file, hosts_file)
        log_func("hosts 文件已还原")
        return True
    except Exception as e:
        log_func(f"还原 hosts 文件失败: {e}")
        return False


def write_hosts_file_with_permission(hosts_file, content, encoding, log_func=print):
    """
    使用适当的权限写入 hosts 文件
    
    参数:
        hosts_file: hosts 文件路径
        content: 要写入的内容
        encoding: 文件编码
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    if sys.platform == 'darwin':
        # macOS: 使用 osascript 请求管理员权限
        import tempfile
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # 使用 osascript 复制文件（需要管理员权限）
            cmd = f'''osascript -e 'do shell script "cp \\"{temp_path}\\" \\"{hosts_file}\\"" with administrator privileges' '''
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                log_func("✅ hosts 文件写入成功")
                return True
            else:
                if "User canceled" in result.stderr:
                    log_func("用户取消了操作")
                else:
                    log_func(f"写入失败: {result.stderr}")
                return False
        finally:
            # 清理临时文件
            try:
                os.remove(temp_path)
            except OSError:
                pass
    else:
        # Windows 和其他系统：直接写入
        try:
            with open(hosts_file, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except PermissionError:
            log_func("❌ 权限不足，请以管理员身份运行")
            return False


def add_hosts_entry(domain, ip="127.0.0.1", log_func=print):
    """
    添加 hosts 条目
    
    参数:
        domain: 域名
        ip: IP 地址
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    hosts_file = get_hosts_file_path()
    backup_file = get_backup_file_path()
    
    log_func(f"开始添加 hosts 条目: {ip} {domain}")
    
    if not os.path.exists(hosts_file):
        log_func(f"错误: hosts 文件不存在: {hosts_file}")
        return False
    
    try:
        # 先备份（如果备份文件不存在）
        if not os.path.exists(backup_file):
            shutil.copy2(hosts_file, backup_file)
            log_func(f"hosts 文件已自动备份到: {backup_file}")
        
        # 检测文件编码
        encoding = detect_file_encoding(hosts_file)
        log_func(f"检测到 hosts 文件编码: {encoding}")
        
        # 读取 hosts 文件内容
        with open(hosts_file, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        # 构造要添加的内容
        hosts_entry = f"{ip} {domain}"
        
        # 检查是否已经包含该条目
        if hosts_entry in content:
            log_func("hosts 文件已包含该条目，无需修改")
            return True
        
        # 添加条目到内容
        content += f"\n# Added by MTGA GUI\n{hosts_entry}\n"
        
        # 使用权限写入
        if write_hosts_file_with_permission(hosts_file, content, encoding, log_func):
            log_func("hosts 文件修改成功！")
            return True
        else:
            return False
        
    except Exception as e:
        log_func(f"修改 hosts 文件失败: {e}")
        return False


def remove_hosts_entry(domain, log_func=print):
    """
    删除 hosts 条目
    
    参数:
        domain: 要删除的域名
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    hosts_file = get_hosts_file_path()
    
    log_func(f"开始删除 hosts 条目: {domain}")
    
    if not os.path.exists(hosts_file):
        log_func(f"错误: hosts 文件不存在: {hosts_file}")
        return False
    
    try:
        # 检测文件编码
        encoding = detect_file_encoding(hosts_file)
        log_func(f"检测到 hosts 文件编码: {encoding}")
        
        with open(hosts_file, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        # 查找并删除包含域名的行
        lines = content.splitlines()
        new_lines = []
        skip_next = False
        removed_count = 0
        
        for line in lines:
            if "Added by MTGA GUI" in line:
                skip_next = True
                continue
            if skip_next and domain in line:
                skip_next = False
                removed_count += 1
                continue
            new_lines.append(line)
        
        if removed_count > 0:
            # 写回文件（使用权限）
            new_content = '\n'.join(new_lines)
            if write_hosts_file_with_permission(hosts_file, new_content, encoding, log_func):
                log_func(f"hosts 文件已重置，删除了 {removed_count} 个 {domain} 条目")
            else:
                return False
        else:
            log_func(f"hosts 文件中未找到 {domain} 条目")
        
        return True
        
    except Exception as e:
        log_func(f"删除 hosts 条目失败: {e}")
        return False


def open_hosts_file(log_func=print):
    """
    根据平台打开 hosts 文件
    
    参数:
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    hosts_file = get_hosts_file_path()
    
    try:
        if os.name == 'nt':  # Windows
            # Windows 使用记事本打开
            subprocess.run(['notepad', hosts_file], check=True)
            log_func("已使用记事本打开 hosts 文件")
        elif sys.platform == 'darwin':  # macOS
            # macOS 使用默认文本编辑器打开
            subprocess.run(['open', '-t', hosts_file], check=True)
            log_func("已使用默认文本编辑器打开 hosts 文件")
        else:  # Linux
            # Linux 尝试使用常见的文本编辑器
            editors = ['gedit', 'nano', 'vim']
            for editor in editors:
                try:
                    subprocess.run([editor, hosts_file], check=True)
                    log_func(f"已使用 {editor} 打开 hosts 文件")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            else:
                log_func("未找到合适的文本编辑器")
                return False
        
        return True
        
    except Exception as e:
        log_func(f"打开 hosts 文件失败: {e}")
        return False


def modify_hosts_file(domain="api.openai.com", action="add", ip="127.0.0.1", log_func=print):
    """
    修改 hosts 文件的主函数
    
    参数:
        domain: 域名
        action: 操作类型 ("add", "remove", "backup", "restore")
        ip: IP 地址（仅在 action="add" 时使用）
        log_func: 日志输出函数
        
    返回:
        成功返回 True，失败返回 False
    """
    action_names = {
        'add': '添加条目',
        'remove': '删除条目', 
        'backup': '备份文件',
        'restore': '还原文件'
    }
    
    log_func(f"开始执行 hosts 文件操作: {action_names.get(action, action)}")
    
    if action == "backup":
        return backup_hosts_file(log_func)
    elif action == "restore":
        return restore_hosts_file(log_func)
    elif action == "add":
        return add_hosts_entry(domain, ip, log_func)
    elif action == "remove":
        return remove_hosts_entry(domain, log_func)
    else:
        log_func(f"错误: 不支持的操作类型: {action}")
        return False
