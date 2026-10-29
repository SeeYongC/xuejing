"""采集研招网公布的历年考研国家线（复试分数线）。

数据源：中国研究生招生信息网「历年复试分数线」专题页
    https://yz.chsi.com.cn/kyzx/zt/lnfsx.shtml
页面里用表格承载各学科门类的总分线，年份列是表头的一部分。

运行方式：
    python scripts/collect_yz_lines.py
"""

import csv
import json
import re
import urllib.request
from pathlib import Path

SOURCE_URL_CSY = "https://yz.chsi.com.cn/kyzx/zt/lnfsx.shtml"

HEADERS_CSY = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
}

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
RAW_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "yz"
OUT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"

TABLE_PATTERN_CSY = re.compile(r'(?s)<table[^>]*class="zg-table"[^>]*>(.*?)</table>')
ROW_PATTERN_CSY = re.compile(r"(?s)<tr[^>]*>(.*?)</tr>")
CELL_PATTERN_CSY = re.compile(r"(?s)<t[hd][^>]*>(.*?)</t[hd]>")
TAG_PATTERN_CSY = re.compile(r"(?s)<[^>]+>")
DIGIT_ARRAY_PATTERN_CSY = re.compile(r"\[\s*\d{3}\s*(?:,\s*\d{3}\s*){2,}\]")

# 页面把国家线数据以内联 JS 的形式给出，变量名固定
DATA_VARS_CSY = {
    "tyhxList": "按学科门类统一划线学科专业",
    "ddhxList": "单独划线学科专业",
    "zgzcList": "少数民族骨干计划与照顾政策考生",
}

# 趋势图数组按年份升序给出；具体年份以 dkx 为准（各组年数可能不同）
DEFAULT_YEARS_CSY = ["2022", "2023", "2024", "2025", "2026"]


def fetch_csy(url: str) -> str:
    """抓取页面文本。"""
    request = urllib.request.Request(url, headers=HEADERS_CSY)
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8", errors="replace")


def cell_text_csy(html: str) -> str:
    """去掉标签取纯文本，把 <br> 当作空格。"""
    text = re.sub(r"(?i)<br\s*/?>", " ", html)
    text = TAG_PATTERN_CSY.sub("", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return " ".join(text.split())


def parse_tables_csy(html: str) -> list:
    """把页面里的表格解析成若干行。"""
    tables = []
    for table_html in TABLE_PATTERN_CSY.findall(html):
        rows = []
        for row_html in ROW_PATTERN_CSY.findall(table_html):
            cells = [cell_text_csy(cell) for cell in CELL_PATTERN_CSY.findall(row_html)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def find_section_title_csy(html: str, position: int) -> str:
    """取表格前面最近的 h5 标题，作为这张表的说明。"""
    head = html[:position]
    titles = re.findall(r"(?s)<h5[^>]*>(.*?)</h5>", head)
    return cell_text_csy(titles[-1]) if titles else ""


def extract_var_json_csy(html: str, var_name: str):
    """把内联 JS 里的 `var xxx = [...]` 提取出来并解析成 Python 对象。

    页面里的数据用的是标准 JSON 写法（双引号键值），所以只要按括号配对
    截出数组，就能直接交给 json 解析。
    """
    start = html.find("var %s" % var_name)
    if start < 0:
        return None
    bracket = html.find("[", start)
    if bracket < 0:
        return None
    depth = 0
    for index in range(bracket, len(html)):
        char = html[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                raw = html[bracket:index + 1]
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return None
    return None


def flatten_lines_csy(data: dict, category: str) -> list:
    """把某个分组下的国家线摊平成 CSV 行。"""
    rows = []
    for item in data or []:
        name = item.get("name", "")
        if not name.strip():
            continue          # 跳过页面里的空模板项
        trend = item.get("gjx") or {}
        type_a = trend.get("typea") or []
        type_b = trend.get("typeb") or []
        single_by_year = {entry.get("year"): entry
                          for entry in (item.get("dkx") or [])}
        # 以 dkx 给出的年份为准（升序），数组长度不足时取默认年份
        years = sorted(single_by_year) or DEFAULT_YEARS_CSY
        for index, year in enumerate(years):
            entry = single_by_year.get(year) or {}
            rows.append({
                "分组": category, "学科门类": name, "年份": year,
                "类别": "A类考生", "总分线": type_a[index] if index < len(type_a) else "",
                "单科满分100": entry.get("typeaone", ""),
                "单科满分150": entry.get("typeatwo", ""),
                "来源": SOURCE_URL_CSY,
            })
            rows.append({
                "分组": category, "学科门类": name, "年份": year,
                "类别": "B类考生", "总分线": type_b[index] if index < len(type_b) else "",
                "单科满分100": entry.get("typebone", ""),
                "单科满分150": entry.get("typebtwo", ""),
                "来源": SOURCE_URL_CSY,
            })
    return rows


def main_csy() -> int:
    """采集并输出国家线表格。"""
    html = fetch_csy(SOURCE_URL_CSY)
    RAW_DIR_CSY.mkdir(parents=True, exist_ok=True)
    (RAW_DIR_CSY / "lnfsx.html").write_text(html, encoding="utf-8")

    tables = parse_tables_csy(html)
    print("页面里的静态表格 %d 张（表头为模板，仅作核对）" % len(tables))

    rows = []
    for var_name, category in DATA_VARS_CSY.items():
        data = extract_var_json_csy(html, var_name)
        if not data:
            print("  未取到 %s（%s）" % (var_name, category))
            continue
        part = flatten_lines_csy(data, category)
        rows.extend(part)
        print("  %s：%d 个学科门类 -> %d 条记录" % (category, len(data), len(part)))

    if not rows:
        print("没有解析到国家线数据，请检查页面结构是否变化")
        return 1

    out = OUT_DIR_CSY / "研招网_历年国家线.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    columns = ["分组", "学科门类", "年份", "类别", "总分线", "单科满分100", "单科满分150", "来源"]
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("\n共 %d 条记录 -> %s" % (len(rows), out))

    print("\n示例（哲学，最近三年）：")
    for row in rows:
        if row["学科门类"] == "哲学" and row["年份"] in ("2024", "2025", "2026"):
            print("  %s %s 总分 %s 单科 %s/%s"
                  % (row["年份"], row["类别"], row["总分线"],
                     row["单科满分100"], row["单科满分150"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
