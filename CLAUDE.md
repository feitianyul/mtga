# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

MTGA 是一个基于本地代理的 IDE 固定模型服务商解决方案，支持 Windows 和 macOS 平台。项目通过本地代理服务器拦截 IDE 对 OpenAI API 的调用，并转发到用户自定义的 API 服务商。

## 核心架构

### 架构版本
项目提供两个版本：
- **mtga_gui.py** - 原版本（多进程架构，开发环境专用）
- **mtga_gui_v2.py** - 重构版本（单进程模块化架构，支持 Nuitka 打包）

### 重构版本架构（推荐用于生产打包）
- **mtga_gui_v2.py** - 主 GUI 应用程序，单进程架构
- **modules/** - 模块化组件目录
  - `resource_manager.py` - 资源路径管理，支持开发和打包环境
  - `cert_generator.py` - 证书生成模块，内置调用
  - `cert_installer.py` - 证书安装模块，支持多平台
  - `hosts_manager.py` - hosts 文件管理模块
  - `proxy_server.py` - 代理服务器模块，使用线程模式

### 工作原理
1. 通过修改 hosts 文件将 `api.openai.com` 指向本地 (127.0.0.1)
2. 启动本地 HTTPS 代理服务器，监听 443 端口
3. 使用自签名证书处理 SSL 连接
4. 将 IDE 发送的请求转发到用户配置的目标 API 端点

### 架构优势（重构版本）
- **无多进程问题** - 所有功能在主进程中通过模块调用实现
- **无虚拟环境依赖** - 消除了对 `.venv` 目录的硬依赖
- **智能路径管理** - 自动检测开发和打包环境，动态调整资源路径
- **线程化代理** - 代理服务器在后台线程运行，避免子进程问题
- **模块化设计** - 便于维护和打包，支持 Nuitka 编译

## 开发环境设置

### 依赖管理
项目使用 `uv` 作为包管理器，支持 Python 3.13：

```bash
# 安装依赖
uv sync

# 安装构建依赖 (Windows)
uv sync --extra win-build

# 安装构建依赖 (macOS)  
uv sync --extra mac-build
```

### 核心依赖
- Flask - Web 服务器框架
- requests - HTTP 请求库
- PyYAML - 配置文件解析
- tkinter - GUI 界面 (内置)

## 常用命令

### 开发调试

#### 原版本（开发环境）
```bash
# 直接运行 GUI
uv run python mtga_gui.py

# 运行代理服务器 (调试模式)
uv run python trae_proxy.py --debug

# 生成证书
uv run python generate_certs.py
```

#### 重构版本（生产推荐）
```bash
# 直接运行重构版 GUI
uv run python mtga_gui_v2.py

# 使用模块化方式测试各组件
uv run python -c "from modules.cert_generator import generate_certificates; generate_certificates()"
uv run python -c "from modules.cert_installer import install_ca_cert; install_ca_cert()"
```

### Windows 平台
```bash
# 使用批处理脚本启动原版本
run_mtga_gui.bat

# 构建原版本独立可执行文件
build_standalone.bat

# 构建重构版本独立可执行文件（推荐）
build_v2.bat
```

### macOS 平台  
```bash
# 使用 shell 脚本启动
./run_mtga_gui.sh

# 创建 macOS 应用包
cd mac && ./create_mac_app.sh
```

## 构建和打包

### Windows (Nuitka)

#### 重构版本（推荐生产使用）
- 使用 `build_v2.bat` 构建重构版本
- 需要 Visual Studio 2022 和 C++ 构建工具  
- 输出位置: `dist\mtga_gui_v2.dist\MTGA_GUI_v2.exe`
- **解决了所有多进程和路径依赖问题**

#### 原版本（开发测试）
- 使用 `build_standalone.bat` 构建原版本
- 需要 Visual Studio 2022 和 C++ 构建工具
- 输出位置: `dist\mtga_gui.dist\mtga_gui.exe`
- **注意：原版本在 Nuitka 打包后可能出现兼容性问题**

### macOS (应用包)
- 使用 `mac/create_mac_app.sh` 创建应用包
- 支持 DMG 安装包生成
- 自动配置应用图标和启动脚本

## 配置文件

### mtga_config.yaml
项目配置文件，包含：
- 目标 API 端点配置
- 自定义模型 ID 映射
- SSL 证书路径设置

### ca/ 目录
证书相关文件和配置：
- OpenSSL 配置文件 (*.cnf)
- 证书主题配置 (*.subj)  
- Shell 脚本 (genca.sh, gencrt.sh)

## 重要注意事项

### 版本选择建议
- **开发和测试** - 使用 `mtga_gui.py`（原版本）
- **生产打包** - 使用 `mtga_gui_v2.py`（重构版本）
- **Nuitka 编译** - 必须使用重构版本，原版本会出现兼容性问题

### 打包相关问题及解决方案

#### 已解决的问题（重构版本）
- ✅ **多进程子进程找不到 Python 解释器** - 改为模块化直接调用
- ✅ **相对路径依赖失效** - 使用智能资源管理器
- ✅ **虚拟环境路径硬编码** - 消除对 `.venv` 的依赖
- ✅ **临时文件创建复杂** - 简化配置管理流程
- ✅ **代理服务器子进程问题** - 改为后台线程模式

#### 架构对比
| 特性 | 原版本 | 重构版本 |
|-----|--------|----------|
| 证书生成 | 子进程调用 | 模块化直接调用 |
| 代理服务器 | 子进程 + 临时文件 | 后台线程 |
| 路径管理 | 硬编码相对路径 | 智能资源管理器 |
| 虚拟环境依赖 | 必需 | 无依赖 |
| Nuitka 兼容性 | ❌ 有问题 | ✅ 完全兼容 |

### 安全考虑
- 证书私钥文件 (*.key) 包含敏感信息，不应提交到版本控制
- 代理服务器需要管理员权限运行 (监听 443 端口)
- hosts 文件修改需要系统管理员权限

### 开发约定
- GUI 相关代码使用中文注释
- 使用 CRLF 换行符 (Windows 兼容)
- 函数级注释保持中文
- 优先编辑现有文件而非创建新文件

### 测试和验证
- 运行 `test_target_api.py` 验证目标 API 连接
- 检查代理服务器日志确认请求转发正常
- 确认 IDE 中自定义模型配置正确

## 故障排除

### 常见问题
1. **端口冲突** - 检查 443 端口是否被其他服务占用
2. **证书信任** - 确保 CA 证书已正确安装到系统信任存储
3. **权限不足** - 确保以管理员权限运行程序
4. **依赖缺失** - 使用 `uv sync` 重新安装依赖

### 调试模式
使用 `--debug` 参数启动代理服务器获取详细日志：
```bash
uv run python trae_proxy.py --debug
```