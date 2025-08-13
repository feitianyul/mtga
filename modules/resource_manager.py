# -*- coding: utf-8 -*-
"""
资源路径管理模块
处理开发环境和打包环境的资源路径问题
"""

import os
import sys
import tempfile
from pathlib import Path


def is_packaged():
    """检测是否在 Nuitka 打包环境中运行"""
    main_module = sys.modules.get('__main__')
    if main_module is not None:
        return hasattr(main_module, '__compiled__')
    return False


def get_base_path():
    """获取程序基础路径"""
    if is_packaged():
        # Nuitka 单文件模式会将资源解压到一个临时目录
        # 尝试多种方式获取正确的资源路径
        
        # 方式1：检查是否有 Nuitka 的临时解压目录
        main_module = sys.modules.get('__main__')
        if main_module and hasattr(main_module, '__file__') and main_module.__file__:
            # 单文件模式下，__main__.__file__ 指向临时解压目录
            main_dir = os.path.dirname(main_module.__file__)
            if os.path.exists(main_dir):
                return main_dir
        
        # 方式2：检查可执行文件同目录（独立模式）
        exe_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exe_dir, 'ca')) or os.path.exists(os.path.join(exe_dir, 'openssl')):
            return exe_dir
        
        # 方式3：检查当前工作目录
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, 'ca')) or os.path.exists(os.path.join(cwd, 'openssl')):
            return cwd
        
        # 默认返回可执行文件目录
        return exe_dir
    else:
        # 开发环境使用项目根目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    
    参数:
        relative_path: 相对于项目根目录的路径
        
    返回:
        绝对路径字符串
    """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)


def get_ca_path():
    """获取 CA 目录路径"""
    return get_resource_path("ca")


def get_openssl_path():
    """获取 OpenSSL 可执行文件路径"""
    if os.name == 'nt':  # Windows
        return get_resource_path("openssl/openssl.exe")
    else:
        # Unix/Linux/macOS 使用系统 OpenSSL
        return "openssl"


def get_openssl_dir():
    """获取 OpenSSL 目录路径"""
    return get_resource_path("openssl")


def get_temp_dir():
    """获取临时文件目录"""
    return tempfile.gettempdir()


def ensure_directory_exists(path):
    """确保目录存在，如果不存在则创建"""
    os.makedirs(path, exist_ok=True)


class ResourceManager:
    """资源管理器类，提供统一的资源访问接口"""
    
    def __init__(self):
        self.base_path = get_base_path()
        self.ca_path = get_ca_path()
        self.openssl_path = get_openssl_path()
        self.openssl_dir = get_openssl_dir()
    
    def get_cert_file(self, domain="api.openai.com"):
        """获取证书文件路径"""
        return os.path.join(self.ca_path, f"{domain}.crt")
    
    def get_key_file(self, domain="api.openai.com"):
        """获取私钥文件路径"""
        return os.path.join(self.ca_path, f"{domain}.key")
    
    def get_ca_cert_file(self):
        """获取 CA 证书文件路径"""
        return os.path.join(self.ca_path, "ca.crt")
    
    def get_ca_key_file(self):
        """获取 CA 私钥文件路径"""
        return os.path.join(self.ca_path, "ca.key")
    
    def get_config_file(self, filename):
        """获取配置文件路径"""
        return os.path.join(self.ca_path, filename)
    
    def check_resources(self):
        """检查必要资源是否存在"""
        missing_resources = []
        
        # 添加调试信息
        debug_info = []
        debug_info.append(f"当前工作目录: {os.getcwd()}")
        debug_info.append(f"基础路径: {self.base_path}")
        debug_info.append(f"CA路径: {self.ca_path}")
        debug_info.append(f"OpenSSL路径: {self.openssl_path}")
        debug_info.append(f"是否打包环境: {is_packaged()}")
        
        # 如果是打包环境，显示额外的调试信息
        if is_packaged():
            debug_info.append(f"可执行文件路径: {sys.executable}")
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, '__file__'):
                debug_info.append(f"主模块文件路径: {main_module.__file__}")
        
        # 打印调试信息
        print("=== 资源路径调试信息 ===")
        for info in debug_info:
            print(info)
        print("=" * 30)
        
        # 检查 CA 目录
        if not os.path.exists(self.ca_path):
            missing_resources.append(f"CA目录: {self.ca_path}")
        
        # 检查 OpenSSL
        if os.name == 'nt' and not os.path.exists(self.openssl_path):
            missing_resources.append(f"OpenSSL可执行文件: {self.openssl_path}")
        
        return missing_resources