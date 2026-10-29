"""旧版 Tkinter 入口（备用）。

React + pywebview 版本是默认入口；本文件保留原 Tkinter 界面，
在 WebView2 不可用或需要纯 Python 运行时可以改用：
    python main_tk.py
"""

import sys
import traceback

from pathway.auth import UserStore
from pathway.login import run_login_csy
from pathway.onboarding import run_onboarding_csy
from pathway.paths import APP_NAME_CSY, users_file_csy
from pathway.window import launch_csy


def main_csy() -> int:
    """登录 -> 引导 -> Tkinter 主界面。"""
    try:
        print("%s 正在启动（Tkinter 版）..." % APP_NAME_CSY)
        user = run_login_csy()
        if not user:
            print("未登录，程序退出。")
            return 0

        if user.get("guest"):
            profile = user.get("profile", {})
        else:
            store = UserStore(users_file_csy())
            profile = store.get_profile_csy(user["user_id"])
            if not profile.get("onboarded"):
                filled = run_onboarding_csy(user)
                profile.update(filled)

        launch_csy(user, profile)
    except Exception:
        print("程序启动失败：")
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main_csy())
