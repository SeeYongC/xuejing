"""资格诊断规则测试。"""

import pytest

from pathway.eligibility import (
    STATUS_AVAILABLE_CSY,
    STATUS_NOT_YET_CSY,
    STATUS_VERIFY_CSY,
    diagnose_kaogong_csy,
    diagnose_kaoyan_csy,
    diagnose_zsb_csy,
)


def test_zsb_guangdong_college_graduate_csy():
    """广东专科应届生符合专插本基本条件。"""
    result = diagnose_zsb_csy({
        "education_level": "专科", "grade": "大三", "region": "广州"})
    assert result["status"] == STATUS_AVAILABLE_CSY
    assert result["policy_year"] == "2026"


def test_zsb_non_guangdong_needs_verification_csy():
    """非广东地区需要核实是否符合在粤就读等例外情形。"""
    result = diagnose_zsb_csy({
        "education_level": "专科", "grade": "大三", "region": "湖南省外"})
    assert result["status"] == STATUS_VERIFY_CSY
    assert result["todo"]


def test_zsb_undergraduate_not_applicable_csy():
    """本科生不适用专插本。"""
    result = diagnose_zsb_csy({"education_level": "本科", "grade": "大二"})
    assert result["status"] == STATUS_NOT_YET_CSY


def test_zsb_lower_grade_not_yet_csy():
    """大一大二还不到专插本报名时间。"""
    result = diagnose_zsb_csy({
        "education_level": "专科", "grade": "大二", "region": "广州"})
    assert result["status"] == STATUS_NOT_YET_CSY


def test_kaoyan_undergraduate_senior_csy():
    """本科大四可以直接考研。"""
    result = diagnose_kaoyan_csy({"education_level": "本科", "grade": "大四"})
    assert result["status"] == STATUS_AVAILABLE_CSY


def test_kaoyan_college_graduate_needs_verification_csy():
    """专科毕业以同等学力报考需要核实院校是否接收。"""
    result = diagnose_kaoyan_csy({"education_level": "专科", "grade": "已毕业"})
    assert result["status"] == STATUS_VERIFY_CSY
    assert any("同等学力" in item for item in result["todo"])


def test_kaogong_guangdong_college_available_csy():
    """广东专科生符合省考基本学历与地区条件。"""
    result = diagnose_kaogong_csy({
        "education_level": "专科", "grade": "已毕业", "region": "广州"})
    assert result["status"] == STATUS_AVAILABLE_CSY


def test_kaogong_non_guangdong_college_needs_verification_csy():
    """非广东户籍的专科生报考省考需要本科以上学历。"""
    result = diagnose_kaogong_csy({
        "education_level": "专科", "grade": "已毕业", "region": "湖南省外"})
    assert result["status"] == STATUS_VERIFY_CSY


def test_kaogong_lower_grade_not_yet_csy():
    """大一大二还不到省考报名时间。"""
    result = diagnose_kaogong_csy({
        "education_level": "本科", "grade": "大二", "region": "广州"})
    assert result["status"] == STATUS_NOT_YET_CSY


def test_guangdong_outside_not_misread_as_inside_csy():
    """广东省外不能被字符串包含关系误判为省内。"""
    result = diagnose_zsb_csy({
        "education_level": "专科", "grade": "大三", "region": "广东省外"})
    assert result["status"] == STATUS_VERIFY_CSY


@pytest.mark.parametrize("region", ["珠三角其他城市", "粤东", "粤西", "粤北"])
def test_guangdong_regions_are_inside_csy(region):
    """广东区域选项应被识别为省内。"""
    result = diagnose_zsb_csy({
        "education_level": "专科", "grade": "大三", "region": region})
    assert result["status"] == STATUS_AVAILABLE_CSY


def test_college_junior_kaogong_needs_verification_csy():
    """专科大三是否属于应届毕业年级，应以当年公告核实。"""
    result = diagnose_kaogong_csy({
        "education_level": "专科", "grade": "大三", "region": "广州"})
    assert result["status"] == STATUS_VERIFY_CSY
