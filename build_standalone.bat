@echo off
chcp 65001

echo 正在使用 Nuitka 构建独立版本...
echo 这可能需要较长时间（约30分钟），请耐心等待...
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo 错误：虚拟环境不存在，请先运行 uv sync --extra win-build 安装依赖
    pause
    exit /b 1
)

REM 检查是否存在 vs 2022
set "VS2022DIR=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build"

if not exist "%VS2022DIR%" (
    echo 错误：未找到 Visual Studio 2022，请先安装 Visual Studio 2022
    pause
    exit /b 1
)else (
    echo 找到 Visual Studio 2022 : %VS2022DIR%
)

REM 创建输出目录
if not exist "dist" mkdir dist

REM 使用 uv 运行 Nuitka 构建独立版本
uv run --python .venv\Scripts\python.exe nuitka ^
    --standalone ^
    --msvc=latest ^
    --show-progress ^
    --show-memory ^
    --output-dir=dist ^
    --include-data-dir=ca=ca ^
    --include-data-files=openssl/openssl.exe=openssl/openssl.exe ^
    --include-data-files=openssl/libcrypto-3-x64.dll=openssl/libcrypto-3-x64.dll ^
    --include-data-files=openssl/libssl-3-x64.dll=openssl/libssl-3-x64.dll ^
    --include-data-files=generate_certs.py=generate_certs.py ^
    --include-data-files=trae_proxy.py=trae_proxy.py ^
    --windows-icon-from-ico=icons/f0bb32_bg-black.ico ^
    --enable-plugin=tk-inter ^
    --remove-output ^
    --windows-console-mode=disable ^
    mtga_gui.py

echo.
echo 构建完成！可执行文件位于：dist\mtga_gui.dist\mtga_gui.exe
pause