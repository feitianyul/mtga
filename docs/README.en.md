# MTGA

<picture>
    <img alt="MTGA" src="https://github.com/BiFangKNT/mtga/blob/gui/icons/hero-img_f0bb32.png?raw=true">
</picture>

[![English](https://img.shields.io/badge/docs-English-purple)](README.en.md) [![简体中文](https://img.shields.io/badge/文档-简体中文-yellow)](../README.md)

## Introduction

MTGA is a local proxy-based IDE fixed model provider solution for Windows and macOS.

**Note: This project currently only supports APIs in OpenAI format. Please confirm. Other formats can be converted to OpenAI format before use.**

<details>
  <summary>You can't see anything~~</summary>
  <br>
  <p>MTGA stands for Make T Great Again!</p>
 </details>

## Table of Contents

* [Changelog](#changelog)
* [Quick Start](#quick-start)
  * [Windows Users (GUI One-Click Startup)](#windows-users-gui-one-click-startup)
  * [macOS Users (Application Installation)](#macos-users-application-installation)
* [Starting from Script](#starting-from-script)
  * [Step 0: Environment Preparation](#step-0-environment-preparation)
    * [Windows](#windows)
      * [Step 1: Generate Self-Signed Certificate](#step-1-generate-self-signed-certificate)
      * [Step 2: Make Windows Trust Your CA Certificate](#step-2-make-windows-trust-your-ca-certificate)
      * [Step 3: Modify Hosts File](#step-3-modify-hosts-file)
      * [Step 4: Run Local Proxy Server (Python)](#step-4-run-local-proxy-server-python)
      * [Step 5: Configure Trae IDE](#step-5-configure-trae-ide)
    * [macOS](#macos)
 * [😎 Stay Updated](#-stay-updated)

---

## Changelog

### v1.1.1 (Latest)

- 🐛 **Fixed hosts modification issue** - Resolved abnormal line breaks when modifying hosts file

### v1.1.0

- ✨ **Added user data management functionality** - Single-file version supports persistent storage of user data
  - Data storage location: Windows `%APPDATA%\MTGA\`, macOS/Linux `~/.mtga/`
  - Supports backup, restore, and clear user data
  - Configuration files, SSL certificates, hosts backups are automatically persisted
- 🔧 **Optimized single-file build** - Improved `build_onefile.bat`, supports version number variable
- 🎯 **Improved user interface** - Added configuration group list refresh button, optimized interface layout
- 📖 **Enhanced documentation** - Added single-file build guide, updated project documentation

### v1.0.0

- ✅ **Adapted for Mac OS** - Supports macOS application installation
- 🔄 **Default provider changed** - Changed from DeepSeek to OpenAI
- 📦 **File restructuring** - Renamed ds-related files to `*_ds.*` format for archiving
- 🌐 **API URL format changed** - From `https://your-api.example.com/v1` to `https://your-api.example.com`

---

## Quick Start

### Windows Users (GUI One-Click Startup)

1. Download the latest version of `MTGA_GUI-v{version}-x64.exe` from [GitHub Releases](https://github.com/BiFangKNT/mtga/releases)
2. Double-click the downloaded exe file to run (requires administrator privileges)
3. In the opened graphical interface, fill in the API URL and Model ID
   - **API URL only needs the domain name (port number is optional, do not fill if unsure), no need to include the route, for example: `https://your-api.example.com`**
   - **Pay attention to distinguish the model name, do not conflict with built-in model names:**
   - <img width="249" height="67" alt="differentiate model name" src="https://github.com/BiFangKNT/mtga/blob/gui/images/differentiate-model_name.png?raw=true" />
4. Click the "Start All Services with One Click" button
5. Wait for the program to automatically complete the following operations:
   - Generate and install the certificate
   - Modify the hosts file
   - Start the proxy server
6. After completion, proceed with IDE configuration according to [Step 5: Configure Trae IDE](#第-5-步配置-trae-ide)

> [!NOTE]
> - First run may require allowing firewall access permissions
> - The single-file version supports persistent storage of user data; configurations and certificates are automatically saved

### macOS Users (Application Installation)

#### Installation Method

1. Download the latest version of `MTGA_GUI-v{version}-aarch64.dmg` from [GitHub Releases](https://github.com/BiFangKNT/mtga/releases)
2. Double-click the DMG file, the system will automatically mount the installation package
3. Drag `MTGA_GUI.app` to the `Applications` folder
4. Launch the application from Launchpad or the Applications folder

#### Usage Instructions

1. Launch `MTGA_GUI.app` (first run may require allowing it to run in System Preferences)
2. Fill in the graphical interface:
   - **API URL**: Your API service address (e.g., `https://your-api.example.com`)
   - **Model ID**: Custom model name (avoid conflicts with built-in models)
3. Click the "Start All Services with One Click" button
4. The program will automatically complete:
   - Generate and install the SSL certificate into the system keychain
   - Modify the `/etc/hosts` file (requires administrator privileges)
5. Manually trust the generated certificate in the opened keychain window; the default name is `MyLocalCA`
6. Start the local proxy server
7. Complete the setup by following the [Trae IDE Configuration](#第-5-步配置-trae-ide) below

> [!IMPORTANT]
> - First run requires entering the administrator password to modify system files
> - May need to allow the application to run in "System Preferences > Security & Privacy"
> - If encountering network permission issues, allow the application network access in "System Preferences > Security & Privacy > Firewall"

---

## Starting from Script

### Step 0: Environment Preparation

#### Windows

- System requirements: Windows 10 or above
- Administrator privileges required
- Install Python environment, recommended Python 3.10 or above
- Install Git

##### Step 1: Generate a Self-Signed Certificate

Open Git Bash:

```bash
# 切换到 ca 目录
cd "mtga/ca"

# 1. 生成 CA 证书 (ca.crt 和 ca.key)
./genca.sh
```

When executing `./genca.sh`, it will ask "Do you want to generate ca cert and key? [yes/no]". Enter `y` and press Enter. Afterwards, it will prompt for some information:

*   `Country Name (2 letter code) []`: Enter `CN` (or another country code)
*   Other fields (like State, Locality, Organization, Common Name for CA) can be filled as needed or left blank; it's suggested to fill them with `X`. The Common Name can be something like `MyLocalCA`. The email field can be left empty.

```bash
# 2. 生成 api.openai.com 的服务器证书 (api.openai.com.crt 和 api.openai.com.key)
# 这个脚本会使用同目录下的 api.openai.com.subj 和 api.openai.com.cnf 配置文件
./gencrt.sh api.openai.com
```

After execution completes, you will find the following important files in the `mtga\ca` directory:

*   `ca.crt` (Your custom CA certificate)
*   `ca.key` (Your custom CA private key - **DO NOT LEAK**)
*   `api.openai.com.crt` (SSL certificate for the local proxy server)
*   `api.openai.com.key` (SSL private key for the local proxy server - **DO NOT LEAK**)

##### Step 2: Make Windows Trust Your CA Certificate

1.  Locate the `mtga\ca\ca.crt` file.
2.  Double-click the `ca.crt` file to open the certificate viewer.
3.  Click the "Install Certificate..." button.
4.  Choose "Current User" or "Local Machine". It is recommended to choose "Local Machine" (this requires administrator privileges) to apply it to all users.
5.  In the next dialog, select "Place all certificates in the following store", then click "Browse...".
6.  Select "Trusted Root Certification Authorities", then click "OK".
7.  Click "Next", then "Finish". If a security warning pops up, select "Yes".

##### Step 3: Modify the Hosts File

**⚠️WARNING: After performing this step, you will not be able to access the original OpenAI API. Web usage is unaffected.**

You need to modify the Hosts file with administrator privileges to point `api.openai.com` to your local machine.

1.  Hosts file path: `C:\Windows\System32\drivers\etc\hosts`
2.  Open this file with Notepad (or another text editor) as an administrator.
3.  Add the following line at the end of the file:
    ```
    127.0.0.1 api.openai.com
    ```
4.  Save the file.

##### Step 4: Run the Local Proxy Server (Python)

**Before running the proxy server:**

1.  **Install Dependencies**:
    ```bash
    pip install Flask requests
    ```
2.  **Configure the Script**:
    *   Open the `trae_proxy.py` file.
    *   **Modify `TARGET_API_BASE_URL`**: Replace it with the base URL of the actual OpenAI-format API site you want to connect to (e.g., `"https://your-api.example.com"`).
    *   **Confirm Certificate Paths**: The script defaults to reading `api.openai.com.crt` and `api.openai.com.key` from `mtga\ca`. If your certificates are not in this path, modify the values of `CERT_FILE` and `KEY_FILE`, or copy these two files to the `CERT_DIR` specified by the script.

**Run the Proxy Server:**

Open Command Prompt (cmd) or PowerShell **Run as Administrator** (because it needs to listen on port 443), then execute:

```bash
python trae_proxy.py
```

If everything goes well, you should see the server startup logs.

##### Step 5: Configure Trae IDE

1.  Open and log in to Trae IDE.
2.  In the AI dialog box, click the model icon in the lower right corner and select "Add Model" at the end.
3.  **Provider**: Select `OpenAI`.
4.  **Model**: Select "Custom Model".
5.  **Model ID**: Enter the value you defined for `CUSTOM_MODEL_ID` in the Python script (e.g., `my-custom-local-model`).
6.  **API Key**:
    *   If your target API requires an API key and Trae will pass it via `Authorization: Bearer <key>`, then the key entered here will be forwarded by the Python proxy.
    *   When configuring OpenAI in Trae, the API key is related to the `remove_reasoning_content` configuration. Our Python proxy does not handle this logic; it simply forwards the Authorization header. You can try entering the key required by your target API, or an arbitrary key in the `sk-xxxx` format.

7.  Click "Add Model".
8.  Return to the AI chat box and select the custom model you just added from the lower right corner.

Now, when you interact with this custom model through Trae, the requests should go through your local Python proxy and be forwarded to your configured `TARGET_API_BASE_URL`.

**Troubleshooting Tips:**

*   **Port Conflict**: If port 443 is already occupied (e.g., by IIS, Skype, or other services), the Python script will fail to start. You need to stop the service occupying that port, or modify the Python script and Nginx (if used) to listen on a different port (though this is more complex because Trae hardcodes access to `https://api.openai.com` on port 443).
*   **Firewall**: Ensure the Windows firewall allows inbound connections for Python listening on port 443 (even though it's a local connection `127.0.0.1`, firewall configuration is usually not required, but it's worth checking).
*   **Certificate Issues**: If Trae reports SSL/TLS related errors, carefully check if the CA certificate has been correctly installed into the "Trusted Root Certification Authorities" store, and if the Python proxy correctly loaded `api.openai.com.crt` and `.key`.
*   **Proxy Logs**: The Python script will print some logs that can help you diagnose issues.

This solution is more integrated than the direct vproxy + nginx approach, placing both TLS termination and proxy logic within a single Python script, making it more suitable for rapid prototyping on Windows.

#### macOS

-> [Mac OS Script Startup Method](https://github.com/BiFangKNT/mtga/blob/gui/docs/README_macOS_cli.md)

---

## 😎 Stay Updated

Click the Star and Watch buttons at the top right of the repository to get the latest updates.

![star to keep latest](https://github.com/BiFangKNT/mtga/blob/gui/images/star-to-keep-latest.gif?raw=true)

---

## References

The `ca` directory is referenced from the `wkgcass/vproxy` repository. Thanks to the original author!