"""对话框：数据来源说明。

系统的数据全部来自官方公开渠道，把来源、发布单位、覆盖范围与已知局限
集中放在一个对话框里，方便答辩时直接展示"数据是哪来的"。
"""

import tkinter as tk
from tkinter import ttk

from .theme import COLORS_CSY, FONTS_CSY, apply_theme_csy
from .widgets import RoundedCard, make_button_csy, make_pill_csy


def center_on_parent_csy(window, parent) -> None:
    """把对话框摆到父窗口中央。"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    window.geometry("+%d+%d" % (max(x, 0), max(y, 0)))


def prepare_dialog_csy(dialog, parent) -> None:
    """对话框公共设置：配色、居中、模态。"""
    dialog.configure(bg=COLORS_CSY["page"])
    apply_theme_csy(dialog)
    dialog.transient(parent)
    dialog.grab_set()
    center_on_parent_csy(dialog, parent)


class DataSourceDialog(tk.Toplevel):
    """数据来源说明框。"""

    def __init__(self, parent, sources: list):
        super().__init__(parent)
        self.sources = sources
        self.title("数据来源说明")
        self.resizable(False, False)
        self.build_csy()
        prepare_dialog_csy(self, parent)
        parent.wait_window(self)

    def build_csy(self) -> None:
        """列出每一处数据来源及其覆盖范围与局限。"""
        wrapper = tk.Frame(self, bg=COLORS_CSY["page"])
        wrapper.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Label(wrapper, text="数据来源与覆盖范围", bg=COLORS_CSY["page"],
                 fg=COLORS_CSY["text"], font=FONTS_CSY["title"]).pack(anchor="w")
        tk.Label(wrapper, text="系统内所有数据均来自官方公开渠道，可逐条追溯。",
                 bg=COLORS_CSY["page"], fg=COLORS_CSY["muted"],
                 font=FONTS_CSY["small"]).pack(anchor="w", pady=(4, 12))

        for source in self.sources:
            card = RoundedCard(wrapper)
            card.pack(fill="x", pady=(0, 10))
            body = card.body
            make_pill_csy(body, source.get("coverage", ""), COLORS_CSY["accent"],
                          COLORS_CSY["accent_soft"]).pack(anchor="w", padx=14, pady=(12, 6))
            tk.Label(body, text=source.get("name", ""), bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text"], font=FONTS_CSY["section"],
                     justify="left", wraplength=470).pack(anchor="w", padx=14)
            tk.Label(body, text="发布单位：" + source.get("publisher", ""),
                     bg=COLORS_CSY["surface"], fg=COLORS_CSY["text_sub"],
                     font=FONTS_CSY["small"]).pack(anchor="w", padx=14, pady=(2, 0))
            note = source.get("note", "")
            if note:
                tk.Label(body, text=note, bg=COLORS_CSY["surface"],
                         fg=COLORS_CSY["muted"], font=FONTS_CSY["small"],
                         justify="left", wraplength=470).pack(
                    anchor="w", padx=14, pady=(2, 0))
            tk.Frame(body, bg=COLORS_CSY["surface"], height=12).pack()

        buttons = tk.Frame(wrapper, bg=COLORS_CSY["page"])
        buttons.pack(fill="x", pady=(6, 0))
        make_button_csy(buttons, "知道了", self.destroy, kind="primary").pack(side="right")


class AboutDialog(tk.Toplevel):
    """关于对话框：说明系统定位。"""

    def __init__(self, parent, full_name: str, version: str):
        super().__init__(parent)
        self.full_name = full_name
        self.version = version
        self.title("关于")
        self.resizable(False, False)
        self.build_csy()
        prepare_dialog_csy(self, parent)
        parent.wait_window(self)

    def build_csy(self) -> None:
        """展示系统定位与用途。"""
        wrapper = tk.Frame(self, bg=COLORS_CSY["page"])
        wrapper.pack(fill="both", expand=True, padx=20, pady=18)
        tk.Label(wrapper, text=self.full_name, bg=COLORS_CSY["page"],
                 fg=COLORS_CSY["text"], font=FONTS_CSY["title"],
                 justify="left", wraplength=460).pack(anchor="w")
        tk.Label(wrapper, text="版本 v%s" % self.version, bg=COLORS_CSY["page"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["small"]).pack(
            anchor="w", pady=(6, 12))
        for text in [
            "本系统面向在校学生（专科与本科），用官方公开数据展示升学与就业的真实路径。",
            "它回答三个问题：我这个专业能报什么？要考什么、分数线多少？"
            "往届和我条件相近的人最后去了哪？",
            "系统不提供录取承诺，所有结论都标明数据来源与样本范围，"
            "请结合自身情况判断。",
        ]:
            tk.Label(wrapper, text=text, bg=COLORS_CSY["page"],
                     fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"],
                     justify="left", wraplength=460).pack(anchor="w", pady=(0, 8))
        buttons = tk.Frame(wrapper, bg=COLORS_CSY["page"])
        buttons.pack(fill="x", pady=(8, 0))
        make_button_csy(buttons, "关闭", self.destroy, kind="primary").pack(side="right")
