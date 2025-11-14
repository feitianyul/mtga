# 常用命令
- `UV_CACHE_DIR="$PWD/.uv_cache" uv sync`：安装/同步依赖（所有 `uv` 命令前都要设置缓存目录）。
- `UV_CACHE_DIR="$PWD/.uv_cache" uv run ruff check .`：交付前的 Ruff 静态检查。
- `UV_CACHE_DIR="$PWD/.uv_cache" uv run pyright`：交付前的 Pyright 类型检查。
- `UV_CACHE_DIR="$PWD/.uv_cache" uv run python mtga_gui.py --debug`：以调试日志启动 GUI。
- `./run_mtga_gui.sh`（macOS）或 `run_mtga_gui.bat`（Windows）：包装了依赖同步与提权的 GUI 启动脚本。
- `./build_mac_app.sh`、`build_onefile.bat`、`build_standalone.bat`：macOS/Windows 的打包脚本。
- 诊断：`UV_CACHE_DIR="$PWD/.uv_cache" uv run python test_target_api.py`、`test_clipboard.py`、`test_tkinter_gui.py` 针对 API 与 GUI 功能。