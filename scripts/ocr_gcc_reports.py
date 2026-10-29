"""对广州商学院毕业生就业质量年度报告做 OCR。

这四份报告是图片型 PDF（没有文字层），pypdf 取不到文字，
所以先用 poppler 把每页渲染成 PNG，再用 rapidocr 做中文识别，
结果按页保存成 txt，供后续脚本解析。

依赖：poppler（pdftoppm）、rapidocr-onnxruntime
运行方式：
    python scripts/ocr_gcc_reports.py            # 处理全部
    python scripts/ocr_gcc_reports.py 2024       # 只处理某一年
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
PDF_DIR_CSY = PROJECT_ROOT_CSY / "data" / "raw" / "gcc"
PAGE_DIR_CSY = PDF_DIR_CSY / "pages"
TEXT_DIR_CSY = PDF_DIR_CSY / "text"

# Codex 运行时自带的 poppler，找不到就退回系统 PATH
POPPLER_DIR_CSY = Path(
    r"C:\Users\csy\.cache\codex-runtimes\codex-primary-runtime"
    r"\dependencies\native\poppler\Library\bin")

RENDER_DPI_CSY = 150


def poppler_exe_csy(name: str) -> str:
    """定位 poppler 可执行文件。"""
    candidate = POPPLER_DIR_CSY / ("%s.exe" % name)
    if candidate.exists():
        return str(candidate)
    found = shutil.which(name)
    if not found:
        raise RuntimeError("找不到 poppler 的 %s，请安装 poppler 或调整 POPPLER_DIR_CSY" % name)
    return found


def year_of_csy(pdf_path: Path) -> str:
    """从文件名里取年份。"""
    for token in pdf_path.stem.replace("毕业生", " ").replace("年", " ").split():
        if token.isdigit() and len(token) == 4:
            return token
    digits = "".join(ch for ch in pdf_path.stem if ch.isdigit())
    return digits[:4]


def render_pages_csy(pdf_path: Path, year: str) -> list:
    """把 PDF 每页渲染成 PNG，返回按页码排序的图片路径。"""
    target = PAGE_DIR_CSY / year
    target.mkdir(parents=True, exist_ok=True)
    if not list(target.glob("*.png")):
        subprocess.run(
            [poppler_exe_csy("pdftoppm"), "-png", "-r", str(RENDER_DPI_CSY),
             str(pdf_path), str(target / "page")],
            check=True, capture_output=True)
    return sorted(target.glob("*.png"))


def ocr_report_csy(pdf_path: Path, engine) -> Path:
    """逐页识别并写出纯文本，返回文本文件路径。"""
    year = year_of_csy(pdf_path)
    output = TEXT_DIR_CSY / ("%s_%s.txt" % (year, pdf_path.stem))
    if output.exists() and output.stat().st_size > 500:
        print("  %s 已有识别结果，跳过" % pdf_path.name)
        return output
    pages = render_pages_csy(pdf_path, year)
    lines = []
    for index, image in enumerate(pages, 1):
        try:
            result, _ = engine(str(image))
        except Exception as error:
            lines.append("\n===== 第 %d 页（识别失败：%s） =====\n" % (index, error))
            continue
        lines.append("\n===== 第 %d 页 =====\n" % index)
        for item in (result or []):
            lines.append(str(item[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print("  %s -> %d 页，%d 字" % (pdf_path.name, len(pages), len("\n".join(lines))))
    return output


def main_csy() -> int:
    """OCR 入口。"""
    wanted = sys.argv[1] if len(sys.argv) > 1 else ""
    pdfs = [p for p in sorted(PDF_DIR_CSY.glob("*.pdf")) if not wanted or wanted in p.name]
    if not pdfs:
        print("没有找到待处理的 PDF（目录：%s）" % PDF_DIR_CSY)
        return 1

    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    print("开始 OCR，共 %d 份报告" % len(pdfs))
    for pdf in pdfs:
        ocr_report_csy(pdf, engine)
    print("文本输出目录：%s" % TEXT_DIR_CSY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_csy())
