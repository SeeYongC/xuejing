"""解析《广东省普通高等学校专升本招生工作规定》附件里的专业目录表。

附件 4：拟招生专业与公共课和专业基础课对应表（专业 -> 公共课 + 专业基础课）
附件 5：拟招生专业统考专业综合课对应表（专业 -> 专业综合课）

两个表都由 PDF 转成按列对齐的文本，再按表头给的列位置切分。
运行方式：
    python scripts/parse_zsb_majors.py
"""

import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
DOC_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "eea" / "docs"
OUT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"

# 各年份招生工作规定附件的文件编号（采集脚本按 post_id 命名）
REGULATION_PDFS_CSY = {
    "2026": "post_4802375_1.pdf",
    "2025": "post_4582897_1.pdf",
    "2024": "post_4298046_1.pdf",
}

SECTION_PATTERN_CSY = re.compile(r"[一二三四五六七八九十]+、([\u4e00-\u9fa5]+类)招生专业与统考科目对应表")
MAJOR_PATTERN_CSY = re.compile(r"(\d{6})\s*([\u4e00-\u9fa5A-Za-z（）]{2,24})")
VOCATIONAL_MARK_CSY = re.compile(r"职业(?:院校)?本科院校专业|职业院校本科专业")

# 「080207       车辆工程             机械工程基础」：以 6 位专业代码为锚点切开
CODE_PATTERN_CSY = re.compile(r"(?P<code>\d{6})\s+(?P<rest>\S.*)$")

# 统考科目白名单：附件 4 的科目列只会出现这些名字，用它可以滤掉串进来的正文
COMMON_SUBJECTS_CSY = {"政治理论", "英语"}
BASIC_SUBJECTS_CSY = {"大学语文", "经济学", "民法", "教育理论", "高等数学",
                      "生态学基础", "生理学", "管理学", "艺术概论"}
SUBJECTS_CSY = COMMON_SUBJECTS_CSY | BASIC_SUBJECTS_CSY

# 说明性文字，不参与解析
NOISE_PATTERN_CSY = re.compile(r"说明|颁发|具体见|可选考")


def page_texts_csy(pdf_name: str) -> list:
    """按 layout 模式逐页取出文本，保留表格列对齐。"""
    path = DOC_DIR_CSY / pdf_name
    if not path.exists():
        return []
    reader = PdfReader(str(path))
    return [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]


def column_positions_csy(header_line: str, names: list) -> dict:
    """在表头行里定位各列的起始下标。"""
    positions = {}
    for name in names:
        index = header_line.find(name)
        if index >= 0:
            positions[name] = index
    return positions


def slice_row_csy(line: str, positions: dict) -> dict:
    """按列位置把一行切成若干字段。"""
    ordered = sorted(positions.items(), key=lambda item: item[1])
    cells = {}
    for index, (name, start) in enumerate(ordered):
        end = ordered[index + 1][1] if index + 1 < len(ordered) else len(line)
        cells[name] = line[start:end].strip() if start < len(line) else ""
    return cells


def merge_or_lines_csy(lines: list) -> list:
    """把「经济学或」+「高等数学」这类被换行拆开的科目名合并成一条。"""
    merged = []
    buffer = ""
    for line in lines:
        buffer = buffer + line if buffer else line
        if buffer.endswith("或"):
            continue
        merged.append(buffer)
        buffer = ""
    if buffer:
        merged.append(buffer)
    return merged


def parse_attachment5_csy(pages: list) -> list:
    """附件 5：专业代码 -> 专业综合课。"""
    rows = []
    current = {"门类": "", "专业类别": ""}
    for page in pages:
        if "体格检查表" in page or "附件  6" in page:
            break
        for line in page.split("\n"):
            if "专业综合课名称" in line and "序号" in line:
                continue
            if NOISE_PATTERN_CSY.search(line):
                continue
            match = CODE_PATTERN_CSY.search(line)
            if not match:
                continue
            left = line[:match.start()]
            fields = [item.strip() for item in re.split(r"\s{2,}", match.group("rest")) if item.strip()]
            order = re.match(r"\s*(\d{1,3})", line)
            # 左侧被多空格切成若干段：第一段是序号，其余是门类与专业类别。
            # 门类不带「类」字（工学、理学…），专业类别带「类」字（机械类、电气类…）。
            for token in [item.strip() for item in re.split(r"\s{2,}", left) if item.strip()][1:]:
                key = "专业类别" if token.endswith("类") else "门类"
                current[key] = token
            rows.append({
                "序号": order.group(1) if order else "",
                "门类": current["门类"],
                "专业类别": current["专业类别"],
                "专业代码": match.group("code"),
                "专业名称": fields[0] if fields else "",
                "专业综合课": fields[1] if len(fields) > 1 else "",
                "备注": fields[2] if len(fields) > 2 else "",
            })
    return rows


