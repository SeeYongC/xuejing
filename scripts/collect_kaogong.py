"""采集广东省考试录用公务员的公开数据。

数据源：广东组织工作网「公务员录用」栏目
    https://www.gdzz.gov.cn/gwygz/lypytzgg/index.html

每一年有两条关键公告：
    招录公告        给出计划招录人数、报名时间、笔试时间与科目
    资格审核公告    给出笔试 / 面试 / 总成绩的合格分数线

运行方式：
    python scripts/collect_kaogong.py
"""

import csv
import re
import urllib.request
from pathlib import Path

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
OUT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"
RAW_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "kaogong"

HEADERS_CSY = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
}

# 年份 -> (招录公告, 资格审核公告)
SOURCES_CSY = {
    "2026": ("https://www.gdzz.gov.cn/gwygz/lypytzgg/content/post_24017.html",
             "https://www.gdzz.gov.cn/gwygz/lypytzgg/content/post_24511.html"),
    "2025": ("https://www.gdzz.gov.cn/gwygz/lypytzgg/content/post_22223.html",
             "https://www.gdzz.gov.cn/gwygz/lypytzgg/content/post_22800.html"),
    "2024": ("https://www.gdzz.gov.cn/gwygz/lypytzgg/content/post_20350.html", ""),
}

TAG_PATTERN_CSY = re.compile(r"(?s)<[^>]+>")
SCRIPT_PATTERN_CSY = re.compile(r"(?s)<script.*?</script>|<style.*?</style>")


def fetch_text_csy(url: str) -> str:
    """抓取网页并压平成纯文本。"""
    request = urllib.request.Request(url, headers=HEADERS_CSY)
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read().decode("utf-8", errors="replace")
    text = SCRIPT_PATTERN_CSY.sub(" ", raw)
    text = TAG_PATTERN_CSY.sub(" ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def search_csy(text: str, pattern: str, default: str = "") -> str:
    """按正则取第一个分组，取不到返回默认值。"""
    match = re.search(pattern, text)
    return match.group(1).strip() if match else default


def parse_year_csy(year: str, recruit_url: str, qualify_url: str) -> dict:
    """解析一年的招录公告与资格审核公告。"""
    record = {
        "年份": year,
        "招录人数": "",
        "合格分数线": "",
        "报名时间": "",
        "笔试时间": "",
        "笔试科目": "",
        "学历要求": "",
        "来源": "广东省%s年考试录用公务员公告" % year,
        "来源链接": recruit_url,
    }
    if not recruit_url:
        return record

    text = fetch_text_csy(recruit_url)
    RAW_DIR_CSY.mkdir(parents=True, exist_ok=True)
    (RAW_DIR_CSY / ("%s_招录公告.txt" % year)).write_text(text, encoding="utf-8")

    record["招录人数"] = search_csy(text, r"计划招考公务员\s*(\d+)\s*名")
    record["报名时间"] = search_csy(
        text, r"报名时间\s*(20\d{2}年\d{1,2}月\d{1,2}日[^。]{0,40}?日[^。]{0,10})")
    record["笔试时间"] = search_csy(
        text, r"笔试时间\s*(20\d{2}年\d{1,2}月\d{1,2}日)")
    if "行政职业能力测验" in text and "申论" in text:
        record["笔试科目"] = "行政职业能力测验 + 申论"
    if "大学专科以上" in text:
        record["学历要求"] = "大学专科以上"
    elif "本科以上" in text:
        record["学历要求"] = "本科以上"

    if qualify_url:
        qualify_text = fetch_text_csy(qualify_url)
        (RAW_DIR_CSY / ("%s_资格审核公告.txt" % year)).write_text(
            qualify_text, encoding="utf-8")
        record["合格分数线"] = search_csy(
            qualify_text, r"合格分数线均为\s*(\d+)\s*分")
    return record


def main_csy() -> int:
    """采集三年数据并输出 CSV。"""
    rows = []
    for year, (recruit_url, qualify_url) in sorted(SOURCES_CSY.items(), reverse=True):
        record = parse_year_csy(year, recruit_url, qualify_url)
        rows.append(record)
        print("%s：招录 %s 人，合格线 %s，报名 %s，笔试 %s"
              % (year, record["招录人数"] or "—", record["合格分数线"] or "—",
                 record["报名时间"] or "—", record["笔试时间"] or "—"))

    OUT_DIR_CSY.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR_CSY / "广东省考公务员.csv"
    columns = ["年份", "招录人数", "合格分数线", "报名时间", "笔试时间",
               "笔试科目", "学历要求", "来源", "来源链接"]
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("已输出：%s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
