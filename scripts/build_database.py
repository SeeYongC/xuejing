"""把 data/processed 下的 CSV 汇入 SQLite 数据库，作为系统的数据底座。

三块数据对应三条路径：
    专升本（专插本）  省控线、专业与考试科目、专业与专业综合课
    就业              毕业生规模、升学与深造、分学历落实率、学院分布、就业流向
    考研              国家线

运行方式：
    python scripts/build_database.py
"""

import csv
import re
import sqlite3
from pathlib import Path

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
PROCESSED_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"
DB_PATH_CSY = PROJECT_ROOT_CSY / "data" / "pathway.db"

SCHEMA_CSY = """
DROP TABLE IF EXISTS zsb_score_line;
DROP TABLE IF EXISTS zsb_major_subject;
DROP TABLE IF EXISTS zsb_major_comprehensive;
DROP TABLE IF EXISTS emp_scale;
DROP TABLE IF EXISTS emp_advance;
DROP TABLE IF EXISTS emp_level;
DROP TABLE IF EXISTS emp_college;
DROP TABLE IF EXISTS emp_flow;
DROP TABLE IF EXISTS kaoyan_national_line;
DROP TABLE IF EXISTS kaogong;
DROP TABLE IF EXISTS kaogong_job_summary;
DROP TABLE IF EXISTS kaogong_job_detail;
DROP TABLE IF EXISTS data_source;

-- 专升本招生最低控制分数线（省控线）
CREATE TABLE zsb_score_line (
    year              INTEGER NOT NULL,   -- 年份
    candidate_type    TEXT    NOT NULL,   -- 考生类别：普通考生 / 建档立卡考生
    basic_subject     TEXT    NOT NULL,   -- 专业基础课名称
    total_line        INTEGER,            -- 三科总分线
    comprehensive_line INTEGER,           -- 专业综合课线
    source            TEXT,               -- 来源文件标题
    source_url        TEXT                -- 来源链接
);

-- 专升本：专业 -> 公共课 + 专业基础课
CREATE TABLE zsb_major_subject (
    year              INTEGER,
    discipline        TEXT,               -- 学科门类
    major_code        TEXT,               -- 专业代码
    major_name        TEXT,               -- 专业名称
    level             TEXT,               -- 普通本科 / 职业本科
    common_subjects   TEXT,               -- 公共课
    basic_subject     TEXT,               -- 专业基础课
    source            TEXT
);

-- 专升本：专业 -> 专业综合课
CREATE TABLE zsb_major_comprehensive (
    year              INTEGER,
    discipline        TEXT,
    major_category    TEXT,               -- 专业类别
    major_code        TEXT,
    major_name        TEXT,
    comprehensive_subject TEXT,           -- 专业综合课名称
    note              TEXT,
    source            TEXT
);

-- 就业：毕业生规模等总量指标
CREATE TABLE emp_scale (
    year              INTEGER,
    school            TEXT,
    metric            TEXT,               -- 指标名
    numeric_value     REAL,               -- 数值
    unit              TEXT,               -- 人 / %
    source            TEXT
);

-- 就业：升学与深造
CREATE TABLE emp_advance (
    year              INTEGER,
    school            TEXT,
    metric            TEXT,
    numeric_value     REAL,
    unit              TEXT,
    note              TEXT,
    source            TEXT
);

-- 就业：分学历落实率
CREATE TABLE emp_level (
    year              INTEGER,
    school            TEXT,
    education_level   TEXT,               -- 本科 / 专科
    metric            TEXT,
    numeric_value     REAL,
    unit              TEXT,
    source            TEXT
);

-- 就业：分学院毕业生人数
CREATE TABLE emp_college (
    year              INTEGER,
    school            TEXT,
    college           TEXT,
    education_level   TEXT,
    student_count     INTEGER,
    ratio             TEXT,
    source            TEXT
);

-- 就业：就业流向（地区 / 城市 / 单位性质 / 行业）
CREATE TABLE emp_flow (
    year              INTEGER,
    school            TEXT,
    dimension         TEXT,               -- 维度
    category          TEXT,               -- 类别
    ratio             TEXT,
    source            TEXT
);

-- 考研国家线
CREATE TABLE kaoyan_national_line (
    grouping          TEXT,               -- 分组：统一划线 / 单独划线 / 少数民族
    discipline        TEXT,               -- 学科门类
    year              INTEGER,
    candidate_class   TEXT,               -- A类考生 / B类考生
    total_line        INTEGER,            -- 总分线
    single_subject_100 INTEGER,           -- 单科（满分 100）
    single_subject_150 INTEGER,           -- 单科（满分 > 100）
    source            TEXT
);

-- 广东省考公务员
CREATE TABLE kaogong (
    year                  INTEGER,
    recruit_count         INTEGER,          -- 计划招录人数
    pass_line             INTEGER,          -- 笔试/面试/总成绩合格分数线
    signup_period         TEXT,             -- 报名时间
    exam_date             TEXT,             -- 笔试时间
    subjects              TEXT,             -- 笔试科目
    education_requirement TEXT,             -- 学历要求
    source                TEXT,
    source_url            TEXT
);

-- 广东省考职位表汇总（按系统 / 学历 / 应届限制）
CREATE TABLE kaogong_job_summary (
    dimension         TEXT,               -- 按系统 / 按学历 / 按应届限制
    category          TEXT,
    job_count         INTEGER,
    headcount         INTEGER
);

-- 广东省考职位明细（逐条职位，便于按条件筛选）
CREATE TABLE kaogong_job_detail (
    system            TEXT,
    unit              TEXT,
    position          TEXT,
    position_type     TEXT,
    headcount         INTEGER,
    education         TEXT,
    degree            TEXT,
    major_graduate    TEXT,
    major_undergrad   TEXT,
    major_college     TEXT,
    fresh_only        TEXT,
    grassroots        TEXT
);

-- 数据来源登记表：每条数据都能追溯到出处
CREATE TABLE data_source (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    publisher         TEXT,               -- 发布单位
    coverage          TEXT,               -- 覆盖范围（年份等）
    note              TEXT
);
"""

