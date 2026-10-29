"""个人条件分析：按固定规则组合资格、路径和公开数据。"""

from datetime import date

from .analysis import PathAnalysis
from .database import PathwayDatabase
from .eligibility import diagnose_all_csy


MAJOR_DISCIPLINE_HINTS_CSY = {
    "计算机": "工学",
    "软件": "工学",
    "电子": "工学",
    "通信": "工学",
    "机械": "工学",
    "自动化": "工学",
    "土木": "工学",
    "会计": "管理学",
    "工商": "管理学",
    "物流": "管理学",
    "金融": "经济学",
    "经济": "经济学",
    "法学": "法学",
    "英语": "文学",
    "汉语言": "文学",
    "新闻": "文学",
    "教育": "教育学",
    "护理": "医学",
    "临床": "医学",
    "艺术": "艺术学",
    "设计": "艺术学",
}

GOAL_LABELS_CSY = {
    "zsb": "升学（专插本）",
    "kaoyan": "升学（考研）",
    "kaogong": "就业（考公）",
    "employment": "直接就业",
}

GUANGDONG_REGION_HINTS_CSY = (
    "广东", "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江",
    "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江",
    "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
    "珠三角", "粤东", "粤西", "粤北",
)


def _infer_discipline_csy(major: str) -> str:
    """按专业关键词做保守门类推断，无法确认时返回空字符串。"""
    text = str(major or "").strip()
    for keyword, discipline in MAJOR_DISCIPLINE_HINTS_CSY.items():
        if keyword in text:
            return discipline
    return ""


def _budget_limit_csy(budget: str) -> float:
    """把预算档位转换为万元上限，无法判断时返回 5 万元。"""
    text = str(budget or "")
    if "1 万以内" in text:
        return 1
    if "1-3 万" in text:
        return 3
    if "3-6 万" in text:
        return 6
    if "6 万以上" in text:
        return 12
    return 5


def _goal_score_csy(goal: str, path_key: str) -> int:
    """按职业目标给路径计算 0-25 的目标一致分。"""
    if "还没想好" in goal:
        return 15
    if path_key in ("zsb", "kaoyan"):
        return 25 if "升学" in goal else 8
    if path_key == "kaogong":
        return 22 if "就业" in goal else 12
    if path_key == "employment":
        return 25 if "就业" in goal else 10
    return 10


def _budget_score_csy(path_key: str, budget: str) -> int:
    """按公开估算费用判断预算适配度，返回 0-20。"""
    limits = _budget_limit_csy(budget)
    estimated = {
        "zsb": 7,
        "equivalent": 2,
        "self_study": 3,
        "kaoyan": 2,
        "kaogong": 0.75,
        "employment": 0,
    }.get(path_key, 3)
    if estimated <= limits:
        return 20
    if estimated - limits <= 2:
        return 12
    return 5


def _status_score_csy(status: str) -> int:
    return {"可报": 30, "需核实": 16, "暂不适用": 2}.get(status, 10)


def _match_level_csy(score: int, status: str, summary: str = "",
                     path_key: str = "") -> str:
    if status == "暂不适用":
        if path_key in ("equivalent", "self_study"):
            return "后续备选"
        if any(keyword in summary for keyword in ("在读", "大一大二", "先了解", "现在可以先")):
            return "准备阶段"
        return "暂不适合"
    if status == "需核实":
        return "需核实"
    if score >= 80:
        return "优先了解"
    return "可比较"


