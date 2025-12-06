## v1.4.0 (Latest)
### :sparkles: 新功能
- feat(proxy): 启动代理时自动修改hosts (187ddfc513f9666a646620dde666203b833314f7)
- feat(macos): 简化macOS证书安装流程并自动设置信任 (b5cf97e0e81685dfbfbcdfc222f9cf5920660c4e)
- feat(证书管理): 添加清除系统CA证书功能 (05994def0e0daa8b7a7c57f78e690b3d82dd1385)
- feat(cert): 添加证书存在性检查功能避免重复生成 (ccbfbee547629a1636b56db7adb249910fe16896)
- feat(更新检查): 优化更新对话框布局并添加前往发布页按钮 (11c812337bdd44cfdcd1a945b0b9fc5cf5abda33)
- feat(gui): 清除CA证书添加确认对话框以可修改变量及避免误操作风险 (3b98f1ecb4527067b70119e2155fdd7bed8fbed8)
- feat(gui): 居中显示对话框以提升用户体验 (170f73c0b30f99116566a54a5033ed971fd88f50)
- feat(gui): 添加全局配置必填项检查功能 (0e35fd3732f1c7e0eb213db9c4b32735646e2a06)
### :bug: 修复
- fix(process): 创建子进程工具模块以避免win端继承无效的stdin句柄 (4fcc18507f90e647fc39f08c8a379f6f656c31d2)
- fix(build): macOS端修复tkhtml库导入失败问题并添加动态库到构建脚本 (6e5fbc5b48ae83a2ee1eef32b35019b651e7a616)
- fix(gui): 提取窗口居中逻辑到独立函数避免macOS闪屏问题 (16d15a2e1ab98353f8dbe43fe0f103959e973704)

## v1.3.1
### :sparkles: 新功能
- 暂无新功能
### :bug: 修复
- fix(process): 创建子进程工具模块以避免win端继承无效的stdin句柄 (4fcc18507f90e647fc39f08c8a379f6f656c31d2)

## v1.3.0
### :sparkles: 新功能
- feat(hosts): hosts 文件支持同时写入 IPv4 与 IPv6 映射 (c62d87cfd1c1057266e688c572c443a4d6f89aa2)
- feat(gui): 引入统一线程管理并强化代码规范 (37cec8d1c38d5daf93fb341ba222e4263c59ad98)
- feat(gui): 停止代理时同步还原 hosts (cf23d939ec03f83380596ab554395541c0b95013)
- feat(gui): 适配 macOS 深色模式悬浮提示 (b7f93d8cd760185ebab6f730874a3144ce28e7b0)
- feat(hosts管理): 修复程序退出时hosts记录未清理的问题 (7249afb730b3b3aa7a634db0577a0b63d283b16a)
- feat(macos): 添加持久化提权模块用于 macOS 管理员权限操作 (d935b8b757abc2751684d1eedc4dc896f2c2a5af)
- feat(gui): 添加版本更新检查功能和Markdown渲染器 (15aec5a8fb5e9c16fdd0f62827129a6e17081f61)
- feat(version): 添加构建时版本注入和错误日志记录 (0c0c4fb44b46a84e19853f0353ca9f5e91fc6015)
- feat(字体): 统一应用字体设置并支持自定义渲染字体 (2546b8e2abd87951ddec81fd68d3feab712a293c)
- feat(界面): 调整主窗口布局并添加关于页脚 (c55c30376084052b9e3e1a2c3d73beaa783300db)
### :bug: 修复
- fix(界面): 调整窗口高度并优化关于标签页样式 (99ae59c1530fdcc52c6522c1bb8578c42e120e28)
- fix(resources): 恢复 Windows 打包后的资源路径回退逻辑 (b087d5c50834fe3e633bb83e838b15ac596d069e)
- fix(proxy): 改进代理服务器的启动和关闭逻辑 (5fc9f935e8a346d508babd2721a41bc4a1235051)
- fix(gui): 增强字体选择避免打包后崩溃 (8f3cdb0b8d38d53564a4c8451388c005c64a7c27)
- fix(tkhtml): 修复tkinterweb资源打包和运行时加载问题 (c071f3bc753bb1598a87ccbc79ef0b9062b6efc8)
- fix(ui): 修复macOS上字体显示过小和DPI缩放问题 (9bac52baec9aa597d7aab99e5d880f02bb5b538d)
- fix(mtga_gui): 重构左侧面板布局以使用网格管理 (0e16c93f756dea8a1069bb817a152751a2af2e1b)

## v1.2.1
此版本主要是合并双端，并跑通自动化发版流程

- feat(mac): 添加macOS应用沙箱权限配置和启动优化 (008c04fb55e3e79b5a362c6573063471d3cbd1a6)
- feat(ci): 添加预发布版本的构建工作流 (7e68b706bec0aea0f272cbc2c6d3739b86736a40)
- fix(macos): 修复打包应用的中文编码和启动问题 (47dbeb68cc6a4aad8bdfc05dfca2327b4e7c556f)

## v1.2.0
- 🔄 **重构模型映射架构** - 从"一对一映射"改为"统一映射模型"架构
  - trae端使用统一的映射模型ID，MTGA通过配置组切换实际后端模型
  - 代理服务器支持模型ID映射和MTGA鉴权验证
  - 全局配置支持映射模型ID和MTGA鉴权Key设置
- ⚡ **配置组管理优化** - 重构配置组字段和验证逻辑
  - 配置组名称改为可选，API URL、实际模型ID、API Key改为必填
  - 移除目标模型ID字段，改为全局映射配置
  - 配置组表头重命名，向下兼容旧配置文件
- 🧪 **新增自动化测试功能** - 完整的模型连接测试体系
  - 保存配置后自动测试模型连接 (GET `/v1/models/{模型id}`)
  - 手动测活功能，支持聊天补全测试 (POST `/v1/chat/completions`)
  - 详细测试日志输出，包括响应内容和token消耗统计
- 🎯 **增强用户体验** - 新增测活按钮和详细提示
  - 测活按钮支持tooltip提示，说明token消耗风险
  - 异步测试避免UI阻塞，完善的错误处理机制
  - API Key安全显示（掩码处理）

## v1.1.1
- 🐛 **修复 hosts 修改功能的问题** - 解决 hosts 文件修改时换行符异常的问题

## v1.1.0
- ✨ **新增用户数据管理功能** - 单文件版本支持用户数据持久化存储
  - 数据存储位置：Windows `%APPDATA%\MTGA\`，macOS/Linux `~/.mtga/`
  - 支持备份、还原、清除用户数据
  - 配置文件、SSL证书、hosts备份自动持久化
- 🔧 **优化单文件构建** - 改进 `build_onefile.bat`，支持版本号变量化
- 🎯 **改进用户界面** - 添加配置组列表刷新按钮，优化界面布局
- 📖 **完善文档** - 新增单文件构建指南，更新项目文档

## v1.0.0
- ✅ **适配 Mac OS 端** - 支持 macOS 应用程序安装方式
- 🔄 **默认服务商变更** - 从 DeepSeek 变更为 OpenAI
- 📦 **文件重构** - ds 相关文件重命名为 `*_ds.*` 格式存档
- 🌐 **API URL 格式变更** - 从 `https://your-api.example.com/v1` 变更为 `https://your-api.example.com`