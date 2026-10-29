"""界面设计规范：配色、字体、图标与 ttk 样式。

界面代码只引用这里的样式名与颜色常量，不写死色值；
想整体换肤只改这一个文件。
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

COLORS_CSY = {
    # 米白系底色：页面用暖米白，卡片保持白色形成层次
    "page": "#F6F3EC",          # 页面底色（米白）
    "page_deep": "#EFEAE0",     # 更深的米白，用于分区与凹陷背景
    "surface": "#FFFFFF",       # 卡片底色
    "surface_alt": "#FAF8F4",   # 卡片内次级底 / 斑马纹
    "border": "#E7E1D6",        # 细分隔线
    "border_strong": "#D7CFC1",
    "shadow": "#E3DCD0",        # 卡片投影
    "text": "#2B2723",
    "text_sub": "#57514A",
    "muted": "#8E867B",
    "accent": "#2F6FED",
    "accent_dark": "#1F55C0",
    "accent_soft": "#E8EFFD",
    "green": "#0E9F6E",
    "green_soft": "#E5F6EF",
    "amber": "#A9631A",
    "amber_soft": "#FBF0DF",
    "red": "#C43B3B",
    "red_soft": "#FBEBEB",
    "code_bg": "#F8F6F1",
    "code_text": "#2E2A26",
    "bubble_user": "#E7EEFD",
}

FONT_FAMILY_CSY = "Microsoft YaHei UI"
FONT_MONO_CSY = "Consolas"

FONTS_CSY = {
    "brand": (FONT_FAMILY_CSY, 15, "bold"),
    "title": (FONT_FAMILY_CSY, 11, "bold"),
    "section": (FONT_FAMILY_CSY, 10, "bold"),
    "body": (FONT_FAMILY_CSY, 10),
    "small": (FONT_FAMILY_CSY, 9),
    "tiny": (FONT_FAMILY_CSY, 8),
    "mono": (FONT_MONO_CSY, 9),
    "icon": (FONT_FAMILY_CSY, 11),
}

# 使用 Windows 自带的图标字体，取不到就自动退化为纯文字按钮
ICON_FONT_CSY = "Segoe MDL2 Assets"
ICONS_CSY = {
    "send": "\uE724",
    "settings": "\uE713",
    "clear": "\uE74D",
    "copy": "\uE8C8",
    "chart": "\uE9D2",
    "database": "\uEE94",
    "table": "\uE80A",
    "hint": "\uEA80",
    "info": "\uE946",
    "warning": "\uE7BA",
    "search": "\uE721",
    "checked": "\uE73E",
}


def icon_csy(name: str) -> str:
    """取图标字形；当前系统没有图标字体时返回空串。"""
    if not has_icon_font_csy():
        return ""
    return ICONS_CSY.get(name, "")


def has_icon_font_csy() -> bool:
    """判断系统是否装有 Segoe MDL2 Assets 图标字体。"""
    try:
        families = set(tkfont.families())
    except tk.TclError:
        return False
    return ICON_FONT_CSY in families


def apply_theme_csy(root) -> None:
    """在根窗口上注册全部 ttk 样式。"""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    color = COLORS_CSY
    font = FONTS_CSY
    root.configure(bg=color["page"])

    style.configure(".", background=color["page"], foreground=color["text"],
                    font=font["body"], focuscolor=color["page"])
    style.configure("TFrame", background=color["page"])
    style.configure("Surface.TFrame", background=color["surface"])
    style.configure("Alt.TFrame", background=color["surface_alt"])
    style.configure("TLabel", background=color["page"], foreground=color["text"], font=font["body"])
    style.configure("Surface.TLabel", background=color["surface"])
    style.configure("Brand.TLabel", background=color["surface"],
                    foreground=color["text"], font=font["brand"])
    style.configure("Title.TLabel", background=color["surface"],
                    foreground=color["text"], font=font["title"])
    style.configure("Section.TLabel", background=color["surface"],
                    foreground=color["text"], font=font["section"])
    style.configure("Muted.TLabel", background=color["surface"],
                    foreground=color["muted"], font=font["small"])
    style.configure("TinyMuted.TLabel", background=color["surface"],
                    foreground=color["muted"], font=font["tiny"])
    style.configure("Page.TLabel", background=color["page"],
                    foreground=color["muted"], font=font["small"])

    # 主按钮：实心强调色，扁平无边框
    style.configure("Accent.TButton", background=color["accent"], foreground="#FFFFFF",
                    font=font["body"], borderwidth=0, relief="flat", focuscolor=color["accent"],
                    padding=(16, 9))
    style.map("Accent.TButton",
              background=[("pressed", color["accent_dark"]), ("active", "#2A64D6"),
                          ("disabled", "#B7C9F1")],
              foreground=[("disabled", "#FFFFFF")])

    # 次按钮：浅暖灰底，无描边
    style.configure("Ghost.TButton", background="#F2EFE8", foreground=color["text_sub"],
                    font=font["small"], borderwidth=0, relief="flat", focuscolor="#F2EFE8",
                    padding=(12, 7))
    style.map("Ghost.TButton",
              background=[("pressed", "#E5DFD4"), ("active", "#EAE5DB")],
              foreground=[("disabled", color["muted"])])

    # 图标按钮：方正的纯图标按钮
    style.configure("Icon.TButton", background="#F2EFE8", foreground=color["text_sub"],
                    font=font["icon"], borderwidth=0, relief="flat", focuscolor="#F2EFE8",
                    padding=(6, 4))
    style.map("Icon.TButton",
              background=[("pressed", "#E5DFD4"), ("active", "#EAE5DB")])

    style.configure("TSeparator", background=color["border"])

    # 表格：去掉外框，表头浅灰，选中行用淡蓝
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview", background=color["surface"], fieldbackground=color["surface"],
                    foreground=color["text"], rowheight=26, font=font["small"],
                    borderwidth=0, relief="flat")
    style.configure("Treeview.Heading", background="#F2EFE8", foreground=color["text_sub"],
                    font=font["tiny"], relief="flat", borderwidth=0, padding=(8, 7))
    style.map("Treeview.Heading", background=[("active", "#EAE5DB")])
    style.map("Treeview", background=[("selected", color["accent_soft"])],
              foreground=[("selected", color["text"])])

    # 左侧结构树：更紧凑，无表头
    style.configure("Schema.Treeview", background=color["surface"],
                    fieldbackground=color["surface"], foreground=color["text_sub"],
                    rowheight=23, font=font["small"], borderwidth=0, relief="flat")
    style.map("Schema.Treeview", background=[("selected", color["accent_soft"])],
              foreground=[("selected", color["text"])])

    # 细滚动条：剥掉两端的箭头按钮
    style.layout("Thin.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
    style.layout("Thin.Horizontal.TScrollbar", [
        ("Horizontal.Scrollbar.trough", {"sticky": "ew", "children": [
            ("Horizontal.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
    for name in ("Thin.Vertical.TScrollbar", "Thin.Horizontal.TScrollbar"):
        style.configure(name, background="#D6CEC0", troughcolor=color["page"],
                        bordercolor=color["page"], lightcolor="#D6CEC0", darkcolor="#D6CEC0",
                        borderwidth=0, arrowsize=1)
        style.map(name, background=[("pressed", "#B6AC9B"), ("active", "#C5BCAC")])

    # 输入框与下拉框：白底细描边，聚焦时描边变成强调色
    style.configure("TEntry", fieldbackground=color["surface"], foreground=color["text"],
                    bordercolor=color["border_strong"], lightcolor=color["border_strong"],
                    darkcolor=color["border_strong"], insertcolor=color["text"],
                    borderwidth=1, relief="flat", padding=8)
    style.map("TEntry",
              bordercolor=[("focus", color["accent"])],
              lightcolor=[("focus", color["accent"])],
              darkcolor=[("focus", color["accent"])])

    style.configure("TCombobox", fieldbackground=color["surface"], background=color["surface"],
                    foreground=color["text"], arrowcolor=color["text_sub"],
                    bordercolor=color["border_strong"], lightcolor=color["border_strong"],
                    darkcolor=color["border_strong"], borderwidth=1, padding=5)
    style.map("TCombobox", fieldbackground=[("readonly", color["surface"])])
