"""把 data/raw/eea 里的原始网页解析成结构化数据集。

目前解析两类数据：
    1. 历年普通专升本招生最低控制分数线（按专业基础课分类）
    2. 历年招生工作规定里的关键规则（报考条件、时间节点、科目分值）

运行方式：
    python scripts/build_zsb_dataset.py
"""

import csv
import json
import re
from pathlib import Path

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
RAW_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "eea" / "docs"
OUT_DIR_CSY = PROJECT_ROOT_CSY / "data" / "processed"

# 「大学语文（三科总分 / 专业综合课分数）： 130 分 / 100 分」
SCORE_LINE_PATTERN_CSY = re.compile(
    r"([\u4e00-\u9fa5]{2,10})（三科总分\s*/\s*专业综合课分数）：\s*(\d+)\s*分\s*/\s*(\d+)\s*分")

YEAR_PATTERN_CSY = re.compile(r"广东省\s*(20\d{2})\s*年普通高等学校专升本")


def read_text_csy(doc_id: str) -> str:
    """读取采集阶段保存的纯文本正文。"""
    path = RAW_DIR_CSY / (doc_id + ".txt")
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_index_csy() -> list:
    """读取采集阶段的索引，按文档编号去重。"""
    index_path = RAW_DIR_CSY.parent / "index.json"
    records = json.loads(index_path.read_text(encoding="utf-8"))
    unique = {}
    for record in records:
        unique.setdefault(record["id"], record)
    return list(unique.values())


def year_of_csy(title: str) -> str:
    """从文档标题里取年份。"""
    match = re.search(r"(20\d{2})\s*年", title)
    return match.group(1) if match else ""


def parse_score_line_csy(record: dict) -> list:
    """解析一篇分数线通知，返回若干行结构化记录。"""
    if "最低控制分数线" not in record["title"]:
        return []
    title_year = year_of_csy(record["title"])
    text = read_text_csy(record["id"])
    if not text:
        return []
    # 正文里的年份写在「广东省 2026 年普通高等学校专升本」，优先用它
    year_match = YEAR_PATTERN_CSY.search(text)
    year = year_match.group(1) if year_match else title_year

    # 用「（三）原建档立卡考生」把普通考生与建档立卡考生切开
    split_at = text.find("原建档立卡考生")
    head = text[:split_at] if split_at > 0 else text
    tail = text[split_at:] if split_at > 0 else ""

    rows = []
    for label, segment in (("普通考生", head), ("建档立卡考生", tail)):
        for match in SCORE_LINE_PATTERN_CSY.finditer(segment):
            rows.append({
                "年份": year,
                "考生类别": label,
                "专业基础课": match.group(1).strip(),
                "三科总分线": int(match.group(2)),
                "专业综合课线": int(match.group(3)),
                "来源": record["title"],
                "来源链接": record["url"],
            })
    return rows


def parse_rules_csy(record: dict) -> dict:
    """从招生工作规定里抽取关键规则，供系统「路径可达性」模块使用。"""
    if "招生工作规定" not in record["title"]:
        return {}
    text = read_text_csy(record["id"])
    if not text:
        return {}
    year = year_of_csy(record["title"])
    info = {
        "年份": year,
        "来源": record["title"],
        "来源链接": record["url"],
        "考试科目数": 4 if "考试科目共设" in text or "共设 4 门" in text else "",
        "公共课": "政治理论、英语" if "政治理论和英语" in text else "",
        "原文节选": {},
    }
    for label, keyword in [("报名时间", "网上预报名时间"), ("考试时间", "招生考试时间为"),
                           ("报考费", "报考费"), ("录取批次", "录取批次")]:
        position = text.find(keyword)
        if position >= 0:
            info["原文节选"][label] = text[position:position + 120]
    return info


def write_csv_csy(rows: list, path: Path, columns: list) -> None:
    """按给定列写 CSV，带 BOM 以便 Excel 正确识别中文。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main_csy() -> int:
    """解析入口。"""
    records = load_index_csy()
    score_rows = []
    rule_rows = []
    for record in records:
        score_rows.extend(parse_score_line_csy(record))
        rules = parse_rules_csy(record)
        if rules:
            rule_rows.append(rules)

    score_rows.sort(key=lambda row: (row["年份"], row["考生类别"], row["专业基础课"]))
    write_csv_csy(score_rows, OUT_DIR_CSY / "专升本省控线.csv",
                  ["年份", "考生类别", "专业基础课", "三科总分线", "专业综合课线", "来源", "来源链接"])

    rules_path = OUT_DIR_CSY / "专升本招生规定要点.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(json.dumps(rule_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print("省控线记录：%d 条" % len(score_rows))
    for row in score_rows:
        print("  %s %s %s：三科 %d / 综合课 %d"
              % (row["年份"], row["考生类别"], row["专业基础课"],
                 row["三科总分线"], row["专业综合课线"]))
    print("招生规定要点：%d 篇 -> %s" % (len(rule_rows), rules_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
