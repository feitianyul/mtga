# -*- coding: utf-8 -*-

# DMG settings for MTGA GUI
# Based on dmgbuild documentation and examples

import os.path

# Application path
application = 'MTGA_GUI.app'
appname = os.path.basename(application)

# Volume settings
volume_name = 'MTGA GUI Installer'
format = 'UDZO'  # Compressed (gzip)
size = None  # Auto-calculate size

# Files to include
files = [application]

# Symlinks to create
symlinks = {'Applications': '/Applications'}

# Icon positions
icon_locations = {
    appname: (160, 140),
    'Applications': (440, 135)
}

# Window settings
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False

# Window position and size
window_rect = ((100, 100), (600, 400))

# Default view
default_view = 'icon-view'

# Icon view settings
arrange_by = None  # No automatic arrangement
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = 'bottom'
text_size = 16
icon_size = 96

# Background image
# Use the dmg_background.png file in the current directory
background = 'dmg_background.png'

# Include icon view settings
include_icon_view_settings = True
include_list_view_settings = False