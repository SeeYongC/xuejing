"""界面层冒烟测试：确保窗口、五个页面与对话框都能正常构建。

模块共用一个隐藏根窗口：在一个进程里反复创建 Tk 根窗口并不稳定。
"""

import tkinter as tk

import pytest


@pytest.fixture(scope="module")
def tk_root_csy():
    """创建隐藏根窗口；没有图形界面时跳过整个模块。"""
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("当前环境没有可用的图形界面")
    root.withdraw()
    yield root
    root.destroy()


def clear_root_csy(root) -> None:
    """清掉上一次用例留下的控件。"""
    for widget in root.winfo_children():
        widget.destroy()
    root.update()


def close_toplevels_csy(root) -> None:
    """关掉弹出窗口，让模态对话框的 wait_window 返回。"""
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()


def test_main_window_builds_csy(tk_root_csy):
    """主窗口能构建，并连上数据库。"""
    from pathway.window import MainWindow

    window = MainWindow(tk_root_csy)
    tk_root_csy.update()
    assert window.db.is_ready_csy() is True
    clear_root_csy(tk_root_csy)


def test_all_pages_render_csy(tk_root_csy):
    """五个页面都能切换并渲染成功。"""
    from pathway.window import NAV_ITEMS_CSY, MainWindow

    window = MainWindow(tk_root_csy)
    for key, _, _ in NAV_ITEMS_CSY:
        window.show_page_csy(key)
        tk_root_csy.update()
        assert window.current_page_csy == key
        assert window.content_inner_csy.winfo_children()
    clear_root_csy(tk_root_csy)


def test_zsb_query_refresh_csy(tk_root_csy):
    """专插本页的关键词查询能刷新出结果。"""
    from pathway.window import MainWindow

    window = MainWindow(tk_root_csy)
    window.show_page_csy("zsb")
    window.zsb_keyword_var_csy.set("会计")
    window.refresh_zsb_csy()
    tk_root_csy.update()
    assert window.zsb_result_holder_csy.winfo_children()
    clear_root_csy(tk_root_csy)


def test_data_source_dialog_builds_csy(tk_root_csy):
    """数据来源对话框能构建并展示全部来源。"""
    from pathway.database import PathwayDatabase
    from pathway.dialogs import DataSourceDialog
    from pathway.paths import database_file_csy

    sources = PathwayDatabase(database_file_csy()).list_sources_csy()
    tk_root_csy.after(300, lambda: close_toplevels_csy(tk_root_csy))
    DataSourceDialog(tk_root_csy, sources)
    clear_root_csy(tk_root_csy)


def test_about_dialog_builds_csy(tk_root_csy):
    """关于对话框能构建。"""
    from pathway.dialogs import AboutDialog

    tk_root_csy.after(300, lambda: close_toplevels_csy(tk_root_csy))
    dialog = AboutDialog(tk_root_csy, "基于公开数据的本专科学历路径分析与推荐系统", "1.0")
    assert dialog.version == "1.0"
    clear_root_csy(tk_root_csy)


def test_guidance_changes_with_profile_csy(tk_root_csy):
    """不同学历与目标应产生不同的引导建议。"""
    from pathway.window import MainWindow

    专科升学 = MainWindow(tk_root_csy, user={"username": "a"}, profile={
        "education_level": "专科", "major": "计算机", "grade": "大二",
        "goal": "升学（专插本 / 考研）"})
    专科页 = [item["page"] for item in 专科升学.guidance_items_csy()]
    assert "compare" in 专科页 and "zsb" in 专科页

    clear_root_csy(tk_root_csy)
    本科就业 = MainWindow(tk_root_csy, user={"username": "b"}, profile={
        "education_level": "本科", "major": "会计", "grade": "大四",
        "goal": "直接就业"})
    本科页 = [item["page"] for item in 本科就业.guidance_items_csy()]
    assert "employment" in 本科页
    assert "compare" in 本科页
    clear_root_csy(tk_root_csy)


def test_login_window_builds_csy(tk_root_csy, tmp_path, monkeypatch):
    """登录窗口能构建，且默认是登录模式。"""
    import pathway.login as login_mod

    monkeypatch.setattr(login_mod, "users_file_csy", lambda: tmp_path / "users.db")
    clear_root_csy(tk_root_csy)
    window = login_mod.LoginWindow(tk_root_csy)
    tk_root_csy.update()
    assert window.mode == "login"
    clear_root_csy(tk_root_csy)


def test_login_switch_to_register_csy(tk_root_csy, tmp_path, monkeypatch):
    """切换到注册模式后表单仍然可构建。"""
    import pathway.login as login_mod

    monkeypatch.setattr(login_mod, "users_file_csy", lambda: tmp_path / "users.db")
    clear_root_csy(tk_root_csy)
    window = login_mod.LoginWindow(tk_root_csy)
    window.switch_mode_csy()
    tk_root_csy.update()
    assert window.mode == "register"
    clear_root_csy(tk_root_csy)


def test_onboarding_window_builds_csy(tk_root_csy, tmp_path, monkeypatch):
    """引导窗口能构建，共四步。"""
    import pathway.onboarding as onboarding_mod

    monkeypatch.setattr(onboarding_mod, "users_file_csy", lambda: tmp_path / "users.db")
    clear_root_csy(tk_root_csy)
    window = onboarding_mod.OnboardingWindow(
        tk_root_csy, {"user_id": 1, "username": "demo"})
    tk_root_csy.update()
    assert window.step == 0
    assert len(onboarding_mod.STEPS_CSY) == 4
    clear_root_csy(tk_root_csy)
