"""把广州商学院就业质量报告的 OCR 文本解析成结构化数据。

报告是图片型 PDF，先由 scripts/ocr_gcc_reports.py 转成文本，
本脚本再从文本里抽取规模、学历结构、学院分布、就业流向等数据。

运行方式：
    python scripts/build_gcc_dataset.py
"""

import csv
import re
from pathlib import Path

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
TEXT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "gcc" / "text"
OUT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"

SCHOOL_CSY = "广州商学院"

# OCR 会把「9.89%」错切成「9. 89%」，统一修回来
SPLIT_DECIMAL_CSY = re.compile(r"(\d)\.\s+(\d)")

PATTERNS_CSY = {
    # OCR 会把「共计」拆成「共 计」，这里容忍中间空白
    "total": re.compile(r"毕业生在全国高校毕业生就业管理系统共\s*计\s*(\d+)\s*人"),
    "settled": re.compile(r"已(?:就业|落实毕业去向)\s*(\d+)\s*人"),
    # 必须排除「未落实率」，否则 2023 届的 7.91% 会被误当成落实率
    "rate": re.compile(r"(?<!未)落实率为\s*([\d.]+)\s*%"),
    # 报告里可能写成「本科毕业生纳入就业统计 4133 人」
    "undergrad": re.compile(r"本科毕业生[^。]{0,20}?(\d+)\s*人"),
    "college": re.compile(r"专科毕业生[^。]{0,20}?(\d+)\s*人"),
    "male": re.compile(r"男生\s*(\d+)\s*人"),
    "in_province": re.compile(r"省内生源\s*(\d+)\s*人"),
}

# 「升学」这一段是系统的核心数据：境内升学里分研究生与专升本，
# 升学率又分总体、本科、专科三层，正好用来做跨层次对比。
ADVANCE_PATTERNS_CSY = {
    "境内升学": re.compile(r"境内升学\s*(\d+)\s*人"),
    "其中研究生": re.compile(r"研究生\s*(\d+)\s*人"),
    "其中专升本": re.compile(r"专升本\s*(\d+)\s*人"),
    "出国深造": re.compile(r"(?:出国[（(]出境[）)]深造|出国[（(]境[）)]深造)\s*(\d+)\s*人"),
    "出国深造本科": re.compile(r"出国[（(]出境[）)]深造\s*\d+\s*人[（(]本科\s*(\d+)\s*人"),
    "出国深造专科": re.compile(r"出国[（(]出境[）)]深造\s*\d+\s*人[（(]本科\s*\d+\s*人[，,]\s*专科\s*(\d+)\s*人"),
    "总体升学率": re.compile(r"总体升学率为\s*([\d.]+)\s*%"),
    "本科升学率": re.compile(r"本科升学率为\s*([\d.]+)\s*%"),
    "专科升学率": re.compile(r"专科升学率为\s*([\d.]+)\s*%"),
    "创业人数": re.compile(r"自主创业人数\s*(\d+)\s*人"),
    "创业率": re.compile(r"创业率\s*([\d.]+)\s*%"),
    "应征入伍": re.compile(r"应征入\s*伍\s*(\d+)\s*人"),
}

# 分学历的就业统计与落实率（2021 用「已就业」，2023 起用「已落实毕业去向」）
LEVEL_PATTERNS_CSY = {
    "本科": {
        "统计人数": re.compile(r"本科毕业生纳入就业统计\s*(\d+)\s*人"),
        "就业人数": re.compile(r"本科毕业生纳入就业统计\s*\d+\s*人[，,]\s*已(?:就业|落实毕业去向)\s*(\d+)\s*人"),
        "落实率": re.compile(r"本科毕业生纳入就业统计\s*\d+\s*人[，,]\s*已(?:就业|落实毕业去向)\s*\d+\s*人[，,]\s*(?:初次)?(?:毕业去向)?落实率为\s*([\d.]+)\s*%"),
    },
    "专科": {
        "统计人数": re.compile(r"专科毕业生纳入就业统计\s*(\d+)\s*人"),
        "就业人数": re.compile(r"专科毕业生纳入就业统计\s*\d+\s*人[，,]\s*已(?:就业|落实毕业去向)\s*(\d+)\s*人"),
        "落实率": re.compile(r"专科毕业生纳入就业统计\s*\d+\s*人[，,]\s*已(?:就业|落实毕业去向)\s*\d+\s*人[，,]\s*(?:初次)?(?:毕业去向)?落实率为\s*([\d.]+)\s*%"),
    },
}

