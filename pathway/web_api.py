"""pywebview 暴露给前端的接口层。

前端通过 window.pywebview.api.<method>() 调用这些方法；
本层只做参数适配与数据组装，业务逻辑仍复用 database / analysis / eligibility。
"""

import re
from datetime import date
from typing import Optional

from .analysis import PathAnalysis
from .auth import UserStore
from .database import PathwayDatabase
from .eligibility import diagnose_all_csy
from .personal_analysis import PersonalAnalyzer
from .paths import database_file_csy, users_file_csy

SOURCE_LINKS_CSY = [
    {
        "name": "中国研究生招生信息网",
        "label": "考研国家线与报名公告",
        "url": "https://yz.chsi.com.cn/kyzx/zt/lnfsx.shtml",
    },
    {
        "name": "广东组织工作网",
        "label": "广东省考公告与职位表",
        "url": "https://www.gdzz.gov.cn/gwygz/lypytzgg/",
    },
    {
        "name": "广东省教育考试院",
        "label": "普通专升本政策与省控线",
        "url": "https://eea.gd.gov.cn/",
    },
    {
        "name": "广州商学院",
        "label": "毕业生就业质量年度报告",
        "url": "https://www.gcc.edu.cn/",
    },
    {
        "name": "广东中公教育",
        "label": "广东省考报名期间公开人数汇总",
        "url": "https://m.gd.offcn.com/zw/tongji/",
    },
]

KAOGONG_CITIES_CSY = [
    "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆",
    "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远",
    "东莞", "中山", "潮州", "揭阳", "云浮",
]

KAOGONG_REGISTRATION_STATS_CSY = {
    2024: {
        "applicants": 170203,
        "as_of": "2024-01-20 16:00",
        "source": "https://gd.offcn.com/html/2024/01/394407.html",
        "note": "报名期间最后一次公开缴费人数，非最终报名人数",
    },
    2025: {
        "applicants": 157100,
        "as_of": "2025-01-12 16:00",
        "source": "https://gd.offcn.com/html/2025/01/428397.html",
        "note": "报名期间最后一次公开缴费人数，非最终报名人数",
    },
    2026: {
        "applicants": 270194,
        "as_of": "2025-10-22 18:00",
        "source": "https://m.gd.offcn.com/zw/tongji/",
        "note": "报名期间最后一次公开报名人数，非最终报名人数",
    },
}