def parse_attachment4_csy(pages: list) -> list:
    """附件 4：专业 -> 公共课 + 专业基础课。

    一个学科门类下可能并列多张对应表（例如文学类分了英语专业和非英语专业两张），
    所以每遇到一次「招生专业 / 统考科目」表头就新起一张表。
    """
    tables = []
    current = None
    skill_column = None
    section_name = ""
    for page in pages:
        if "统考专业综合课对应表" in page or "附件  5" in page:
            break
        for line in page.split("\n"):
            match = SECTION_PATTERN_CSY.search(line)
            if match:
                section_name = match.group(1)
                continue
            if "统考科目" in line and "招生专业" in line:
                current = {"门类": section_name, "专业": [], "科目": []}
                tables.append(current)
                skill_column = line.find("统考科目")
                continue
            if current is None or skill_column is None:
                continue
            if NOISE_PATTERN_CSY.search(line):
                continue

            left = line[:skill_column]
            right = line[skill_column:].strip()
            for match in MAJOR_PATTERN_CSY.finditer(left):
                current["专业"].append({
                    "专业代码": match.group(1),
                    "专业名称": match.group(2).strip(),
                    "层次": "普通本科",
                })
            if not MAJOR_PATTERN_CSY.search(left) and VOCATIONAL_MARK_CSY.search(left) \
                    and current["专业"]:
                current["专业"][-1]["层次"] = "职业本科"
            # 只保留白名单内的科目，避免把正文或页码当成科目
            if right in SUBJECTS_CSY or right.endswith("或"):
                current["科目"].append(right)

    rows = []
    for table in tables:
        subjects = merge_or_lines_csy(table["科目"])
        if len(subjects) < 2:
            continue
        common, basic = subjects[:-1], subjects[-1]
        for major in table["专业"]:
            rows.append({
                "学科门类": table["门类"],
                "专业代码": major["专业代码"],
                "专业名称": major["专业名称"],
                "层次": major["层次"],
                "公共课": "、".join(common),
                "专业基础课": basic,
            })
    return rows


def write_csv_csy(rows: list, path: Path, columns: list) -> None:
    """写 CSV，带 BOM 方便 Excel 打开中文。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main_csy() -> int:
    """解析各年份招生工作规定的附件，输出专业科目映射表。"""
    all_basic = []
    all_comprehensive = []

    for year, pdf_name in sorted(REGULATION_PDFS_CSY.items(), reverse=True):
        pages = page_texts_csy(pdf_name)
        if not pages:
            print("%s：未找到附件 %s" % (year, pdf_name))
            continue
        basic_rows = parse_attachment4_csy(pages)
        comp_rows = parse_attachment5_csy(pages)
        if not basic_rows and not comp_rows:
            print("%s：附件无可提取文字层（可能是扫描件），已跳过" % year)
            continue
        # 附件 5 的门类列存在合并单元格，用附件 4（门类取自章节标题，可靠）反查补全
        category_by_code = {row["专业代码"]: row["学科门类"] for row in basic_rows}
        for row in comp_rows:
            if row["专业代码"] in category_by_code:
                row["门类"] = category_by_code[row["专业代码"]]
        for row in basic_rows:
            row["年份"] = year
        for row in comp_rows:
            row["年份"] = year
        all_basic.extend(basic_rows)
        all_comprehensive.extend(comp_rows)
        matched = sum(1 for row in comp_rows if row["专业代码"] in category_by_code)
        print("%s：专业-专业基础课 %d 条，专业-专业综合课 %d 条（门类反查成功 %d 条）"
              % (year, len(basic_rows), len(comp_rows), matched))

    write_csv_csy(all_basic, OUT_DIR_CSY / "专升本专业与考试科目.csv",
                  ["年份", "学科门类", "专业代码", "专业名称", "层次", "公共课", "专业基础课"])
    write_csv_csy(all_comprehensive, OUT_DIR_CSY / "专升本专业与专业综合课.csv",
                  ["年份", "门类", "专业类别", "专业代码", "专业名称", "专业综合课", "备注"])

    summary = {}
    for row in all_basic:
        summary.setdefault(row["学科门类"], 0)
        summary[row["学科门类"]] += 1
    print("\n按学科门类统计（含各年份）：")
    for name, count in sorted(summary.items(), key=lambda item: -item[1]):
        print("  %-8s %d 个专业" % (name, count))
    print("\n输出目录：%s" % OUT_DIR_CSY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
