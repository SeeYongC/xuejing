"""路径分析：把三块数据组织成学生能看懂的结论。

三块数据各回答一段路：
    专升本    专科升本科要考什么、分数线多少
    考研      读研的国家线门槛
    就业      毕业生的真实去向（规模、升学、落实率、流向）

本模块负责跨块整合，输出"跨学历层次对比"和"路径时间成本对比"这类结论。
"""

from .database import PathwayDatabase

# 各条升学路径的时间成本模型（单位：年）
# 口径在每条路径里写明，避免"从哪一年开始算"说不清
PATH_MODELS_CSY = [
    {
        "key": "zsb_then_kaoyan",
        "name": "专插本后再考研",
        "steps": ["大三开始备考专插本", "专插本上岸，本科在读 2 年",
                  "本科第二年同步备考考研", "硕士在读 3 年"],
        "years": 6,
        "years_text": "6 年",
        "basis": "从大三开始备考专插本起算，本硕无缝衔接",
        "tuition_years": 2,          # 需要额外缴两年本科学费
        "note": "以普通本科生身份考研，可报考院校与专业范围最宽",
    },
    {
        "key": "equivalent",
        "name": "专科毕业满 2 年以同等学力直考",
        "steps": ["专科毕业", "等待期 2 年内同步备考", "硕士在读 3 年"],
        "years": 5,
        "years_text": "5-6 年",
        "basis": "从专科毕业起算；等待期内备考顺利为 5 年，备考不顺利则 6 年",
        "tuition_years": 0,
        "note": "复试需加试两门本科主干课程，部分院校专业不接收同等学力考生",
    },
    {
        "key": "self_study",
        "name": "先拿自考 / 成考本科再考研",
        "steps": ["专科毕业", "自考本科约 2 年，期间同步备考", "硕士在读 3 年"],
        "years": 5,
        "years_text": "5-6 年",
        "basis": "从专科毕业起算；自考与备考并行为 5 年，自考周期延长则 6 年",
        "tuition_years": 0,
        "note": "非全日制本科，部分院校复试另有附加要求",
    },
]


