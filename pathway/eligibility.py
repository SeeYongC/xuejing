"""升学与就业资格的规则诊断。

只依据公开政策做"能不能报"的判断，不计算录取概率。
每条结论都带政策依据与适用年份；无法确认的条件放进「待核实项」。
"""

# 政策依据（年份随数据更新）
POLICY_YEARS_CSY = {
    "zsb": "2026",
    "kaoyan": "2026",
    "kaogong": "2026",
}

STATUS_AVAILABLE_CSY = "可报"
STATUS_VERIFY_CSY = "需核实"
STATUS_NOT_YET_CSY = "暂不适用"

GUANGDONG_CITY_KEYWORDS_CSY = (
    "广州", "深圳", "珠海", "佛山", "东莞", "中山", "惠州", "江门", "肇庆",
    "汕头", "潮州", "揭阳", "汕尾", "湛江", "茂名", "阳江", "清远",
    "韶关", "河源", "梅州", "云浮",
)


def _contains_guangdong_csy(text: str) -> bool:
    """判断地区文本是否落在广东。"""
    normalized = str(text or "").strip()
    if not normalized or "省外" in normalized:
        return False
    if normalized in ("广东", "广东省内", "珠三角其他城市", "粤东", "粤西", "粤北"):
        return True
    return any(key in normalized for key in GUANGDONG_CITY_KEYWORDS_CSY)


def diagnose_zsb_csy(profile: dict) -> dict:
    """专插本（广东省普通专升本）资格诊断。"""
    level = profile.get("education_level", "")
    grade = profile.get("grade", "")
    region = profile.get("region", "")
    result = {
        "path": "专插本",
        "policy_year": POLICY_YEARS_CSY["zsb"],
        "source": "广东省2026年普通高等学校专升本招生工作规定",
        "reasons": [],
        "todo": [],
    }

    if level != "专科":
        result.update(status=STATUS_NOT_YET_CSY,
                      summary="专插本面向专科毕业生，你当前填写的是「%s」，"
                              "请确认学历是否填错。" % (level or "未填写"))
        return result

    if grade in ("大一", "大二"):
        result.update(status=STATUS_NOT_YET_CSY,
                      summary="专插本在大三下学期报名、毕业当年参加考试。"
                              "你现在可以先了解专业与考试科目。")
        result["todo"].append("大三时关注省考试院当年的招生工作规定")
        return result

    if _contains_guangdong_csy(region):
        result.update(status=STATUS_AVAILABLE_CSY,
                      summary="你的地区在广东范围内，符合「广东省户籍专科毕业生」"
                              "或「在广东就读的应届专科毕业生」的基本条件。")
        result["reasons"].append("学历：专科（符合）")
        result["reasons"].append("地区：%s（在广东范围内）" % region)
    else:
        result.update(status=STATUS_VERIFY_CSY,
                      summary="你的地区不在广东。非广东户籍的考生只有在"
                              "「在广东就读的应届专科毕业生」或"
                              "「在广东参加高考被外省高校录取的应届专科毕业生」"
                              "两种情况下可以报考。")
        result["todo"].append("确认自己是否属于上述两种非广东户籍可报情形")

    result["todo"].append("往届生需户籍连续满 3 年，具体以当年文件为准")
    return result


