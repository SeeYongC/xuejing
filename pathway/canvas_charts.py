"""自绘图表：环形图、柱状图、折线图。

不用 matplotlib，也不用 pyecharts：
    - matplotlib 体积大、默认样式偏"学术"
    - pyecharts 面向网页，嵌入 Tkinter 需要浏览器内核
这里直接用 Canvas 绘制，风格扁平、无外部依赖，打包后体积更小。
"""

import tkinter as tk

from .theme import COLORS_CSY, FONTS_CSY

PALETTE_CSY = [
    "#2F6FED", "#12B886", "#F2A33C", "#E8590C",
    "#7048E8", "#159AA8", "#D6336C", "#6BA829", "#7B8794",
]

GRID_COLOR_CSY = "#EDF0F5"
AXIS_COLOR_CSY = "#DCE1E9"
TEXT_COLOR_CSY = "#6B7280"


class ChartBase(tk.Canvas):
    """图表基类：处理尺寸变化与标题。"""

    def __init__(self, parent, height: int = 260, title: str = ""):
        super().__init__(parent, bg=COLORS_CSY["surface"], highlightthickness=0, bd=0,
                         width=640, height=height)
        self.chart_title_csy = title
        self.bind("<Configure>", lambda event: self.redraw_csy())

    def redraw_csy(self) -> None:
        """子类实现具体绘制。"""
        raise NotImplementedError

    def draw_title_csy(self) -> None:
        """在顶部居中画标题。"""
        if self.chart_title_csy:
            self.create_text(self.chart_width_csy() / 2, 16, text=self.chart_title_csy,
                             fill="#4B5563", font=FONTS_CSY["small"])

    def chart_width_csy(self) -> int:
        """取绘制宽度；窗口未映射时退回控件配置的宽度。"""
        width = self.winfo_width()
        if width <= 1:
            try:
                width = int(self.cget("width")) or 640
            except (TypeError, ValueError):
                width = 640
        return width

    def chart_height_csy(self) -> int:
        """取绘制高度；窗口未映射时退回控件配置的高度。"""
        height = self.winfo_height()
        if height <= 1:
            try:
                height = int(self.cget("height")) or 280
            except (TypeError, ValueError):
                height = 280
        return height


class DonutChart(ChartBase):
    """环形图：适合看占比。"""

    def __init__(self, parent, data: list, title: str = "", height: int = 280):
        self.data_csy = data
        super().__init__(parent, height=height, title=title)

    def redraw_csy(self) -> None:
        self.delete("all")
        width = self.chart_width_csy()
        height = self.chart_height_csy()
        if width < 60 or not self.data_csy:
            return
        self.draw_title_csy()

        total = sum(value for _, value in self.data_csy) or 1
        # 左侧画环，右侧画图例
        diameter = min(height - 60, width * 0.45)
        left = 24
        top = (height - diameter) / 2 + 8
        box = (left, top, left + diameter, top + diameter)

        start = 90.0
        for index, (label, value) in enumerate(self.data_csy):
            extent = -360.0 * value / total
            self.create_arc(*box, start=start, extent=extent, fill=PALETTE_CSY[index % len(PALETTE_CSY)],
                            outline=COLORS_CSY["surface"], width=2, style="pieslice")
            start += extent

        # 中间挖空形成环形
        inner = diameter * 0.55
        cx = left + diameter / 2
        cy = top + diameter / 2
        self.create_oval(cx - inner / 2, cy - inner / 2, cx + inner / 2, cy + inner / 2,
                         fill=COLORS_CSY["surface"], outline=COLORS_CSY["surface"])
        self.create_text(cx, cy - 8, text="合计", fill=TEXT_COLOR_CSY,
                         font=FONTS_CSY["tiny"])
        self.create_text(cx, cy + 10, text="%.0f%%" % 100, fill=COLORS_CSY["text"],
                         font=FONTS_CSY["section"])

        legend_x = left + diameter + 28
        legend_y = top + 6
        for index, (label, value) in enumerate(self.data_csy):
            color = PALETTE_CSY[index % len(PALETTE_CSY)]
            self.create_rectangle(legend_x, legend_y, legend_x + 10, legend_y + 10,
                                  fill=color, outline=color)
            self.create_text(legend_x + 18, legend_y + 5, anchor="w",
                             text="%s  %.1f%%" % (label, value * 100.0 / total),
                             fill=COLORS_CSY["text_sub"], font=FONTS_CSY["tiny"])
            legend_y += 22
            if legend_y > height - 24:
                break


