#!/bin/bash

# 创建 macOS 应用程序包结构的脚本
# 用于构建 MTGA_GUI.app 应用程序包

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

# 获取脚本所在目录的上一级目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
print_info "项目根目录: $SCRIPT_DIR"

# 定义应用程序包路径
APP_DIR="$SCRIPT_DIR/MTGA_GUI.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
PROJECT_DIR="$RESOURCES_DIR/mtga_project"

echo "===================================="
echo "MTGA GUI macOS 应用程序包构建脚本"
echo "===================================="

# 检查必要文件是否存在
print_info "检查必要文件..."
required_files=(
    "$SCRIPT_DIR/mac/Info.plist"
    "$SCRIPT_DIR/mac/MTGA_GUI"
    "$SCRIPT_DIR/icons/f0bb32_bg-black.png"
    "$SCRIPT_DIR/generate_certs.py"
    "$SCRIPT_DIR/mtga_gui.py"
    "$SCRIPT_DIR/pyproject.toml"
    "$SCRIPT_DIR/README.md"
    "$SCRIPT_DIR/run_mtga_gui.sh"
    "$SCRIPT_DIR/trae_proxy.py"
    "$SCRIPT_DIR/uv.lock"
)

required_dirs=(
    "$SCRIPT_DIR/ca"
    "$SCRIPT_DIR/openssl"
)

# 检查文件
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_error "必需文件不存在: $file"
        exit 1
    fi
done

# 检查目录
for dir in "${required_dirs[@]}"; do
    if [[ ! -d "$dir" ]]; then
        print_error "必需目录不存在: $dir"
        exit 1
    fi
done

print_success "所有必需文件和目录检查通过"

# 如果应用程序包已存在，询问是否删除
if [[ -d "$APP_DIR" ]]; then
    print_warning "应用程序包已存在: $APP_DIR"
    read -p "是否删除现有应用程序包并重新创建？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "删除现有应用程序包..."
        rm -rf "$APP_DIR"
        print_success "现有应用程序包已删除"
    else
        print_info "取消操作"
        exit 0
    fi
fi

# 创建应用程序包目录结构
print_info "创建应用程序包目录结构..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"
mkdir -p "$PROJECT_DIR"

if [[ -d "$MACOS_DIR" && -d "$RESOURCES_DIR" && -d "$PROJECT_DIR" ]]; then
    print_success "目录结构创建成功"
else
    print_error "目录结构创建失败"
    exit 1
fi

# 复制 Info.plist 到 Contents 目录
print_info "复制 Info.plist..."
cp "$SCRIPT_DIR/mac/Info.plist" "$CONTENTS_DIR/"
if [[ $? -eq 0 ]]; then
    print_success "Info.plist 复制成功"
else
    print_error "Info.plist 复制失败"
    exit 1
fi

# 复制 MTGA_GUI 可执行文件到 MacOS 目录
print_info "复制 MTGA_GUI 可执行文件..."
cp "$SCRIPT_DIR/mac/MTGA_GUI" "$MACOS_DIR/"
# 确保可执行文件有执行权限
chmod +x "$MACOS_DIR/MTGA_GUI"
if [[ $? -eq 0 ]]; then
    print_success "MTGA_GUI 可执行文件复制成功"
else
    print_error "MTGA_GUI 可执行文件复制失败"
    exit 1
fi

# 复制 icon.png 到 Resources 目录
print_info "复制应用程序图标..."
cp "$SCRIPT_DIR/mac/icon.png" "$RESOURCES_DIR/"
if [[ $? -eq 0 ]]; then
    print_success "应用程序图标复制成功"
else
    print_error "应用程序图标复制失败"
    exit 1
fi

# 复制项目文件到 mtga_project 目录
print_info "复制项目文件..."
project_files=(
    "generate_certs.py"
    "mtga_gui.py"
    "pyproject.toml"
    "README.md"
    "run_mtga_gui.sh"
    "trae_proxy.py"
    "uv.lock"
)

for file in "${project_files[@]}"; do
    print_info "复制 $file..."
    cp "$SCRIPT_DIR/$file" "$PROJECT_DIR/"
    if [[ $? -eq 0 ]]; then
        print_success "$file 复制成功"
    else
        print_error "$file 复制失败"
        exit 1
    fi
done

# 复制项目目录（处理权限问题）
print_info "复制 ca 目录..."
# 创建 ca 目录
mkdir -p "$PROJECT_DIR/ca"
# 复制 ca 目录内容，跳过权限被拒绝的文件
cp -r "$SCRIPT_DIR/ca/"* "$PROJECT_DIR/ca/" 2>/dev/null || {
    print_warning "部分 ca 目录文件因权限问题无法复制，尝试使用 sudo..."
    # 尝试使用 sudo 复制
    if sudo cp -r "$SCRIPT_DIR/ca/"* "$PROJECT_DIR/ca/" 2>/dev/null; then
        print_success "ca 目录复制成功（使用 sudo）"
    else
        print_warning "ca 目录部分文件复制失败，但应用程序包仍可使用"
        # 至少确保有基本的 ca 目录结构
        touch "$PROJECT_DIR/ca/.gitkeep"
    fi
}

print_info "复制 openssl 目录..."
# 创建 openssl 目录
mkdir -p "$PROJECT_DIR/openssl"
# 复制 openssl 目录内容
cp -r "$SCRIPT_DIR/openssl/"* "$PROJECT_DIR/openssl/" 2>/dev/null || {
    print_warning "部分 openssl 目录文件因权限问题无法复制，尝试使用 sudo..."
    if sudo cp -r "$SCRIPT_DIR/openssl/"* "$PROJECT_DIR/openssl/" 2>/dev/null; then
        print_success "openssl 目录复制成功（使用 sudo）"
    else
        print_warning "openssl 目录部分文件复制失败，但应用程序包仍可使用"
        touch "$PROJECT_DIR/openssl/.gitkeep"
    fi
}

# 确保 run_mtga_gui.sh 有执行权限
chmod +x "$PROJECT_DIR/run_mtga_gui.sh"

# 显示应用程序包结构
print_info "应用程序包结构:"
tree "$APP_DIR" 2>/dev/null || find "$APP_DIR" -type f | sort

echo
print_success "===================================="
print_success "macOS 应用程序包构建完成！"
print_success "===================================="
print_success "应用程序包位置: $APP_DIR"
print_info "你现在可以:"
print_info "1. 双击 MTGA_GUI.app 启动应用程序"
print_info "2. 将应用程序拖拽到 Applications 文件夹"
print_info "3. 或者通过 Finder 直接运行"
echo