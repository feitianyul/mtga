# Repository Guidelines

## 项目结构与模块组织
- `app/`：Nuxt 前端入口，当前从 `app/app.vue` 渲染页面。
- `public/`：静态资源目录（图标、图片等）。
- `src-tauri/`：Tauri 后端与桌面打包配置，关键文件包括 `src-tauri/src/main.rs`、`src-tauri/src/lib.rs`、`src-tauri/Cargo.toml` 与 `src-tauri/tauri.conf.json`。
- `src-tauri/mtga-app/`：Python 后端源码（`__init__.py`、`__main__.py`），通过 `pytauri-wheel` 绑定 Tauri，无需手写 Rust glue 代码。
- `src-tauri/pyproject.toml`、`src-tauri/uv.lock`、`src-tauri/.venv/`：Python 依赖与虚拟环境配置。
- `src-tauri/icons/` 与 `src-tauri/capabilities/`：桌面图标与权限能力定义。
- `nuxt.config.ts`、`tsconfig.json`：前端构建与类型配置。

## 构建、测试与开发命令
优先使用 `pnpm`（已有 `pnpm-lock.yaml`），常用命令如下：
- `pnpm install`：安装依赖并触发 `nuxt prepare`。
- `pnpm dev`：启动前端开发服务器（默认 `http://localhost:3000`）。
- `pnpm build`：构建生产包；`pnpm preview` 本地预览。
- `pnpm generate`：生成静态站点输出。
- `pnpm tauri dev` / `pnpm tauri build`：启动或打包桌面端（依赖 `src-tauri/` 配置）。
- `uv sync --project .`：在 `src-tauri/` 安装 Python 运行时依赖（依赖由 uv 管理）。

## 编码风格与命名约定
- Vue 单文件组件保持 2 空格缩进，遵循 Nuxt/Vue 默认结构。
- `package.json` 为 ESM（`"type": "module"`），使用 `import` 语法。
- Python 目标版本为 3.13（见 `src-tauri/pyproject.toml`），使用 4 空格缩进与 PEP 8 命名。
- Rust 代码位于 `src-tauri/src/`，沿用 `rustfmt` 默认风格与 `snake_case` 命名。

## 测试指引
- `package.json` 未配置 `test` 脚本，当前无固定前端测试框架。
- 如新增 Rust 测试，可在 `src-tauri/` 运行 `cargo test` 并在 PR 中说明覆盖范围。

## 交付前质量检查
- 任何 Python 变更：必须运行 `pyright` 与 `ruff check .`。
- 修改 YAML：必须运行 `yamllint <filename>`。
- Linux：先设置 `UV_CACHE_DIR="$PWD/.uv_cache"`，再用 `uv run` 调用。
- macOS/Windows：不要用 `uv`，改用虚拟环境：
  - `./.venv/bin/python -m pyright` 或 `.\.venv\Scripts\python -m pyright`
  - etc.

## 提交与 PR 指南
- 提交信息采用 Conventional Commits：`feat: ...`、`feat(tauri): ...`、`chore: ...`。
- PR 需说明变更目的、影响范围与验证方式；涉及 UI 或 Tauri 配置时附截图与说明。

## 安全与配置提示
- 变更 `src-tauri/tauri.conf.json` 或 `src-tauri/capabilities/` 时需明确权限影响。
- 避免提交生成产物：`node_modules/`、`src-tauri/target/`、`dist/`、本地 `.venv/`。
