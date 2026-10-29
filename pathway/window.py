"""主窗口：左侧导航 + 右侧内容区。

界面按"学生想知道什么"组织成五个页面：
    数据总览   这批数据从哪来、覆盖什么范围
    专插本     专科升本科：能报什么专业、考什么、分数线多少
    考研       读研的国家线门槛与走势
    就业       毕业生真实去向与升学情况
    路径对比   把几条路放在一起比时间成本与可行性

界面只负责展示，取数与统计交给 database.py 与 analysis.py。
"""

import tkinter as tk
from tkinter import ttk

from .analysis import PathAnalysis
from .auth import (
    BUDGETS_CSY,
    EDUCATION_LEVELS_CSY,
    GOALS_CSY,
    GRADES_CSY,
    REGIONS_CSY,
    SCORE_BANDS_CSY,
    UserStore,
)
from .canvas_charts import BarChart, DonutChart, LineChart
from .config import load_config_csy, update_config_csy
from .database import PathwayDatabase
from .dialogs import AboutDialog, DataSourceDialog
from .eligibility import (
    STATUS_AVAILABLE_CSY,
    STATUS_NOT_YET_CSY,
    STATUS_VERIFY_CSY,
    diagnose_all_csy,
)
from .paths import (
    APP_FULL_NAME_CSY,
    APP_NAME_CSY,
    APP_VERSION_CSY,
    database_file_csy,
    users_file_csy,
)
from .theme import COLORS_CSY, FONTS_CSY, ICON_FONT_CSY, apply_theme_csy, icon_csy
from .widgets import (
    RoundedCard,
    StatBox,
    Tooltip,
    draw_round_rect_csy,
    make_button_csy,
    make_icon_csy,
    make_pill_csy,
)

# 导航分组：决策链四步 + 数据查询 + 数据总览
NAV_GROUPS_CSY = [
    ("决策链", [
        ("profile", "1. 我的情况", "hint"),
        ("eligibility", "2. 资格诊断", "checked"),
        ("compare", "3. 路径比较", "chart"),
        ("action", "4. 行动计划", "table"),
    ]),
    ("数据查询", [
        ("zsb", "专插本", "table"),
        ("kaoyan", "考研", "chart"),
        ("employment", "就业去向", "database"),
        ("kaogong", "考公", "database"),
    ]),
    ("", [
        ("overview", "数据总览", "table"),
    ]),
]

# 扁平化，便于按 key 查名称
NAV_ITEMS_CSY = [(key, label, icon)
                 for _, items in NAV_GROUPS_CSY
                 for key, label, icon in items]

# 页面标题下方的一句话说明
PAGE_HINTS_CSY = {
    "profile": "先把自己的情况填清楚，后面的诊断和比较才有依据",
    "eligibility": "只判断「能不能报」，不预测录取概率；不确定的条件会列为待核实",
    "compare": "时间、费用、报考范围、职业目标、主要风险五个维度放在一起看",
    "action": "把前面的诊断变成可以执行的下一步",
    "zsb": "选专业看考试科目，对照历年省控线判断难度",
    "kaoyan": "国家线是进入复试的最低门槛，A 类考生适用于广东",
    "employment": "毕业生的真实去向，含升学、单位性质与地区分布",
    "kaogong": "广东省考的计划招录、合格线与职位表",
    "overview": "系统用到的数据全部来自官方公开渠道，可逐条追溯",
}