# CSV 文件名 -> (表名, {数据库列: CSV 中文表头})
IMPORT_MAP_CSY = {
    "专升本省控线.csv": ("zsb_score_line", {
        "year": "年份", "candidate_type": "考生类别", "basic_subject": "专业基础课",
        "total_line": "三科总分线", "comprehensive_line": "专业综合课线",
        "source": "来源", "source_url": "来源链接"}),
    "专升本专业与考试科目.csv": ("zsb_major_subject", {
        "year": "年份", "discipline": "学科门类", "major_code": "专业代码",
        "major_name": "专业名称", "level": "层次", "common_subjects": "公共课",
        "basic_subject": "专业基础课"}),
    "专升本专业与专业综合课.csv": ("zsb_major_comprehensive", {
        "year": "年份", "discipline": "门类", "major_category": "专业类别",
        "major_code": "专业代码", "major_name": "专业名称",
        "comprehensive_subject": "专业综合课", "note": "备注"}),
    "广州商学院_毕业生规模.csv": ("emp_scale", {
        "year": "年份", "school": "学校", "metric": "指标",
        "numeric_value": "数值", "unit": "单位", "source": "来源"}),
    "广州商学院_升学与深造.csv": ("emp_advance", {
        "year": "年份", "school": "学校", "metric": "指标",
        "numeric_value": "数值", "unit": "单位", "note": "说明", "source": "来源"}),
    "广州商学院_分学历落实率.csv": ("emp_level", {
        "year": "年份", "school": "学校", "education_level": "学历", "metric": "指标",
        "numeric_value": "数值", "unit": "单位", "source": "来源"}),
    "广州商学院_学院分布.csv": ("emp_college", {
        "year": "年份", "school": "学校", "college": "学院",
        "education_level": "学历", "student_count": "人数", "ratio": "占比",
        "source": "来源"}),
    "广州商学院_就业流向.csv": ("emp_flow", {
        "year": "年份", "school": "学校", "dimension": "维度",
        "category": "类别", "ratio": "占比", "source": "来源"}),
    "研招网_历年国家线.csv": ("kaoyan_national_line", {
        "grouping": "分组", "discipline": "学科门类", "year": "年份",
        "candidate_class": "类别", "total_line": "总分线",
        "single_subject_100": "单科满分100",
        "single_subject_150": "单科满分150", "source": "来源"}),
    "广东省考公务员.csv": ("kaogong", {
        "year": "年份", "recruit_count": "招录人数", "pass_line": "合格分数线",
        "signup_period": "报名时间", "exam_date": "笔试时间",
        "subjects": "笔试科目", "education_requirement": "学历要求",
        "source": "来源", "source_url": "来源链接"}),
    "广东省考_职位表汇总.csv": ("kaogong_job_summary", {
        "dimension": "统计维度", "category": "类别",
        "job_count": "职位数", "headcount": "招录人数"}),
    "广东省考_职位明细.csv": ("kaogong_job_detail", {
        "system": "系统", "unit": "招考单位", "position": "招考职位",
        "position_type": "职位类型", "headcount": "录用人数",
        "education": "学历", "degree": "学位",
        "major_graduate": "研究生专业", "major_undergrad": "本科专业",
        "major_college": "大专专业", "fresh_only": "限应届",
        "grassroots": "基层经历"}),
}

