# UI 迁移总览（Nuxt + Tailwind + daisyUI）

本文件合并原有分析/计划/配置说明，用于指导从 Tkinter UI 迁移到 `app/`。

## 当前进度摘要（便于恢复上下文）
- 已确定 UI 技术选型：Tailwind + daisyUI（基于 daisyUI 5 / Tailwind v4 的 CSS-first 配置方式）。
- 已搭建组件骨架：`AppShell`、`LogPanel`、`FooterActions`、`panels/*`、`tabs/*`、`dialogs/*`。
- 已在 `app/app.vue` 挂载骨架布局：左侧面板 + Tabs，右侧日志面板，底部按钮。
- 交互方式确认：前端通过 `pyInvoke` 调用 Python 后端命令（pytauri-wheel）。

## TODO（下一步执行清单）
- [x] 安装并启用 Tailwind + daisyUI（创建 `app/assets/css/tailwind.css`，在 `nuxt.config.ts` 引入）。
- [ ] `MainTabs` 支持切换并挂载各 Tab 内容（证书/hosts/代理/数据/关于）。
- [ ] `ConfigGroupPanel` 改为可交互：列表数据、选中状态、增删改弹窗。
- [ ] `GlobalConfigPanel` 与 `RuntimeOptionsPanel` 接入真实数据与保存逻辑。
- [ ] `LogPanel` 支持追加日志流（从后端或前端事件）。
- [ ] `UpdateDialog`、确认弹窗完善交互与 HTML 内容渲染。
- [ ] 用 `pyInvoke` 串起最小功能链路（例如 `greet` -> 日志输出）。

## 现有 UI 功能梳理
- **整体布局**：标题 + 左右分栏，左侧操作区，右侧日志滚动面板。
- **配置区**：配置组列表（含新增/修改/删除/上移/下移/测活/刷新）、全局配置（映射模型 ID / MTGA 鉴权 Key）。
- **运行时选项**：调试模式、关闭 SSL 严格模式、强制流模式。
- **功能标签页**：
  - 证书管理：生成 / 安装 / 清除（确认弹窗）
  - hosts 文件：修改 / 备份 / 还原 / 打开
  - 代理操作：启动 / 停止 / 检查网络环境
  - 用户数据管理（仅打包态）：打开目录 / 备份 / 还原 / 清除
  - 关于：版本信息 + 检查更新
- **更新弹窗**：展示 HTML release notes + 跳转发布页

## 迁移目标与组件拆分
- 页面级布局：`AppShell`（标题 + 分栏）
- 主要组件：
  - `ConfigGroupPanel`、`GlobalConfigPanel`、`RuntimeOptionsPanel`
  - `MainTabs` + 各 Tab 组件
  - `LogPanel`、`FooterActions`
  - `UpdateDialog`、`ConfirmDialog`

## 页面骨架建议（目录结构）
```
app/
  app.vue
  components/
    AppShell.vue
    LogPanel.vue
    FooterActions.vue
    panels/
      ConfigGroupPanel.vue
      GlobalConfigPanel.vue
      RuntimeOptionsPanel.vue
    tabs/
      MainTabs.vue
      CertTab.vue
      HostsTab.vue
      ProxyTab.vue
      DataManagementTab.vue
      AboutTab.vue
    dialogs/
      UpdateDialog.vue
      ConfirmDialog.vue
```

## 交互方式（pytauri-wheel）
前端通过 `tauri-plugin-pytauri-api` 调用 Python 后端：
```ts
import { pyInvoke } from "tauri-plugin-pytauri-api";
const msg = await pyInvoke("greet", { name: "bifang" });
```
需要对接的能力包括：配置读写、证书/hosts/代理操作、用户数据管理、更新检查、运行环境标志。

## Tailwind + daisyUI 最小集成（按 daisyUI 5 / Tailwind v4）
依赖（示例 pnpm）：
```
pnpm add -D tailwindcss daisyui
```

`app/assets/css/tailwind.css`：
```css
@import "tailwindcss";
@plugin "daisyui";

/* 主题（可选）：先用 light 作为默认主题 */
@plugin "daisyui" {
  themes: light --default;
}
```

`nuxt.config.ts` 引入样式：
```ts
export default defineNuxtConfig({
  css: ['./app/assets/css/tailwind.css'],
})
```

常用组件类：
- Tabs：`tabs` / `tab`
- Dialog：`modal` / `modal-box`
- Tooltip：`tooltip`
- 表格：`table`
- 表单：`input` / `select` / `checkbox`
- 按钮：`btn` + `btn-primary/secondary`

## 迁移顺序建议
1) 布局 + 日志面板
2) 配置组 / 全局配置 / 运行时选项
3) Tabs 功能区
4) 更新弹窗与确认弹窗
