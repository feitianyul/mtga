@echo off
chcp 65001
setlocal enabledelayedexpansion

:: 设置标题
title MTGA GUI 启动器

:: 设置颜色
color 0A

:: 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: 检查uv是否已安装
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo uv未安装，开始自动安装uv...
    echo 正在通过PowerShell安装uv，请稍候...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %ERRORLEVEL% neq 0 (
        echo uv安装失败，错误代码: %ERRORLEVEL%
        pause
        exit /b 1
    )
    echo uv安装成功！
    
    :: 刷新环境变量
    call refreshenv >nul 2>nul
    
    :: 再次检查uv是否可用
    where uv >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo 警告: uv安装后仍无法找到，请重新启动命令行窗口
        echo 或手动将uv添加到PATH环境变量中
        pause
        exit /b 1
    )
)

echo 检测到uv已安装

:: 设置Python虚拟环境路径
set "VENV_DIR=%SCRIPT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

:: 设置OpenSSL路径
set "OPENSSL_DIR=%SCRIPT_DIR%\openssl"

:: 检查虚拟环境是否存在
if not exist "%VENV_PYTHON%" (
    echo 虚拟环境不存在，开始创建...
    
    :: 使用uv安装Python 3.13
    echo 正在安装Python 3.13...
    uv python install 3.13
    if %ERRORLEVEL% neq 0 (
        echo Python 3.13安装失败
        pause
        exit /b 1
    )
    
    :: 创建虚拟环境
    echo 正在创建虚拟环境...
    uv venv --python 3.13
    if %ERRORLEVEL% neq 0 (
        echo 创建虚拟环境失败
        pause
        exit /b 1
    )
    
    :: 同步依赖
    echo 正在同步依赖...
    uv sync
    if %ERRORLEVEL% neq 0 (
        echo 依赖同步失败
        pause
        exit /b 1
    )
    
    echo 虚拟环境和依赖安装完成！
)

:: 检查OpenSSL是否存在
if not exist "%OPENSSL_DIR%\openssl.exe" (
    echo 错误: OpenSSL不存在: %OPENSSL_DIR%\openssl.exe
    echo 请确保OpenSSL已正确安装。
    pause
    exit /b 1
)

:: 检查主程序是否存在
if not exist "%SCRIPT_DIR%\mtga_gui.py" (
    echo 错误: 主程序不存在: %SCRIPT_DIR%\mtga_gui.py
    echo 请确保程序文件完整。
    pause
    exit /b 1
)

:: 设置环境变量
set "PATH=%OPENSSL_DIR%;%PATH%"
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

echo ====================================
echo MTGA GUI 启动器
echo ====================================
echo 正在启动程序，请稍候...

:: 使用uv运行程序（自动使用虚拟环境）
uv run python "%SCRIPT_DIR%\mtga_gui.py"

:: 如果程序异常退出，暂停显示错误信息
if %ERRORLEVEL% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %ERRORLEVEL%
    pause
)

endlocal