COLLEGE_ROW_CSY = re.compile(
    # 「学院」前至少 1 个汉字即可：像「法学院」这种三字院名也要能匹配
    r"([\u4e00-\u9fa5]{1,12}学院)\s*(本科|专科)\s*(\d{2,5})\s*([\d.]+)\s*%")


def normalize_csy(text: str) -> str:
    """压平空白并修回被切开的百分数。"""
    flat = " ".join(text.split())
    return SPLIT_DECIMAL_CSY.sub(r"\1.\2", flat)


def compact_csy(text: str) -> str:
    """去掉所有空白，用于匹配被 OCR 换行拆开的关键词（如「研究 生」）。"""
    return re.sub(r"\s+", "", text)


def search_csy(pattern, text: str, compact: str):
    """先在有空格文本里找，找不到再到去空格文本里找。"""
    return pattern.search(text) or pattern.search(compact)


def load_reports_csy() -> dict:
    """读取全部 OCR 文本，按年份返回。"""
    reports = {}
    for path in sorted(TEXT_DIR_CSY.glob("*.txt")):
        match = re.match(r"(\d{4})", path.name)
        if match:
            reports[match.group(1)] = normalize_csy(path.read_text(encoding="utf-8"))
    return reports


def extract_summary_csy(year: str, text: str) -> list:
    """抽取总体规模与学历结构。"""
    rows = []
    for key, label, unit in [("total", "毕业生总数", "人"),
                             ("undergrad", "本科毕业生", "人"),
                             ("college", "专科毕业生", "人"),
                             ("settled", "已落实毕业去向", "人"),
                             ("male", "男生", "人"),
                             ("in_province", "省内生源", "人")]:
        match = PATTERNS_CSY[key].search(text)
        if match:
            rows.append({"年份": year, "学校": SCHOOL_CSY, "指标": label,
                         "数值": int(match.group(1)), "单位": unit,
                         "来源": "%s届毕业生就业质量年度报告" % year})
    rate = PATTERNS_CSY["rate"].search(text)
    if rate:
        rows.append({"年份": year, "学校": SCHOOL_CSY, "指标": "毕业去向落实率",
                     "数值": rate.group(1) + "%", "单位": "%",
                     "来源": "%s届毕业生就业质量年度报告" % year})
    else:
        # 报告原文里的落实率被裁掉时，用「已落实人数 / 总人数」计算，并标明口径
        total_match = PATTERNS_CSY["total"].search(text)
        settled_match = PATTERNS_CSY["settled"].search(text)
        if total_match and settled_match:
            total = int(total_match.group(1))
            settled = int(settled_match.group(1))
            if total:
                rows.append({
                    "年份": year, "学校": SCHOOL_CSY,
                    "指标": "毕业去向落实率（按人数计算）",
                    "数值": "%.2f%%" % (settled * 100.0 / total), "单位": "%",
                    "来源": "%s届毕业生就业质量年度报告（原文比例被裁，"
                            "按已落实 %d / 总数 %d 计算）" % (year, settled, total),
                })
    return rows


def extract_colleges_csy(year: str, text: str) -> list:
    """抽取分学院分学历的毕业生人数（表 1-1）。"""
    rows = []
    for match in COLLEGE_ROW_CSY.finditer(text):
        rows.append({"年份": year, "学校": SCHOOL_CSY,
                     "学院": match.group(1), "学历": match.group(2),
                     "人数": int(match.group(3)), "占比": match.group(4) + "%",
                     "来源": "%s届毕业生就业质量年度报告" % year})
    return rows


# 就业流向：报告把这些数字写进了正文，按正文句式抽取
FLOW_PATTERNS_CSY = [
    ("就业地区", "广东省内",
     re.compile(r"主要选择在广东省内就业（([\d.]+)%）")),
    ("就业地区", "珠三角地区",
     re.compile(r"主要集中于珠三角地区（([\d.]+)%）")),
    ("省内就业城市", "广州市",
     re.compile(r"主要流向了广州市（([\d.]+)%）")),
    ("省内就业城市", "深圳市",
     re.compile(r"深圳市（([\d.]+)%）")),
    ("省内就业城市", "佛山市",
     re.compile(r"佛山市（([\d.]+)%）")),
    ("单位性质", "企业单位",
     re.compile(r"流向单位类型为企业单位\d?，占比为([\d.]+)%")),
    ("单位性质", "国有企业",
     re.compile(r"国有企业占比为([\d.]+)%")),
    ("单位性质", "其他企业",
     re.compile(r"其他企业为([\d.]+)%")),
    ("单位性质", "自由职业",
     re.compile(r"选择自由职业（([\d.]+)%）")),
    ("单位性质", "机关单位",
     re.compile(r"到机关单位（([\d.]+)%）")),
    ("单位性质", "事业单位",
     re.compile(r"事业单位（([\d.]+)%）")),
    ("单位性质", "自主创业",
     re.compile(r"选择自主创业（([\d.]+)%）")),
]


