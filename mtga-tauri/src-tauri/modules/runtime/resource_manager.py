"""资源路径管理模块分发器（tauri/legacy）。"""

from modules.platform.platform_context import get_platform

if get_platform() == "tauri":
    from .resource_manager_tauri import *  # noqa: F401,F403
else:
    from .resource_manager_legacy import *  # noqa: F401,F403

