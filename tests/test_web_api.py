"""WebApi 学历分流测试。"""

import pytest

import pathway.web_api as web_api_module
from pathway.auth import UserStore
from pathway.web_api import WebApi


@pytest.fixture()
def api_csy():
    """游客接口只读现有数据库，不写入用户数据。"""
    return WebApi({"user_id": 0, "username": "测试游客", "guest": True})


def test_compare_paths_differs_by_level_csy(api_csy):
    college = api_csy.compare_paths("专科")
    undergrad = api_csy.compare_paths("本科")
    college_names = " ".join(item["path"] for item in college)
    undergrad_names = " ".join(item["path"] for item in undergrad)
    assert "专插本后再考研" in college_names
    assert "专插本后再考研" not in undergrad_names
    assert "本科毕业后考研" in undergrad_names


def test_zsb_majors_only_for_college_csy(api_csy):
    assert api_csy.zsb_majors("专科", "计算机", "")
    assert api_csy.zsb_majors("本科", "计算机", "") == []


def test_calendar_excludes_zsb_for_undergraduate_csy(api_csy):
    college_categories = {item["category"] for item in api_csy.calendar("专科", "全部")}
    undergrad_categories = {item["category"] for item in api_csy.calendar("本科", "全部")}
    assert "专插本" in college_categories
    assert "专插本" not in undergrad_categories


def test_save_profile_persists_undergrad_type_csy(tmp_path, monkeypatch):
    """WebApi 保存个人资料时应把本科类型写入临时用户库。"""
    users_db = tmp_path / "users.db"
    monkeypatch.setattr(web_api_module, "users_file_csy", lambda: users_db)
    store = UserStore(users_db)
    ok, _, user = store.register_csy("api_user", "123456")
    assert ok

    api = WebApi(user)
    result = api.save_profile({
        "education_level": "本科",
        "undergrad_type": "专插本本科",
    })
    saved = UserStore(users_db).get_profile_csy(user["user_id"])
    assert result["success"] is True
    assert saved["undergrad_type"] == "专插本本科"


def test_kaoyan_2027_calendar_uses_official_dates_csy(api_csy):
    """2027 考研报名日期应来自研招网官方日程表。"""
    events = api_csy.calendar("本科", "考研")
    event = next(item for item in events if item["year"] == "2027")
    assert event["start_date"] == "2026-10-15"
    assert event["end_date"] == "2026-10-24"
    assert event["exam_date"] == "2026-12-19 至 2026-12-20"
    assert "预报名 2026-10-09" in event["note"]
    assert "2293971536" in event["source_url"]


def test_employment_overview_contains_four_reports_csy(api_csy):
    """首页就业概览应覆盖 2021-2024 四届。"""
    overview = api_csy.bootstrap()["employment_overview"]
    assert [item["year"] for item in overview] == [2021, 2022, 2023, 2024]
    assert all(item["total"] and item["placement_rate"] for item in overview)


def test_ggs_2021_to_2023_scale_matches_reports_csy(api_csy):
    """广商三年毕业生人数应与报告原值完全一致。"""
    overview = {
        item["year"]: item for item in api_csy.bootstrap()["employment_overview"]
    }
    assert overview[2021]["total"] == 4430
    assert overview[2021]["undergrad"] == 4133
    assert overview[2021]["college"] == 297
    assert overview[2022]["total"] == 3951
    assert overview[2022]["undergrad"] == 3780
    assert overview[2022]["college"] == 171
    assert overview[2023]["total"] == 7512
    assert overview[2023]["undergrad"] == 7335
    assert overview[2023]["college"] == 177


def test_kaogong_city_filter_and_ratio_note_csy(api_csy):
    """城市筛选应返回对应城市职位，缺报名人数时不得伪造报录比。"""
    result = api_csy.kaogong("本科", "广州")
    assert result["rows"]
    assert all(row["city"] == "广州" for row in result["rows"])
    assert result["report_ratio"] is None
    assert "暂无法计算" in result["ratio_note"]
    assert any(item["city"] == "广州" for item in result["city_options"])


def test_kaogong_registration_and_competition_ratio_csy(api_csy):
    """报名人数采用最后公开值，报录比按报名人数除以招录人数计算。"""
    years = {
        item["year"]: item for item in api_csy.kaogong("本科", "全部")["years"]
    }
    assert years[2024]["applicants"] == 170203
    assert years[2024]["competition_ratio"] == 9.83
    assert years[2025]["applicants"] == 157100
    assert years[2025]["competition_ratio"] == 9.02
    assert years[2026]["applicants"] == 270194
    assert years[2026]["competition_ratio"] == 22.94
    assert all("非最终报名人数" in item["note"] for item in years.values())


def test_zsb_major_filter_by_basic_subject_csy(api_csy):
    """专插本专业可按专业基础课筛选。"""
    rows = api_csy.zsb_majors("专科", "", "", "高等数学")
    assert rows
    assert all(row["basic_subject"] == "高等数学" for row in rows)


def test_zsb_score_contains_total_and_comprehensive_lines_csy(api_csy):
    """专插本图同时需要三科总分线和专业综合课线。"""
    trend = api_csy.zsb_score("高等数学")["trend"]
    assert trend
    assert all(item["total_line"] is not None for item in trend)
    assert all(item["comprehensive_line"] is not None for item in trend)


def test_guest_cannot_add_favorite_csy(api_csy):
    """游客模式不应写入收藏。"""
    result = api_csy.add_favorite_csy(
        "kaoyan_discipline", "工学", "工学考研国家线")
    assert result["success"] is False
    assert "登录" in result["error"]


def test_web_api_favorite_crud_csy(tmp_path, monkeypatch):
    """登录用户可通过 WebApi 完成收藏增删查改。"""
    users_db = tmp_path / "users.db"
    monkeypatch.setattr(web_api_module, "users_file_csy", lambda: users_db)
    store = UserStore(users_db)
    _, _, user = store.register_csy("favorite_user", "123456")
    api = WebApi(user)

    added = api.add_favorite_csy(
        "kaogong_job", "job-1", "广州市某职位", "初始备注")
    assert added["success"] is True
    rows = api.list_favorites_csy()["rows"]
    assert len(rows) == 1

    favorite_id = rows[0]["id"]
    assert api.update_favorite_csy(favorite_id, "修改后的备注")["success"] is True
    assert api.list_favorites_csy()["rows"][0]["note"] == "修改后的备注"
    assert api.delete_favorite_csy(favorite_id)["success"] is True
    assert api.list_favorites_csy()["rows"] == []
