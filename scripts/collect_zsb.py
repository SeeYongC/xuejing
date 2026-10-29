"""采集广东省教育考试院公开的普通专升本（专插本）数据。

数据来源全部是官方公开发布的通知与附件，采集结果落盘到 data/raw/eea/，
再由 scripts/build_zsb_dataset.py 解析成结构化数据。

运行方式：
    python scripts/collect_zsb.py
"""

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL_CSY = "https://eea.gd.gov.cn"

# 专升本信息分散在这三个栏目里：业务文件、通知公告、招考公示
SECTIONS_CSY = ["bmbk_sksywj", "tzgg", "zwgk_zkgs"]
PAGES_PER_SECTION_CSY = 8

KEYWORD_CSY = "专升本"
INTERESTING_CSY = ("招生工作规定", "最低控制分数线", "志愿填报", "招生录取",
                   "成绩发布", "招生专业目录", "征集志愿", "三二分段")

HEADERS_CSY = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
}

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
RAW_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "eea"
DOC_DIR_CSY = RAW_DIR_CSY / "docs"
INDEX_PATH_CSY = RAW_DIR_CSY / "index.json"

ATTACHMENT_PATTERN_CSY = re.compile(
    r'href="([^"]+\.(?:pdf|doc|docx|xls|xlsx))"', re.IGNORECASE)
ANCHOR_PATTERN_CSY = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
TAG_PATTERN_CSY = re.compile(r"<[^>]+>")
SCRIPT_PATTERN_CSY = re.compile(r"(?s)<script.*?</script>|<style.*?</style>")


def fetch_text_csy(url: str, retries: int = 2) -> str:
    """抓取一个页面并返回文本；失败重试若干次后抛异常。"""
    last_error = None
    for _ in range(retries + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS_CSY)
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
            return raw.decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(1.5)
    raise RuntimeError("抓取失败：%s（%s）" % (url, last_error))


def fetch_bytes_csy(url: str) -> bytes:
    """抓取二进制附件（PDF / Excel）。"""
    request = urllib.request.Request(url, headers=HEADERS_CSY)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def strip_html_csy(html: str) -> str:
    """去掉标签与脚本，压成一行纯文本。"""
    text = SCRIPT_PATTERN_CSY.sub(" ", html)
    text = TAG_PATTERN_CSY.sub(" ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def section_list_urls_csy() -> list:
    """列出待翻页的栏目地址（第一页没有页码后缀）。"""
    urls = []
    for section in SECTIONS_CSY:
        urls.append("%s/%s/index.html" % (BASE_URL_CSY, section))
        for page in range(1, PAGES_PER_SECTION_CSY):
            urls.append("%s/%s/index_%d.html" % (BASE_URL_CSY, section, page))
    return urls


def find_documents_csy() -> list:
    """翻遍栏目列表，收集标题里带「专升本」的文档。"""
    found = {}
    for url in section_list_urls_csy():
        try:
            html = fetch_text_csy(url, retries=1)
        except RuntimeError:
            continue
        for match in ANCHOR_PATTERN_CSY.finditer(html):
            href = match.group(1)
            title = strip_html_csy(match.group(2))
            if KEYWORD_CSY not in title or len(title) < 8:
                continue
            if not href.startswith("http"):
                href = BASE_URL_CSY + "/" + href.lstrip("/")
            found[href] = title
        time.sleep(0.4)
    documents = [{"url": url, "title": title} for url, title in sorted(found.items())]
    documents.sort(key=lambda item: item["title"], reverse=True)
    return documents


def document_id_csy(url: str) -> str:
    """从详情页地址里取出 post_xxxxx 作为文件名。"""
    match = re.search(r"(post_\d+)", url)
    return match.group(1) if match else re.sub(r"\W+", "_", url)[-40:]


def save_document_csy(document: dict) -> dict:
    """抓取详情页正文与附件，落盘并返回记录。"""
    html = fetch_text_csy(document["url"])
    doc_id = document_id_csy(document["url"])
    (DOC_DIR_CSY / (doc_id + ".html")).write_text(html, encoding="utf-8")
    plain = strip_html_csy(html)
    (DOC_DIR_CSY / (doc_id + ".txt")).write_text(plain, encoding="utf-8")

    attachments = []
    for match in ATTACHMENT_PATTERN_CSY.finditer(html):
        href = match.group(1)
        if not href.startswith("http"):
            href = BASE_URL_CSY + "/" + href.lstrip("/")
        if href in attachments:
            continue
        attachments.append(href)
        suffix = Path(href).suffix.lower()
        target = DOC_DIR_CSY / (doc_id + "_" + str(len(attachments)) + suffix)
        try:
            target.write_bytes(fetch_bytes_csy(href))
        except Exception:
            attachments.pop()
        time.sleep(0.3)

    record = dict(document)
    record["id"] = doc_id
    record["attachments"] = attachments
    record["text_length"] = len(plain)
    record["interesting"] = any(key in document["title"] for key in INTERESTING_CSY)
    return record


def main_csy() -> int:
    """采集入口：找文档、抓正文与附件、写索引。"""
    DOC_DIR_CSY.mkdir(parents=True, exist_ok=True)
    documents = find_documents_csy()
    print("发现专升本相关文档 %d 篇" % len(documents))

    records = []
    for index, document in enumerate(documents, 1):
        try:
            record = save_document_csy(document)
        except Exception as error:
            print("  [%d/%d] 失败：%s（%s）" % (index, len(documents), document["title"][:30], error))
            continue
        records.append(record)
        flag = "★" if record["interesting"] else " "
        print("  [%d/%d]%s %s" % (index, len(documents), flag, document["title"][:44]))
        time.sleep(0.5)

    INDEX_PATH_CSY.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print("索引已写入：%s" % INDEX_PATH_CSY)
    print("原始文件目录：%s" % DOC_DIR_CSY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