class BarChart(ChartBase):
    """柱状图：适合做分类对比。"""

    def __init__(self, parent, labels: list, values: list, xlabel: str = "",
                 ylabel: str = "", title: str = "", height: int = 280):
        self.labels_csy = labels
        self.values_csy = values
        self.xlabel_csy = xlabel
        self.ylabel_csy = ylabel
        super().__init__(parent, height=height, title=title)

    def redraw_csy(self) -> None:
        self.delete("all")
        width = self.chart_width_csy()
        height = self.chart_height_csy()
        if width < 80 or not self.values_csy:
            return
        self.draw_title_csy()

        left, right = 62, 24
        top, bottom = 44, 56
        plot_w = width - left - right
        plot_h = height - top - bottom
        if plot_w <= 0 or plot_h <= 0:
            return

        max_value = max(self.values_csy) or 1
        # 网格与纵轴刻度
        for step in range(5):
            value = max_value * step / 4
            y = top + plot_h - plot_h * step / 4
            self.create_line(left, y, left + plot_w, y, fill=GRID_COLOR_CSY)
            self.create_text(left - 8, y, anchor="e", text="%.0f" % value,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])
        self.create_line(left, top, left, top + plot_h, fill=AXIS_COLOR_CSY)
        self.create_line(left, top + plot_h, left + plot_w, top + plot_h,
                         fill=AXIS_COLOR_CSY)

        count = len(self.values_csy)
        slot = plot_w / max(count, 1)
        bar_width = min(slot * 0.58, 46)
        for index, (label, value) in enumerate(zip(self.labels_csy, self.values_csy)):
            center = left + slot * (index + 0.5)
            bar_h = plot_h * value / max_value
            x1 = center - bar_width / 2
            x2 = center + bar_width / 2
            y1 = top + plot_h - bar_h
            y2 = top + plot_h
            color = PALETTE_CSY[0] if value == max_value else "#B9CCF5"
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
            self.create_text(center, y1 - 7, text="%.1f" % value,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])
            self.create_text(center, top + plot_h + 10, text=str(label),
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"], angle=0)

        if self.xlabel_csy:
            self.create_text(left + plot_w / 2, height - 16, text=self.xlabel_csy,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])
        if self.ylabel_csy:
            self.create_text(14, top + plot_h / 2, text=self.ylabel_csy,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"], angle=90)


class LineChart(ChartBase):
    """折线图：适合看趋势。"""

    def __init__(self, parent, labels: list, values: list, xlabel: str = "",
                 ylabel: str = "", title: str = "", height: int = 280):
        self.labels_csy = labels
        self.values_csy = values
        self.xlabel_csy = xlabel
        self.ylabel_csy = ylabel
        super().__init__(parent, height=height, title=title)

    def redraw_csy(self) -> None:
        self.delete("all")
        width = self.chart_width_csy()
        height = self.chart_height_csy()
        if width < 80 or len(self.values_csy) < 2:
            return
        self.draw_title_csy()

        left, right = 62, 24
        top, bottom = 44, 56
        plot_w = width - left - right
        plot_h = height - top - bottom
        if plot_w <= 0 or plot_h <= 0:
            return

        max_value = max(self.values_csy) or 1
        min_value = min(self.values_csy)
        span = (max_value - min_value) or 1

        for step in range(5):
            value = min_value + span * step / 4
            y = top + plot_h - plot_h * step / 4
            self.create_line(left, y, left + plot_w, y, fill=GRID_COLOR_CSY)
            self.create_text(left - 8, y, anchor="e", text="%.0f" % value,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])
        self.create_line(left, top, left, top + plot_h, fill=AXIS_COLOR_CSY)
        self.create_line(left, top + plot_h, left + plot_w, top + plot_h,
                         fill=AXIS_COLOR_CSY)

        count = len(self.values_csy)
        points = []
        for index, value in enumerate(self.values_csy):
            x = left + plot_w * index / max(count - 1, 1)
            y = top + plot_h - plot_h * (value - min_value) / span
            points.append((x, y))

        # 面积
        polygon = [(left, top + plot_h)] + points + [(left + plot_w, top + plot_h)]
        self.create_polygon([coord for point in polygon for coord in point],
                            fill="#E9F0FE", outline="")
        # 折线
        self.create_line([coord for point in points for coord in point],
                         fill=PALETTE_CSY[0], width=2.5, smooth=True)
        for index, (label, (x, y)) in enumerate(zip(self.labels_csy, points)):
            self.create_oval(x - 4, y - 4, x + 4, y + 4,
                             fill=COLORS_CSY["surface"], outline=PALETTE_CSY[0], width=2)
            self.create_text(x, top + plot_h + 10, text=str(label),
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])
            if index == max(range(count), key=lambda i: self.values_csy[i]):
                self.create_text(x, y - 12, text="%.1f" % self.values_csy[index],
                                 fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])

        if self.xlabel_csy:
            self.create_text(left + plot_w / 2, height - 16, text=self.xlabel_csy,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"])
        if self.ylabel_csy:
            self.create_text(14, top + plot_h / 2, text=self.ylabel_csy,
                             fill=TEXT_COLOR_CSY, font=FONTS_CSY["tiny"], angle=90)