class PersonalAnalyzer:
    """按固定流程生成可解释的个人条件分析结果。"""

    def __init__(self, db: PathwayDatabase, analysis: PathAnalysis):
        self.db = db
        self.analysis = analysis

    def _profile_gaps_csy(self, profile: dict) -> list:
        gaps = []
        required = [
            ("education_level", "学历层次"),
            ("major", "专业"),
            ("grade", "年级"),
            ("region", "地区"),
            ("goal", "职业目标"),
        ]
        for key, label in required:
            if not str(profile.get(key) or "").strip():
                gaps.append("请补充%s" % label)
        if not str(profile.get("score") or "").strip():
            gaps.append("成绩水平未填写，不影响资格判断，但会降低建议针对性")
        if not str(profile.get("budget") or "").strip():
            gaps.append("预算未填写，费用适配只能按保守区间估算")
        return gaps

    def _diagnosis_map_csy(self, profile: dict) -> dict:
        return {item["path"]: item for item in diagnose_all_csy(profile)}

    def _collect_evidence_csy(self, profile: dict, path_key: str,
                              eligibility: dict) -> tuple:
        """返回建议理由、数据证据、缺口和下一步核实项。"""
        major = str(profile.get("major") or "").strip()
        region = str(profile.get("region") or "").strip()
        reasons = []
        evidence = []
        gaps = []
        next_checks = list(eligibility.get("todo") or [])

        if eligibility.get("status"):
            reasons.append("资格判断：%s" % eligibility["status"])
        if eligibility.get("summary"):
            reasons.append(eligibility["summary"])
        if profile.get("score"):
            reasons.append(
                "成绩自评：%s（只用于准备度提示，不换算为考试分数）"
                % profile["score"])

        if path_key == "zsb":
            majors = self.db.list_zsb_majors_csy(keyword=major) if major else []
            if majors:
                subjects = sorted({
                    item.get("basic_subject")
                    for item in majors if item.get("basic_subject")
                })
                evidence.append("2026 专插本专业目录匹配到 %d 个专业" % len(majors))
                if subjects:
                    evidence.append("相关专业基础课：%s" % "、".join(subjects))
            else:
                gaps.append("当前专业未匹配到 2026 专插本专业目录，需要核对专业名称")
        elif path_key == "kaoyan":
            discipline = _infer_discipline_csy(major)
            if discipline:
                trend = self.db.kaoyan_line_trend_csy(discipline, "A类考生")
                evidence.append("按专业关键词保守推断学科门类：%s" % discipline)
                if trend:
                    latest = trend[-1]
                    evidence.append(
                        "%d 年 A 类国家线：总分 %s，单科满分100 %s，单科满分>100 %s"
                        % (latest["year"], latest["total_line"],
                           latest["single_subject_100"], latest["single_subject_150"]))
                else:
                    gaps.append("该学科门类暂无国家线数据")
            else:
                gaps.append("专业名称无法可靠映射到考研学科门类，请手动核实目标门类")
        elif path_key == "kaogong":
            level = profile.get("education_level")
            keyword = "大专" if level == "专科" else "本科"
            jobs = self.db.list_kaogong_jobs_for_match_csy(keyword=keyword)
            major_verified = False
            if region and region not in ("广东省外", "没想好"):
                jobs = [
                    item for item in jobs
                    if region.replace("市", "") in str(item.get("unit") or "")
                ]
            if major:
                major_keyword = major.replace("专业", "")
                major_jobs = [
                    item for item in jobs
                    if major_keyword in str(item.get("major_undergrad") or "")
                    or major_keyword in str(item.get("major_college") or "")
                ]
                if major_jobs:
                    jobs = major_jobs
                    major_verified = True
                    evidence.append("专业栏直接匹配到 %d 个职位" % len(major_jobs))
                else:
                    gaps.append("职位专业栏未直接匹配该专业，最终以职位表和资格审核为准")
            if jobs:
                evidence.append(
                    "按学历%s%s筛选到 %d 个职位，计划招录 %d 人"
                    % ("、地区%s" % region if region else "",
                       "、专业关键词%s" % major if major_verified else "",
                       len(jobs),
                       sum(int(item.get("headcount") or 0) for item in jobs)))
            else:
                gaps.append("当前条件下未匹配到职位，可能由地区或专业口径造成")
        elif path_key == "employment":
            overview = self.analysis.employment_overview_csy()
            latest = overview[-1] if overview else {}
            if latest:
                evidence.append(
                    "%d 届广州商学院样本毕业生 %s 人，毕业去向落实率 %s%%"
                    % (latest["year"], latest["total"], latest["placement_rate"]))
                gaps.append("现有就业数据为学校整体样本，不能推断具体专业或个人就业结果")
        elif path_key in ("equivalent", "self_study"):
            gaps.append("同等学力与自考路径的院校接收条件差异较大，需要逐校核实")
        elif path_key == "tuimian":
            gaps.append("系统没有本校推免资格、名额和综合排名数据，不能判断能否获得推免资格")
            next_checks.append("向所在学院核实本校推免资格、名额和成绩排名要求")

        if not next_checks:
            next_checks.append("查看对应公开数据，并以当年官方公告为准")
        next_checks = list(dict.fromkeys(next_checks))
        return reasons, evidence, gaps, next_checks

    def _make_item_csy(self, path_key: str, title: str, status: str,
                       profile: dict, page: str, eligibility: dict) -> dict:
        score = _status_score_csy(status)
        score += _goal_score_csy(str(profile.get("goal") or ""), path_key)
        score += _budget_score_csy(path_key, str(profile.get("budget") or ""))

        region = str(profile.get("region") or "")
        if any(keyword in region for keyword in GUANGDONG_REGION_HINTS_CSY):
            score += 15
        elif region:
            score += 5

        reasons, evidence, gaps, next_checks = self._collect_evidence_csy(
            profile, path_key, eligibility)
        if evidence:
            score += min(10, 4 + len(evidence) * 2)
        else:
            gaps.append("公开数据证据不足，暂不给出数据匹配结论")

        score = max(0, min(100, score))
        return {
            "key": path_key,
            "title": title,
            "status": status,
            "match_level": _match_level_csy(
                score, status, str(eligibility.get("summary") or ""), path_key),
            "score": score,
            "reasons": reasons,
            "evidence": evidence,
            "gaps": gaps,
            "next_checks": next_checks,
            "page": page,
        }

    def analyze_csy(self, profile: dict) -> dict:
        """执行完整分析流程并返回可追溯结果。"""
        normalized = {
            "education_level": str(profile.get("education_level") or "").strip(),
            "undergrad_type": str(profile.get("undergrad_type") or "").strip(),
            "major": str(profile.get("major") or "").strip(),
            "grade": str(profile.get("grade") or "").strip(),
            "score": str(profile.get("score") or "").strip(),
            "budget": str(profile.get("budget") or "").strip(),
            "region": str(profile.get("region") or "").strip(),
            "goal": str(profile.get("goal") or "").strip(),
        }
        gaps = self._profile_gaps_csy(normalized)
        required_ready = all(normalized.get(key) for key in
                             ("education_level", "major", "grade", "region", "goal"))
        if not required_ready:
            return {
                "profile_ready": False,
                "summary": "个人资料还不完整，暂不生成路径推荐。",
                "profile_gaps": gaps,
                "recommendations": [],
                "rules_version": "1.0",
                "calculated_at": date.today().isoformat(),
                "note": "匹配分只表示资料与公开数据的适配程度，不是录取概率。",
            }

        diagnoses = self._diagnosis_map_csy(normalized)
        level = normalized["education_level"]
        if level == "专科":
            definitions = [
                ("zsb", "专插本", "专插本", "college"),
                ("equivalent", "同等学力考研", "考研", "compare"),
                ("self_study", "自考 / 成考本科后考研", "考研", "compare"),
                ("kaogong", "考公（广东省考）", "考公（广东省考）", "calendar"),
                ("employment", "直接就业", "", "overview"),
            ]
        else:
            definitions = [
                ("kaoyan", "本科毕业后考研", "考研", "undergrad"),
                ("tuimian", "推免（需核实）", "", "undergrad"),
                ("kaogong", "考公（广东省考）", "考公（广东省考）", "calendar"),
                ("employment", "直接就业", "", "overview"),
            ]

        recommendations = []
        for path_key, title, diagnosis_key, page in definitions:
            if path_key == "tuimian":
                eligibility = {
                    "status": "需核实",
                    "summary": "普通本科与专插本本科都需要以本校当年推免政策为准。",
                    "todo": ["核实本校是否具有推免资格、名额及排名要求"],
                }
            else:
                eligibility = diagnoses.get(diagnosis_key, {
                    "status": "可参考",
                    "summary": "该去向不涉及学历报考资格。",
                    "todo": [],
                })
            recommendations.append(
                self._make_item_csy(
                    path_key, title, eligibility["status"], normalized,
                    page, eligibility))

        recommendations.sort(
            key=lambda item: (item["status"] == "暂不适用", -item["score"]))
        degree_label = (
            "%s（%s）" % (level, normalized["undergrad_type"])
            if level == "本科" and normalized["undergrad_type"] else level
        )
        summary = "%s · %s · %s · 预算：%s · 目标：%s" % (
            degree_label,
            normalized["major"],
            normalized["grade"],
            normalized["budget"] or "未填写",
            normalized["goal"],
        )
        return {
            "profile_ready": True,
            "summary": summary,
            "input_snapshot": normalized,
            "profile_gaps": gaps,
            "recommendations": recommendations,
            "rules_version": "1.0",
            "calculated_at": date.today().isoformat(),
            "note": "匹配分只表示资料与公开数据的适配程度，不是录取概率。"
                    "标记为「需核实」的路径必须确认政策后才能作为报考依据。",
        }
