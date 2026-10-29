"""自绘控件：圆角卡片、分段控件、图标按钮、悬停提示。

Tkinter 原生控件外观比较朴素，这里用 Canvas 自己画几个常用部件，
让界面看起来更像一个现代桌面应用。
"""

import tkinter as tk

from .theme import COLORS_CSY, FONTS_CSY, ICON_FONT_CSY, icon_csy


def draw_round_rect_csy(canvas: tk.Canvas, x1, y1, x2, y2, radius=10, **kwargs):
    """在画布上绘制圆角矩形（用平滑多边形近似出圆角）。"""
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedCard(tk.Frame):
    """圆角卡片：Canvas 画圆角底，内容 Frame 嵌在中间。

    使用方式：card = RoundedCard(parent); 然后把子控件放进 card.body。
    """

    def __init__(self, parent, card_bg: str = None, page_bg: str = None,
                 radius: int = 10, border: str = None, shadow: bool = True,
                 accent: str = None):
        self.page_bg = page_bg or COLORS_CSY["page"]
        self.card_bg = card_bg or COLORS_CSY["surface"]
        self.radius = radius
        self.border = border or COLORS_CSY["border"]
        self.accent = accent            # 卡片顶部的强调色横条（可为空）
        # 投影往右下偏移，让卡片从米白底上"浮"起来
        self.shadow_x = 3 if shadow else 0
        self.shadow_y = 4 if shadow else 0
        super().__init__(parent, bg=self.page_bg)

        self.canvas = tk.Canvas(self, bg=self.page_bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=self.card_bg)
        self.window_id = self.canvas.create_window(
            radius, radius, anchor="nw", window=self.body)
        self._last_height = -1
        self.canvas.bind("<Configure>", self.on_canvas_configure_csy)
        self.body.bind("<Configure>", self.on_body_configure_csy)

    def on_canvas_configure_csy(self, event) -> None:
        """画布变宽时同步内容宽度，并重画圆角底。

        注意只固定宽度、不固定高度：高度由内容自然撑开，
        否则内容尺寸变化时不会再触发 Configure，卡片会一直停留在初始高度。
        """
        inner_w = max(event.width - self.radius * 2 - self.shadow_x, 1)
        self.canvas.itemconfigure(self.window_id, width=inner_w)
        self.redraw_csy(event.width, event.height)

    def on_body_configure_csy(self, event=None) -> None:
        """内容变高时把卡片撑到刚好包住内容。"""
        wanted = self.body.winfo_reqheight() + self.radius * 2 + self.shadow_y
        if wanted != self.canvas.winfo_reqheight():
            self._last_height = wanted
            self.canvas.configure(height=wanted)

    def redraw_csy(self, width: int, height: int) -> None:
        """重画投影与圆角底，并压到最下层。"""
        self.canvas.delete("card_bg")
        if self.shadow_x:
            draw_round_rect_csy(self.canvas, self.shadow_x, self.shadow_y, width, height,
                                self.radius, fill=COLORS_CSY["shadow"],
                                outline=COLORS_CSY["shadow"], tags="card_bg")
        draw_round_rect_csy(self.canvas, 0, 0, width - self.shadow_x, height - self.shadow_y,
                            self.radius,
                            fill=self.card_bg, outline=self.border, tags="card_bg")
        if self.accent:
            self.canvas.create_rectangle(
                self.radius + 2, 1, width - self.shadow_x - self.radius - 2, 5,
                fill=self.accent, outline=self.accent, tags="card_bg")
        self.canvas.tag_lower("card_bg")


class RoundedBox(tk.Canvas):
    """尺寸随内容收缩的圆角容器，适合做消息气泡这类自适应宽度的元素。

    使用方式：box = RoundedBox(parent, ...); 把内容放进 box.body。
    """

    def __init__(self, parent, card_bg: str, page_bg: str = None, radius: int = 12,
                 pad_x: int = 14, pad_y: int = 9):
        self.page_bg = page_bg or COLORS_CSY["page"]
        self.card_bg = card_bg
        self.radius = radius
        self.pad_x = pad_x
        self.pad_y = pad_y
        super().__init__(parent, bg=self.page_bg, highlightthickness=0, bd=0)
        self.body = tk.Frame(self, bg=card_bg)
        self.window_id = self.create_window(
            radius + pad_x, radius + pad_y, anchor="nw", window=self.body)
        self.body.bind("<Configure>", self.sync_size_csy)
        self.sync_size_csy()

    def sync_size_csy(self, event=None) -> None:
        """按内容尺寸重算画布大小并重画圆角底。"""
        width = self.body.winfo_reqwidth() + (self.radius + self.pad_x) * 2
        height = self.body.winfo_reqheight() + (self.radius + self.pad_y) * 2
        self.configure(width=width, height=height)
        self.delete("bubble_bg")
        draw_round_rect_csy(self, 0, 0, width, height, self.radius,
                            fill=self.card_bg, outline=self.card_bg, tags="bubble_bg")
        self.tag_lower("bubble_bg")


