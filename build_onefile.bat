@echo off
chcp 65001

REM ========== 版本配置 ==========
set "VERSION=1.2.0"
REM ================================

echo 正在使用 Nuitka 构建单文件版本...
echo 这可能需要较长时间（约40分钟），请耐心等待...
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo 错误：虚拟环境不存在，请先运行 uv sync --extra win-build 安装依赖
    if defined GITHUB_ACTIONS (
        exit /b 1
    ) else (
        pause
        exit /b 1
    )
)

REM 检查是否存在可用的 Visual Studio MSVC 工具链
if not "%~1"=="" (
    set "VC_BUILD_DIR=%~1"
)

if defined VC_BUILD_DIR (
    if exist "%VC_BUILD_DIR%" (
        echo 使用外部提供的 MSVC 工具链目录：%VC_BUILD_DIR%
    ) else (
        echo 错误：传入的 MSVC 目录不存在：%VC_BUILD_DIR%
        if defined GITHUB_ACTIONS (
            exit /b 1
        ) else (
            pause
            exit /b 1
        )
    )
) else (
    set "PREFERRED_VS_DIR=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build"
    if exist "%PREFERRED_VS_DIR%" (
        set "VC_BUILD_DIR=%PREFERRED_VS_DIR%"
    ) else (
        for %%I in (
            "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build"
            "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build"
            "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build"
            "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build"
            "C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build"
            "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build"
            "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build"
        ) do (
            if not defined VC_BUILD_DIR (
                if exist %%~I (
                    set "VC_BUILD_DIR=%%~I"
                )
            )
        )
    )

    if defined VC_BUILD_DIR (
        echo 找到 Visual Studio 工具链目录：%VC_BUILD_DIR%
    ) else (
        echo 错误：未找到可用的 Visual Studio 工具链，请先安装 Visual Studio（含 MSVC）
        if defined GITHUB_ACTIONS (
            exit /b 1
        ) else (
            pause
            exit /b 1
        )
    )
)

REM 创建输出目录
if not exist "dist-onefile" mkdir dist-onefile

echo 正在构建单文件版本 (mtga_gui.py)...

REM 使用 uv 运行 Nuitka 构建单文件版本
uv run --python .venv\Scripts\python.exe nuitka ^
    --onefile ^
    --msvc=latest ^
    --show-progress ^
    --show-memory ^
    --output-dir=dist-onefile ^
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
    --include-data-files=icons/f0bb32_bg-black.ico=icons/f0bb32_bg-black.ico ^
    --windows-icon-from-ico=icons/f0bb32_bg-black.ico ^
    --enable-plugin=tk-inter ^
    --remove-output ^
    --windows-console-mode=disable ^
    --include-package=modules ^
    --windows-uac-admin ^
    --output-filename=MTGA_GUI-v%VERSION%-x64.exe ^
    mtga_gui.py

echo.
if %ERRORLEVEL% equ 0 (
    set "EXPECTED_EXE=dist-onefile\MTGA_GUI-v%VERSION%-x64.exe"
    if exist "%EXPECTED_EXE%" (
        echo ✅ 单文件版本构建完成！
        echo 可执行文件位于：%EXPECTED_EXE%
    ) else (
        for %%F in ("dist-onefile\*.exe") do (
            if not exist "%EXPECTED_EXE%" (
                echo ⚠️  检测到输出文件 %%~nxF ，重命名为 MTGA_GUI-v%VERSION%-x64.exe
                move "%%~F" "%EXPECTED_EXE%" >nul
            )
        )
        if exist "%EXPECTED_EXE%" (
            echo ✅ 单文件版本构建完成（已重命名）！
            echo 可执行文件位于：%EXPECTED_EXE%
        ) else (
            echo ⚠️  未能找到或重命名生成的可执行文件，请检查 dist-onefile 目录
        )
    )
    echo.
    echo 单文件版本特点:
    echo • ✅ 仅一个 .exe 文件，便于分发
    echo • ✅ 启动时自动解压到临时目录
    echo • ✅ 包含所有依赖，无需额外文件
    echo • ✅ 自动请求管理员权限
    echo • ⚠️  首次运行较慢（需要解压）
    echo.
) else (
    echo ❌ 构建失败，返回码: %ERRORLEVEL%
)

if defined GITHUB_ACTIONS (
    goto :EOF
)

pause
