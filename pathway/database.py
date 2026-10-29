"""数据访问层：封装 pathway.db 的全部查询。

数据库由 scripts/build_database.py 生成，包含三块数据：
    专升本（专插本）  省控线、专业与考试科目、专业与专业综合课
    就业              毕业生规模、升学与深造、分学历落实率、学院分布、就业流向
    考研              国家线（2022-2026，A/B 类，总分与单科）

界面层只调用这里的业务方法，不直接拼 SQL；
需要新增查询时在这里加方法，保证 SQL 集中在一处。
"""

import sqlite3
from typing import Optional


class PathwayDatabase:
    """学历路径数据库的只读访问封装。"""

    def __init__(self, db_path):
        self.db_path = str(db_path)

    def connect_csy(self) -> sqlite3.Connection:
        """建立连接，并把查询结果设成可按列名取值。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def query_csy(self, sql: str, params: Optional[dict] = None) -> list:
        """执行查询，返回字典列表。"""
        with self.connect_csy() as conn:
            cursor = conn.execute(sql, params or {})
            return [dict(row) for row in cursor.fetchall()]

    def scalar_csy(self, sql: str, params: Optional[dict] = None):
        """执行只取一个值的查询。"""
        rows = self.query_csy(sql, params)
        return list(rows[0].values())[0] if rows else None

    def is_ready_csy(self) -> bool:
        """数据库是否已经建好。"""
        try:
            with self.connect_csy() as conn:
                conn.execute("SELECT 1 FROM data_source LIMIT 1")
            return True
        except sqlite3.Error:
            return False

    # ------------------------------------------------------ 数据来源

    def list_sources_csy(self) -> list:
        """列出全部数据来源，用于界面展示与溯源。"""
        return self.query_csy(
            "SELECT name, publisher, coverage, note FROM data_source ORDER BY id")

    # ------------------------------------------------------ 专升本

    def list_zsb_disciplines_csy(self) -> list:
        """专升本招生的学科门类清单。"""
        return [row["discipline"] for row in self.query_csy(
            "SELECT DISTINCT discipline FROM zsb_major_subject "
            "WHERE discipline IS NOT NULL AND discipline <> '' ORDER BY discipline")]

    def list_zsb_basic_subjects_csy(self) -> list:
        """专升本的专业基础课清单（省控线按它分类）。"""
        return [row["basic_subject"] for row in self.query_csy(
            "SELECT DISTINCT basic_subject FROM zsb_score_line ORDER BY basic_subject")]

    def list_zsb_major_subjects_csy(self) -> list:
        """专业目录中实际可匹配专业的专业基础课及数量。"""
        return self.query_csy(
            "SELECT basic_subject AS subject, COUNT(*) AS major_count "
            "FROM zsb_major_subject "
            "WHERE basic_subject IS NOT NULL AND basic_subject <> '' "
            "GROUP BY basic_subject ORDER BY basic_subject")

    def list_zsb_majors_csy(self, keyword: str = "",
                            discipline: str = "",
                            basic_subject: str = "") -> list:
        """按关键词、学科门类或专业基础课查专升本招生专业。"""
        sql = ("SELECT m.year, m.discipline, m.major_code, m.major_name, m.level, "
               "m.common_subjects, m.basic_subject, c.comprehensive_subject "
               "FROM zsb_major_subject m "
               "LEFT JOIN zsb_major_comprehensive c "
               "  ON c.major_code = m.major_code AND c.year = m.year "
               "WHERE 1 = 1")
        params = {}
        if keyword:
            sql += " AND m.major_name LIKE :kw"
            params["kw"] = "%" + keyword + "%"
        if discipline:
            sql += " AND m.discipline = :discipline"
            params["discipline"] = discipline
        if basic_subject:
            sql += " AND m.basic_subject = :basic_subject"
            params["basic_subject"] = basic_subject
        sql += " ORDER BY m.discipline, m.major_code"
        return self.query_csy(sql, params)

    def zsb_score_trend_csy(self, basic_subject: str, candidate_type: str = "普通考生") -> list:
        """某个专业基础课的省控线走势。"""
        return self.query_csy(
            "SELECT year, total_line, comprehensive_line FROM zsb_score_line "
            "WHERE basic_subject = :subject AND candidate_type = :ctype ORDER BY year",
            {"subject": basic_subject, "ctype": candidate_type})

    def zsb_score_table_csy(self, candidate_type: str = "普通考生", year: int = None) -> list:
        """省控线全表，用于横向对比各专业基础课。"""
        if year:
            return self.query_csy(
                "SELECT basic_subject, total_line, comprehensive_line FROM zsb_score_line "
                "WHERE candidate_type = :ctype AND year = :year ORDER BY total_line DESC",
                {"ctype": candidate_type, "year": year})
        return self.query_csy(
            "SELECT year, basic_subject, total_line, comprehensive_line "
            "FROM zsb_score_line WHERE candidate_type = :ctype ORDER BY year, total_line DESC",
            {"ctype": candidate_type})

    # ------------------------------------------------------ 就业

    def list_employment_schools_csy(self) -> list:
        """有就业数据的学校清单。"""
        return [row["school"] for row in self.query_csy(
            "SELECT DISTINCT school FROM emp_scale ORDER BY school")]

    def employment_years_csy(self, school: str = "") -> list:
        """有就业数据的届别。"""
        sql = "SELECT DISTINCT year FROM emp_scale"
        params = {}
        if school:
            sql += " WHERE school = :school"
            params["school"] = school
        sql += " ORDER BY year"
        return [row["year"] for row in self.query_csy(sql, params)]

    def employment_scale_csy(self, year: int, school: str = "") -> list:
        """某届的毕业生规模指标。"""
        sql = ("SELECT metric, numeric_value, unit FROM emp_scale WHERE year = :year")
        params = {"year": year}
        if school:
            sql += " AND school = :school"
            params["school"] = school
        return self.query_csy(sql, params)

    def employment_advance_csy(self, school: str = "") -> list:
        """升学与深造数据（含本科 / 专科升学率），用于跨层次对比。"""
        sql = ("SELECT year, metric, numeric_value, unit FROM emp_advance")
        params = {}
        if school:
            sql += " WHERE school = :school"
            params["school"] = school
        sql += " ORDER BY year, metric"
        return self.query_csy(sql, params)

    def education_level_rates_csy(self, school: str = "") -> list:
        """分学历（本科 / 专科）的就业统计与落实率。"""
        sql = ("SELECT year, education_level, metric, numeric_value, unit "
               "FROM emp_level")
        params = {}
        if school:
            sql += " WHERE school = :school"
            params["school"] = school
        sql += " ORDER BY year, education_level, metric"
        return self.query_csy(sql, params)

    def employment_flow_csy(self, year: int, dimension: str = "") -> list:
        """某届的就业流向，可按维度过滤（地区 / 单位性质 / 行业）。"""
        sql = ("SELECT dimension, category, ratio FROM emp_flow WHERE year = :year")
        params = {"year": year}
        if dimension:
            sql += " AND dimension = :dimension"
            params["dimension"] = dimension
        sql += " ORDER BY dimension, category"
        return self.query_csy(sql, params)

    def employment_colleges_csy(self, year: int, education_level: str = "") -> list:
        """某届分学院的毕业生人数。"""
        sql = ("SELECT college, education_level, student_count, ratio "
               "FROM emp_college WHERE year = :year")
        params = {"year": year}
        if education_level:
            sql += " AND education_level = :level"
            params["level"] = education_level
        sql += " ORDER BY student_count DESC"
        return self.query_csy(sql, params)

    # ------------------------------------------------------ 考研

    def list_kaoyan_disciplines_csy(self) -> list:
        """国家线覆盖的学科门类。"""
        return [row["discipline"] for row in self.query_csy(
            "SELECT DISTINCT discipline FROM kaoyan_national_line "
            "WHERE grouping LIKE '按学科门类%' ORDER BY discipline")]

    def kaoyan_line_trend_csy(self, discipline: str, candidate_class: str = "A类考生") -> list:
        """某学科门类的国家线走势。"""
        return self.query_csy(
            "SELECT year, total_line, single_subject_100, single_subject_150 "
            "FROM kaoyan_national_line "
            "WHERE discipline = :discipline AND candidate_class = :cls "
            "ORDER BY year",
            {"discipline": discipline, "cls": candidate_class})

    def kaoyan_latest_csy(self, candidate_class: str = "A类考生") -> list:
        """最新一年的国家线总览。"""
        latest = self.scalar_csy(
            "SELECT MAX(year) FROM kaoyan_national_line WHERE candidate_class = :cls",
            {"cls": candidate_class})
        if latest is None:
            return []
        return self.query_csy(
            "SELECT year, discipline, total_line, single_subject_100, single_subject_150 "
            "FROM kaoyan_national_line "
            "WHERE year = :year AND candidate_class = :cls "
            "AND grouping LIKE '按学科门类%' ORDER BY total_line DESC",
            {"year": latest, "cls": candidate_class})

    # ------------------------------------------------------ 考公

    def list_kaogong_csy(self) -> list:
        """广东省考公务员的历年数据（招录人数、合格线、时间节点）。"""
        return self.query_csy(
            "SELECT year, recruit_count, pass_line, signup_period, exam_date, "
            "subjects, education_requirement, source, source_url "
            "FROM kaogong ORDER BY year DESC")

    def kaogong_latest_csy(self) -> dict:
        """最新一年的考公数据。"""
        rows = self.list_kaogong_csy()
        return rows[0] if rows else {}