def diagnose_kaoyan_csy(profile: dict) -> dict:
    """考研资格诊断，区分本科生与专科同等学力。"""
    level = profile.get("education_level", "")
    grade = profile.get("grade", "")
    result = {
        "path": "考研",
        "policy_year": POLICY_YEARS_CSY["kaoyan"],
        "source": "教育部全国硕士研究生招生工作管理规定（以当年文件为准）",
        "reasons": [],
        "todo": [],
    }

    if level == "本科":
        if grade in ("大四", "已毕业"):
            result.update(status=STATUS_AVAILABLE_CSY,
                          summary="本科应届或往届毕业生可以直接报考硕士研究生。")
            result["reasons"].append("学历：本科（符合）")
        else:
            result.update(status=STATUS_NOT_YET_CSY,
                          summary="你还在读，暂时不能报名。大四上学期（10 月）报名、"
                                  "12 月初试，现在可以先准备英语和数学。")
            result["todo"].append("大三下学期开始确定目标院校与专业")
        return result

    if level == "专科":
        if grade == "已毕业":
            result.update(status=STATUS_VERIFY_CSY,
                          summary="专科毕业满 2 年（从毕业到录取当年入学之日）可以"
                                  "「同等学力」身份报考，但复试要加试两门本科主干课程，"
                                  "且不少院校专业明确不接收同等学力考生。")
            result["todo"].append("逐校确认目标专业是否接收同等学力")
            result["todo"].append("确认加试科目与是否需要进修本科课程")
        else:
            result.update(status=STATUS_NOT_YET_CSY,
                          summary="专科生需要毕业满 2 年才能以同等学力报考；"
                                  "也可以先专插本，再以本科生身份考研。")
            result["todo"].append("比较「专插本后再考研」与「同等学力直考」两条路")
        return result

    result.update(status=STATUS_VERIFY_CSY, summary="请先填写学历层次。")
    return result


def diagnose_kaogong_csy(profile: dict) -> dict:
    """广东省考公务员资格诊断。"""
    level = profile.get("education_level", "")
    grade = profile.get("grade", "")
    region = profile.get("region", "")
    result = {
        "path": "考公（广东省考）",
        "policy_year": POLICY_YEARS_CSY["kaogong"],
        "source": "广东省2026年考试录用公务员公告",
        "reasons": [],
        "todo": [],
    }

    if level not in ("专科", "本科"):
        result.update(status=STATUS_VERIFY_CSY, summary="请先填写学历层次。")
        return result

    if level == "专科" and grade in ("大一", "大二"):
        result.update(status=STATUS_NOT_YET_CSY,
                      summary="你还没有进入毕业年级，可以先了解职位表、专业和学历要求。")
        result["todo"].append("关注广东省考公告与职位表")
        return result

    if level == "专科" and grade == "大三":
        result.update(status=STATUS_VERIFY_CSY,
                      summary="专科大三通常是毕业年级。能否以应届毕业生身份报考，"
                              "要以当年公告、职位表和学历性质为准。")
        result["todo"].append("核对当年公告是否允许专科应届毕业生报考")
        result["todo"].append("逐项确认职位表中的学历、学位、专业和应届限制")
        return result

    if level == "本科" and grade in ("大一", "大二", "大三"):
        result.update(status=STATUS_NOT_YET_CSY,
                      summary="省考一般在大四上学期报名、年底笔试。"
                              "你现在可以先了解职位表与专业要求。")
        result["todo"].append("关注广东省考公告与职位表")
        return result

    result["reasons"].append("学历：%s（大学专科以上，符合基本学历要求）" % level)

    if level == "专科" and not _contains_guangdong_csy(region):
        result.update(status=STATUS_VERIFY_CSY,
                      summary="广东省考要求大学专科以上学历，但非广东户籍（生源）"
                              "报考者需具有本科以上学历并取得学士以上学位。")
        result["todo"].append("确认户籍/生源是否符合专科报考条件")
    else:
        result.update(status=STATUS_AVAILABLE_CSY,
                      summary="你的学历与地区符合广东省考的基本报考条件。")

    result["todo"].append("年龄需在 18-38 周岁（应届硕士博士可放宽到 43 周岁）")
    result["todo"].append("部分职位要求应届身份、基层工作经历或特定专业")
    return result


def diagnose_all_csy(profile: dict) -> list:
    """返回专插本、考研、考公三条路的资格诊断。"""
    return [
        diagnose_zsb_csy(profile),
        diagnose_kaoyan_csy(profile),
        diagnose_kaogong_csy(profile),
    ]


def available_paths_csy(profile: dict) -> list:
    """只返回状态为「可报」的路径名。"""
    return [item["path"] for item in diagnose_all_csy(profile)
            if item["status"] == STATUS_AVAILABLE_CSY]
