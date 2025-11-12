@echo off
chcp 65001 >nul

REM ========== Probe 构建配置 ==========
set "PROBE_ENTRY=tests\nuitka_probe_app.py"
set "PROBE_OUTPUT_DIR=dist-onefile"
set "PROBE_VERSION=0.0.0-probe"
REM ====================================

echo [probe] 当前工作目录: %CD%

REM 参数：1=MSVC 目录（可选），2=版本号（可选），3=入口文件（可选）
if not "%~1"=="" (
    set "VC_BUILD_DIR=%~1"
)
if not "%~2"=="" (
    set "PROBE_VERSION=%~2"
)
if not "%~3"=="" (
    set "PROBE_ENTRY=%~3"
)

set "PROBE_EXE_NAME=MTGA_GUI-v%PROBE_VERSION%-x64.exe"

REM 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [probe] 错误：虚拟环境不存在，请先运行 uv sync --extra win-build
    if defined GITHUB_ACTIONS (
        exit /b 1
    ) else (
        pause
        exit /b 1
    )
)

REM 入口脚本检查
if not exist "%PROBE_ENTRY%" (
    echo [probe] 错误：入口文件不存在：%PROBE_ENTRY%
    if defined GITHUB_ACTIONS (
        exit /b 1
    ) else (
        pause
        exit /b 1
    )
)

REM MSVC 目录检查（与主构建脚本保持一致）
if defined VC_BUILD_DIR (
    if exist "%VC_BUILD_DIR%" (
        echo [probe] 使用外部提供的 MSVC 目录：%VC_BUILD_DIR%
    ) else (
        echo [probe] 错误：传入的 MSVC 目录不存在：%VC_BUILD_DIR%
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
        echo [probe] 找到 Visual Studio 工具链目录：%VC_BUILD_DIR%
    ) else (
        echo [probe] 错误：未找到可用的 Visual Studio 工具链
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
if not exist "%PROBE_OUTPUT_DIR%" mkdir "%PROBE_OUTPUT_DIR%"

set "EXPECTED_EXE=%PROBE_OUTPUT_DIR%\%PROBE_EXE_NAME%"
if exist "%EXPECTED_EXE%" del /f "%EXPECTED_EXE%" >nul 2>nul

echo [probe] 使用入口：%PROBE_ENTRY%
echo [probe] 目标版本：%PROBE_VERSION%
echo [probe] 输出路径：%EXPECTED_EXE%

uv run --python .venv\Scripts\python.exe nuitka ^
    --onefile ^
    --msvc=latest ^
    --assume-yes-for-downloads ^
    --output-dir=%PROBE_OUTPUT_DIR% ^
    --output-filename=%PROBE_EXE_NAME% ^
    "%PROBE_ENTRY%"

if %ERRORLEVEL% neq 0 goto PROBE_BUILD_FAIL

set "WAIT_ATTEMPTS=0"
set "ABS_EXPECTED_EXE="

:WAIT_PROBE_EXE
if exist "%EXPECTED_EXE%" (
    for %%I in ("%EXPECTED_EXE%") do set "ABS_EXPECTED_EXE=%%~fI"
    goto REPORT_PROBE_SUCCESS
)
if %WAIT_ATTEMPTS% GEQ 15 (
    goto REPORT_PROBE_FAILURE
)
set /a WAIT_ATTEMPTS+=1
timeout /t 2 /nobreak >nul
goto WAIT_PROBE_EXE

:REPORT_PROBE_SUCCESS
echo [probe] ✅ 构建完成，产物：%ABS_EXPECTED_EXE%
if defined GITHUB_ENV (
    >>"%GITHUB_ENV%" echo PROBE_EXE_PATH=%ABS_EXPECTED_EXE%
)
goto AFTER_PROBE_RESULT

:REPORT_PROBE_FAILURE
echo [probe] ❌ 构建完成但未找到产物，请检查 %PROBE_OUTPUT_DIR%
dir "%PROBE_OUTPUT_DIR%"
if defined GITHUB_ACTIONS (
    exit /b 1
) else (
    pause
    exit /b 1
)

:AFTER_PROBE_RESULT

goto END_PROBE

:PROBE_BUILD_FAIL
echo [probe] ❌ 构建失败，返回码：%ERRORLEVEL%
if defined GITHUB_ACTIONS (
    exit /b %ERRORLEVEL%
) else (
    pause
    exit /b %ERRORLEVEL%
)

:END_PROBE

if defined GITHUB_ACTIONS (
    goto :EOF
)

pause
