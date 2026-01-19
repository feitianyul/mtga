@echo off
chcp 65001

echo 正在使用 Nuitka 构建独立版本...
echo 这可能需要较长时间（约30分钟），请耐心等待...
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo 错误：虚拟环境不存在，请先运行 uv sync --group win-build 安装依赖
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
if not exist "dist-standalone" mkdir dist-standalone

echo 正在构建独立版本 (mtga_gui.py)...

REM 使用 uv 运行 Nuitka 构建独立版本
uv run --python .venv\Scripts\python.exe nuitka ^
    --standalone ^
    --msvc=latest ^
    --show-progress ^
    --show-memory ^
    --output-dir=dist-standalone ^
    --output-filename=MTGA_GUI.exe ^
    --include-data-files=ca/README.md=ca/README.md ^
    --include-data-files=ca/api.openai.com.cnf=ca/api.openai.com.cnf ^
    --include-data-files=ca/api.openai.com.subj=ca/api.openai.com.subj ^
    --include-data-files=ca/genca.sh=ca/genca.sh ^
    --include-data-files=ca/gencrt.sh=ca/gencrt.sh ^
    --include-data-files=ca/google.cnf=ca/google.cnf ^
    --include-data-files=ca/google.subj=ca/google.subj ^
    --include-data-files=ca/openssl.cnf=ca/openssl.cnf ^
    --include-data-files=ca/pixiv.cnf=ca/pixiv.cnf ^
    --include-data-files=ca/pixiv.subj=ca/pixiv.subj ^
    --include-data-files=ca/v3_ca.cnf=ca/v3_ca.cnf ^
    --include-data-files=ca/v3_req.cnf=ca/v3_req.cnf ^
    --include-data-files=ca/youtube.cnf=ca/youtube.cnf ^
    --include-data-files=ca/youtube.subj=ca/youtube.subj ^
    --include-data-files=openssl/openssl.exe=openssl/openssl.exe ^
    --include-data-files=openssl/libcrypto-3-x64.dll=openssl/libcrypto-3-x64.dll ^
    --include-data-files=openssl/libssl-3-x64.dll=openssl/libssl-3-x64.dll ^
    --windows-icon-from-ico=icons/f0bb32_bg-black.ico ^
    --enable-plugin=tk-inter ^
    --remove-output ^
    --windows-console-mode=disable ^
    --include-package=modules ^
    --windows-uac-admin ^
    mtga_gui.py

echo.
if %ERRORLEVEL% equ 0 (
    echo ✅ 独立版本构建完成！
    echo 可执行文件位于：dist-standalone\mtga_gui.dist\MTGA_GUI.exe
    echo.
    echo 主要改进:
    echo • ✅ 解决了多进程架构问题
    echo • ✅ 消除了虚拟环境依赖
    echo • ✅ 统一了资源路径管理
    echo • ✅ 代理服务器使用线程模式
    echo • ✅ 支持 Nuitka 打包环境检测
    echo.
) else (
    echo ❌ 构建失败，返回码: %ERRORLEVEL%
)

pause