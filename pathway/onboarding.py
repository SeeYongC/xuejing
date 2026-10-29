"""首次使用引导。

新用户注册后先走四步引导：学历层次、专业、年级、目标。
结果写入个人档案，主界面据此给出个性化提示。
"""

import tkinter as tk

from .auth import EDUCATION_LEVELS_CSY, GOALS_CSY, GRADES_CSY, UserStore
from .paths import APP_NAME_CSY, users_file_csy
from .theme import COLORS_CSY, FONTS_CSY, apply_theme_csy
from .widgets import RoundedCard, draw_round_rect_csy, make_button_csy

STEPS_CSY = [
    {"key": "education_level", "title": "你现在读的是？",
     "hint": "不同学历层次的升学路径完全不同，系统会按你的选择组织内容。",
     "options": EDUCATION_LEVELS_CSY},
    {"key": "grade", "title": "你目前是几年级？",
     "hint": "年级决定了你该关注「了解方向」还是「准备冲刺」。",
     "options": GRADES_CSY},
    {"key": "goal", "title": "你更倾向于？",
     "hint": "没有标准答案，选「还没想好」也没关系，系统会把几条路都摆给你看。",
     "options": GOALS_CSY},
    {"key": "major", "title": "你读什么专业？",
     "hint": "填一个大致方向即可，例如「计算机」「会计」「汉语言文学」，用来匹配考试科目。",
     "options": []},
]


