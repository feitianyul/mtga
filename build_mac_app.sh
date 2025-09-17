#!/bin/bash

# 设置UTF-8编码
export LC_ALL=en_US.UTF-8

# ========== 版本配置 ==========
VERSION="1.2.0"
# ================================

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

echo "正在使用 Nuitka 构建 macOS 应用包..."
echo "这可能需要较长时间，请耐心等待..."
echo

# 检查虚拟环境是否存在
if [[ ! -f ".venv/bin/python" ]]; then
    print_error "虚拟环境不存在，请先运行 uv sync --extra mac-build 安装依赖"
    exit 1
fi

print_success "找到虚拟环境: .venv/bin/python"

# 检查是否安装了 Xcode Command Line Tools
if ! command -v clang &> /dev/null; then
    print_error "未找到 clang，请先安装 Xcode Command Line Tools:"
    print_error "xcode-select --install"
    exit 1
fi

print_success "找到 clang 编译器"

# 检查是否安装了 Nuitka
if ! .venv/bin/python -c "import nuitka" &> /dev/null; then
    print_error "Nuitka 未安装，请先运行 uv sync --extra mac-build 安装依赖"
    print_warning "如果仍然出现问题，请手动安装: uv add nuitka"
    exit 1
fi

print_success "找到 Nuitka"

# 创建输出目录
if [[ ! -d "dist-onefile" ]]; then
    mkdir dist-onefile
    print_success "创建输出目录: dist-onefile"
fi

print_info "正在构建 macOS 应用包 (mtga_gui.py)..."

# 使用 uv 运行 Nuitka 构建 macOS 应用包
# 设置编码环境变量，确保 UTF-8 处理
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8

uv run --python .venv/bin/python nuitka \
    --standalone \
    --macos-create-app-bundle \
    --show-progress \
    --show-memory \
    --output-dir=dist-onefile \
    --include-data-files=ca/README.md=ca/README.md \
    --include-data-files=ca/api.openai.com.cnf=ca/api.openai.com.cnf \
    --include-data-files=ca/api.openai.com.subj=ca/api.openai.com.subj \
    --include-data-files=ca/genca.sh=ca/genca.sh \
    --include-data-files=ca/gencrt.sh=ca/gencrt.sh \
    --include-data-files=ca/google.cnf=ca/google.cnf \
    --include-data-files=ca/google.subj=ca/google.subj \
    --include-data-files=ca/openssl.cnf=ca/openssl.cnf \
    --include-data-files=ca/pixiv.cnf=ca/pixiv.cnf \
    --include-data-files=ca/pixiv.subj=ca/pixiv.subj \
    --include-data-files=ca/v3_ca.cnf=ca/v3_ca.cnf \
    --include-data-files=ca/v3_req.cnf=ca/v3_req.cnf \
    --include-data-files=ca/youtube.cnf=ca/youtube.cnf \
    --include-data-files=ca/youtube.subj=ca/youtube.subj \
    --macos-app-icon=mac/icon.icns \
    --enable-plugin=tk-inter \
    --macos-target-arch=arm64 \
    --remove-output \
    --disable-console \
    --include-package=modules \
    --macos-app-name="MTGA GUI" \
    --macos-signed-app-name="com.mtga.gui" \
    --macos-app-version="$VERSION" \
    --output-filename=MTGA_GUI-v$VERSION-$(uname -m) \
    mtga_gui.py

# 保存 Nuitka 构建的退出码
build_exit_code=$?

echo
if [[ $build_exit_code -eq 0 ]]; then
    print_success "✅ macOS 应用包构建完成！"

    app_path="dist-onefile/mtga_gui.app"
    
    # 修复权限问题 - 将应用包所有权改为当前用户
    # print_info "修复应用包权限..."
    # current_user=$(whoami)
    # if [[ -d "$app_path" && "$current_user" != "root" ]]; then
    #     sudo chown -R "$current_user:staff" "$app_path"
    #     print_success "权限修复完成"
    # fi

    # 修改 Info.plist 使用启动器作为主可执行文件（已不再需要）
    # 检查 .app 文件是否创建成功
    APP_PATH="dist-onefile/mtga_gui.app"
    if [ -d "$APP_PATH" ]; then
        # 修复 Info.plist 中的 CFBundleIdentifier（如果需要）
        INFO_PLIST="$APP_PATH/Contents/Info.plist"
        if [ -f "$INFO_PLIST" ]; then
            # 检查是否还是无效的 Bundle ID
            if grep -q '<string>MTGA GUI</string>' "$INFO_PLIST"; then
                # 使用 sed 替换无效的 Bundle ID
                sed -i '' 's/<string>MTGA GUI<\/string>/<string>com.mtga.gui<\/string>/' "$INFO_PLIST"
                print_success "已修复 Bundle ID 为标准格式: com.mtga.gui"
            fi
        fi
    fi
    
    print_success "应用包构建完成，无需额外配置"
    print_info "环境变量已在 Python 代码中设置"
    # 应用包构建完成，无需重新签名
    print_success "应用程序包位于：$app_path"
    echo
    print_success "macOS 应用包特点:"
    print_success "• ✅ 标准 macOS .app 应用程序包格式"
    print_success "• ✅ 独立运行，包含所有依赖"
    print_success "• ✅ 启动速度快，无需解压"
    print_success "• ✅ 可直接拖拽到 Applications 文件夹"
    print_success "• ✅ 支持 Spotlight 搜索和系统集成"
    echo
    print_info "安装方法:"
    print_info "1. 双击 .app 文件直接运行"
    print_info "2. 或将 .app 文件拖拽到 /Applications 文件夹"
    print_info "3. 首次运行可能需要在 系统偏好设置 > 安全性与隐私 中允许运行"
    echo
    print_info "创建 DMG 安装包（可选）:"
    print_info "uv run dmgbuild -s mac/dmg_settings.py \"MTGA GUI Installer\" MTGA_GUI-v$VERSION-$(uname -m).dmg"
    echo
else
    print_error "❌ 构建失败，返回码: $build_exit_code"
    print_error "请检查错误信息并确保所有依赖已正确安装"
    print_error "常见问题解决方案:"
    print_error "1. 确保已安装 Xcode Command Line Tools: xcode-select --install"
    print_error "2. 确保已安装 Nuitka: uv add nuitka"
    print_error "3. 检查 Python 版本兼容性"
fi