# MTGA GUI DMG 打包说明

本文档说明如何为 MTGA GUI 创建专业的 macOS 安装包（DMG 文件）。

## 文件说明

### 核心脚本
- `mac/create_mac_app.sh` - 创建 macOS 应用程序包（.app）
- `mac/dmg_settings.py` - dmgbuild 配置文件，定义 DMG 的外观和布局

### 资源文件
- `mac/dmg_background.svg` - DMG 安装界面的背景图（SVG 格式）
- `mac/dmg_background.png` - 从 SVG 转换的背景图（PNG 格式）
- `mac/icon.png` - 应用程序图标
- `mac/Info.plist` - macOS 应用程序信息配置
- `mac/MTGA_GUI` - macOS 启动脚本

## 使用步骤

### 0. 生成 Mac 风格图标

**目前的圆角矩形风格为使用 Inkscape 进行的纯 svg 手k，下面流程仅作归档。**

检查 `mac/icon.png` 是否存在，如果不存在，执行以下步骤：

检查 ImageMagick 是否安装：
```bash
magick -version
```

如果未安装，使用 Homebrew 安装：
```bash
brew install imagemagick
```

生成图标：
```bash
# 使用 ImageMagick 将原始图标转换为 Mac 风格的圆角矩形图标
# 根据苹果官方设计规范，图标内容应该居中并留有适当边距以避免被圆角遮罩截断
# 1024x1024 图标的圆角半径为 228px，对于 128x128 图标，圆角半径应为 28.5px
# 添加 10% 的边距（约 13px）确保内容不会被圆角截断
magick icons/f0bb32_bg-black.png -resize 102x102 -alpha set -background none -compose copy -gravity center -extent 128x128 \( +clone -threshold -1 -negate -fill white -draw 'roundrectangle 0,0 127,127 28.5,28.5' \) -alpha off -compose copy_opacity -composite mac/icon.png
```

### 1. 构建应用程序包
```bash
mac/create_mac_app.sh
```

这将创建 `MTGA_GUI.app` 应用程序包，包含：
- 完整的项目文件
- 依赖管理
- 启动脚本
- 图标和配置

### 2. 创建 DMG 安装包

使用现代化的 dmgbuild 工具创建 DMG：

```bash
# 安装构建依赖
uv sync --extra build

# 构建 DMG
uv run dmgbuild -s mac/dmg_settings.py "MTGA GUI Installer" MTGA_GUI-v1.x.x-aarch64.dmg
```

这将创建 `MTGA_GUI-v1.x.x-aarch64.dmg` 文件，具有以下特性：
- 专业的安装界面
- 拖拽安装指导
- 自定义背景图
- 精确的图标位置控制
- 现代化的构建工具链

## DMG 特性

### 安装界面
- **背景图**：使用 `dmg_background.svg` 创建的专业安装指导图
- **布局**：通过 `dmg_settings.py` 精确控制图标位置
- **指导**：清晰的拖拽安装说明
- **品牌**：统一的视觉风格

### 技术特性
- **压缩**：使用 UDZO 格式，最大压缩比
- **兼容性**：支持所有 macOS 版本
- **现代工具**：基于 dmgbuild，无需 GUI 依赖
- **可重现构建**：配置文件化，构建结果一致

## 自定义选项

### 修改背景图
编辑 `dmg_background.svg` 文件来自定义安装界面：
- 修改颜色和样式
- 更改文字内容
- 调整布局位置

### 修改窗口设置
在 `dmg_settings.py` 中可以调整：
- 窗口大小和位置 (`window_rect`)
- 图标大小 (`icon_size`)
- 背景设置 (`background`)
- 图标位置 (`icon_locations`)

## 分发说明

### GitHub Releases 发版
开发者构建完成后，将 DMG 文件上传到 GitHub Releases：
1. 在 GitHub 仓库中创建新的 Release
2. 上传构建好的 `MTGA_GUI_Installer.dmg` 文件
3. 添加版本说明和更新日志
4. 发布 Release 供用户下载

### 用户安装步骤
1. 从 GitHub Releases 下载 `MTGA_GUI_Installer.dmg` 文件
2. 双击 DMG 文件，系统自动挂载安装包到访达
3. 将 `MTGA_GUI.app` 拖拽到 `Applications` 文件夹
4. 从启动台或 Applications 文件夹启动应用程序

## 故障排除

### 依赖安装问题
如果 `uv sync --extra build` 失败：
- 确保已安装 `uv` 包管理器
- 检查网络连接，dmgbuild 需要从 PyPI 下载
- 如遇权限问题，可能需要重新创建虚拟环境

### 背景图问题
- 确保 `dmg_background.png` 文件存在且可读
- 背景图尺寸应与 `window_rect` 中的窗口大小匹配
- SVG 文件修改后需要重新转换为 PNG 格式

### DMG 构建失败
- 检查 `MTGA_GUI.app` 是否存在且完整
- 确保有足够的磁盘空间
- 如遇文件权限问题，检查应用包内文件的权限设置

## 开发说明

### 依赖工具
- `uv` - Python 包管理器
- `dmgbuild` - 现代 DMG 构建工具
- `ds-store` 和 `mac-alias` - dmgbuild 的依赖库

### 配置特性
- 基于 Python 配置文件，易于版本控制
- 支持精确的图标位置控制
- 无需 GUI 环境，适合 CI/CD
- 可重现的构建结果

---

**注意**：所有修改应在项目根目录和 `mac/` 目录中进行，因为 `create_mac_app.sh` 会覆盖应用程序包中的文件。`ds-store` 和 `mac-alias` - dmgbuild 的依赖库

### 配置特性
- 基于 Python 配置文件，易于版本控制
- 支持精确的图标位置控制
- 无需 GUI 环境，适合 CI/CD
- 可重现的构建结果

---

**注意**：所有修改应在项目根目录和 `mac/` 目录中进行，因为 `create_mac_app.sh` 会覆盖应用程序包中的文件。