# MTGA
<picture>
    <img alt="MTGA" src="https://github.com/BiFangKNT/mtga/blob/gui/icons/hero-img_f0bb32.png?raw=true">
</picture>

[![English](https://img.shields.io/badge/docs-English-purple)](docs/README.en.md) [![简体中文](https://img.shields.io/badge/文档-简体中文-yellow)](README.md) [![日本語](https://img.shields.io/badge/ドキュ-日本語-b7003a)](docs/README.ja.md) [![한국어 문서](https://img.shields.io/badge/docs-한국어-green)](docs/README.ko.md) [![Documentación en Español](https://img.shields.io/badge/docs-Español-orange)](docs/README.es.md) [![Documentation en Français](https://img.shields.io/badge/docs-Français-blue)](docs/README.fr.md) [![Documentação em Português (Brasil)](<https://img.shields.io/badge/docs-Português-purple>)](docs/README.pt.md) [![Dokumentation auf Deutsch](https://img.shields.io/badge/docs-Deutsch-darkgreen)](docs/README.de.md) [![Документация на русском языке](https://img.shields.io/badge/доки-Русский-darkblue)](docs/README.ru.md)

## 简介

 MTGA 是一个基于本地代理的 IDE 固定模型服务商解决方案，适用于 Windows 和 macOS。

 **注意：本项目目前只支持 openai 格式的 api ，请确认。其他格式可以转为 openai 格式后再使用。**



 <details>
  <summary>你什么也看不见~~</summary>
  <br>
  <p>MTGA 即 Make T Great Again !</p>
 </details>

## 目录

* [更新日志](#更新日志)
* [快速开始](#快速开始)
  * [Windows 用户（GUI一键启动方式）](#windows-用户gui一键启动方式)
  * [macOS 用户（应用程序安装）](#macos-用户应用程序安装)
* [从脚本启动](#从脚本启动)
  * [第 0 步：环境准备](#第-0-步环境准备)
    * [Windows](#windows)
      * [第 1 步：生成自签名证书](#第-1-步生成自签名证书)
      * [第 2 步：让 Windows 信任你的 CA 证书](#第-2-步让-windows-信任你的-ca-证书)
      * [第 3 步：修改 Hosts 文件](#第-3-步修改-hosts-文件)
      * [第 4 步：运行本地代理服务器 (Python)](#第-4-步运行本地代理服务器-python)
      * [第 5 步：配置 Trae IDE](#第-5-步配置-trae-ide)
    * [macOS](#macos)
 * [😎 保持更新](#-保持更新)

---

## 更新日志

### v1.1.1 (Latest)
- 🐛 **修复 hosts 修改功能的问题** - 解决 hosts 文件修改时换行符异常的问题

### v1.1.0
- ✨ **新增用户数据管理功能** - 单文件版本支持用户数据持久化存储
  - 数据存储位置：Windows `%APPDATA%\MTGA\`，macOS/Linux `~/.mtga/`
  - 支持备份、还原、清除用户数据
  - 配置文件、SSL证书、hosts备份自动持久化
- 🔧 **优化单文件构建** - 改进 `build_onefile.bat`，支持版本号变量化
- 🎯 **改进用户界面** - 添加配置组列表刷新按钮，优化界面布局
- 📖 **完善文档** - 新增单文件构建指南，更新项目文档

### v1.0.0
- ✅ **适配 Mac OS 端** - 支持 macOS 应用程序安装方式
- 🔄 **默认服务商变更** - 从 DeepSeek 变更为 OpenAI
- 📦 **文件重构** - ds 相关文件重命名为 `*_ds.*` 格式存档
- 🌐 **API URL 格式变更** - 从 `https://your-api.example.com/v1` 变更为 `https://your-api.example.com`

---

## 快速开始

### Windows 用户（GUI一键启动方式）

1. 从 [GitHub Releases](https://github.com/BiFangKNT/mtga/releases) 下载最新版本的 `MTGA_GUI-v{版本号}-x64.exe`
2. 双击运行下载的 exe 文件（需要管理员权限）
3. 在打开的图形界面中，填写 API URL 和模型 ID
   - **API URL 只需要填域名（端口号可选，不懂的就不要填），不需要填后面的路由，例如：`https://your-api.example.com`**
   - **如果希望启用多模态能力，可以将模型名映射到内置多模态模型名上：**
   - <img width="247" height="76" alt="model mapping" src="./images/model-mapping.png?raw=true" />
   - <img width="380" height="141" alt="model mapping effects" src="./images/model-mapping-effects.png?raw=true" />
4. 点击"一键启动全部服务"按钮
5. 等待程序自动完成以下操作：
   - 生成并安装证书
   - 修改hosts文件
   - 启动代理服务器
6. 完成后，按照[第 5 步：配置 Trae IDE](#第-5-步配置-trae-ide)进行IDE配置

> **注意：**
> - 首次运行可能需要允许防火墙访问权限
> - 单文件版本支持用户数据持久化存储，配置和证书会自动保存

### macOS 用户（应用程序安装）

#### 安装方式

1. 从 [GitHub Releases](https://github.com/BiFangKNT/mtga/releases) 下载最新版本的 `MTGA_GUI-v{版本号}-aarch64.dmg`
2. 双击 DMG 文件，系统会自动挂载安装包
3. 将 `MTGA_GUI.app` 拖拽到 `Applications` 文件夹
4. 从启动台或 Applications 文件夹启动应用程序

#### 使用方法

1. 启动 `MTGA_GUI.app`（首次运行可能需要在系统偏好设置中允许运行）
2. 在图形界面中填写：
   - **API URL**：你的 API 服务地址（例如：`https://your-api.example.com`）
   - **如果希望启用多模态能力，可以将模型名映射到内置多模态模型名上：**
   - <img width="247" height="76" alt="model mapping" src="./images/model-mapping.png?raw=true" />
   - <img width="380" height="141" alt="model mapping effects" src="./images/model-mapping-effects.png?raw=true" />
3. 点击"一键启动全部服务"按钮
4. 程序会自动完成：
   - 生成并安装 SSL 证书到系统钥匙串
   - 修改 `/etc/hosts` 文件（需要管理员权限）
5. 需要手动在打开的钥匙串窗口中信任生成的证书，默认名称为 `MyLocalCA`
6. 启动本地代理服务器
7. 按照下方的 [Trae IDE 配置](#第-5-步配置-trae-ide) 完成设置

> **注意事项：**
> - 首次运行需要输入管理员密码以修改系统文件
> - 可能需要在"系统偏好设置 > 安全性与隐私"中允许应用运行
> - 如遇到网络权限问题，请在"系统偏好设置 > 安全性与隐私 > 防火墙"中允许应用访问网络

---

## 从脚本启动

### 第 0 步：环境准备

#### Windows

- 系统为 windows 10 以上
- 拥有管理员权限
- 安装 python 环境，推荐 python 3.10 以上
- 安装 git

##### 第 1 步：生成自签名证书

打开 Git Bash:

```bash
# 切换到 ca 目录
cd "mtga/ca"

# 1. 生成 CA 证书 (ca.crt 和 ca.key)
./genca.sh
```

执行 `./genca.sh` 时，它会问你 "Do you want to generate ca cert and key? [yes/no]"，输入 `y` 并按回车。之后会要求填写一些信息：
*   `Country Name (2 letter code) []`: 填 `CN` (或其他国家代码)
*   其他字段（如 State, Locality, Organization, Common Name for CA）可以按需填写或留空，建议填`X`。Common Name 可以填 `MyLocalCA` 之类的。邮箱可以留空。

```bash
# 2. 生成 api.openai.com 的服务器证书 (api.openai.com.crt 和 api.openai.com.key)
# 这个脚本会使用同目录下的 api.openai.com.subj 和 api.openai.com.cnf 配置文件
./gencrt.sh api.openai.com
```

执行完毕后，在 `mtga\ca` 目录下你会找到以下重要文件：
*   `ca.crt` (你的自定义 CA 证书)
*   `ca.key` (你的自定义 CA 私钥 - **请勿泄露**)
*   `api.openai.com.crt` (用于本地代理服务器的 SSL 证书)
*   `api.openai.com.key` (用于本地代理服务器的 SSL 私钥 - **请勿泄露**)

##### 第 2 步：让 Windows 信任你的 CA 证书

1.  找到 `mtga\ca\ca.crt` 文件。
2.  双击 `ca.crt` 文件，打开证书查看器。
3.  点击"安装证书..."按钮。
4.  选择"当前用户"或"本地计算机"。推荐选择"本地计算机"（这需要管理员权限），这样对所有用户生效。
5.  在下一个对话框中，选择"将所有的证书都放入下列存储"，然后点击"浏览..."。
6.  选择"受信任的根证书颁发机构"，然后点击"确定"。
7.  点击"下一步"，然后"完成"。如果弹出安全警告，选择"是"。

##### 第 3 步：修改 Hosts 文件

**⚠️警告：执行这一步之后，你将无法访问原来的 openai 的api。网页使用不影响。**

你需要用管理员权限修改 Hosts 文件，将 `api.openai.com` 指向你的本地机器。

1.  Hosts 文件路径: `C:\Windows\System32\drivers\etc\hosts`
2.  以管理员身份，使用记事本（或其他文本编辑器）打开此文件。
3.  在文件末尾添加一行：
    ```
    127.0.0.1 api.openai.com
    ```
4.  保存文件。  

##### 第 4 步：运行本地代理服务器 (Python)

**运行代理服务器之前：**

1.  **安装依赖**:
    ```bash
    pip install Flask requests
    ```
2.  **配置脚本**:
    *   打开 `trae_proxy.py` 文件。
    *   **修改 `TARGET_API_BASE_URL`**: 将其替换为你实际要连接的那个站点的 OpenAI 格式 API 的基础 URL (例如: `"https://your-api.example.com"`)。
    *   **确认证书路径**: 脚本默认会从 `mtga\ca` 读取 `api.openai.com.crt` 和 `api.openai.com.key`。如果你的证书不在此路径，请修改 `CERT_FILE` 和 `KEY_FILE` 的值，或者将这两个文件复制到脚本指定的 `CERT_DIR`。

**运行代理服务器：**

打开命令提示符 (cmd) 或 PowerShell **以管理员身份运行** (因为要监听 443 端口)，然后执行：

```bash
python trae_proxy.py
```

如果一切顺利，你应该会看到服务器启动的日志。

##### 第 5 步：配置 Trae IDE

1.  打开并登录 Trae IDE。
2.  在 AI 对话框中，点击右下角的模型图标，选择末尾的"添加模型"。
3.  **服务商**：选择 `OpenAI`。
4.  **模型**：选择"自定义模型"。
5.  **模型 ID**：填写你在 Python 脚本中 `CUSTOM_MODEL_ID` 定义的值 (例如: `my-custom-local-model`)。
6.  **API 密钥**：
    *   如果你的目标 API 需要 API 密钥，并且 Trae 会将其通过 `Authorization: Bearer <key>` 传递，那么这里填写的密钥会被 Python 代理转发。
    *   Trae 配置 OpenAI 时，API 密钥与 `remove_reasoning_content` 配置相关。我们的 Python 代理不处理这个逻辑，它只是简单地转发 Authorization 头部。你可以尝试填写你的目标 API 所需的密钥，或者一个任意的 `sk-xxxx` 格式的密钥。

7.  点击"添加模型"。
8.  回到 AI 聊天框，右下角选择你刚刚添加的自定义模型。

现在，当你通过 Trae 与这个自定义模型交互时，请求应该会经过你的本地 Python 代理，并被转发到你配置的 `TARGET_API_BASE_URL`。

**故障排除提示：**
*   **端口冲突**：如果 443 端口已被占用 (例如被 IIS、Skype 或其他服务占用)，Python 脚本会启动失败。你需要停止占用该端口的服务，或者修改 Python 脚本和 Nginx (如果使用) 监听其他端口 (但这会更复杂，因为 Trae 硬编码访问 `https://api.openai.com` 的 443 端口)。
*   **防火墙**：确保 Windows 防火墙允许 Python 监听 443 端口的入站连接 (尽管是本地连接 `127.0.0.1`，通常不需要特别配置防火墙，但值得检查)。
*   **证书问题**：如果 Trae 报错 SSL/TLS 相关错误，请仔细检查 CA 证书是否已正确安装到"受信任的根证书颁发机构"，以及 Python 代理是否正确加载了 `api.openai.com.crt` 和 `.key`。
*   **代理日志**：Python 脚本会打印一些日志，可以帮助你诊断问题。

这个方案比直接使用 vproxy + nginx 的方式更集成一些，将 TLS 终止和代理逻辑都放在了一个 Python 脚本中，更适合快速在 Windows 上进行原型验证。

#### macOS

-> [Mac OS 脚本启动方法](https://github.com/BiFangKNT/mtga/blob/gui/docs/README_macOS_cli.md)

---

## 😎 保持更新

点击仓库右上角 Star 和 Watch 按钮，获取最新动态。

![star to keep latest](https://github.com/BiFangKNT/mtga/blob/gui/images/star-to-keep-latest.gif?raw=true)

---

## 引用

`ca`目录引用自`wkgcass/vproxy`仓库，感谢大佬！
