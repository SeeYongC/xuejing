"""学径 · 学历与升学数据平台 —— 程序入口。

默认启动 React + pywebview 桌面界面；
旧的 Tkinter 界面保留在 main_tk.py，可作备用。
"""

import sys

from main_web import main_csy


if __name__ == "__main__":
    sys.exit(main_csy())
