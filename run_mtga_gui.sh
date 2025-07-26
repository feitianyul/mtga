#!/bin/bash

# 设置脚本编码为UTF-8
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否为root权限
check_admin() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "检测到以root权限运行"
        return 0
    else
        print_info "当前以普通用户权限运行"
        # 对于macOS，某些操作可能需要sudo权限，但不强制要求root
        return 1
    fi
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
print_info "脚本目录: $SCRIPT_DIR"

# 检查uv是否已安装
check_uv() {
    if command -v uv &> /dev/null; then
        print_success "检测到uv已安装"
        return 0
    else
        return 1
    fi
}

# 安装uv
install_uv() {
    print_info "uv未安装，开始自动安装uv..."
    print_info "正在通过curl安装uv，请稍候..."
    
    # 使用官方安装脚本
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        print_success "uv安装成功！"
        
        # 添加可能的uv安装路径到当前会话的PATH
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        
        # 如果安装脚本提示了env文件，则source它
        if [[ -f "$HOME/.local/bin/env" ]]; then
            source "$HOME/.local/bin/env" 2>/dev/null || true
        fi
        
        # 重新加载shell配置
        if [[ -f "$HOME/.zshrc" ]]; then
            source "$HOME/.zshrc" 2>/dev/null || true
        fi
        if [[ -f "$HOME/.bashrc" ]]; then
            source "$HOME/.bashrc" 2>/dev/null || true
        fi
        
        # 再次检查uv是否可用
        if command -v uv &> /dev/null; then
            print_success "uv现在可用: $(which uv)"
            return 0
        else
            print_error "uv安装后仍无法找到，请手动将 $HOME/.local/bin 或 $HOME/.cargo/bin 添加到PATH环境变量中"
            print_error "或重新启动终端窗口"
            return 1
        fi
    else
        print_error "uv安装失败"
        return 1
    fi
}

# 设置路径变量
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_ACTIVATE="$VENV_DIR/bin/activate"
OPENSSL_DIR="$SCRIPT_DIR/openssl"

# 检查并创建虚拟环境
setup_venv() {
    # 切换到脚本目录
    cd "$SCRIPT_DIR" || exit 1
    
    if [[ ! -f "$VENV_PYTHON" ]]; then
        print_info "虚拟环境不存在，开始创建..."
        
        # 使用uv安装Python 3.13
        print_info "正在安装Python 3.13..."
        if ! uv python install 3.13; then
            print_error "Python 3.13安装失败"
            exit 1
        fi
        
        # 创建虚拟环境
        print_info "正在创建虚拟环境..."
        if ! uv venv --python 3.13; then
            print_error "创建虚拟环境失败"
            exit 1
        fi
        
        # 同步依赖
        print_info "正在同步依赖..."
        if ! uv sync; then
            print_error "依赖同步失败"
            exit 1
        fi
        
        print_success "虚拟环境和依赖安装完成！"
    else
        print_success "虚拟环境已存在"
        
        # 检查依赖是否需要更新
        print_info "检查依赖状态..."
        if ! uv sync --frozen; then
            print_warning "依赖可能需要更新，正在同步..."
            if ! uv sync; then
                print_error "依赖同步失败"
                exit 1
            fi
            print_success "依赖同步完成！"
        else
            print_success "依赖状态正常"
        fi
    fi
}

# 检查OpenSSL
check_openssl() {
    # 在macOS上，优先使用系统自带的openssl或通过Homebrew安装的openssl
    if command -v openssl &> /dev/null; then
        print_success "检测到系统OpenSSL: $(which openssl)"
        return 0
    elif [[ -f "$OPENSSL_DIR/openssl" ]]; then
        print_success "检测到项目OpenSSL: $OPENSSL_DIR/openssl"
        export PATH="$OPENSSL_DIR:$PATH"
        return 0
    else
        print_error "OpenSSL不存在"
        print_info "请安装OpenSSL: brew install openssl"
        print_info "或确保项目目录下的openssl文件存在"
        return 1
    fi
}

# 检查主程序
check_main_program() {
    if [[ ! -f "$SCRIPT_DIR/mtga_gui.py" ]]; then
        print_error "主程序不存在: $SCRIPT_DIR/mtga_gui.py"
        print_error "请确保程序文件完整"
        return 1
    else
        print_success "主程序文件存在"
        return 0
    fi
}

# 主函数
main() {
    echo "===================================="
    echo "MTGA GUI 启动器 (macOS)"
    echo "===================================="
    
    # 预先设置可能的uv路径到PATH
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    # 检查管理员权限
    check_admin
    
    # 检查并安装uv
    if ! check_uv; then
        if ! install_uv; then
            exit 1
        fi
    fi
    
    # 设置虚拟环境
    setup_venv
    
    # 检查OpenSSL
    if ! check_openssl; then
        exit 1
    fi
    
    # 检查主程序
    if ! check_main_program; then
        exit 1
    fi
    
    # 设置环境变量
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    print_info "正在启动程序，请稍候..."
    
    # 切换到脚本目录并使用uv运行程序（自动使用虚拟环境）
    cd "$SCRIPT_DIR" || exit 1
    
    # 运行程序（需要sudo权限）
    print_info "程序需要管理员权限来修改网络设置，将提示输入密码..."
    if sudo uv run python "$SCRIPT_DIR/mtga_gui.py"; then
        print_success "程序正常退出"
    else
        exit_code=$?
        print_error "程序异常退出，错误代码: $exit_code"
        echo "按任意键继续..."
        read -n 1 -s
        exit $exit_code
    fi
}

# 运行主函数
main "$@"