# 项目概览
- 名称：MTGA GUI，本地 Tkinter GUI 工具，负责生成/安装代理证书、修改 hosts 并启动 Flask 代理服务器，帮助桌面 IDE 绕过固定模型服务商限制。
- 核心入口为 `mtga_gui.py`，UI 负责调度 `modules/` 中的证书、hosts、代理等子模块；`modules/proxy_server.py` 提供 Flask 反向代理；`modules/*.py` 负责资源管理、证书生成/安装和 hosts 操作。
- 其它重要目录：`docs/` 文档、`mac/` 与 `helper-tool/` 提供打包资源和脚本、`icons/` 图标、`tests/` 与根目录 `test_*.py` 为诊断脚本、`archive/` 存放旧版备份。
- 依赖栈：Python 3.13、Tkinter、Flask/Werkzeug、requests、PyYAML、Nuitka（打包）、dmgbuild（macOS）。
- 资源与配置通过 `modules/resource_manager.py` 抽象，证书文件位于用户目录 `~/.mtga/ca` 等，打包运行需要尊重 `setup_environment()` 的路径设置。