class OnboardingWindow:
    """四步引导窗口。"""

    def __init__(self, root: tk.Tk, user: dict):
        self.root = root
        self.user = user
        self.store = UserStore(users_file_csy())
        self.profile = {"education_level": "", "grade": "", "goal": "", "major": ""}
        self.step = 0
        self.finished = False
        self.option_var_csy = tk.StringVar()
        self.major_var_csy = tk.StringVar()

        self.root.title("%s · 新用户引导" % APP_NAME_CSY)
        self.root.geometry("720x520")
        self.root.resizable(False, False)
        apply_theme_csy(self.root)
        self.build_csy()

    def build_csy(self) -> None:
        """搭外壳：标题、进度点、内容区、按钮。"""
        shell = tk.Frame(self.root, bg=COLORS_CSY["page"])
        shell.pack(fill="both", expand=True, padx=28, pady=22)

        top = tk.Frame(shell, bg=COLORS_CSY["page"])
        top.pack(fill="x")
        tk.Label(top, text="你好，%s" % self.user.get("username", ""),
                 bg=COLORS_CSY["page"], fg=COLORS_CSY["text"],
                 font=FONTS_CSY["title"]).pack(anchor="w")
        tk.Label(top, text="先花一分钟填几项，系统会把和你相关的数据放在前面。",
                 bg=COLORS_CSY["page"], fg=COLORS_CSY["muted"],
                 font=FONTS_CSY["small"]).pack(anchor="w", pady=(3, 0))

        self.progress_canvas_csy = tk.Canvas(shell, height=26, bg=COLORS_CSY["page"],
                                             highlightthickness=0, bd=0)
        self.progress_canvas_csy.pack(fill="x", pady=(16, 8))
        self.progress_canvas_csy.bind(
            "<Configure>", lambda event: self.render_progress_csy())

        self.card_holder_csy = tk.Frame(shell, bg=COLORS_CSY["page"])
        self.card_holder_csy.pack(fill="both", expand=True)

        buttons = tk.Frame(shell, bg=COLORS_CSY["page"])
        buttons.pack(fill="x", pady=(10, 0))
        self.back_button_csy = make_button_csy(
            buttons, "上一步", self.back_csy, kind="ghost")
        self.back_button_csy.pack(side="left")
        self.next_button_csy = make_button_csy(
            buttons, "下一步", self.next_csy, kind="primary", padx=18, pady=7)
        self.next_button_csy.pack(side="right")
        tk.Label(buttons, text="之后可以在「关于」里查看说明", bg=COLORS_CSY["page"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["tiny"]).pack(side="right", padx=12)

        self.render_step_csy()

    def render_progress_csy(self) -> None:
        """画四个进度点，当前步高亮。"""
        canvas = self.progress_canvas_csy
        canvas.delete("all")
        # 初次渲染时 Canvas 宽度可能还是 1，给一个下限避免所有点挤在一起
        width = max(canvas.winfo_width(), 480)
        gap = width / (len(STEPS_CSY) + 1)
        for index in range(len(STEPS_CSY)):
            x = gap * (index + 1)
            done = index < self.step
            current = index == self.step
            color = COLORS_CSY["accent"] if done or current else COLORS_CSY["border"]
            radius = 7 if current else 5
            canvas.create_oval(x - radius, 13 - radius, x + radius, 13 + radius,
                               fill=color, outline=color)
            if index < len(STEPS_CSY) - 1:
                canvas.create_line(x + radius + 4, 13, gap * (index + 2) - radius - 4, 13,
                                   fill=COLORS_CSY["border"], width=1)
        canvas.create_text(width - 4, 13, anchor="e",
                           text="第 %d / %d 步" % (self.step + 1, len(STEPS_CSY)),
                           fill=COLORS_CSY["muted"], font=FONTS_CSY["tiny"])

    def render_step_csy(self) -> None:
        """渲染当前步骤的内容。"""
        self.render_progress_csy()
        for child in self.card_holder_csy.winfo_children():
            child.destroy()
        step = STEPS_CSY[self.step]
        card = RoundedCard(self.card_holder_csy, radius=14)
        card.pack(fill="both", expand=True)
        body = card.body

        tk.Label(body, text=step["title"], bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text"], font=FONTS_CSY["title"]).pack(
            anchor="w", padx=22, pady=(18, 4))
        tk.Label(body, text=step["hint"], bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["small"],
                 justify="left", wraplength=560).pack(anchor="w", padx=22)

        if step["options"]:
            self.render_options_csy(body, step)
        else:
            self.render_major_input_csy(body)

        self.back_button_csy.configure(
            state="normal" if self.step > 0 else "disabled",
            cursor="hand2" if self.step > 0 else "")
        self.next_button_csy.configure(
            text="完成" if self.step == len(STEPS_CSY) - 1 else "下一步")

    def render_options_csy(self, parent, step: dict) -> None:
        """渲染可选项（大卡片式按钮）。"""
        self.option_var_csy.set(self.profile.get(step["key"], ""))
        holder = tk.Frame(parent, bg=COLORS_CSY["surface"])
        holder.pack(fill="x", padx=22, pady=(16, 18))
        for column in range(3):
            holder.columnconfigure(column, weight=1, uniform="option")
        self.option_labels_csy = {}
        for index, option in enumerate(step["options"]):
            label = tk.Label(holder, text=option, bg=COLORS_CSY["surface_alt"],
                             fg=COLORS_CSY["text_sub"], font=FONTS_CSY["body"],
                             padx=16, pady=14, cursor="hand2",
                             highlightthickness=1,
                             highlightbackground=COLORS_CSY["border"])
            row, column = divmod(index, 3)
            label.grid(row=row, column=column, padx=6, pady=6, sticky="ew")
            label.bind("<Button-1>", lambda event, value=option: self.pick_csy(value))
            self.option_labels_csy[option] = label
        self.refresh_option_style_csy()

    def pick_csy(self, value: str) -> None:
        """选中一个选项。"""
        self.option_var_csy.set(value)
        self.refresh_option_style_csy()

    def refresh_option_style_csy(self) -> None:
        """刷新选项的选中样式。"""
        selected = self.option_var_csy.get()
        for value, label in self.option_labels_csy.items():
            if value == selected:
                label.configure(bg=COLORS_CSY["accent_soft"], fg=COLORS_CSY["accent"],
                                highlightbackground=COLORS_CSY["accent"])
            else:
                label.configure(bg=COLORS_CSY["surface_alt"], fg=COLORS_CSY["text_sub"],
                                highlightbackground=COLORS_CSY["border"])

    def render_major_input_csy(self, parent) -> None:
        """专业用输入框，并给几个常见方向做快捷选择。"""
        holder = tk.Frame(parent, bg=COLORS_CSY["surface"])
        holder.pack(fill="x", padx=22, pady=(16, 6))
        self.major_var_csy.set(self.profile.get("major", ""))
        entry = tk.Entry(holder, textvariable=self.major_var_csy,
                         font=FONTS_CSY["body"], bg=COLORS_CSY["surface"],
                         fg=COLORS_CSY["text"], insertbackground=COLORS_CSY["text"],
                         bd=0, highlightthickness=1,
                         highlightbackground=COLORS_CSY["border_strong"],
                         highlightcolor=COLORS_CSY["accent"])
        entry.pack(fill="x", ipady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.next_csy())

        quick = tk.Frame(parent, bg=COLORS_CSY["surface"])
        quick.pack(fill="x", padx=22, pady=(6, 0))
        for name in ["计算机", "会计", "汉语言文学", "学前教育", "护理", "电子商务"]:
            chip = tk.Label(quick, text=name, bg=COLORS_CSY["surface_alt"],
                            fg=COLORS_CSY["text_sub"], font=FONTS_CSY["tiny"],
                            padx=10, pady=4, cursor="hand2")
            chip.pack(side="left", padx=(0, 8))
            chip.bind("<Button-1>", lambda event, value=name: self.major_var_csy.set(value))

        self.option_var_csy.set("")

    def collect_csy(self) -> bool:
        """把当前步骤的选择写进档案；不合法时返回 False。"""
        step = STEPS_CSY[self.step]
        if step["options"]:
            value = self.option_var_csy.get().strip()
        else:
            value = self.major_var_csy.get().strip()
        if not value:
            self.flash_hint_csy("请先选择或填写一项")
            return False
        self.profile[step["key"]] = value
        return True

    def flash_hint_csy(self, text: str) -> None:
        """在按钮旁临时提示，避免弹窗打断。"""
        self.next_button_csy.configure(text=text)
        self.root.after(1600, lambda: self.next_button_csy.configure(
            text="完成" if self.step == len(STEPS_CSY) - 1 else "下一步"))

    def next_csy(self) -> None:
        """下一步；最后一步保存并关闭。"""
        if not self.collect_csy():
            return
        if self.step < len(STEPS_CSY) - 1:
            self.step += 1
            self.render_step_csy()
            return
        self.store.save_profile_csy(
            self.user["user_id"], onboarded=1, **self.profile)
        self.finished = True
        self.root.destroy()

    def back_csy(self) -> None:
        """上一步。"""
        if self.step > 0:
            self.step -= 1
            self.render_step_csy()


def run_onboarding_csy(user: dict) -> dict:
    """显示引导窗口，返回填好的档案；关闭窗口返回空字典。"""
    root = tk.Tk()
    window = OnboardingWindow(root, user)
    root.mainloop()
    if not window.finished:
        return {}
    return dict(window.profile, onboarded=1)
