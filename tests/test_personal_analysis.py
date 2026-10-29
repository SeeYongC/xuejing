"""个人条件分析流程测试。"""

import pytest

from pathway.analysis import PathAnalysis
from pathway.database import PathwayDatabase
from pathway.paths import database_file_csy
from pathway.personal_analysis import PersonalAnalyzer


@pytest.fixture(scope="module")
def analyzer_csy():
    path = database_file_csy()
    if not path.exists():
        pytest.skip("尚未生成数据库")
    db = PathwayDatabase(path)
    return PersonalAnalyzer(db, PathAnalysis(db))


def test_incomplete_profile_stops_before_recommendation_csy(analyzer_csy):
    """缺少关键资料时只返回缺口，不强行推荐路径。"""
    result = analyzer_csy.analyze_csy({
        "education_level": "专科",
        "major": "",
        "grade": "",
        "region": "",
        "goal": "",
    })
    assert result["profile_ready"] is False
    assert result["recommendations"] == []
    assert any("专业" in item for item in result["profile_gaps"])


def test_college_analysis_uses_eligibility_and_major_data_csy(analyzer_csy):
    """专科分析应包含专插本、考研、考公和就业，并引用专业目录。"""
    result = analyzer_csy.analyze_csy({
        "education_level": "专科",
        "undergrad_type": "",
        "major": "计算机",
        "grade": "大三",
        "score": "专业前 30%",
        "budget": "3-6 万",
        "region": "广州",
        "goal": "升学（专插本 / 考研）",
    })
    assert result["profile_ready"] is True
    titles = {item["title"] for item in result["recommendations"]}
    assert "专插本" in titles
    assert "考公（广东省考）" in titles
    zsb = next(item for item in result["recommendations"] if item["key"] == "zsb")
    assert zsb["status"] == "可报"
    assert zsb["score"] >= 80
    assert any("专业目录" in item for item in zsb["evidence"])
    kaogong = next(item for item in result["recommendations"]
                   if item["key"] == "kaogong")
    assert not any("专业关键词" in item for item in kaogong["evidence"])
    assert 0 <= zsb["score"] <= 100
    assert "录取概率" in result["note"]


def test_lower_grade_path_is_preparation_not_excluded_csy(analyzer_csy):
    """年级未到报名阶段时应标为准备阶段，而不是永久不适合。"""
    result = analyzer_csy.analyze_csy({
        "education_level": "专科",
        "major": "计算机",
        "grade": "大二",
        "score": "专业中游",
        "budget": "1-3 万",
        "region": "广州",
        "goal": "升学（专插本 / 考研）",
    })
    zsb = next(item for item in result["recommendations"] if item["key"] == "zsb")
    assert zsb["status"] == "暂不适用"
    assert zsb["match_level"] == "准备阶段"


def test_undergraduate_analysis_has_no_zsb_path_csy(analyzer_csy):
    """本科分析不能混入专插本路径，并应提示推免资格需核实。"""
    result = analyzer_csy.analyze_csy({
        "education_level": "本科",
        "undergrad_type": "普通四年制本科",
        "major": "计算机科学与技术",
        "grade": "大三",
        "score": "专业前 10%",
        "budget": "3-6 万",
        "region": "广州",
        "goal": "升学（专插本 / 考研）",
    })
    keys = {item["key"] for item in result["recommendations"]}
    assert "zsb" not in keys
    assert "kaoyan" in keys
    tuimian = next(item for item in result["recommendations"] if item["key"] == "tuimian")
    assert tuimian["status"] == "需核实"
    assert any("推免资格" in item for item in tuimian["gaps"])


def test_grade_and_budget_changes_affect_analysis_csy(analyzer_csy):
    """修改年级或预算后，资格状态、匹配分和摘要必须变化。"""
    base = {
        "education_level": "专科",
        "major": "计算机",
        "grade": "大二",
        "score": "专业中游",
        "budget": "1-3 万",
        "region": "广州",
        "goal": "升学（专插本 / 考研）",
    }
    earlier = analyzer_csy.analyze_csy(base)
    later_profile = dict(base, grade="大三", budget="6 万以上")
    later = analyzer_csy.analyze_csy(later_profile)

    earlier_zsb = next(item for item in earlier["recommendations"] if item["key"] == "zsb")
    later_zsb = next(item for item in later["recommendations"] if item["key"] == "zsb")
    assert earlier_zsb["status"] == "暂不适用"
    assert later_zsb["status"] == "可报"
    assert later_zsb["score"] > earlier_zsb["score"]
    assert earlier["summary"] != later["summary"]
    assert later["input_snapshot"]["grade"] == "大三"
    assert later["input_snapshot"]["budget"] == "6 万以上"