NUMBER_PATTERN_CSY = re.compile(r"-?\d+(?:\.\d+)?")


def to_number_csy(value: str):
    """把「8800」「90.19%」「1234」这类文本转成数值，转不了就返回 None。"""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = NUMBER_PATTERN_CSY.search(text)
    if not match:
        return None
    number = float(match.group())
    return int(number) if number == int(number) else number


def read_csv_csy(path: Path) -> list:
    """读取 CSV（带 BOM），返回字典列表。"""
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def import_table_csy(conn: sqlite3.Connection, csv_path: Path, table: str,
                     column_map: dict) -> int:
    """把一份 CSV 导入一张表，返回导入行数。"""
    rows = read_csv_csy(csv_path)
    if not rows:
        return 0
    source_name = csv_path.stem
    columns = list(column_map)
    placeholders = ", ".join("?" for _ in columns)
    insert_sql = "INSERT INTO %s (%s) VALUES (%s)" % (
        table, ", ".join(columns), placeholders)

    payload = []
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column_map[column])
            if column in ("year", "total_line", "comprehensive_line",
                          "single_subject_100", "single_subject_150",
                          "student_count", "numeric_value",
                          "recruit_count", "pass_line",
                          "job_count", "headcount"):
                value = to_number_csy(value)
            values.append(value)
        if "source" in columns and not row.get(column_map["source"]):
            values[columns.index("source")] = source_name
        payload.append(values)

    conn.executemany(insert_sql, payload)
    return len(payload)


def register_sources_csy(conn: sqlite3.Connection) -> None:
    """登记数据来源，供界面展示与文档引用。"""
    sources = [
        ("广东省普通专升本招生最低控制分数线", "广东省教育考试院", "2024-2026 年",
         "来源于省考试院历年《招生最低控制分数线的通知》"),
        ("广东省普通专升本招生专业目录", "广东省教育考试院", "2026 年",
         "摘自招生工作规定附件 4、附件 5"),
        ("广州商学院毕业生就业质量年度报告", "广州商学院（信息公开网）", "2021-2024 届",
         "学校自行统计发布，未经第三方核验；原始文件为图片型 PDF，经 OCR 提取"),
        ("全国硕士研究生招生考试考生进入复试的初试成绩基本要求（国家线）",
         "中国研究生招生信息网", "2022-2026 年", "含 A 类 / B 类考生，总分线与单科线"),
        ("广东省考试录用公务员数据", "中共广东省委组织部（广东组织工作网）", "2024-2026 年",
         "含计划招录人数、合格分数线、报名与笔试时间；2024 年合格线公告未纳入本次采集"),
    ]
    conn.executemany(
        "INSERT INTO data_source (name, publisher, coverage, note) VALUES (?, ?, ?, ?)",
        sources)


def main_csy() -> int:
    """建库入口：重建表结构、导入全部 CSV、登记来源。"""
    DB_PATH_CSY.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH_CSY))
    try:
        conn.executescript(SCHEMA_CSY)
        print("数据库：%s" % DB_PATH_CSY)
        total = 0
        for file_name, (table, column_map) in IMPORT_MAP_CSY.items():
            count = import_table_csy(conn, PROCESSED_DIR_CSY / file_name, table, column_map)
            total += count
            flag = "OK " if count else "缺少"
            print("  %s %-28s -> %-24s %d 行" % (flag, file_name, table, count))
        register_sources_csy(conn)
        conn.commit()
        print("\n共导入 %d 行，数据来源登记 %d 条" % (total, 5))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
