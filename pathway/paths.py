"""路径工具：同时兼容开发环境与 PyInstaller 打包后的运行环境。

打包成 exe 后，代码与数据会被解压到临时目录（sys._MEIPASS），而用户
配置文件应当落在 exe 旁边的可写目录里，因此两种路径必须区分开。
"""

import sys
from pathlib import Path
from typing import Optional

APP_NAME_CSY = "学历路径分析与推荐系统"
APP_FULL_NAME_CSY = "基于公开数据的本专科学历路径分析与推荐系统"
APP_VERSION_CSY = "1.0"


def is_frozen_csy() -> bool:
    """判断当前是否运行在 PyInstaller 打包出的可执行文件里。"""
    return bool(getattr(sys, "frozen", False))


def resource_root_csy() -> Path:
    """只读资源根目录：打包后是临时解压目录，开发时是项目根目录。"""
    if is_frozen_csy():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def writable_root_csy() -> Path:
    """可写根目录：打包后是 exe 所在目录，开发时是项目根目录。"""
    if is_frozen_csy():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def database_file_csy() -> Path:
    """定位 SQLite 数据库文件，优先使用随包分发的数据文件。"""
    bundled = resource_root_csy() / "data" / "pathway.db"
    if bundled.exists():
        return bundled
    return writable_root_csy() / "data" / "pathway.db"


def config_file_csy() -> Path:
    """定位配置文件，始终放在可写目录，便于用户手工修改。"""
    return writable_root_csy() / "config.json"


def users_file_csy() -> Path:
    """定位用户账号数据库。

    与只读的参考数据分开：pathway.db 随程序分发、只读；
    users.db 存放注册的账号与个人档案，必须可写。
    """
    return writable_root_csy() / "users.db"


def ensure_data_dir_csy() -> Optional[Path]:
    """确保数据目录存在，返回数据目录路径。"""
    target = writable_root_csy() / "data"
    try:
        target.mkdir(parents=True, exist_ok=True)
        return target
    except OSError:
        return None
