# DMG settings for MTGA GUI
# Based on dmgbuild documentation and examples

import os
import os.path

# Application path - 使用环境变量或默认值
application = os.environ.get("MTGA_APP_NAME", "MTGA_GUI.app")

# 确保使用相对于当前工作目录的路径
if os.path.isabs(application):
    # 如果是绝对路径，提取应用名称并构造相对路径
    app_name = os.path.basename(application)
    # 假设应用在 dist-onefile 目录中
    relative_app = application if application.startswith("/") else application
    application = relative_app

appname = os.path.basename(application)

# 添加调试信息
print("DMG配置调试信息:")
print(f"环境变量 MTGA_APP_NAME: {os.environ.get('MTGA_APP_NAME', 'Not Set')}")
print(f"应用路径: {application}")
print(f"应用名称: {appname}")
print(f"应用路径存在: {os.path.exists(application)}")

# Volume settings
volume_name = "MTGA GUI Installer"
format = "UDZO"  # Compressed (gzip)
size = None  # Auto-calculate size

# Files to include
files = [application]

# Symlinks to create
symlinks = {"Applications": "/Applications"}

# Icon positions
icon_locations = {appname: (160, 140), "Applications": (440, 135)}

# Window settings
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False

# Window position and size
window_rect = ((100, 100), (600, 400))

# Default view
default_view = "icon-view"

# Icon view settings
arrange_by = None  # No automatic arrangement
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = "bottom"
text_size = 16
icon_size = 96

# Background image
# Use the dmg_background.png file in the mac directory
background = "mac/dmg_background.png"

# Include icon view settings
include_icon_view_settings = True
include_list_view_settings = False