class MainWindow:
    """学历路径分析与推荐系统主窗口。"""

    def __init__(self, root: tk.Tk, user: dict = None, profile: dict = None):
        self.root = root
        self.user = user or {}
        self.profile = profile or {}
        self.db = PathwayDatabase(database_file_csy())
        self.analysis = PathAnalysis(self.db)
        self.current_page_csy = None
        self.nav_buttons_csy = {}

        self.root.title("%s v%s" % (APP_NAME_CSY, APP_VERSION_CSY))
        self.fit_window_csy()
        apply_theme_csy(self.root)

        self.status_var_csy = tk.StringVar(value="就绪")
        self.build_csy()
        self.show_page_csy("overview")

    def fit_window_csy(self) -> None:
        """按屏幕自适应窗口尺寸并居中。"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(1320, max(940, int(screen_width * 0.78)))
        height = min(880, max(700, int(screen_height * 0.82)))
        left = max(0, (screen_width - width) // 2)
        top = max(0, (screen_height - height) // 2 - 20)
        self.root.geometry("%dx%d+%d+%d" % (width, height, left, top))
        self.root.minsize(min(940, width), min(700, height))

    # ------------------------------------------------------------------ 骨架

    def build_csy(self) -> None:
        """搭建标题栏、左侧导航、右侧内容区与状态栏。"""
        self.build_header_csy()
        body = tk.Frame(self.root, bg=COLORS_CSY["page"])
        body.pack(fill="both", expand=True)
        self.build_nav_csy(body)
        self.build_content_csy(body)
        self.build_statusbar_csy()

    def build_header_csy(self) -> None:
        """顶部标题栏：品牌标识与系统全称。"""
        header = tk.Frame(self.root, bg=COLORS_CSY["surface"])
        header.pack(fill="x")
        tk.Frame(self.root, bg=COLORS_CSY["border"], height=1).pack(fill="x")

        left = tk.Frame(header, bg=COLORS_CSY["surface"])
        left.pack(side="left", padx=(18, 0), pady=11)
        mark = tk.Canvas(left, width=34, height=34, bg=COLORS_CSY["surface"],
                         highlightthickness=0, bd=0)
        mark.pack(side="left")
        draw_round_rect_csy(mark, 1, 1, 33, 33, 9,
                            fill=COLORS_CSY["accent"], outline=COLORS_CSY["accent"])
        glyph = icon_csy("chart")
        mark.create_text(17, 18, text=glyph or "径", fill="#FFFFFF",
                         font=(ICON_FONT_CSY, 13) if glyph else FONTS_CSY["title"])

        titles = tk.Frame(left, bg=COLORS_CSY["surface"])
        titles.pack(side="left", padx=(10, 0))
        tk.Label(titles, text=APP_NAME_CSY, bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text"], font=FONTS_CSY["brand"]).pack(anchor="w")
        tk.Label(titles, text="面向广东省专科与本科在校生的升学就业数据工具",
                 bg=COLORS_CSY["surface"], fg=COLORS_CSY["muted"],
                 font=FONTS_CSY["tiny"]).pack(anchor="w")

        right = tk.Frame(header, bg=COLORS_CSY["surface"])
        right.pack(side="right", padx=(0, 18))
        username = self.user.get("username", "")
        if username:
            tk.Label(right, text="你好，%s" % username, bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(
                side="left", padx=(0, 10))
            make_button_csy(right, "退出", self.logout_csy, kind="ghost").pack(
                side="left", padx=(0, 8))
        make_button_csy(right, "数据来源", self.open_sources_csy, kind="ghost",
                        icon_name="database").pack(side="left", padx=(0, 8))
        make_button_csy(right, "关于", self.open_about_csy, kind="ghost").pack(side="left")
        make_pill_csy(right, "广东 · 专升本 + 考研 + 就业",
                      COLORS_CSY["accent"], COLORS_CSY["accent_soft"]).pack(
            side="left", padx=(0, 10))

    def build_nav_csy(self, parent) -> None:
        """左侧导航栏。"""
        nav = tk.Frame(parent, bg=COLORS_CSY["surface"], width=180)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        tk.Frame(parent, bg=COLORS_CSY["border"], width=1).pack(side="left", fill="y")

        for group_name, items in NAV_GROUPS_CSY:
            if group_name:
                tk.Label(nav, text=group_name, bg=COLORS_CSY["surface"],
                         fg=COLORS_CSY["muted"], font=FONTS_CSY["tiny"]).pack(
                    anchor="w", padx=16, pady=(14, 4))
            for key, label, icon_name in items:
                glyph = icon_csy(icon_name)
                text = ("%s   %s" % (glyph, label)) if glyph else label
                button = tk.Label(nav, text=text,
                                  bg=COLORS_CSY["surface"], fg=COLORS_CSY["text_sub"],
                                  font=FONTS_CSY["small"], anchor="w",
                                  padx=12, pady=7, cursor="hand2")
                button.pack(fill="x", padx=8, pady=1)
                button.bind("<Button-1>", lambda event, name=key: self.show_page_csy(name))
                button.bind("<Enter>", lambda event, widget=button: self.hover_nav_csy(widget, True))
                button.bind("<Leave>", lambda event, widget=button: self.hover_nav_csy(widget, False))
                self.nav_buttons_csy[key] = button

        tk.Frame(nav, bg=COLORS_CSY["surface"], height=12).pack()

    def build_content_csy(self, parent) -> None:
        """右侧内容区：标题 + 可滚动页面容器。"""
        wrapper = tk.Frame(parent, bg=COLORS_CSY["page"])
        wrapper.pack(side="left", fill="both", expand=True)

        head = tk.Frame(wrapper, bg=COLORS_CSY["page"])
        head.pack(fill="x", padx=20, pady=(16, 6))
        self.page_title_csy = tk.Label(head, text="", bg=COLORS_CSY["page"],
                                       fg=COLORS_CSY["text"], font=FONTS_CSY["title"])
        self.page_title_csy.pack(anchor="w")
        self.page_hint_csy = tk.Label(head, text="", bg=COLORS_CSY["page"],
                                      fg=COLORS_CSY["muted"], font=FONTS_CSY["small"])
        self.page_hint_csy.pack(anchor="w", pady=(2, 0))

        area = tk.Frame(wrapper, bg=COLORS_CSY["page"])
        area.pack(fill="both", expand=True)
        self.content_canvas_csy = tk.Canvas(area, bg=COLORS_CSY["page"],
                                            highlightthickness=0, bd=0)
        self.content_canvas_csy.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(area, orient="vertical",
                            style="Thin.Vertical.TScrollbar",
                            command=self.content_canvas_csy.yview)
        bar.pack(side="right", fill="y", padx=(4, 6))
        self.content_canvas_csy.configure(yscrollcommand=bar.set)

        self.content_inner_csy = tk.Frame(self.content_canvas_csy, bg=COLORS_CSY["page"])
        self.content_window_csy = self.content_canvas_csy.create_window(
            (0, 0), window=self.content_inner_csy, anchor="nw")
        self.content_inner_csy.bind(
            "<Configure>",
            lambda event: self.content_canvas_csy.configure(
                scrollregion=self.content_canvas_csy.bbox("all")))
        self.content_canvas_csy.bind(
            "<Configure>",
            lambda event: self.content_canvas_csy.itemconfigure(
                self.content_window_csy, width=event.width))
        self.root.bind("<MouseWheel>", self.on_mousewheel_csy)

    def build_statusbar_csy(self) -> None:
        """底部状态栏。"""
        tk.Frame(self.root, bg=COLORS_CSY["border"], height=1).pack(fill="x", side="bottom")
        bar = tk.Frame(self.root, bg=COLORS_CSY["surface"])
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self.status_var_csy, bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["tiny"]).pack(
            side="left", padx=16, pady=6)
        tk.Label(bar, text=APP_FULL_NAME_CSY, bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["tiny"]).pack(
            side="right", padx=16, pady=6)

    # ------------------------------------------------------------------ 导航

    def hover_nav_csy(self, widget, entering: bool) -> None:
        """导航项悬停效果（选中项不参与）。"""
        if widget is self.nav_buttons_csy.get(self.current_page_csy):
            return
        widget.configure(bg=COLORS_CSY["surface_alt"] if entering
                         else COLORS_CSY["surface"])

    def show_page_csy(self, key: str) -> None:
        """切换页面：清空内容区并按 key 重新构建。"""
        self.current_page_csy = key
        for name, button in self.nav_buttons_csy.items():
            if name == key:
                button.configure(bg=COLORS_CSY["accent_soft"], fg=COLORS_CSY["accent"])
            else:
                button.configure(bg=COLORS_CSY["surface"], fg=COLORS_CSY["text_sub"])

        label = dict((item[0], item[1]) for item in NAV_ITEMS_CSY).get(key, "")
        self.page_title_csy.configure(text=label)
        self.page_hint_csy.configure(text=PAGE_HINTS_CSY.get(key, ""))

        for child in self.content_inner_csy.winfo_children():
            child.destroy()
        builder = {
            "profile": self.build_profile_csy,
            "eligibility": self.build_eligibility_csy,
            "compare": self.build_compare_csy,
            "action": self.build_action_csy,
            "zsb": self.build_zsb_csy,
            "kaoyan": self.build_kaoyan_csy,
            "employment": self.build_employment_csy,
            "kaogong": self.build_kaogong_csy,
            "overview": self.build_overview_csy,
        }.get(key)
        if builder:
            builder(self.content_inner_csy)
        self.content_canvas_csy.yview_moveto(0)
        self.set_status_csy("已切换到「%s」" % label)
        # 记住用户停留的页面，下次启动直接回到这里
        update_config_csy(last_page=key)

    def on_mousewheel_csy(self, event) -> None:
        """滚轮滚动内容区。"""
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        while widget is not None:
            if widget is self.content_canvas_csy:
                self.content_canvas_csy.yview_scroll(int(-event.delta / 120), "units")
                return
            widget = getattr(widget, "master", None)

    def set_status_csy(self, text: str) -> None:
        """更新状态栏。"""
        self.status_var_csy.set(text)

    def open_sources_csy(self) -> None:
        """打开数据来源说明框。"""
        DataSourceDialog(self.root, self.db.list_sources_csy())
        self.set_status_csy("已查看数据来源说明")

    def open_about_csy(self) -> None:
        """打开关于框。"""
        AboutDialog(self.root, APP_FULL_NAME_CSY, APP_VERSION_CSY)

    def logout_csy(self) -> None:
        """退出当前账号，关闭程序。"""
        self.root.destroy()

    # ------------------------------------------------------------------ 个性化引导

    def guidance_items_csy(self) -> list:
        """根据个人档案给出「先看什么」的建议。

        返回若干条 {"title", "text", "page"}，page 是点击后跳转的页面标识。
        """
        level = self.profile.get("education_level", "")
        grade = self.profile.get("grade", "")
        goal = self.profile.get("goal", "")
        major = self.profile.get("major", "")

        items = []
        # 档案不完整时，第一件事是补全
        if not all((level, grade, goal)):
            items.append({
                "title": "第一步：完善「我的情况」",
                "text": "学历、专业、年级、成绩、预算、地区、职业目标——"
                        "这些是后面资格诊断和路径比较的依据。",
                "page": "profile",
            })

        if level and grade and goal:
            items.append({
                "title": "第二步：做一次资格诊断",
                "text": "系统只判断「能不能报」，不预测录取概率；"
                        "不确定的条件会列为待核实项。",
                "page": "eligibility",
            })
            items.append({
                "title": "第三步：比较几条路",
                "text": "时间、费用、报考范围、职业目标、主要风险放在一起看，"
                        "再决定优先准备哪一条。",
                "page": "compare",
            })
            items.append({
                "title": "第四步：拿到行动计划",
                "text": "把诊断结果转成考试科目、关键时间节点和待核实事项。",
                "page": "action",
            })

        if level == "专科" and "升学" in goal:
            items.append({
                "title": "专科读研的三条路",
                "text": "专插本后再考研、同等学力直考、自考本科再考研，"
                        "时间与可报范围差别很大，先看清再选。",
                "page": "compare",
            })
        elif level == "本科" and "升学" in goal:
            items.append({
                "title": "先看考研国家线",
                "text": "在「考研」页选你的学科门类，看近五年国家线走势，"
                        "判断自己需要考到什么水平。",
                "page": "kaoyan",
            })
        elif "就业" in goal:
            items.append({
                "title": "先看往届去向",
                "text": "在「就业去向」页选择届别，查看毕业生规模、落实率、"
                        "单位性质与地区分布。",
                "page": "employment",
            })

        if major:
            items.append({
                "title": "查「%s」对应的考试科目" % major,
                "text": "去「专插本」页输入这个专业，系统会列出公共课、"
                        "专业基础课与专业综合课。",
                "page": "zsb",
            })
        items.append({
            "title": "看看考公这条去向",
            "text": "广东省考 2026 年计划招录 11779 人，职位表 9344 个职位，"
                    "可以在「考公」页按学历与系统查看。",
            "page": "kaogong",
        })
        return items

    def build_guidance_csy(self, parent) -> None:
        """在总览页顶部放一张「给你的建议」卡片。"""
        items = self.guidance_items_csy()
        if not items:
            return
        nickname = self.profile.get("major") or self.user.get("username", "")
        body = self.make_section_csy(parent, "给你的建议", "hint")
        if nickname:
            self.add_note_csy(body, "根据你填写的资料（%s），先从这里开始："
                               % self.profile_summary_csy(), level="key")

        for index, item in enumerate(items, 1):
            row = tk.Frame(body, bg=COLORS_CSY["surface"])
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text="%d" % index, bg=COLORS_CSY["accent_soft"],
                     fg=COLORS_CSY["accent"], font=FONTS_CSY["tiny"],
                     width=2, padx=4, pady=2).pack(side="left", padx=(0, 10))
            text = tk.Frame(row, bg=COLORS_CSY["surface"])
            text.pack(side="left", fill="x", expand=True)
            tk.Label(text, text=item["title"], bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text"], font=FONTS_CSY["small"],
                     anchor="w").pack(fill="x")
            tk.Label(text, text=item["text"], bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["muted"], font=FONTS_CSY["tiny"],
                     anchor="w", justify="left", wraplength=620).pack(fill="x")
            make_button_csy(row, "去看看",
                            lambda page=item["page"]: self.show_page_csy(page),
                            kind="plain", padx=10, pady=3).pack(side="right")
        tk.Frame(body, bg=COLORS_CSY["surface"], height=12).pack()

    def profile_summary_csy(self) -> str:
        """把个人档案拼成一句可读的摘要。"""
        parts = []
        for key in ("education_level", "major", "grade"):
            value = self.profile.get(key, "")
            if value:
                parts.append(value)
        goal = self.profile.get("goal", "")
        if goal:
            parts.append("目标：" + goal)
        return " · ".join(parts) if parts else "未填写"

    # ------------------------------------------------------------------ 通用构件

    def make_section_csy(self, parent, title: str, icon_name: str = "table") -> tk.Frame:
        """带标题的圆角卡片，返回卡片的 body 供继续放内容。"""
        card = RoundedCard(parent)
        card.pack(fill="x", padx=20, pady=(0, 14))
        head = tk.Frame(card.body, bg=COLORS_CSY["surface"])
        head.pack(fill="x", padx=16, pady=(14, 6))
        make_icon_csy(head, icon_name, COLORS_CSY["accent"]).pack(side="left")
        tk.Label(head, text=title, bg=COLORS_CSY["surface"], fg=COLORS_CSY["text"],
                 font=FONTS_CSY["section"]).pack(side="left", padx=(6, 0))
        return card.body

    def add_note_csy(self, parent, text: str, level: str = "info") -> None:
        """在卡片里加一行说明文字。"""
        palette = {
            "info": COLORS_CSY["muted"],
            "warn": COLORS_CSY["amber"],
            "key": COLORS_CSY["accent"],
        }
        tk.Label(parent, text=text, bg=COLORS_CSY["surface"],
                 fg=palette.get(level, palette["info"]), font=FONTS_CSY["small"],
                 justify="left", anchor="w", wraplength=780).pack(
            fill="x", padx=16, pady=(0, 6))

    def add_stat_row_csy(self, parent, items: list) -> None:
        """一行统计块：[{label, value}, ...]。"""
        row = tk.Frame(parent, bg=COLORS_CSY["surface"])
        row.pack(fill="x", padx=16, pady=(4, 12))
        for index, item in enumerate(items):
            box = StatBox(row, item["label"], str(item["value"]))
            box.pack(side="left", fill="x", expand=True,
                     padx=(0 if index == 0 else 8, 0))

    def add_table_csy(self, parent, columns: list, rows: list, height: int = 8) -> None:
        """在卡片里放一张只读表格。"""
        if not columns:
            return
        holder = tk.Frame(parent, bg=COLORS_CSY["surface"])
        holder.pack(fill="x", padx=16, pady=(0, 14))
        grid = tk.Frame(holder, bg=COLORS_CSY["surface"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)

        names = ["c%d" % index for index in range(len(columns))]
        tree = ttk.Treeview(grid, columns=names, show="headings",
                            height=min(max(len(rows), 1), height))
        for index, name in enumerate(names):
            tree.heading(name, text=str(columns[index]), anchor="w")
            tree.column(name, width=180 if index == 0 else 130,
                        minwidth=90, anchor="w", stretch=True)
        tree.tag_configure("odd", background=COLORS_CSY["surface_alt"])
        for position, row in enumerate(rows):
            tree.insert("", "end", tags=("odd",) if position % 2 else (),
                        values=[self.format_cell_csy(value) for value in row])
        vertical = ttk.Scrollbar(grid, orient="vertical",
                                 style="Thin.Vertical.TScrollbar", command=tree.yview)
        tree.configure(yscrollcommand=vertical.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        if len(columns) > 3:
            horizontal = ttk.Scrollbar(grid, orient="horizontal",
                                       style="Thin.Horizontal.TScrollbar",
                                       command=tree.xview)
            tree.configure(xscrollcommand=horizontal.set)
            horizontal.grid(row=1, column=0, sticky="ew")

    @staticmethod
    def format_cell_csy(value) -> str:
        """表格单元格显示格式。"""
        if value is None:
            return ""
        if isinstance(value, float):
            return format(int(value), ",") if value == int(value) else "%.2f" % value
        return str(value)

    def add_chart_csy(self, parent, columns: list, rows: list, chart_type: str = "bar",
                      height: float = 2.7, xlabel: str = "", ylabel: str = "",
                      title: str = "") -> None:
        """在卡片里嵌一张自绘图表，横纵轴标签与标题都由调用方明确给出。"""
        if not rows:
            return
        holder = tk.Frame(parent, bg=COLORS_CSY["surface"])
        holder.pack(fill="x", padx=16, pady=(0, 14))
        labels = [str(row[0]) for row in rows]
        try:
            values = [float(row[1]) for row in rows]
        except (TypeError, ValueError, IndexError):
            return
        pixel_height = int(height * 90)
        if chart_type == "pie":
            chart = DonutChart(holder, list(zip(labels, values)),
                               title=title, height=pixel_height)
        elif chart_type == "line":
            chart = LineChart(holder, labels, values, xlabel=xlabel,
                              ylabel=ylabel, title=title, height=pixel_height)
        else:
            chart = BarChart(holder, labels, values, xlabel=xlabel,
                             ylabel=ylabel, title=title, height=pixel_height)
        chart.pack(fill="x")

    # ------------------------------------------------------------------ 页面：数据总览

    def build_overview_csy(self, parent) -> None:
        """数据总览：这批数据从哪来、覆盖什么范围、最关键的发现是什么。"""
        self.build_guidance_csy(parent)
        sources = self.db.list_sources_csy()
        major_count = len(self.db.list_zsb_majors_csy())
        line_count = len(self.db.kaoyan_latest_csy())

        body = self.make_section_csy(parent, "数据概况", "table")
        self.add_stat_row_csy(body, [
            {"label": "数据来源", "value": "%d 处" % len(sources)},
            {"label": "专升本专业", "value": "%d 个" % major_count},
            {"label": "考研学科门类", "value": "%d 个" % line_count},
            {"label": "就业届别", "value": "%d 届" % len(self.db.employment_years_csy())},
            {"label": "考公年份", "value": "%d 年" % len(self.db.list_kaogong_csy())},
        ])
        self.add_note_csy(
            body, "数据全部来自官方公开渠道（省教育考试院、高校就业质量报告、研招网），"
                  "每条记录都保留了来源链接，可在文档中逐条追溯。")

        body = self.make_section_csy(parent, "数据来源与覆盖范围", "database")
        self.add_table_csy(body, ["数据名称", "发布单位", "覆盖范围"],
                           [[s["name"], s["publisher"], s["coverage"]] for s in sources],
                           height=4)
        self.add_note_csy(
            body, "高校就业质量报告由学校自行统计发布，未经第三方核验，使用时请注意这一点。",
            level="warn")

        body = self.make_section_csy(parent, "升学率差异：说明结构，不说明优劣", "hint")
        rows = self.analysis.cross_level_rates_csy()
        if rows:
            compare = []
            for item in rows:
                compare.append([
                    "%s 届" % item.get("year", ""),
                    self.percent_text_csy(item.get("本科")),
                    self.percent_text_csy(item.get("专科")),
                    self.percent_text_csy(item.get("总体")),
                ])
            self.add_table_csy(body, ["届别", "本科升学率", "专科升学率", "总体升学率"],
                               compare, height=4)
            self.add_note_csy(
                body, "专科升学率高，主要是因为「专插本」本身就是专科生的主流选择；"
                      "本科升学率低，也不代表本科生发展差——本科生的主流方向是直接就业。"
                      "升学、就业、收入、职业发展是四个不同维度，不能用一个指标下结论。",
                level="key")

        body = self.make_section_csy(parent, "另一个维度：毕业去向落实率", "table")
        employment_rows = self.analysis.education_level_outcome_csy()
        if employment_rows:
            self.add_table_csy(
                body, ["届别", "学历", "统计人数", "就业人数", "落实率"],
                [["%s 届" % item["year"], item["学历"],
                  self.format_cell_csy(item.get("统计人数")),
                  self.format_cell_csy(item.get("就业人数")),
                  self.percent_text_csy(item.get("落实率"))]
                 for item in employment_rows], height=6)
            self.add_note_csy(
                body, "落实率统计的是「已落实毕业去向」，与升学率口径不同，"
                      "两者不能互相替代。", level="warn")

        body = self.make_section_csy(parent, "决策链进度", "checked")
        self.add_note_csy(
            body, "完成前三步后，首页会给出下一步行动；也可以直接点左侧导航进入任一步骤。",
            level="key")
        progress = tk.Frame(body, bg=COLORS_CSY["surface"])
        progress.pack(fill="x", padx=16, pady=(2, 14))
        steps = [("1. 我的情况", "profile"), ("2. 资格诊断", "eligibility"),
                 ("3. 路径比较", "compare"), ("4. 行动计划", "action")]
        for index, (label, page) in enumerate(steps):
            make_button_csy(progress, label,
                            lambda target=page: self.show_page_csy(target),
                            kind="ghost").pack(side="left", padx=(0, 8))

    @staticmethod
    def percent_text_csy(value) -> str:
        """百分比显示，缺数据时显示破折号。"""
        return "—" if value is None else "%.2f%%" % float(value)

    # ------------------------------------------------------------------ 页面：专插本

    def build_zsb_csy(self, parent) -> None:
        """专插本：查专业考什么、看省控线走势。"""
        body = self.make_section_csy(parent, "按专业查询考试科目", "table")
        controls = tk.Frame(body, bg=COLORS_CSY["surface"])
        controls.pack(fill="x", padx=16, pady=(2, 10))

        tk.Label(controls, text="专业关键词", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(side="left")
        self.zsb_keyword_var_csy = tk.StringVar(value="计算机")
        entry = ttk.Entry(controls, textvariable=self.zsb_keyword_var_csy, width=18)
        entry.pack(side="left", padx=(8, 12))
        entry.bind("<Return>", lambda event: self.refresh_zsb_csy())

        tk.Label(controls, text="学科门类", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(side="left")
        self.zsb_discipline_var_csy = tk.StringVar(value="全部")
        disciplines = ["全部"] + self.db.list_zsb_disciplines_csy()
        box = ttk.Combobox(controls, state="readonly", width=12,
                           values=disciplines, textvariable=self.zsb_discipline_var_csy)
        box.pack(side="left", padx=(8, 12))
        box.bind("<<ComboboxSelected>>", lambda event: self.refresh_zsb_csy())
        make_button_csy(controls, "查询", self.refresh_zsb_csy,
                        kind="primary", padx=14, pady=4).pack(side="left")

        self.zsb_result_holder_csy = tk.Frame(body, bg=COLORS_CSY["surface"])
        self.zsb_result_holder_csy.pack(fill="x")
        self.refresh_zsb_csy()

        body = self.make_section_csy(parent, "省控线走势（按专业基础课）", "chart")
        subjects = self.db.list_zsb_basic_subjects_csy()
        if subjects:
            self.subject_var_csy = tk.StringVar(value=subjects[-1])
            picker = tk.Frame(body, bg=COLORS_CSY["surface"])
            picker.pack(fill="x", padx=16, pady=(0, 8))
            tk.Label(picker, text="专业基础课", bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(side="left")
            subject_box = ttk.Combobox(picker, state="readonly", width=14,
                                       values=subjects, textvariable=self.subject_var_csy)
            subject_box.pack(side="left", padx=(8, 0))
            subject_box.bind("<<ComboboxSelected>>",
                             lambda event: self.refresh_zsb_chart_csy())
        self.zsb_chart_holder_csy = tk.Frame(body, bg=COLORS_CSY["surface"])
        self.zsb_chart_holder_csy.pack(fill="x")
        self.refresh_zsb_chart_csy()

        body = self.make_section_csy(parent, "报考条件提醒（广东省）", "hint")
        self.add_note_csy(
            body, "外省户籍但在广东就读的应届专科毕业生同样可以报考；"
                  "往届生需户籍连续满 3 年。考试科目为 2 门公共课 + 1 门专业基础课 + "
                  "1 门专业综合课，总分 500 分。")
        self.add_note_csy(
            body, "以上为广东省 2026 年招生工作规定的内容，报考前请以当年最新文件为准。",
            level="warn")

    def refresh_zsb_csy(self) -> None:
        """刷新专插本专业查询结果。"""
        for child in self.zsb_result_holder_csy.winfo_children():
            child.destroy()
        keyword = self.zsb_keyword_var_csy.get().strip()
        discipline = self.zsb_discipline_var_csy.get()
        if discipline == "全部":
            discipline = ""
        rows = self.db.list_zsb_majors_csy(keyword=keyword, discipline=discipline)
        if not rows:
            self.add_note_csy(self.zsb_result_holder_csy, "没有匹配的专业，换个关键词试试。",
                              level="warn")
            return
        table_rows = [[row["major_code"], row["major_name"], row["discipline"],
                       row["common_subjects"], row["basic_subject"],
                       row["comprehensive_subject"] or "院校自命题"]
                      for row in rows[:40]]
        self.add_table_csy(self.zsb_result_holder_csy,
                           ["专业代码", "专业名称", "学科门类", "公共课",
                            "专业基础课", "专业综合课"],
                           table_rows, height=8)
        self.add_note_csy(self.zsb_result_holder_csy,
                          "共匹配到 %d 个专业，表中显示前 %d 个。" % (len(rows), len(table_rows)))
        self.set_status_csy("专插本专业查询：匹配 %d 个专业" % len(rows))

    def refresh_zsb_chart_csy(self) -> None:
        """刷新省控线走势图。"""
        for child in self.zsb_chart_holder_csy.winfo_children():
            child.destroy()
        subject = self.subject_var_csy.get()
        trend = self.db.zsb_score_trend_csy(subject)
        if not trend:
            self.add_note_csy(self.zsb_chart_holder_csy, "该科目暂无省控线数据。", level="warn")
            return
        columns = ["年份", "三科总分线"]
        rows = [[str(item["year"]), item["total_line"]] for item in trend]
        self.add_chart_csy(self.zsb_chart_holder_csy, columns, rows, "line", height=2.4,
                           xlabel="年份", ylabel="三科总分线（分）",
                           title="%s 历年省控线" % subject)
        detail = [[str(item["year"]), item["total_line"], item["comprehensive_line"]]
                  for item in trend]
        self.add_table_csy(self.zsb_chart_holder_csy,
                           ["年份", "三科总分线", "专业综合课线"], detail, height=4)

    # ------------------------------------------------------------------ 页面：考研

    def build_kaoyan_csy(self, parent) -> None:
        """考研：国家线走势与最新门槛。"""
        body = self.make_section_csy(parent, "国家线走势（学术学位 / 专业学位合并线）", "chart")
        disciplines = self.db.list_kaoyan_disciplines_csy()
        if not disciplines:
            self.add_note_csy(body, "暂无国家线数据。", level="warn")
            return

        picker = tk.Frame(body, bg=COLORS_CSY["surface"])
        picker.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(picker, text="学科门类", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(side="left")
        default = "工学" if "工学" in disciplines else disciplines[0]
        self.kaoyan_discipline_var_csy = tk.StringVar(value=default)
        box = ttk.Combobox(picker, state="readonly", width=12,
                           values=disciplines, textvariable=self.kaoyan_discipline_var_csy)
        box.pack(side="left", padx=(8, 14))
        box.bind("<<ComboboxSelected>>", lambda event: self.refresh_kaoyan_csy())

        tk.Label(picker, text="考生类别", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(side="left")
        self.kaoyan_class_var_csy = tk.StringVar(value="A类考生")
        class_box = ttk.Combobox(picker, state="readonly", width=10,
                                 values=["A类考生", "B类考生"],
                                 textvariable=self.kaoyan_class_var_csy)
        class_box.pack(side="left", padx=(8, 0))
        class_box.bind("<<ComboboxSelected>>", lambda event: self.refresh_kaoyan_csy())

        self.kaoyan_holder_csy = tk.Frame(body, bg=COLORS_CSY["surface"])
        self.kaoyan_holder_csy.pack(fill="x")
        self.refresh_kaoyan_csy()

        body = self.make_section_csy(parent, "最新一年国家线总览", "table")
        latest = self.db.kaoyan_latest_csy()
        if latest:
            latest_year = latest[0]["year"]
            self.add_note_csy(
                body, "%d 年国家线（A 类考生）——总分线与两类单科线的最低要求" % latest_year,
                level="key")
            self.add_table_csy(
                body, ["学科门类", "总分线（分）",
                       "单科线（满分100分科目）", "单科线（满分150分科目）"],
                [[item["discipline"], item["total_line"],
                  item["single_subject_100"], item["single_subject_150"]]
                 for item in latest], height=8)
        self.add_note_csy(
            body, "A 类考生适用于广东等 21 个省市，B 类考生适用于内蒙古、广西、"
                  "海南、贵州、云南、西藏、甘肃、青海、宁夏、新疆等地区。", level="warn")

    def refresh_kaoyan_csy(self) -> None:
        """刷新国家线走势图与明细表。"""
        for child in self.kaoyan_holder_csy.winfo_children():
            child.destroy()
        discipline = self.kaoyan_discipline_var_csy.get()
        candidate_class = self.kaoyan_class_var_csy.get()
        trend = self.db.kaoyan_line_trend_csy(discipline, candidate_class)
        if not trend:
            self.add_note_csy(self.kaoyan_holder_csy, "该学科门类暂无数据。", level="warn")
            return
        columns = ["年份", "总分线"]
        rows = [[str(item["year"]), item["total_line"]] for item in trend]
        self.add_chart_csy(self.kaoyan_holder_csy, columns, rows, "line", height=2.4,
                           xlabel="年份", ylabel="总分线（分）",
                           title="%s 国家线走势（%s）" % (discipline, candidate_class))
        self.add_note_csy(
            self.kaoyan_holder_csy,
            "怎么读下面这张表：考研初试中，政治、英语满分 100 分，数学、专业课满分 150 分。"
            "国家线对这两类科目分别划最低单科线，任何一科低于对应分数线都不能进入复试。",
            level="key")
        tk.Label(self.kaoyan_holder_csy,
                 text="%s 各年份国家线明细（%s）" % (discipline, candidate_class),
                 bg=COLORS_CSY["surface"], fg=COLORS_CSY["text_sub"],
                 font=FONTS_CSY["small"]).pack(anchor="w", padx=16, pady=(4, 2))
        detail = [[str(item["year"]), item["total_line"],
                   item["single_subject_100"], item["single_subject_150"]]
                  for item in trend]
        self.add_table_csy(self.kaoyan_holder_csy,
                           ["年份", "总分线（分）",
                            "单科线（满分100分科目）", "单科线（满分150分科目）"],
                           detail, height=5)
        self.set_status_csy("考研国家线：%s · %s" % (discipline, candidate_class))

    # ------------------------------------------------------------------ 页面：就业去向

    def build_employment_csy(self, parent) -> None:
        """就业去向：毕业生规模、升学情况与流向。"""
        years = self.db.employment_years_csy()
        if not years:
            self.make_section_csy(parent, "暂无就业数据", "database")
            return

        body = self.make_section_csy(parent, "毕业生规模与升学", "database")
        picker = tk.Frame(body, bg=COLORS_CSY["surface"])
        picker.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(picker, text="届别", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(side="left")
        self.emp_year_var_csy = tk.StringVar(value="%s 届" % years[-1])
        box = ttk.Combobox(picker, state="readonly", width=10,
                           values=["%s 届" % y for y in years],
                           textvariable=self.emp_year_var_csy)
        box.pack(side="left", padx=(8, 0))
        box.bind("<<ComboboxSelected>>", lambda event: self.refresh_employment_csy())

        self.emp_holder_csy = tk.Frame(body, bg=COLORS_CSY["surface"])
        self.emp_holder_csy.pack(fill="x")
        self.refresh_employment_csy()

        body = self.make_section_csy(parent, "跨学历层次升学率对比", "chart")
        rows = self.analysis.cross_level_rates_csy()
        chart_rows = []
        for item in rows:
            if item.get("本科") is not None:
                chart_rows.append(["%s 本科" % item["year"], item["本科"]])
            if item.get("专科") is not None:
                chart_rows.append(["%s 专科" % item["year"], item["专科"]])
        if chart_rows:
            self.add_chart_csy(
                body, ["届别与学历", "升学率（%）"], chart_rows, "bar", height=2.6,
                xlabel="届别与学历层次", ylabel="升学率（%）",
                title="本科与专科升学率对比")
        self.add_note_csy(
            body, "升学率 = 境内升学（含研究生、专升本、第二学位）+ 出国（境）深造"
                  "占该学历毕业生人数的比例。专科升学率高的原因是主力方向为专插本。",
            level="key")

        body = self.make_section_csy(parent, "就业单位性质", "table")
        self.add_note_csy(
            body, "数据来源：广州商学院历年《毕业生就业质量年度报告》。"
                  "统计口径为「毕业生就业单位性质」，分母是纳入就业统计的毕业生，"
                  "数据由学校自行统计发布，未经第三方核验。", level="warn")
        self.emp_flow_holder_csy = tk.Frame(body, bg=COLORS_CSY["surface"])
        self.emp_flow_holder_csy.pack(fill="x")
        self.refresh_employment_flow_csy()

        body = self.make_section_csy(parent, "原始报告说明", "hint")
        self.add_note_csy(
            body, "数据来自广州商学院历年《毕业生就业质量年度报告》，由学校自行统计发布，"
                  "未经第三方核验。报告原件为网页打印版 PDF，经 OCR 提取，"
                  "个别数值可能缺失。")

    def refresh_employment_csy(self) -> None:
        """刷新指定届别的规模与落实率。"""
        for child in self.emp_holder_csy.winfo_children():
            child.destroy()
        year = int(self.emp_year_var_csy.get().replace(" 届", ""))
        scale = {item["metric"]: item for item in self.db.employment_scale_csy(year)}

        def value_of(metric: str) -> str:
            # 报告原文比例被裁时，数据里会存成「指标（按人数计算）」
            item = scale.get(metric) or scale.get(metric + "（按人数计算）")
            if not item or item["numeric_value"] is None:
                return "—"
            if item["unit"] == "%":
                return "%.2f%%" % item["numeric_value"]
            return format(int(item["numeric_value"]), ",")

        self.add_stat_row_csy(self.emp_holder_csy, [
            {"label": "毕业生总数", "value": value_of("毕业生总数")},
            {"label": "本科毕业生", "value": value_of("本科毕业生")},
            {"label": "专科毕业生", "value": value_of("专科毕业生")},
            {"label": "毕业去向落实率", "value": value_of("毕业去向落实率")},
        ])

        advance = [item for item in self.db.employment_advance_csy()
                   if item["year"] == year and item["metric"] in
                   ("境内升学", "其中研究生", "其中专升本", "出国深造",
                    "本科升学率", "专科升学率", "总体升学率")]
        if advance:
            self.add_table_csy(
                self.emp_holder_csy, ["指标", "数值", "单位"],
                [[item["metric"], self.format_cell_csy(item["numeric_value"]),
                  item["unit"]] for item in advance], height=7)
        else:
            self.add_note_csy(self.emp_holder_csy, "该届报告未提供升学明细。", level="warn")
        self.set_status_csy("就业数据：%s 届" % year)

    def refresh_employment_flow_csy(self) -> None:
        """刷新就业单位性质分布。"""
        for child in self.emp_flow_holder_csy.winfo_children():
            child.destroy()
        years = self.db.employment_years_csy()
        if not years:
            return
        year = years[-1]
        rows = self.analysis.flow_rank_csy(year, "单位性质", top=8)
        if not rows:
            self.add_note_csy(self.emp_flow_holder_csy, "暂无该届流向数据。", level="warn")
            return
        self.add_table_csy(self.emp_flow_holder_csy, ["单位性质", "占比"],
                           [[item["category"], item["ratio"]] for item in rows], height=5)

    # ------------------------------------------------------------------ 决策链 1：我的情况

    def build_profile_csy(self, parent) -> None:
        """第一步：了解我自己。"""
        body = self.make_section_csy(parent, "第一步：了解我自己", "hint")
        self.add_note_csy(
            body, "这些信息只保存在本机，用来做资格诊断与路径比较；"
                  "不填写也能看数据，但首页建议和诊断会不准确。", level="warn")

        form = tk.Frame(body, bg=COLORS_CSY["surface"])
        form.pack(fill="x", padx=16, pady=(6, 10))
        self.profile_vars_csy = {}
        fields = [
            ("education_level", "学历层次", EDUCATION_LEVELS_CSY),
            ("major", "专业", None),
            ("grade", "年级", GRADES_CSY),
            ("score", "成绩水平", SCORE_BANDS_CSY),
            ("budget", "可接受预算", BUDGETS_CSY),
            ("region", "地区", REGIONS_CSY),
            ("goal", "职业目标", GOALS_CSY),
        ]
        for key, label, options in fields:
            row = tk.Frame(form, bg=COLORS_CSY["surface"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, width=10, anchor="w",
                     bg=COLORS_CSY["surface"], fg=COLORS_CSY["text_sub"],
                     font=FONTS_CSY["small"]).pack(side="left")
            variable = tk.StringVar(value=self.profile.get(key, "") or "")
            self.profile_vars_csy[key] = variable
            if options:
                widget = ttk.Combobox(row, state="readonly", values=options,
                                      textvariable=variable, width=26)
            else:
                widget = ttk.Entry(row, textvariable=variable, width=28)
            widget.pack(side="left", fill="x", expand=True, padx=(8, 0))

        buttons = tk.Frame(body, bg=COLORS_CSY["surface"])
        buttons.pack(fill="x", padx=16, pady=(6, 14))
        make_button_csy(buttons, "保存，去资格诊断", self.save_profile_csy,
                        kind="primary", padx=18, pady=7).pack(side="left")
        make_button_csy(buttons, "直接看数据", lambda: self.show_page_csy("overview"),
                        kind="ghost").pack(side="left", padx=(10, 0))

        if any(self.profile.get(key) for key in
               ("education_level", "major", "grade", "goal")):
            self.add_note_csy(
                body, "当前档案：%s" % self.profile_summary_csy(), level="key")

    def save_profile_csy(self) -> None:
        """保存个人情况到内存与本地档案。"""
        for key, variable in self.profile_vars_csy.items():
            self.profile[key] = variable.get().strip()
        if self.user.get("user_id"):
            try:
                UserStore(users_file_csy()).save_profile_csy(
                    self.user["user_id"], **self.profile)
            except Exception:
                pass
        self.set_status_csy("个人情况已保存")
        self.show_page_csy("eligibility")

    # ------------------------------------------------------------------ 决策链 2：资格诊断

    def build_eligibility_csy(self, parent) -> None:
        """第二步：判断能走哪些路。"""
        results = diagnose_all_csy(self.profile)
        body = self.make_section_csy(parent, "第二步：判断我能走哪些路", "checked")
        self.add_note_csy(
            body, "这里只判断「能不能报」，不预测录取概率。"
                  "无法确认的条件会列入「待核实项」，请以当年官方文件为准。",
            level="warn")

        colors = {
            STATUS_AVAILABLE_CSY: (COLORS_CSY["green"], COLORS_CSY["green_soft"]),
            STATUS_VERIFY_CSY: (COLORS_CSY["amber"], COLORS_CSY["amber_soft"]),
            STATUS_NOT_YET_CSY: (COLORS_CSY["muted"], COLORS_CSY["surface_alt"]),
        }
        for item in results:
            foreground, background = colors.get(
                item["status"], (COLORS_CSY["muted"], COLORS_CSY["surface_alt"]))
            card = RoundedCard(body, radius=12)
            card.pack(fill="x", padx=16, pady=(0, 10))
            inner = card.body
            head = tk.Frame(inner, bg=COLORS_CSY["surface"])
            head.pack(fill="x", padx=14, pady=(12, 4))
            tk.Label(head, text=item["path"], bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text"], font=FONTS_CSY["section"]).pack(side="left")
            make_pill_csy(head, item["status"], foreground, background).pack(
                side="right")
            tk.Label(inner, text=item["summary"], bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"],
                     justify="left", wraplength=720).pack(
                anchor="w", padx=14, pady=(0, 4))
            if item["reasons"]:
                tk.Label(inner, text="符合项：" + "；".join(item["reasons"]),
                         bg=COLORS_CSY["surface"], fg=COLORS_CSY["green"],
                         font=FONTS_CSY["tiny"], justify="left",
                         wraplength=720).pack(anchor="w", padx=14)
            if item["todo"]:
                tk.Label(inner, text="待核实：" + "；".join(item["todo"]),
                         bg=COLORS_CSY["surface"], fg=COLORS_CSY["amber"],
                         font=FONTS_CSY["tiny"], justify="left",
                         wraplength=720).pack(anchor="w", padx=14)
            tk.Label(inner, text="政策依据：%s（%s 年适用）"
                     % (item["source"], item["policy_year"]),
                     bg=COLORS_CSY["surface"], fg=COLORS_CSY["muted"],
                     font=FONTS_CSY["tiny"], justify="left",
                     wraplength=720).pack(anchor="w", padx=14, pady=(2, 10))

        buttons = tk.Frame(body, bg=COLORS_CSY["surface"])
        buttons.pack(fill="x", padx=16, pady=(4, 14))
        make_button_csy(buttons, "下一步：路径比较", lambda: self.show_page_csy("compare"),
                        kind="primary", padx=18, pady=7).pack(side="left")
        make_button_csy(buttons, "修改我的情况", lambda: self.show_page_csy("profile"),
                        kind="ghost").pack(side="left", padx=(10, 0))

    # ------------------------------------------------------------------ 决策链 3：路径比较

    def build_compare_csy(self, parent) -> None:
        """第三步：比较哪条路更适合我（四维比较）。"""
        body = self.make_section_csy(parent, "第三步：比较哪条路更适合我", "chart")
        self.add_note_csy(
            body, "费用是估算区间，不是精确账单；时间按各路径标注的起算口径计算。"
                  "没有「哪条路更好」的统一答案，要看你的目标和能接受的风险。",
            level="warn")
        rows = self.analysis.compare_paths_csy()
        for item in rows:
            card = RoundedCard(body, radius=12)
            card.pack(fill="x", padx=16, pady=(0, 10))
            inner = card.body
            head = tk.Frame(inner, bg=COLORS_CSY["surface"])
            head.pack(fill="x", padx=14, pady=(12, 4))
            tk.Label(head, text=item["路径"], bg=COLORS_CSY["surface"],
                     fg=COLORS_CSY["text"], font=FONTS_CSY["section"]).pack(side="left")
            make_pill_csy(head, item["时间"], COLORS_CSY["accent"],
                          COLORS_CSY["accent_soft"]).pack(side="right")
            for label, key, color in (
                    ("费用（估算）", "费用", COLORS_CSY["text_sub"]),
                    ("报考范围", "报考范围", COLORS_CSY["text_sub"]),
                    ("适合目标", "适合目标", COLORS_CSY["green"]),
                    ("主要风险", "主要风险", COLORS_CSY["amber"])):
                line = tk.Frame(inner, bg=COLORS_CSY["surface"])
                line.pack(fill="x", padx=14, pady=1)
                tk.Label(line, text=label, width=10, anchor="w",
                         bg=COLORS_CSY["surface"], fg=COLORS_CSY["muted"],
                         font=FONTS_CSY["tiny"]).pack(side="left")
                tk.Label(line, text=item[key], bg=COLORS_CSY["surface"],
                         fg=color, font=FONTS_CSY["small"], anchor="w",
                         justify="left", wraplength=620).pack(
                    side="left", fill="x", expand=True)
            tk.Label(inner, text="依据：" + item["evidence"],
                     bg=COLORS_CSY["surface"], fg=COLORS_CSY["muted"],
                     font=FONTS_CSY["tiny"], justify="left",
                     wraplength=700).pack(anchor="w", padx=14, pady=(2, 10))

        body = self.make_section_csy(parent, "三条升学路径的时间口径", "table")
        paths = self.analysis.path_timeline_csy()
        for item in paths:
            line = tk.Frame(body, bg=COLORS_CSY["surface"])
            line.pack(fill="x", padx=16, pady=3)
            tk.Label(line, text="%s（%s）" % (item["路径"], item["年限文本"]),
                     bg=COLORS_CSY["surface"], fg=COLORS_CSY["accent"],
                     font=FONTS_CSY["small"], width=24, anchor="w").pack(side="left")
            tk.Label(line, text="%s；%s" % (item["起算口径"], item["步骤"]),
                     bg=COLORS_CSY["surface"], fg=COLORS_CSY["text_sub"],
                     font=FONTS_CSY["small"], anchor="w", justify="left",
                     wraplength=560).pack(side="left", fill="x", expand=True)
        tk.Frame(body, bg=COLORS_CSY["surface"], height=10).pack()

        body = self.make_section_csy(parent, "不要只看升学率", "hint")
        self.add_note_csy(
            body, "升学率高不等于这条路更好。专科升学率高，很大程度是因为"
                  "「专插本」本身就是专科生的主流选择；本科升学率低，也不代表"
                  "本科生发展差——本科生的主流方向是直接就业。"
                  "升学、就业、收入、职业发展是四个不同的评价维度，需要分开看。",
            level="key")
        years = self.db.employment_years_csy()
        if years:
            year = years[-1]
            scale = {item["metric"]: item["numeric_value"]
                     for item in self.db.employment_scale_csy(year)}
            settled = scale.get("已落实毕业去向")
            total = scale.get("毕业生总数")
            if settled and total:
                self.add_note_csy(
                    body, "%d 届同时给出的两个维度：毕业去向落实率 %.2f%%，"
                          "升学率另见「就业去向」页。两者口径不同，不能互相替代。"
                          % (year, settled * 100.0 / total))

        buttons = tk.Frame(body, bg=COLORS_CSY["surface"])
        buttons.pack(fill="x", padx=16, pady=(4, 14))
        make_button_csy(buttons, "下一步：行动计划", lambda: self.show_page_csy("action"),
                        kind="primary", padx=18, pady=7).pack(side="left")

    # ------------------------------------------------------------------ 决策链 4：行动计划

    def build_action_csy(self, parent) -> None:
        """第四步：制定具体行动计划。"""
        results = diagnose_all_csy(self.profile)
        available = [item for item in results
                     if item["status"] == STATUS_AVAILABLE_CSY]

        body = self.make_section_csy(parent, "第四步：制定具体行动计划", "table")
        if available:
            names = "、".join(item["path"] for item in available)
            self.add_note_csy(body, "按你填写的情况，当前可直接考虑：%s。" % names,
                              level="key")
        else:
            self.add_note_csy(
                body, "当前没有「可报」的路径，可能因为年级未到或条件需核实。"
                      "下面仍然列出可以提前准备的事项。", level="warn")

        # 考试科目
        major = self.profile.get("major", "")
        if major:
            bundle = self.analysis.major_exam_bundle_csy(major)
            if bundle:
                first = bundle["专业"]
                self.add_note_csy(
                    body, "「%s」对应的专插本考试科目：%s + %s + %s。"
                          % (first["major_name"], first["common_subjects"],
                             first["basic_subject"],
                             first["comprehensive_subject"] or "院校自命题"),
                    level="key")
            else:
                self.add_note_csy(
                    body, "没有匹配到「%s」的专插本专业，可在「专插本」页换个关键词查。"
                          % major)

        # 关键节点
        self.add_table_csy(
            body, ["事项", "时间节点", "说明"],
            [
                ["专插本报名", "约 1 月中下旬", "省考试院网上报名"],
                ["专插本考试", "约 3 月下旬", "四门科目"],
                ["考研报名", "约 10 月", "研招网"],
                ["考研初试", "约 12 月下旬", "以当年公告为准"],
                ["广东省考报名", "约 10 月下旬", "省考报名系统"],
                ["广东省考笔试", "约 12 月上旬", "行测 + 申论"],
            ], height=6)
        self.add_note_csy(
            body, "以上为近年常见时间，具体日期以当年官方公告为准，不要按旧年份直接安排。",
            level="warn")

        # 待核实项
        todo = []
        for item in results:
            for entry in item["todo"]:
                todo.append("%s：%s" % (item["path"], entry))
        if todo:
            body = self.make_section_csy(parent, "还需要你核实的条件", "hint")
            self.add_table_csy(body, ["路径", "待核实事项"],
                               [item.split("：", 1) for item in todo], height=6)

        # 快捷入口
        body = self.make_section_csy(parent, "去查具体数据", "database")
        links = tk.Frame(body, bg=COLORS_CSY["surface"])
        links.pack(fill="x", padx=16, pady=(2, 14))
        for label, page in (("专插本专业与省控线", "zsb"),
                            ("考研国家线", "kaoyan"),
                            ("就业去向", "employment"),
                            ("考公职位表", "kaogong")):
            make_button_csy(links, label, lambda target=page: self.show_page_csy(target),
                            kind="ghost").pack(side="left", padx=(0, 8))

    # ------------------------------------------------------------------ 页面：考公

    def build_kaogong_csy(self, parent) -> None:
        """考公：计划招录、合格线与职位表。"""
        body = self.make_section_csy(parent, "广东省考近三年招录与合格线", "table")
        rows = self.db.list_kaogong_csy()
        if rows:
            self.add_table_csy(
                body, ["年份", "计划招录", "合格分数线", "报名时间", "笔试时间", "笔试科目"],
                [[item["year"], self.format_cell_csy(item["recruit_count"]),
                  ("%s 分" % item["pass_line"]) if item["pass_line"] else "—",
                  item["signup_period"] or "—", item["exam_date"] or "—",
                  item["subjects"] or "—"] for item in rows], height=4)
        self.add_note_csy(
            body, "数据来源：中共广东省委组织部《广东省考试录用公务员公告》与"
                  "《资格审核和面试等事项公告》。2024 年合格线公告未纳入本次采集，"
                  "表格中显示为「—」。", level="warn")

        body = self.make_section_csy(parent, "2026 年职位表：按系统分布", "chart")
        summary = self.db.query_csy(
            "SELECT category, job_count, headcount FROM kaogong_job_summary "
            "WHERE dimension = '按系统' ORDER BY headcount DESC")
        if summary:
            self.add_table_csy(
                body, ["系统", "职位数", "招录人数"],
                [[item["category"], item["job_count"], item["headcount"]]
                 for item in summary], height=7)
            self.add_note_csy(
                body, "共 9344 个职位、招录 11779 人，与公告口径一致。"
                      "数据来自 2026 年公告附件 1《职位表》。", level="key")

        body = self.make_section_csy(parent, "2026 年职位表：按学历要求", "table")
        education = self.db.query_csy(
            "SELECT category, job_count, headcount FROM kaogong_job_summary "
            "WHERE dimension = '按学历' ORDER BY headcount DESC")
        if education:
            self.add_table_csy(
                body, ["学历要求", "职位数", "招录人数"],
                [[item["category"], item["job_count"], item["headcount"]]
                 for item in education], height=7)
            self.add_note_csy(
                body, "「大专以上」与「大专、本科」的职位可以专科学历报考；"
                      "其余职位要求本科或研究生。", level="warn")

        body = self.make_section_csy(parent, "职位明细（示例 20 条）", "database")
        detail = self.db.query_csy(
            "SELECT system, unit, position, headcount, education, fresh_only "
            "FROM kaogong_job_detail ORDER BY system, unit LIMIT 20")
        if detail:
            self.add_table_csy(
                body, ["系统", "招考单位", "职位", "人数", "学历", "限应届"],
                [[item["system"], item["unit"], item["position"],
                  item["headcount"], item["education"], item["fresh_only"]]
                 for item in detail], height=8)
            self.add_note_csy(
                body, "职位明细共 9344 条，界面只展示前 20 条；"
                      "完整数据在 data/processed/广东省考_职位明细.csv。")


def launch_csy(user: dict = None, profile: dict = None) -> None:
    """创建根窗口并进入事件循环。"""
    root = tk.Tk()
    root.window_csy = MainWindow(root, user=user, profile=profile)
    root.lift()
    root.attributes("-topmost", True)
    root.after(400, lambda: root.attributes("-topmost", False))
    root.focus_force()
    root.mainloop()
