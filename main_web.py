"""学径 · 学历与升学数据平台 —— pywebview 桌面入口。

启动流程：
    登录 / 注册（Tkinter）  ->  React 前端（pywebview）

运行方式：
    开发环境：python main_web.py
    打包之后：直接双击生成的可执行文件
"""

import sys
import traceback
from pathlib import Path

import webview

from pathway.auth import UserStore
from pathway.login import run_login_csy
from pathway.onboarding import run_onboarding_csy
from pathway.paths import APP_NAME_CSY, resource_root_csy, users_file_csy
from pathway.web_api import WebApi


def frontend_index_csy() -> Path:
    """定位前端构建产物。"""
    root = resource_root_csy()
    candidates = [
        root / "frontend" / "dist" / "index.html",
        Path(__file__).resolve().parent / "frontend" / "dist" / "index.html",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("未找到前端构建产物，请先在 frontend 目录执行 npm run build")


def main_csy() -> int:
    """登录后启动 pywebview 窗口。"""
    try:
        print("%s 正在启动..." % APP_NAME_CSY)
        user = run_login_csy()
        if not user:
            print("未登录，程序退出。")
            return 0

        if not user.get("guest"):
            store = UserStore(users_file_csy())
            profile = store.get_profile_csy(user["user_id"])
            if not profile.get("onboarded"):
                run_onboarding_csy(user)

        api = WebApi(user)
        index = frontend_index_csy()
        webview.create_window(
            "学径 · 学历与升学数据平台",
            url=str(index),
            js_api=api,
            width=1440,
            height=900,
            min_size=(1120, 720),
        )
        webview.start()
    except Exception:
        print("程序启动失败：")
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main_csy())
