# MTGA GUI macOS 启动脚本

本项目为 MTGA GUI 提供了适配 macOS 系统的启动脚本，基于原有的 Windows 批处理脚本进行了完整的移植和优化。

## 脚本文件

- `run_mtga_gui.sh` - 中文版启动脚本
- `run_mtga_gui_en.sh` - 英文版启动脚本

## 主要功能

### 1. 权限检查
- 自动检测当前运行权限
- 提示是否以 root 权限运行
- 对于 macOS，不强制要求 root 权限

### 2. 依赖管理
- 自动检测 `uv` 包管理器是否已安装
- 如未安装，自动通过官方脚本安装 `uv`
- 自动刷新环境变量和 PATH 设置

### 3. Python 环境
- 自动安装 Python 3.13
- 创建项目专用的虚拟环境
- 同步项目依赖包

### 4. OpenSSL 支持
- 优先使用系统自带的 OpenSSL
- 支持通过 Homebrew 安装的 OpenSSL
- 回退到项目目录下的 OpenSSL

### 5. 程序启动
- 自动设置环境变量
- 使用 `uv run` 启动主程序
- 提供详细的错误信息和退出状态

## 使用方法

1. **赋予执行权限**（首次使用）：
   ```bash
   chmod +x run_mtga_gui.sh
   chmod +x run_mtga_gui_en.sh
   ```

2. **运行脚本**：
   ```bash
   # 中文版
   ./run_mtga_gui.sh
   
   # 英文版
   ./run_mtga_gui_en.sh
   ```

   **注意**：程序需要管理员权限来修改网络设置，运行时会提示输入密码。

### 方法二：通过 bash 运行

```bash
# 中文版
bash run_mtga_gui.sh

# 英文版
bash run_mtga_gui_en.sh
```

## 系统要求

- macOS 10.15 或更高版本
- 网络连接（用于下载 uv 和 Python）
- 足够的磁盘空间（约 500MB 用于 Python 环境）

## 可选依赖

### OpenSSL
如果系统没有 OpenSSL，建议通过 Homebrew 安装：

```bash
brew install openssl
```

### uv 包管理器
脚本会自动安装，但也可以手动预安装：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 故障排除

### 1. 权限问题
如果遇到权限错误，可以尝试：

```bash
sudo ./run_mtga_gui.sh
```

### 2. uv 安装失败
手动安装 uv：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc  # 或 source ~/.bashrc
```

### 3. Python 安装失败
确保有足够的磁盘空间和网络连接，或手动安装 Python 3.13：

```bash
brew install python@3.13
```

### 4. OpenSSL 问题
安装 Homebrew 版本的 OpenSSL：

```bash
brew install openssl
```

## 与 Windows 版本的差异

1. **权限管理**：macOS 版本不强制要求 root 权限
2. **路径分隔符**：使用 Unix 风格的路径分隔符
3. **虚拟环境**：使用 `bin/python` 而非 `Scripts/python.exe`
4. **OpenSSL**：优先使用系统或 Homebrew 版本
5. **颜色输出**：添加了彩色终端输出支持
6. **错误处理**：更详细的错误信息和状态提示

## 注意事项

- 首次运行可能需要较长时间（下载和安装依赖）
- 确保网络连接稳定
- 某些操作可能需要输入管理员密码
- 脚本会自动处理环境变量设置

## 技术细节

脚本采用了以下技术特性：

- **错误处理**：完整的错误检查和退出状态管理
- **颜色输出**：使用 ANSI 颜色代码提供友好的用户界面
- **模块化设计**：将功能拆分为独立的函数
- **环境检测**：智能检测系统环境和依赖状态
- **自动恢复**：在可能的情况下自动修复环境问题

---

如有问题，请检查终端输出的错误信息，或参考上述故障排除部分。