def _years_csy(text: str) -> float:
    """把「6 年」「5-6 年」「约 0.5-1 年」「0 年」转成用于绘图的数值。"""
    match = re.search(
        r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?\s*年", text or "")
    if not match:
        return 0.0
    numbers = [float(match.group(1))]
    if match.group(2):
        numbers.append(float(match.group(2)))
    return sum(numbers) / len(numbers)


def _cost_csy(text: str) -> Optional[float]:
    """把「约 6-8 万」「约 1-3 万」「0」转成万元数值。"""
    # 只取「万」前面的数字区间，避免把「本科 2 年」里的 2 也算进去
    match = re.search(r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?\s*万", text or "")
    if not match:
        return 0.0 if re.match(r"\s*0(?:\D|$)", text or "") else None
    numbers = [float(match.group(1))]
    if match.group(2):
        numbers.append(float(match.group(2)))
    if not numbers:
        return 0.0
    return round(sum(numbers) / len(numbers), 2)


def _kaogong_city_csy(unit: str) -> str:
    """按招考单位名称中明确出现的广东地级市归类。"""
    text = str(unit or "")
    for city in KAOGONG_CITIES_CSY:
        if city in text:
            return city
    if text.startswith("广东省"):
        return "省直单位"
    return "未标注城市"


def _calendar_status_csy(start_date: str, end_date: str, exam_date: str) -> str:
    """根据公告日期计算报名中、待考试或已结束，不写死当前状态。"""
    today = date.today()
    try:
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            if start <= today <= end:
                return "报名中"
            if today < start:
                return "已公布"
        exam_text = exam_date.split(" 至 ")[0] if exam_date else ""
        if exam_text:
            exam = date.fromisoformat(exam_text)
            if today < exam:
                return "待考试"
    except ValueError:
        pass
    return "已结束"


class WebApi:
    """前端可调用的方法集合。"""

    def __init__(self, user: dict = None):
        self.db = PathwayDatabase(database_file_csy())
        self.analysis = PathAnalysis(self.db)
        self.personal_analyzer = PersonalAnalyzer(self.db, self.analysis)
        self.user = user or {}
        self.profile = self.load_profile_csy()

    # ------------------------------------------------------ 基础

    def load_profile_csy(self) -> dict:
        """读取个人档案，合并登录用户信息。"""
        profile = {
            "username": self.user.get("username", "游客"),
            "education_level": "专科",
            "undergrad_type": "",
            "major": "计算机",
            "grade": "大三",
            "score": "专业前 30%",
            "budget": "3-6 万",
            "region": "广州",
            "goal": "升学（专插本 / 考研）",
        }
        if self.user.get("user_id"):
            try:
                stored = UserStore(users_file_csy()).get_profile_csy(
                    self.user["user_id"])
                for key, value in stored.items():
                    if value is not None:
                        profile[key] = value
            except Exception:
                pass
        return profile

    def bootstrap(self) -> dict:
        """首页初始化数据。"""
        sources = self.db.list_sources_csy()
        stats = [
            {"label": "数据来源", "value": "%d 处" % len(sources)},
            {"label": "专升本专业", "value": "%d 个" % len(self.db.list_zsb_majors_csy())},
            {"label": "考研学科门类", "value": "%d 个" % len(self.db.kaoyan_latest_csy())},
            {"label": "就业届别", "value": "%d 届" % len(self.db.employment_years_csy())},
            {"label": "考公年份", "value": "%d 年" % len(self.db.list_kaogong_csy())},
        ]
        return {
            "profile": self.profile,
            "sources": sources,
            "source_links": SOURCE_LINKS_CSY,
            "stats": stats,
            "upcoming": self.upcoming_csy(),
            "cross_level": self.analysis.cross_level_rates_csy(),
            "employment_overview": self.analysis.employment_overview_csy(),
            "data_gaps": [
                "2022、2023 届本科或专科升学率受原报告裁切和 OCR 影响，部分值缺失。",
                "2024 届报告未取得本科、专科升学率，页面不以 0 替代。",
                "2026 专升本专业目录中管理学、经济学、生态学基础目前没有匹配专业记录。",
                "广东省考职位明细目前只有 2026 年，2024、2025 年仅保留汇总数据。",
                "广东省考报名人数采用报名期间最后一次公开数据，不是最终报名人数。",
                "广东省考目前只有 2024–2026 三年报名与招录数据，不能展示完整五年序列。",
                "2027 年广东普通专升本和广东省考公告尚未发布。",
            ],
        }

    def save_profile(self, profile: dict) -> dict:
        """保存个人信息。"""
        editable = {
            "education_level", "undergrad_type", "major", "grade", "goal",
            "score", "budget", "region", "city", "onboarded",
        }
        self.profile.update({
            key: value for key, value in (profile or {}).items()
            if key in editable
        })
        if self.user.get("user_id"):
            try:
                UserStore(users_file_csy()).save_profile_csy(
                    self.user["user_id"], **self.profile)
            except Exception as error:
                return {"success": False, "error": str(error)}
        return {"success": True}

    # ------------------------------------------------------ 我的关注

    def _favorite_user_id_csy(self) -> Optional[int]:
        """返回可写收藏的用户编号；游客和未登录用户不允许写入。"""
        user_id = self.user.get("user_id")
        if self.user.get("guest") or not user_id:
            return None
        return int(user_id)

    def list_favorites_csy(self, item_type: str = "全部") -> dict:
        """读取当前用户的收藏。"""
        user_id = self._favorite_user_id_csy()
        if user_id is None:
            return {
                "success": False,
                "rows": [],
                "error": "游客模式不能保存收藏，请登录后使用。",
            }
        try:
            rows = UserStore(users_file_csy()).list_favorites_csy(user_id, item_type)
            return {"success": True, "rows": rows}
        except Exception as error:
            return {"success": False, "rows": [], "error": str(error)}

    def add_favorite_csy(self, item_type: str, item_key: str,
                         item_title: str, note: str = "") -> dict:
        """收藏一个专业、学科门类或考公职位。"""
        user_id = self._favorite_user_id_csy()
        if user_id is None:
            return {"success": False, "error": "游客模式不能保存收藏，请登录后使用。"}
        if item_type not in ("zsb_major", "kaoyan_discipline", "kaogong_job"):
            return {"success": False, "error": "不支持的收藏类型。"}
        if not item_key or not item_title:
            return {"success": False, "error": "收藏内容不完整。"}
        try:
            favorite_id = UserStore(users_file_csy()).add_favorite_csy(
                user_id, item_type, item_key, item_title, note)
            return {"success": True, "id": favorite_id}
        except Exception as error:
            return {"success": False, "error": str(error)}

    def update_favorite_csy(self, favorite_id: int, note: str = "") -> dict:
        """修改当前用户收藏的备注。"""
        user_id = self._favorite_user_id_csy()
        if user_id is None:
            return {"success": False, "error": "游客模式不能修改收藏，请登录后使用。"}
        try:
            updated = UserStore(users_file_csy()).update_favorite_csy(
                user_id, int(favorite_id), note)
            if not updated:
                return {"success": False, "error": "收藏不存在或不属于当前用户。"}
            return {"success": True}
        except Exception as error:
            return {"success": False, "error": str(error)}

    def delete_favorite_csy(self, favorite_id: int) -> dict:
        """删除当前用户的一条收藏。"""
        user_id = self._favorite_user_id_csy()
        if user_id is None:
            return {"success": False, "error": "游客模式不能删除收藏，请登录后使用。"}
        try:
            deleted = UserStore(users_file_csy()).delete_favorite_csy(
                user_id, int(favorite_id))
            if not deleted:
                return {"success": False, "error": "收藏不存在或不属于当前用户。"}
            return {"success": True}
        except Exception as error:
            return {"success": False, "error": str(error)}

    # ------------------------------------------------------ 资格诊断

    def diagnose(self, profile: dict = None) -> list:
        """资格诊断。"""
        merged = dict(self.profile)
        merged.update(profile or {})
        return diagnose_all_csy(merged)

    def personal_analysis_csy(self, profile: dict = None) -> dict:
        """按固定规则分析个人条件与公开数据。"""
        merged = dict(self.profile)
        merged.update(profile or {})
        return self.personal_analyzer.analyze_csy(merged)

    # ------------------------------------------------------ 专科 / 本科

    def level_summary(self, level: str) -> dict:
        """按学历返回升学路径、专业基础课与跨层次数据。"""
        if level not in ("专科", "本科"):
            raise ValueError("不支持的学历层次：%s" % level)
        if level == "本科":
            paths = [
                {"name": "考研", "time": "本科毕业当年或往届", "note": "以本科生身份报考，可报范围最宽"},
                {"name": "保研（推免）", "time": "大三暑期至大四上学期", "note": "仅部分院校有推免资格，需看本校政策"},
                {"name": "直接就业", "time": "毕业当年", "note": "往届去向见「就业去向」"},
                {"name": "考公（广东省考）", "time": "备考约 0.5-1 年", "note": "本科可报岗位范围更宽"},
            ]
            subjects = []
        else:
            paths = [
                {"name": "专插本", "time": "从大三备考起算，本硕无缝约 6 年", "note": "以本科生身份继续考研"},
                {"name": "同等学力直考", "time": "专科毕业满 2 年，约 5-6 年", "note": "复试需加试，部分院校不接收"},
                {"name": "自考 / 成考本科后考研", "time": "约 5-6 年", "note": "自考周期因人而异"},
                {"name": "直接就业", "time": "毕业当年", "note": "往届去向见「就业去向」"},
                {"name": "考公（广东省考）", "time": "备考约 0.5-1 年", "note": "大专以上学历可报部分岗位"},
            ]
            subjects = self.db.list_zsb_basic_subjects_csy()
        return {
            "level": level,
            "paths": paths,
            "subjects": subjects,
            "major_subjects": (
                self.db.list_zsb_major_subjects_csy()
                if level == "专科" else []
            ),
            "cross_level": self.analysis.cross_level_rates_csy(),
        }

    def zsb_majors(self, level: str = "专科", keyword: str = "",
                   discipline: str = "", basic_subject: str = "") -> list:
        """专插本专业查询（仅专科入口使用）。"""
        if level != "专科":
            return []
        return self.db.list_zsb_majors_csy(
            keyword=keyword,
            discipline=discipline,
            basic_subject=basic_subject,
        )

    def zsb_score(self, subject: str) -> dict:
        """省控线走势。"""
        return {
            "subject": subject,
            "trend": self.db.zsb_score_trend_csy(subject),
            "subjects": self.db.list_zsb_basic_subjects_csy(),
        }

    def kaoyan_lines(self, discipline: str = "工学", candidate_class: str = "A类考生") -> dict:
        """考研国家线。"""
        return {
            "discipline": discipline,
            "class": candidate_class,
            "trend": self.db.kaoyan_line_trend_csy(discipline, candidate_class),
            "disciplines": self.db.list_kaoyan_disciplines_csy(),
        }

    # ------------------------------------------------------ 路径比较

    def compare_paths(self, level: str = "专科") -> list:
        """按学历比较可用路径，并补上绘图用的数值。"""
        if level not in ("专科", "本科"):
            raise ValueError("不支持的学历层次：%s" % level)
        rows = []
        for item in self.analysis.compare_paths_csy(level):
            rows.append({
                "path": item["路径"],
                "time": item["时间"],
                "years": _years_csy(item["时间"]),
                "cost_text": item["费用"],
                "cost": _cost_csy(item["费用"]),
                "scope": item["报考范围"],
                "goal": item["适合目标"],
                "risk": item["主要风险"],
                "evidence": item["evidence"],
            })
        return rows

    # ------------------------------------------------------ 就业 / 考公

    def employment(self, year: int) -> dict:
        """某一届的就业数据。"""
        return {
            "year": year,
            "years": self.db.employment_years_csy(),
            "scale": self.db.employment_scale_csy(year),
            "advance": self.db.employment_advance_csy(),
            "flow": self.db.employment_flow_csy(year),
        }

    def kaogong(self, level: str = "专科", city: str = "全部") -> dict:
        """考公数据；按学历过滤可报职位。"""
        if level not in ("专科", "本科"):
            raise ValueError("不支持的学历层次：%s" % level)
        rows_all = self.db.query_csy(
            "SELECT system, unit, position, headcount, education, fresh_only "
            "FROM kaogong_job_detail ORDER BY system, unit")
        if level == "专科":
            rows = [r for r in rows_all
                    if "大专" in str(r.get("education") or "")]
        else:
            rows = [r for r in rows_all
                    if "本科" in str(r.get("education") or "")]
        for row in rows:
            row["city"] = _kaogong_city_csy(row.get("unit"))

        city_stats = {}
        for row in rows:
            item = city_stats.setdefault(
                row["city"], {"city": row["city"], "jobs": 0, "headcount": 0})
            item["jobs"] += 1
            item["headcount"] += int(row.get("headcount") or 0)

        city_options = sorted(
            city_stats.values(),
            key=lambda item: (-item["headcount"], item["city"]),
        )
        if city and city != "全部":
            rows = [row for row in rows if row["city"] == city]
        summary = self.db.query_csy(
            "SELECT category, job_count, headcount FROM kaogong_job_summary "
            "WHERE dimension = '按系统' ORDER BY headcount DESC")
        education = self.db.query_csy(
            "SELECT category, job_count, headcount FROM kaogong_job_summary "
            "WHERE dimension = '按学历' ORDER BY headcount DESC")
        years = self.db.list_kaogong_csy()
        for year_row in years:
            stats = KAOGONG_REGISTRATION_STATS_CSY.get(year_row.get("year"))
            if not stats:
                continue
            year_row.update(stats)
            year_row["competition_ratio"] = round(
                stats["applicants"] / year_row["recruit_count"], 2)

        return {
            "rows": rows[:20],
            "total": len(rows),
            "headcount": sum(int(row.get("headcount") or 0) for row in rows),
            "city_options": city_options,
            "selected_city": city,
            "applicants": None,
            "report_ratio": None,
            "ratio_note": "职位表未公开报名人数，暂无法计算官方报录比。",
            "summary": summary,
            "education": education,
            "years": years,
        }

    # ------------------------------------------------------ 考试日历

    @staticmethod
    def calendar_events_csy() -> list:
        """招考日历。往年记录标为历史，未发布年份标为「暂未公布」。"""
        return [
            {
                "year": "2026", "category": "专插本",
                "event": "广东省普通专升本 报名",
                "start_date": "2026-01-12", "end_date": "2026-01-19",
                "exam_date": "2026-03-28 至 2026-03-29",
                "audience": "广东省专科应届 / 往届毕业生",
                "publisher": "广东省教育考试院",
                "status": "已结束",
                "source_url": "https://eea.gd.gov.cn/bmbk_sksywj/content/post_4802375.html",
                "note": "历史记录，仅供参考",
            },
            {
                "year": "2026", "category": "考研",
                "event": "全国硕士研究生招生考试",
                "start_date": "2025-10-15", "end_date": "2025-10-28",
                "exam_date": "2025-12-20 至 2025-12-21",
                "audience": "本科应届 / 往届及同等学力考生",
                "publisher": "教育部 / 中国研究生招生信息网",
                "status": "已结束",
                "source_url": "https://yz.chsi.com.cn/",
                "note": "历史记录，具体日期以当年公告为准",
            },
            {
                "year": "2026", "category": "考公",
                "event": "广东省考试录用公务员 报名与笔试",
                "start_date": "2025-10-20", "end_date": "2025-10-24",
                "exam_date": "2025-12-07",
                "audience": "大学专科以上学历，符合职位要求",
                "publisher": "中共广东省委组织部",
                "status": "已结束",
                "source_url": "https://www.gdzz.gov.cn/gwygz/lypytzgg/content/post_24017.html",
                "note": "历史记录，仅供参考",
            },
            {
                "year": "2027", "category": "专插本",
                "event": "广东省普通专升本 报名",
                "start_date": "", "end_date": "",
                "exam_date": "",
                "audience": "广东省专科应届 / 往届毕业生",
                "publisher": "广东省教育考试院",
                "status": "暂未公布",
                "source_url": "https://eea.gd.gov.cn/",
                "note": "截至目前尚未发布 2027 年招生工作规定",
            },
            {
                "year": "2027", "category": "考研",
                "event": "全国硕士研究生招生考试",
                "start_date": "2026-10-15", "end_date": "2026-10-24",
                "exam_date": "2026-12-19 至 2026-12-20",
                "audience": "本科应届 / 往届及同等学力考生",
                "publisher": "教育部 / 中国研究生招生信息网",
                "status": _calendar_status_csy(
                    "2026-10-15", "2026-10-24", "2026-12-19 至 2026-12-20"),
                "source_url": "https://yz.chsi.com.cn/kyzx/kydt/202609/20260924/2293971536.html",
                "note": "官方日程：预报名 2026-10-09 至 10-12；正式报名 2026-10-15 至 10-24；初试 2026-12-19 至 12-20。",
            },
            {
                "year": "2027", "category": "考公",
                "event": "广东省考试录用公务员",
                "start_date": "", "end_date": "",
                "exam_date": "",
                "audience": "大学专科以上学历，符合职位要求",
                "publisher": "中共广东省委组织部",
                "status": "暂未公布",
                "source_url": "https://www.gdzz.gov.cn/",
                "note": "请以广东组织工作网当年公告为准",
            },
        ]

    def calendar(self, level: str = "专科", category: str = "全部") -> list:
        """按学历与类别筛选招考日历。"""
        if level not in ("专科", "本科"):
            raise ValueError("不支持的学历层次：%s" % level)
        events = self.calendar_events_csy()
        if level == "本科":
            events = [event for event in events if event["category"] != "专插本"]
        if category and category != "全部":
            events = [e for e in events if e["category"] == category]
        return events

    def upcoming_csy(self) -> list:
        """首页「最新考试时间」：取已公布的历史节点，按报名/考试日期展示。"""
        items = []
        level = self.profile.get("education_level") or "专科"
        for event in self.calendar(level, "全部"):
            if event["status"] == "暂未公布":
                continue
            date = event["start_date"] or event["exam_date"]
            if not date:
                continue
            items.append({
                "date": date[5:],
                "title": "%s %s" % (event["category"], event["event"].split(" ")[-1]),
                "desc": ("%s 至 %s" % (event["start_date"], event["end_date"]))
                        if event["start_date"] else event["exam_date"],
                "status": event["status"],
            })
        return items[:5]
