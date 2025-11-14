# 交付前检查
- 必须运行 `UV_CACHE_DIR="$PWD/.uv_cache" uv run ruff check .` 与 `UV_CACHE_DIR="$PWD/.uv_cache" uv run pyright`，确保零报错。
- 如涉及 API/代理功能，使用 `UV_CACHE_DIR="$PWD/.uv_cache" uv run python test_target_api.py`（替换私有参数）验证远端兼容性。
- GUI 改动需在当前操作系统上运行 `UV_CACHE_DIR="$PWD/.uv_cache" uv run python test_clipboard.py` 或 `test_tkinter_gui.py` 并记录异常。
- 打包改动需执行相应 build 脚本并在生成的 `.exe/.app` 上手动验证证书、hosts 与代理流程。