class Tooltip:
    """悬停提示：鼠标停在控件上时弹出一行说明。"""

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show_csy, add="+")
        widget.bind("<Leave>", self.hide_csy, add="+")
        widget.bind("<ButtonPress>", self.hide_csy, add="+")

    def show_csy(self, event=None) -> None:
        """在控件下方弹出提示框。"""
        if self.tip or not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=self.text, bg="#2B3441", fg="#FFFFFF",
                 font=FONTS_CSY["tiny"], padx=8, pady=4).pack()
        self.tip.update_idletasks()
        x = self.widget.winfo_rootx() + 6
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip.geometry("+%d+%d" % (x, y))

    def hide_csy(self, event=None) -> None:
        """收起提示框。"""
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


class SegmentedControl(tk.Frame):
    """分段控件：一组互斥选项，用来切换模式（例如图表类型）。"""

    def __init__(self, parent, options: list, value: str = None, command=None,
                 bg: str = None):
        self.track_bg = bg or COLORS_CSY["surface_alt"]
        super().__init__(parent, bg=self.track_bg)
        self.command = command
        self.value = value or options[0]
        self.labels = {}
        for option in options:
            label = tk.Label(self, text=option, font=FONTS_CSY["tiny"],
                             cursor="hand2", padx=10, pady=3)
            label.pack(side="left", padx=1, pady=1)
            label.bind("<Button-1>", lambda event, name=option: self.select_csy(name))
            self.labels[option] = label
        self.refresh_csy()

    def select_csy(self, option: str) -> None:
        """选中某个选项并通知调用方。"""
        if option == self.value:
            return
        self.value = option
        self.refresh_csy()
        if self.command:
            self.command(option)

    def refresh_csy(self) -> None:
        """刷新各选项的选中样式。"""
        for option, label in self.labels.items():
            if option == self.value:
                label.configure(bg="#FFFFFF", fg=COLORS_CSY["accent"],
                                font=(FONTS_CSY["tiny"][0], FONTS_CSY["tiny"][1], "bold"))
            else:
                label.configure(bg=self.track_bg, fg=COLORS_CSY["muted"],
                                font=FONTS_CSY["tiny"])


# 各类按钮的外观：底色 / 悬停底色 / 文字色
BUTTON_KINDS_CSY = {
    "primary": ("#2F6FED", "#2A64D6", "#FFFFFF"),
    "ghost": ("#F2EFE8", "#E7E1D5", "#57514A"),
    "plain": ("#FFFFFF", "#F4F1EA", "#57514A"),
}


class StatBox(tk.Frame):
    """小统计块：上面一个大数字，下面一行说明，用于展示数据源规模。"""

    def __init__(self, parent, label: str, value: str = "-", background: str = None):
        background = background or COLORS_CSY["surface_alt"]
        super().__init__(parent, bg=background, padx=10, pady=8)
        self.value_label_csy = tk.Label(self, text=value, bg=background,
                                        fg=COLORS_CSY["text"], font=FONTS_CSY["title"])
        self.value_label_csy.pack(anchor="w")
        tk.Label(self, text=label, bg=background, fg=COLORS_CSY["muted"],
                 font=FONTS_CSY["tiny"]).pack(anchor="w")

    def set_value_csy(self, value: str) -> None:
        """更新大数字。"""
        self.value_label_csy.configure(text=value)


def make_button_csy(parent, text: str, command, kind: str = "ghost",
                    icon_name: str = "", tooltip: str = "", padx: int = 12,
                    pady: int = 6, font=None):
    """统一风格的扁平按钮，可选配一个前缀图标。"""
    background, hover, foreground = BUTTON_KINDS_CSY.get(kind, BUTTON_KINDS_CSY["ghost"])
    label = text
    if icon_name:
        glyph = icon_csy(icon_name)
        if glyph:
            label = "%s  %s" % (glyph, text) if text else glyph
    button = tk.Button(
        parent, text=label, command=command, font=font or FONTS_CSY["small"],
        bg=background, fg=foreground, activebackground=hover, activeforeground=foreground,
        relief="flat", bd=0, highlightthickness=0, padx=padx, pady=pady, cursor="hand2")
    if tooltip:
        Tooltip(button, tooltip)
    return button


def make_pill_csy(parent, text: str, foreground: str, background: str) -> tk.Label:
    """小标记：用于"来源""已自动修正"这类状态说明。"""
    return tk.Label(parent, text=text, fg=foreground, bg=background,
                    font=FONTS_CSY["tiny"], padx=8, pady=2)


def make_icon_csy(parent, icon_name: str, color: str = None,
                  background: str = None, size: int = 11) -> tk.Label:
    """一个纯图标标签；没有图标字体时返回空标签。"""
    glyph = icon_csy(icon_name)
    return tk.Label(parent, text=glyph, fg=color or COLORS_CSY["muted"],
                    bg=background or COLORS_CSY["surface"],
                    font=(ICON_FONT_CSY, size) if glyph else FONTS_CSY["tiny"])
