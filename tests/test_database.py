"""数据访问层测试：验证各类查询能取到预期数据。"""

import sqlite3

import pytest

from pathway.database import PathwayDatabase
from pathway.paths import database_file_csy


@pytest.fixture(scope="module")
def db_csy():
    """连到项目自带的数据库；库不存在时跳过（先跑 build_database.py）。"""
    path = database_file_csy()
    if not path.exists():
        pytest.skip("尚未生成数据库，请先运行 python scripts/build_database.py")
    database = PathwayDatabase(path)
    if not database.is_ready_csy():
        pytest.skip("数据库结构不完整，请重新运行 scripts/build_database.py")
    return database


def test_sources_registered_csy(db_csy):
    """四处数据来源都要有登记，便于溯源。"""
    sources = db_csy.list_sources_csy()
    assert len(sources) >= 4
    names = " ".join(item["name"] for item in sources)
    assert "专升本" in names
    assert "就业质量" in names
    assert "国家线" in names or "复试" in names


def test_zsb_disciplines_and_subjects_csy(db_csy):
    """专升本应覆盖多个学科门类与全部 9 门专业基础课。"""
    disciplines = db_csy.list_zsb_disciplines_csy()
    subjects = db_csy.list_zsb_basic_subjects_csy()
    assert len(disciplines) >= 10
    assert "高等数学" in subjects
    assert "民法" in subjects


def test_major_query_returns_exam_bundle_csy(db_csy):
    """查专业时应同时带出公共课、专业基础课与专业综合课。"""
    rows = db_csy.list_zsb_majors_csy(keyword="计算机")
    assert rows
    first = rows[0]
    assert first["major_code"]
    assert "政治理论" in first["common_subjects"]
    assert first["basic_subject"] in ("高等数学", "经济学")


def test_major_filter_by_discipline_csy(db_csy):
    """按学科门类过滤应只返回该门类的专业。"""
    rows = db_csy.list_zsb_majors_csy(discipline="法学类")
    assert rows
    assert all(row["discipline"] == "法学类" for row in rows)


def test_zsb_score_trend_is_sorted_csy(db_csy):
    """省控线走势应按年份升序，且只包含指定类别。"""
    trend = db_csy.zsb_score_trend_csy("高等数学", "普通考生")
    assert len(trend) >= 3
    years = [item["year"] for item in trend]
    assert years == sorted(years)
    assert all(item["total_line"] for item in trend)


def test_employment_advance_has_both_levels_csy(db_csy):
    """升学数据里应同时有本科与专科升学率，这是跨层次对比的基础。"""
    metrics = {item["metric"] for item in db_csy.employment_advance_csy()}
    assert "本科升学率" in metrics
    assert "专科升学率" in metrics


def test_kaoyan_line_has_two_classes_csy(db_csy):
    """国家线应同时有 A 类与 B 类考生，且 B 类不高于 A 类。"""
    a = db_csy.kaoyan_line_trend_csy("工学", "A类考生")
    b = db_csy.kaoyan_line_trend_csy("工学", "B类考生")
    assert a and b
    assert len(a) == len(b)
    for row_a, row_b in zip(a, b):
        assert row_a["year"] == row_b["year"]
        assert row_b["total_line"] <= row_a["total_line"]


def test_kaoyan_latest_sorted_desc_csy(db_csy):
    """最新一年国家线应按总分降序返回。"""
    rows = db_csy.kaoyan_latest_csy()
    assert rows
    totals = [item["total_line"] for item in rows]
    assert totals == sorted(totals, reverse=True)


def test_missing_database_reports_not_ready_csy(tmp_path):
    """库不存在时 is_ready 应返回 False，而不是抛异常。"""
    empty = tmp_path / "empty.db"
    sqlite3.connect(str(empty)).close()
    assert PathwayDatabase(empty).is_ready_csy() is False


def test_kaogong_data_csy(db_csy):
    """考公数据应有招录人数，最新一年合格线为 60 分。"""
    rows = db_csy.list_kaogong_csy()
    assert len(rows) >= 3
    latest = db_csy.kaogong_latest_csy()
    assert latest["year"] >= 2026
    assert latest["recruit_count"] > 0
    assert latest["pass_line"] == 60


def test_college_totals_match_scale_csy(db_csy):
    """分学院人数按学历合计应与规模表一致，防止漏掉某个学院。"""
    for year in db_csy.employment_years_csy():
        scale = {item["metric"]: item["numeric_value"]
                 for item in db_csy.employment_scale_csy(year)}
        colleges = db_csy.employment_colleges_csy(year)
        if not colleges:
            continue
        by_level = {}
        for row in colleges:
            by_level[row["education_level"]] = (
                by_level.get(row["education_level"], 0) + row["student_count"])
        for metric, level in (("本科毕业生", "本科"), ("专科毕业生", "专科")):
            if scale.get(metric) is not None and by_level.get(level) is not None:
                assert by_level[level] == scale[metric], (
                    "%s 届 %s 分学院合计 %s 与规模表 %s 不一致"
                    % (year, level, by_level[level], scale[metric]))


def test_education_totals_match_grand_total_csy(db_csy):
    """每一届的本科人数 + 专科人数必须等于毕业生总数。"""
    for year in db_csy.employment_years_csy():
        scale = {item["metric"]: item["numeric_value"]
                 for item in db_csy.employment_scale_csy(year)}
        total = scale.get("毕业生总数")
        under = scale.get("本科毕业生")
        college = scale.get("专科毕业生")
        if None in (total, under, college):
            continue
        assert under + college == total, (
            "%s 届：本科 %s + 专科 %s != 总数 %s" % (year, under, college, total))


def test_settled_not_more_than_total_csy(db_csy):
    """已落实人数不能超过毕业生总数。"""
    for year in db_csy.employment_years_csy():
        scale = {item["metric"]: item["numeric_value"]
                 for item in db_csy.employment_scale_csy(year)}
        total = scale.get("毕业生总数")
        settled = scale.get("已落实毕业去向")
        if total and settled:
            assert settled <= total


def test_kaogong_job_table_csy(db_csy):
    """2026 年职位表按系统汇总应合计 11779 人。"""
    rows = db_csy.query_csy(
        "SELECT category, headcount FROM kaogong_job_summary "
        "WHERE dimension = '按系统'")
    assert rows
    assert sum(item["headcount"] for item in rows) == 11779
    detail_count = db_csy.scalar_csy("SELECT COUNT(*) FROM kaogong_job_detail")
    assert detail_count > 9000
