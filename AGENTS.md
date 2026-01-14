# 仓库指南

## 项目结构与模块组织
- `mtga_gui.py` 负责环境初始化、启动装配与 GUI 入口协调，调用 `modules/ui` 构建界面。
- `modules/` 采用分层结构：`ui/` 负责界面与布局，`actions/` 编排用户操作，`services/` 作为副作用边界，领域模块落在 `cert/hosts/network/proxy/update`，基础设施在 `runtime/` 与 `platform/`。
- 文档位于 `docs/`；打包资源在 `mac/`、`helper-tool/`、`icons/`，诊断脚本（`test_*.py`、`debug_test.py`）放在仓库根目录。

## 构建、测试与开发命令
- 任何 Python 变更：必须运行 `pyright` 与 `ruff check .`。
- 修改 YAML：必须运行 `yamllint <filename>`。
- Linux：先设置 `UV_CACHE_DIR="$PWD/.uv_cache"`，再用 `uv run` 调用。
- macOS/Windows：不要用 `uv`，改用虚拟环境：
  - `./.venv/bin/python -m pyright` 或 `.\.venv\Scripts\python -m pyright`
  - etc.
- `uv sync --project .` 安装运行时依赖；在调用 Nuitka 打包脚本前附加 `--group win-build` 或 `--group mac-build`。
- `python mtga_gui.py --debug` 以详细日志启动 GUI；`./run_mtga_gui.sh`（macOS）与 `run_mtga_gui.bat`（Windows）封装了依赖同步与提权步骤。
- `./build_mac_app.sh` 生成位于 `dist-onefile/` 的 `.app` 包；`build_onefile.bat` 生成 Windows 可分发包。

## 编码风格与命名约定
- 目标 Python 3.13，使用四空格缩进，并遵循 PEP 8 命名（函数 `snake_case`、类 `CamelCase`、常量全大写）。
- 保持模块导入位于文件顶部，并按照 `setup_environment()` 的方式保护平台相关逻辑，避免启动回归。
- 更新 YAML schema 时同步到本地化文档，并保证现有 `config_groups` 的向后兼容。

## 测试指引
- `uv run python test_target_api.py` 用于验证远程 API 兼容性；请在本地替换占位符，勿提交任何机密信息。
- GUI 检查在 `test_clipboard.py` 与 `test_tkinter_gui.py`；在你修改的操作系统上运行，并在 PR 中总结异常。
- 发布安装包前，启动生成的 `.exe` 或 `.app`，确认打包资源、TLS 资料与 hosts 修改仍能生效。

## 提交与 PR 指南
- 遵循历史中的 `type(scope): summary` 提交风格（如 `feat(mac):`、`ci(workflow):`、`docs:`）；每个提交聚焦单一主题，除非正式发布否则不要提交生成的二进制文件。
- PR 需说明用户影响、列出手动或自动测试、关联相关问题，并在 GUI 或安装流程更新时附上截图。
- 涉及安全敏感内容（证书处理、代理路由、entitlements）时请标注并描述缓解措施，方便评审快速评估风险。

## 安全与配置提示
- 不要提交 CA 私钥、用户证书或 `~/.mtga/` 产物；使用辅助脚本完成每台机器的配置。
- 示例配置应放在 `docs/` 且遮蔽令牌。鼓励贡献者通过代理设置映射模型，而不是硬编码 ID。
- 变更端口或沙箱 entitlements 时，记得同步更新 shell 启动脚本与 `mac/entitlements.plist`，以保持公证一致。