def extract_flow_csy(year: str, text: str) -> list:
    """抽取就业流向（地区、城市、单位性质）。"""
    rows = []
    for dimension, label, pattern in FLOW_PATTERNS_CSY:
        match = pattern.search(text)
        if match:
            rows.append({"年份": year, "学校": SCHOOL_CSY, "维度": dimension,
                         "类别": label, "占比": match.group(1) + "%",
                         "来源": "%s届毕业生就业质量年度报告" % year})
    # 就业量最大的前三个行业
    industries = re.findall(r"“([^”]{2,20})”领域（([\d.]+)%）", text)
    for name, share in industries[:3]:
        rows.append({"年份": year, "学校": SCHOOL_CSY, "维度": "行业流向",
                     "类别": name.strip(), "占比": share + "%",
                     "来源": "%s届毕业生就业质量年度报告" % year})
    return rows


def extract_advance_csy(year: str, text: str) -> list:
    """抽取升学与深造的规模和比例，这是跨层次对比的核心数据。"""
    flat = compact_csy(text)
    rows = []
    for label, pattern in ADVANCE_PATTERNS_CSY.items():
        match = search_csy(pattern, text, flat)
        if not match:
            continue
        value = match.group(1)
        unit = "%" if label.endswith("率") else "人"
        rows.append({
            "年份": year, "学校": SCHOOL_CSY, "指标": label,
            "数值": value + "%" if unit == "%" else int(value),
            "单位": unit,
            "说明": "境内升学含研究生、专升本、第二学位" if label.startswith(("境内", "其中", "总体", "本科升学", "专科升学")) else "",
            "来源": "%s届毕业生就业质量年度报告" % year,
        })
    return rows


def extract_levels_csy(year: str, text: str) -> list:
    """抽取分学历（本科 / 专科）的就业统计与落实率。"""
    flat = compact_csy(text)
    rows = []
    for level, patterns in LEVEL_PATTERNS_CSY.items():
        for label, pattern in patterns.items():
            match = search_csy(pattern, text, flat)
            if not match:
                continue
            value = match.group(1)
            unit = "%" if label == "落实率" else "人"
            rows.append({
                "年份": year, "学校": SCHOOL_CSY, "学历": level, "指标": label,
                "数值": value + "%" if unit == "%" else int(value),
                "单位": unit,
                "来源": "%s届毕业生就业质量年度报告" % year,
            })
    return rows


def write_csv_csy(rows: list, path: Path) -> None:
    """写 CSV；没有数据时也要留下表头。"""
    if not rows:
        return
    columns = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main_csy() -> int:
    """解析入口：逐份报告抽取，汇总输出。"""
    reports = load_reports_csy()
    if not reports:
        print("没有找到 OCR 文本，请先运行 scripts/ocr_gcc_reports.py")
        return 1

    summary, colleges, flows = [], [], []
    advances, levels = [], []
    for year, text in sorted(reports.items()):
        part1 = extract_summary_csy(year, text)
        part2 = extract_colleges_csy(year, text)
        part3 = extract_flow_csy(year, text)
        part4 = extract_advance_csy(year, text)
        part5 = extract_levels_csy(year, text)
        summary.extend(part1)
        colleges.extend(part2)
        flows.extend(part3)
        advances.extend(part4)
        levels.extend(part5)
        print("%s：规模 %d，学院 %d，流向 %d，升学 %d，分学历 %d"
              % (year, len(part1), len(part2), len(part3), len(part4), len(part5)))

    write_csv_csy(summary, OUT_DIR_CSY / "广州商学院_毕业生规模.csv")
    write_csv_csy(colleges, OUT_DIR_CSY / "广州商学院_学院分布.csv")
    write_csv_csy(flows, OUT_DIR_CSY / "广州商学院_就业流向.csv")
    write_csv_csy(advances, OUT_DIR_CSY / "广州商学院_升学与深造.csv")
    write_csv_csy(levels, OUT_DIR_CSY / "广州商学院_分学历落实率.csv")
    print("\n输出目录：%s" % OUT_DIR_CSY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