class PathAnalysis:
    """基于数据库的路径分析。"""

    def __init__(self, db: PathwayDatabase):
        self.db = db

    # ------------------------------------------------------ 跨学历层次对比

    def cross_level_rates_csy(self, school: str = "") -> list:
        """本科与专科的升学率逐年对比，这是本项目最核心的一组数据。

        返回形如 [
            {"year": 2021, "本科": 4.38, "专科": 85.52, "总体": 9.82, "倍数": 19.5},
            ...
        ]
        """
        rows = self.db.employment_advance_csy(school)
        grouped = {}
        for row in rows:
            metric = row["metric"]
            if not metric.endswith("升学率"):
                continue
            key = {"本科升学率": "本科", "专科升学率": "专科",
                   "总体升学率": "总体"}.get(metric)
            if not key:
                continue
            grouped.setdefault(row["year"], {})[key] = row["numeric_value"]

        result = []
        for year in sorted(grouped):
            item = dict(grouped[year])
            item["year"] = year
            under = item.get("本科")
            college = item.get("专科")
            item["倍数"] = round(college / under, 1) if under and college else None
            result.append(item)
        return result

    def education_level_outcome_csy(self, school: str = "") -> list:
        """分学历的就业人数与落实率，用于说明两类学生的去向差异。"""
        rows = self.db.education_level_rates_csy(school)
        grouped = {}
        for row in rows:
            key = (row["year"], row["education_level"])
            grouped.setdefault(key, {})[row["metric"]] = row["numeric_value"]
        result = []
        for (year, level) in sorted(grouped):
            item = dict(grouped[(year, level)])
            item["year"] = year
            item["学历"] = level
            result.append(item)
        return result

    def employment_overview_csy(self) -> list:
        """汇总 2021-2024 届毕业生规模与去向落实率，缺失值保持为空。"""
        result = []
        for year in self.db.employment_years_csy():
            scale = {
                item["metric"]: item["numeric_value"]
                for item in self.db.employment_scale_csy(year)
            }
            rate = next(
                (value for metric, value in scale.items() if "落实率" in metric),
                None,
            )
            result.append({
                "year": year,
                "total": scale.get("毕业生总数"),
                "undergrad": scale.get("本科毕业生"),
                "college": scale.get("专科毕业生"),
                "placement_rate": rate,
            })
        return result

    # ------------------------------------------------------ 路径时间成本

    def path_timeline_csy(self) -> list:
        """三条升学路径的时间成本与代价对比。

        注意每条路径的起算点不同，结果里用「起算口径」写明；
        同等学力直考时间更短，但可报考范围更窄——这正是系统要讲清楚的事实。
        """
        result = []
        for model in PATH_MODELS_CSY:
            result.append({
                "key": model["key"],
                "路径": model["name"],
                "年限": model["years"],
                "年限文本": model["years_text"],
                "起算口径": model["basis"],
                "需读本科": model["tuition_years"] > 0,
                "步骤": " → ".join(model["steps"]),
                "说明": model["note"],
            })
        result.sort(key=lambda item: item["年限"])
        return result

    def shortest_path_csy(self) -> dict:
        """时间最短的那条路，供界面直接给结论。"""
        paths = self.path_timeline_csy()
        return paths[0] if paths else {}

    def kaogong_timeline_csy(self) -> dict:
        """考公的时间成本与流程（不是学历路径，单独列一条）。"""
        return {
            "路径": "考公（广东省考）",
            "年限文本": "约 0.5-1 年",
            "起算口径": "从开始备考到录用的周期，不含未上岸后重考的时间",
            "步骤": "确定岗位并备考（约 3-6 个月） → 笔试（行测 + 申论） → "
                    "资格审核与面试 → 体检与政审 → 录用",
            "说明": "考公不是学历路径，与升学、就业并列；专科可报，"
                    "非广东户籍报考需本科以上学历",
        }

    def compare_paths_csy(self, level: str = "专科") -> list:
        """按学历返回可比较路径：时间、费用、报考范围、职业目标和风险。

        费用是估算区间，不是精确账单；每一条都标明这是估算。
        本科与专科适用路径不同，页面不能共用同一组路径。
        """
        if level not in ("专科", "本科"):
            raise ValueError("不支持的学历层次：%s" % level)

        rows = [
            {
                "路径": "专插本后再考研",
                "时间": "6 年",
                "费用": "约 6-8 万（本科 2 年学费 + 备考）",
                "报考范围": "最宽：以普通本科生身份考研，院校专业限制最少",
                "适合目标": "想读研、进高校/科研/研发岗，且愿意多读两年本科",
                "主要风险": "专插本录取存在竞争；比同等学力多花 1 年左右",
                "evidence": "时间按大三备考起算；费用为估算，不含生活费",
            },
            {
                "路径": "专科满 2 年以同等学力直考",
                "时间": "5-6 年",
                "费用": "约 1-3 万（备考资料与培训，无本科学费）",
                "报考范围": "窄：部分院校专业不接收同等学力，复试需加试",
                "适合目标": "想读研但不想再读本科，能接受院校选择受限",
                "主要风险": "可报院校专业少；加试不合格会被刷",
                "evidence": "时间按专科毕业起算；费用为估算",
            },
            {
                "路径": "先拿自考/成考本科再考研",
                "时间": "5-6 年",
                "费用": "约 2-4 万（自考 + 备考）",
                "报考范围": "中等：以本科学历报考，但部分院校对非全日制本科有附加要求",
                "适合目标": "想边工作边提升学历，再决定是否读研",
                "主要风险": "自考周期不确定；非全日制本科在部分院校受限",
                "evidence": "时间按专科毕业起算；费用为估算",
            },
            {
                "路径": "考公（广东省考）",
                "时间": "约 0.5-1 年（备考到录用）",
                "费用": "约 0.5-1 万（报名费 + 备考资料）",
                "报考范围": "按当年职位表：9344 个职位、招录 11779 人（2026）",
                "适合目标": "想进体制内、追求稳定",
                "主要风险": "竞争激烈；未上岸需重考，时间成本会叠加",
                "evidence": "职位数来自广东省2026年考试录用公务员职位表",
            },
            {
                "路径": "直接就业",
                "时间": "0 年，毕业即入职",
                "费用": "0（求职成本除外）",
                "报考范围": "按专业与岗位匹配",
                "适合目标": "想尽快积累工作经验、经济独立",
                "主要风险": "起薪可能较低；部分岗位与晋升对学历有要求",
                "evidence": "就业去向数据来自广州商学院就业质量年度报告",
            },
        ]
        if level == "专科":
            return rows

        by_name = {item["路径"]: item for item in rows}
        return [
            {
                "路径": "本科毕业后考研",
                "时间": "约 4 年（备考 1 年 + 硕士 3 年）",
                "费用": "因院校和专业差异大，暂不估算",
                "报考范围": "以本科学历报考，部分院校专业有前置课程或学位要求",
                "适合目标": "希望继续深造，或进入对研究生学历有要求的岗位",
                "主要风险": "备考周期长，院校专业竞争差异大；推免资格需另行核实",
                "evidence": "时间按备考起算；费用缺少统一官方口径，因此不做精确估算",
            },
            {
                "路径": "保研（推免，需核实）",
                "时间": "约 3 年（硕士阶段）",
                "费用": "按录取院校和专业缴纳，暂无统一估算",
                "报考范围": "仅限具有推免资格的高校和专业，专插本本科需核实本校政策",
                "适合目标": "成绩、科研和综合表现符合本校推免要求的本科生",
                "主要风险": "并非所有本科院校和本科类型都有推免资格",
                "evidence": "推免规则以本校当年政策和教育部文件为准",
            },
            by_name["考公（广东省考）"],
            by_name["直接就业"],
        ]

    # ------------------------------------------------------ 专业报考信息

    def major_exam_bundle_csy(self, major_name: str) -> dict:
        """给定专业名，返回考试科目组合与对应省控线走势。"""
        majors = self.db.list_zsb_majors_csy(keyword=major_name)
        if not majors:
            return {}
        first = majors[0]
        subject = first.get("basic_subject") or ""
        return {
            "专业": first,
            "全部匹配": majors,
            "省控线走势": self.db.zsb_score_trend_csy(subject) if subject else [],
        }

    def subject_majors_csy(self, basic_subject: str) -> list:
        """按专业基础课反查可选专业，便于"我擅长数学，能报什么"这类提问。"""
        return [row for row in self.db.list_zsb_majors_csy()
                if row.get("basic_subject") == basic_subject]

    # ------------------------------------------------------ 就业去向画像

    def employment_snapshot_csy(self, year: int) -> dict:
        """某一届的就业概况：规模、升学、去向。"""
        return {
            "year": year,
            "规模": self.db.employment_scale_csy(year),
            "流向": self.db.employment_flow_csy(year),
            "学院": self.db.employment_colleges_csy(year),
        }

    def flow_rank_csy(self, year: int, dimension: str, top: int = 5) -> list:
        """某维度下占比最高的若干项（占比字段是文本，这里转成数值排序）。"""
        rows = self.db.employment_flow_csy(year, dimension)
        parsed = []
        for row in rows:
            text = str(row.get("ratio") or "").replace("%", "").strip()
            try:
                parsed.append((float(text), row))
            except ValueError:
                continue
        parsed.sort(key=lambda item: -item[0])
        return [row for _, row in parsed[:top]]
