"""采集并解析广东省考职位表。

数据源：广东省2026年考试录用公务员公告附件1（职位表）
    https://www.gdzz.gov.cn/public/广东省2026年考试录用公务员公告附件.zip

职位表是旧版 .xls，含 6 个工作表：
    县以上机关 / 公安 / 法院 / 检察院 / 监狱戒毒 / 乡镇机关
共约 9000 条职位记录。

输出：
    data/processed/广东省考_职位表汇总.csv   按系统、学历、应届限制统计
    data/processed/广东省考_职位明细.csv     逐条职位（便于按条件筛选）

运行方式：
    python scripts/collect_kaogong_jobs.py
"""

import csv
import re
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import quote

import xlrd

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
RAW_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "kaogong"
OUT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"

ZIP_URL_CSY = ("https://www.gdzz.gov.cn/public/"
               "广东省2026年考试录用公务员公告附件.zip")

HEADERS_CSY = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
}

# 职位表里各列的标准名 -> 可能出现的表头写法
COLUMN_ALIASES_CSY = {
    "unit": ["招考单位"],
    "position": ["招考职位"],
    "position_type": ["职位类型"],
    "headcount": ["录用人数"],
    "education": ["学历"],
    "degree": ["学位"],
    "major_graduate": ["研究生专业名称及代码"],
    "major_undergrad": ["本科专业名称及代码"],
    "major_college": ["大专专业名称及代码"],
    "fresh_only": ["是否限应届毕业生报考"],
    "grassroots": ["是否要求2年以上基层工作经历"],
}


def download_zip_csy() -> Path:
    """下载公告附件压缩包，已存在则复用。"""
    RAW_DIR_CSY.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR_CSY / "2026职位表附件.zip"
    if target.exists() and target.stat().st_size > 100000:
        return target
    # URL 里含中文文件名，必须先做百分号编码
    safe_url = quote(ZIP_URL_CSY, safe=":/?&=%")
    request = urllib.request.Request(safe_url, headers=HEADERS_CSY)
    with urllib.request.urlopen(request, timeout=90) as response:
        target.write_bytes(response.read())
    return target


def extract_job_table_csy(zip_path: Path) -> Path:
    """从压缩包里取出职位表 .xls。"""
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            name = info.filename
            try:
                name = name.encode("cp437").decode("gbk")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
            if "职位表" in name and name.lower().endswith(".xls"):
                target = RAW_DIR_CSY / "2026职位表.xls"
                with archive.open(info) as source, target.open("wb") as output:
                    output.write(source.read())
                return target
    raise FileNotFoundError("压缩包里没有找到职位表 .xls")


def normalize_header_csy(text: str) -> str:
    """去掉表头里的换行与空白，便于匹配。"""
    return re.sub(r"\s+", "", str(text))


def find_header_row_csy(sheet) -> int:
    """找到含「招考单位」的表头行。"""
    for row in range(min(8, sheet.nrows)):
        values = [normalize_header_csy(sheet.cell_value(row, col))
                  for col in range(sheet.ncols)]
        if "招考单位" in values:
            return row
    return -1


def map_columns_csy(sheet, header_row: int) -> dict:
    """把标准列名映射到实际列下标。"""
    headers = [normalize_header_csy(sheet.cell_value(header_row, col))
               for col in range(sheet.ncols)]
    mapping = {}
    for key, aliases in COLUMN_ALIASES_CSY.items():
        for alias in aliases:
            normalized = normalize_header_csy(alias)
            if normalized in headers:
                mapping[key] = headers.index(normalized)
                break
    return mapping


def cell_csy(sheet, row: int, mapping: dict, key: str) -> str:
    """安全取一个单元格的值。"""
    index = mapping.get(key)
    if index is None or index >= sheet.ncols:
        return ""
    return str(sheet.cell_value(row, index)).strip()


def parse_jobs_csy(xls_path: Path) -> list:
    """解析全部工作表，返回职位记录。"""
    book = xlrd.open_workbook(str(xls_path))
    records = []
    for sheet_name in book.sheet_names():
        sheet = book.sheet_by_name(sheet_name)
        header_row = find_header_row_csy(sheet)
        if header_row < 0:
            continue
        mapping = map_columns_csy(sheet, header_row)
        for row in range(header_row + 1, sheet.nrows):
            unit = cell_csy(sheet, row, mapping, "unit")
            headcount_text = cell_csy(sheet, row, mapping, "headcount")
            if not unit or not headcount_text:
                continue
            try:
                headcount = int(float(headcount_text))
            except ValueError:
                continue
            records.append({
                "系统": sheet_name,
                "招考单位": unit,
                "招考职位": cell_csy(sheet, row, mapping, "position"),
                "职位类型": cell_csy(sheet, row, mapping, "position_type"),
                "录用人数": headcount,
                "学历": cell_csy(sheet, row, mapping, "education"),
                "学位": cell_csy(sheet, row, mapping, "degree"),
                "研究生专业": cell_csy(sheet, row, mapping, "major_graduate"),
                "本科专业": cell_csy(sheet, row, mapping, "major_undergrad"),
                "大专专业": cell_csy(sheet, row, mapping, "major_college"),
                "限应届": cell_csy(sheet, row, mapping, "fresh_only"),
                "基层经历": cell_csy(sheet, row, mapping, "grassroots"),
            })
    return records


def summarize_csy(records: list) -> list:
    """按系统、学历、应届限制做汇总。"""
    rows = []
    systems = sorted({item["系统"] for item in records})
    for system in systems:
        subset = [item for item in records if item["系统"] == system]
        rows.append({
            "统计维度": "按系统", "类别": system,
            "职位数": len(subset),
            "招录人数": sum(item["录用人数"] for item in subset),
        })

    educations = {}
    for item in records:
        key = item["学历"] or "未注明"
        educations[key] = educations.get(key, 0) + item["录用人数"]
    for key, value in sorted(educations.items(), key=lambda pair: -pair[1]):
        rows.append({"统计维度": "按学历", "类别": key,
                     "职位数": sum(1 for item in records if (item["学历"] or "未注明") == key),
                     "招录人数": value})

    fresh = {}
    for item in records:
        key = item["限应届"] or "未注明"
        fresh[key] = fresh.get(key, 0) + item["录用人数"]
    for key, value in sorted(fresh.items(), key=lambda pair: -pair[1]):
        rows.append({"统计维度": "按应届限制", "类别": key,
                     "职位数": sum(1 for item in records if (item["限应届"] or "未注明") == key),
                     "招录人数": value})
    return rows


def write_csv_csy(rows: list, path: Path) -> None:
    """写 CSV。"""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main_csy() -> int:
    """采集并解析入口。"""
    zip_path = download_zip_csy()
    xls_path = extract_job_table_csy(zip_path)
    records = parse_jobs_csy(xls_path)
    print("解析职位记录：%d 条，合计招录 %d 人"
          % (len(records), sum(item["录用人数"] for item in records)))

    write_csv_csy(records, OUT_DIR_CSY / "广东省考_职位明细.csv")
    summary = summarize_csy(records)
    write_csv_csy(summary, OUT_DIR_CSY / "广东省考_职位表汇总.csv")

    print("\n按系统：")
    for item in summary:
        if item["统计维度"] == "按系统":
            print("  %-10s %4d 个职位，%5d 人"
                  % (item["类别"], item["职位数"], item["招录人数"]))
    print("\n按学历（前 8）：")
    count = 0
    for item in summary:
        if item["统计维度"] == "按学历":
            print("  %-12s %5d 人" % (item["类别"], item["招录人数"]))
            count += 1
            if count >= 8:
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
