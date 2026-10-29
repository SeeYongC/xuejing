"""路径分析测试：验证跨层次对比与路径时间成本的计算。"""

import pytest

from pathway.analysis import PathAnalysis
from pathway.database import PathwayDatabase
from pathway.paths import database_file_csy


@pytest.fixture(scope="module")
def analysis_csy():
    """构造分析对象；数据库缺失时跳过。"""
    path = database_file_csy()
    if not path.exists():
        pytest.skip("尚未生成数据库，请先运行 python scripts/build_database.py")
    return PathAnalysis(PathwayDatabase(path))


def test_cross_level_rates_has_both_levels_csy(analysis_csy):
    """跨层次对比应同时给出本科与专科升学率，并算出倍数。"""
    rows = analysis_csy.cross_level_rates_csy()
    assert rows
    with_both = [item for item in rows
                 if item.get("本科") is not None and item.get("专科") is not None]
    assert with_both, "至少要有一届同时有本科与专科升学率"
    for item in with_both:
        assert item["倍数"] > 1, "专科升学率应显著高于本科"


def test_path_timeline_sorted_by_years_csy(analysis_csy):
    """三条路径按年限升序返回，且都包含完整步骤。"""
    paths = analysis_csy.path_timeline_csy()
    assert len(paths) == 3
    years = [item["年限"] for item in paths]
    assert years == sorted(years)
    for item in paths:
        assert item["步骤"]
        assert item["说明"]


def test_equivalent_path_is_fastest_csy(analysis_csy):
    """同等学力直考的时间成本应当最短——这是系统的核心结论。"""
    shortest = analysis_csy.shortest_path_csy()
    assert "同等学力" in shortest["路径"]
    assert shortest["需读本科"] is False


def test_major_exam_bundle_csy(analysis_csy):
    """给定专业应返回考试科目与省控线走势。"""
    bundle = analysis_csy.major_exam_bundle_csy("计算机科学与技术")
    assert bundle
    assert bundle["专业"]["basic_subject"] == "高等数学"
    assert bundle["省控线走势"]


def test_major_exam_bundle_missing_returns_empty_csy(analysis_csy):
    """查不到的专业返回空字典，不抛异常。"""
    assert analysis_csy.major_exam_bundle_csy("这个专业不存在") == {}


def test_flow_rank_sorted_desc_csy(analysis_csy):
    """就业流向排名应按占比降序。"""
    rows = analysis_csy.flow_rank_csy(2024, "单位性质", top=5)
    assert rows
    values = [float(str(item["ratio"]).replace("%", "")) for item in rows]
    assert values == sorted(values, reverse=True)


def test_path_years_match_stated_basis_csy(analysis_csy):
    """专插本后再考研应按大三起算 6 年，其余两条为 5-6 年。"""
    paths = {item["路径"]: item for item in analysis_csy.path_timeline_csy()}
    zsb = [item for name, item in paths.items() if "专插本" in name][0]
    assert zsb["年限文本"] == "6 年"
    assert "大三" in zsb["起算口径"]
    others = [item for name, item in paths.items() if "专插本" not in name]
    assert all(item["年限文本"] == "5-6 年" for item in others)


def test_compare_paths_has_five_dimensions_csy(analysis_csy):
    """四维比较应覆盖五条去向，且费用明确标注为估算。"""
    rows = analysis_csy.compare_paths_csy()
    assert len(rows) == 5
    names = " ".join(item["路径"] for item in rows)
    for keyword in ("专插本", "同等学力", "自考", "考公", "直接就业"):
        assert keyword in names
    for item in rows:
        assert item["时间"] and item["费用"] and item["主要风险"]


def test_compare_paths_for_undergraduate_csy(analysis_csy):
    """本科路径应包含考研，但不能混入专科专属路径。"""
    rows = analysis_csy.compare_paths_csy("本科")
    names = " ".join(item["路径"] for item in rows)
    assert "本科毕业后考研" in names
    assert "直接就业" in names
    assert "专插本后再考研" not in names
    assert "同等学力" not in names
