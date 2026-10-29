"""登录 / 注册窗口。

程序启动后先显示这个窗口，登录成功才进入主界面。
账号存在本地 users.db 中，不联网。
"""

import tkinter as tk
from tkinter import ttk
import traceback

from .auth import UserStore
from .paths import APP_NAME_CSY, APP_VERSION_CSY, users_file_csy, writable_root_csy
from .theme import COLORS_CSY, FONTS_CSY, ICON_FONT_CSY, apply_theme_csy, icon_csy
from .widgets import RoundedCard, draw_round_rect_csy, make_button_csy, make_icon_csy

GUEST_PROFILE_CSY = {
    "education_level": "专科",
    "major": "计算机",
    "grade": "大二",
    "goal": "升学（专插本 / 考研）",
    "onboarded": 1,
}


def log_error_csy(message: str) -> None:
    """把异常写到程序目录下的 error.log，打包后也能排查问题。"""
    try:
        path = writable_root_csy() / "error.log"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


class LoginWindow:
    """登录 / 注册窗口。"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.store_error_csy = ""
        try:
            self.store = UserStore(users_file_csy())
        except Exception:
            detail = traceback.format_exc()
            log_error_csy(detail)
            self.store = None
            self.store_error_csy = "账号库初始化失败，可直接使用「游客体验」进入"
        self.result = None          # 登录成功后写入用户信息
        self.mode = "login"         # login / register

        self.root.title("%s v%s" % (APP_NAME_CSY, APP_VERSION_CSY))
        self.root.geometry("860x560")
        self.root.resizable(False, False)
        apply_theme_csy(self.root)
        self.build_csy()

    def build_csy(self) -> None:
        """左侧品牌区 + 右侧表单区。"""
        shell = tk.Frame(self.root, bg=COLORS_CSY["page"])
        shell.pack(fill="both", expand=True)

        # 左侧品牌区
        left = tk.Frame(shell, bg=COLORS_CSY["surface"])
        left.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(left, bg=COLORS_CSY["surface"])
        inner.pack(expand=True, padx=44)

        mark = tk.Canvas(inner, width=56, height=56, bg=COLORS_CSY["surface"],
                         highlightthickness=0, bd=0)
        mark.pack(anchor="w")
        draw_round_rect_csy(mark, 2, 2, 54, 54, 14,
                            fill=COLORS_CSY["accent"], outline=COLORS_CSY["accent"])
        glyph = icon_csy("chart")
        mark.create_text(28, 29, text=glyph or "径", fill="#FFFFFF",
                         font=(ICON_FONT_CSY, 22) if glyph else FONTS_CSY["brand"])

        tk.Label(inner, text=APP_NAME_CSY, bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text"], font=(FONTS_CSY["brand"][0], 17, "bold")).pack(
            anchor="w", pady=(16, 6))
        tk.Label(inner, text="聚焦广东省专科与本科学生的升学与发展", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(anchor="w")
        tk.Label(inner, text="· 广东省专升本考试科目与省控线\n"
                             "· 考研国家线五年走势\n"
                             "· 毕业生真实去向与升学率",
                 bg=COLORS_CSY["surface"], fg=COLORS_CSY["muted"],
                 font=FONTS_CSY["small"], justify="left").pack(anchor="w", pady=(22, 0))

        tk.Frame(shell, bg=COLORS_CSY["border"], width=1).pack(side="left", fill="y")

        # 右侧表单区
        right = tk.Frame(shell, bg=COLORS_CSY["page"])
        right.pack(side="left", fill="both", expand=True)
        self.form_holder_csy = tk.Frame(right, bg=COLORS_CSY["page"])
        self.form_holder_csy.pack(expand=True, padx=40)
        self.render_form_csy()

    def render_form_csy(self) -> None:
        """渲染登录或注册表单。"""
        for child in self.form_holder_csy.winfo_children():
            child.destroy()

        card = RoundedCard(self.form_holder_csy, radius=14)
        card.pack(fill="x")
        body = card.body
        form = tk.Frame(body, bg=COLORS_CSY["surface"])
        form.pack(fill="x", padx=28, pady=(24, 22))

        title = "登录" if self.mode == "login" else "注册新账号"
        tk.Label(form, text=title, bg=COLORS_CSY["surface"], fg=COLORS_CSY["text"],
                 font=FONTS_CSY["title"]).pack(anchor="w")
        tk.Label(form, text="账号只保存在本机，不会上传到任何服务器。",
                 bg=COLORS_CSY["surface"], fg=COLORS_CSY["muted"],
                 font=FONTS_CSY["tiny"]).pack(anchor="w", pady=(4, 14))

        self.username_var_csy = tk.StringVar()
        self.add_field_csy(form, "用户名", self.username_var_csy)
        self.username_entry_csy = self.last_entry_csy

        self.password_var_csy = tk.StringVar()
        self.add_field_csy(form, "密码", self.password_var_csy, show="*")

        self.confirm_var_csy = tk.StringVar()
        if self.mode == "register":
            self.add_field_csy(form, "确认密码", self.confirm_var_csy, show="*")

        self.message_var_csy = tk.StringVar()
        self.message_label_csy = tk.Label(
            form, textvariable=self.message_var_csy, bg=COLORS_CSY["surface"],
            fg=COLORS_CSY["red"], font=FONTS_CSY["small"],
            justify="left", wraplength=280)
        self.message_label_csy.pack(anchor="w", pady=(2, 10))

        action = "登录" if self.mode == "login" else "注册并开始"
        make_button_csy(form, action, self.submit_csy, kind="primary",
                        padx=18, pady=8).pack(fill="x")

        switch = tk.Frame(form, bg=COLORS_CSY["surface"])
        switch.pack(fill="x", pady=(12, 0))
        hint = "还没有账号？" if self.mode == "login" else "已经有账号？"
        other = "注册" if self.mode == "login" else "登录"
        tk.Label(switch, text=hint, bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["small"]).pack(side="left")
        link = tk.Label(switch, text=other, bg=COLORS_CSY["surface"],
                        fg=COLORS_CSY["accent"], font=FONTS_CSY["small"],
                        cursor="hand2")
        link.pack(side="left", padx=(4, 0))
        link.bind("<Button-1>", lambda event: self.switch_mode_csy())

        self.password_entry_csy = self.last_entry_csy
        self.username_entry_csy.focus_set()

        guest_row = tk.Frame(form, bg=COLORS_CSY["surface"])
        guest_row.pack(fill="x", pady=(14, 0))
        tk.Label(guest_row, text="不想注册？", bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["muted"], font=FONTS_CSY["tiny"]).pack(side="left")
        guest = tk.Label(guest_row, text="游客体验", bg=COLORS_CSY["surface"],
                         fg=COLORS_CSY["accent"], font=FONTS_CSY["tiny"],
                         cursor="hand2")
        guest.pack(side="left", padx=(4, 0))
        guest.bind("<Button-1>", lambda event: self.enter_as_guest_csy())

    def add_field_csy(self, parent, label: str, variable, show: str = "") -> None:
        """一行「标签 + 输入框」。"""
        tk.Label(parent, text=label, bg=COLORS_CSY["surface"],
                 fg=COLORS_CSY["text_sub"], font=FONTS_CSY["small"]).pack(
            anchor="w", pady=(0, 3))
        entry = ttk.Entry(parent, textvariable=variable, show=show)
        entry.pack(fill="x", pady=(0, 10), ipady=3)
        entry.bind("<Return>", lambda event: self.submit_csy())
        self.last_entry_csy = entry

    def switch_mode_csy(self) -> None:
        """在登录与注册之间切换。"""
        self.mode = "register" if self.mode == "login" else "login"
        self.render_form_csy()

    def show_message_csy(self, text: str, is_error: bool = True) -> None:
        """显示提示信息。"""
        self.message_label_csy.configure(
            fg=COLORS_CSY["red"] if is_error else COLORS_CSY["green"])
        self.message_var_csy.set(text)

    def submit_csy(self) -> None:
        """提交登录或注册。

        整个流程包在异常处理里：打包后的窗口没有控制台，
        如果这里抛异常，用户只会看到「点了没反应」。
        """
        try:
            if self.store is None:
                self.show_message_csy(self.store_error_csy or "账号库不可用，请使用游客体验")
                return
            username = self.username_var_csy.get().strip()
            password = self.password_var_csy.get()

            if not username:
                self.show_message_csy("请输入用户名")
                return
            if not password:
                self.show_message_csy("请输入密码")
                return

            if self.mode == "login":
                ok, message, user = self.store.login_csy(username, password)
            else:
                if password != self.confirm_var_csy.get():
                    self.show_message_csy("两次输入的密码不一致")
                    return
                ok, message, user = self.store.register_csy(username, password)

            if not ok:
                self.show_message_csy(message)
                return
            self.result = user
            self.root.destroy()
        except Exception:
            detail = traceback.format_exc()
            log_error_csy(detail)
            self.show_message_csy("操作失败：" + detail.strip().splitlines()[-1][:80])

    def enter_as_guest_csy(self) -> None:
        """不注册，用预设档案进入主界面。"""
        self.result = {"user_id": 0, "username": "游客", "guest": True,
                       "profile": dict(GUEST_PROFILE_CSY)}
        self.root.destroy()


def run_login_csy() -> dict:
    """显示登录窗口，返回登录成功的用户信息；关闭窗口返回空字典。"""
    root = tk.Tk()
    window = LoginWindow(root)
    root.mainloop()
    return window.result or {}
