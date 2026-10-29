"""生成课程设计交付文档：系统开发文档与系统使用说明书。

运行方式：
    python scripts/build_docs.py

输出到 docs/ 目录下的两个 PDF。文档里的模块表、测试统计、数据规模
都直接取自项目本身，改完代码重跑一次即可保持文档与实现一致。
"""

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT_CSY = Path(__file__).resolve().parent.parent
OUTPUT_DIR_CSY = PROJECT_ROOT_CSY / "docs"

FONT_BODY_CSY = "DocBody"
FONT_BOLD_CSY = "DocBold"
FONT_MONO_CSY = "DocMono"

COLOR_TEXT_CSY = colors.HexColor("#2B2723")
COLOR_MUTED_CSY = colors.HexColor("#6E675D")
COLOR_ACCENT_CSY = colors.HexColor("#2F6FED")
COLOR_LINE_CSY = colors.HexColor("#D7CFC1")
COLOR_CODE_BG_CSY = colors.HexColor("#F8F6F1")
COLOR_HEAD_BG_CSY = colors.HexColor("#F2EFE8")

SYSTEM_SHORT_CSY = "学历路径分析与推荐系统"
SYSTEM_FULL_CSY = "基于公开数据的本专科学历路径分析与推荐系统"


def register_fonts_csy() -> None:
    """注册中文字体：优先用微软雅黑，取不到时退回 reportlab 内置的中文宋体。"""
    candidates = [
        (FONT_BODY_CSY, r"C:\Windows\Fonts\msyh.ttc", 0),
        (FONT_BOLD_CSY, r"C:\Windows\Fonts\msyhbd.ttc", 0),
    ]
    ok = True
    for name, path, index in candidates:
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=index))
        except Exception:
            ok = False
    if not ok:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        globals()[FONT_BODY_CSY] = "STSong-Light"
        globals()[FONT_BOLD_CSY] = "STSong-Light"
    # 代码块里既有 ASCII 也有中文注释，必须选一款中英文都覆盖的等宽字体。
    for mono_name, mono_path, mono_index in [
        (FONT_MONO_CSY, r"C:\Windows\Fonts\simsun.ttc", 1),
        (FONT_MONO_CSY, r"C:\Windows\Fonts\simsun.ttc", 0),
        (FONT_MONO_CSY, r"C:\Windows\Fonts\consola.ttf", 0),
    ]:
        try:
            pdfmetrics.registerFont(TTFont(mono_name, mono_path, subfontIndex=mono_index))
            break
        except Exception:
            continue
    else:
        globals()[FONT_MONO_CSY] = FONT_BODY_CSY


def build_styles_csy() -> dict:
    """构造文档用到的全部段落样式。中文必须用 CJK 换行，否则会整段溢出。"""
    return {
        "cover_title": ParagraphStyle("cover_title", fontName=FONT_BOLD_CSY, fontSize=24,
                                      leading=36, textColor=COLOR_TEXT_CSY,
                                      alignment=TA_LEFT, wordWrap="CJK"),
        "cover_sub": ParagraphStyle("cover_sub", fontName=FONT_BODY_CSY, fontSize=13,
                                    leading=22, textColor=COLOR_MUTED_CSY, wordWrap="CJK"),
        "cover_meta": ParagraphStyle("cover_meta", fontName=FONT_BODY_CSY, fontSize=10,
                                     leading=18, textColor=COLOR_TEXT_CSY, wordWrap="CJK"),
        "h1": ParagraphStyle("h1", fontName=FONT_BOLD_CSY, fontSize=15, leading=24,
                             textColor=COLOR_TEXT_CSY, spaceBefore=16, spaceAfter=8,
                             wordWrap="CJK"),
        "h2": ParagraphStyle("h2", fontName=FONT_BOLD_CSY, fontSize=12, leading=20,
                             textColor=COLOR_TEXT_CSY, spaceBefore=10, spaceAfter=5,
                             wordWrap="CJK"),
        "h3": ParagraphStyle("h3", fontName=FONT_BOLD_CSY, fontSize=10.5, leading=18,
                             textColor=COLOR_ACCENT_CSY, spaceBefore=8, spaceAfter=4,
                             wordWrap="CJK"),
        "body": ParagraphStyle("body", fontName=FONT_BODY_CSY, fontSize=10, leading=17,
                               textColor=COLOR_TEXT_CSY, spaceAfter=6, wordWrap="CJK"),
        # 项目符号不用 reportlab 的 bulletText：中英混排加 CJK 换行时符号会丢
        "bullet": ParagraphStyle("bullet", fontName=FONT_BODY_CSY, fontSize=10, leading=17,
                                 textColor=COLOR_TEXT_CSY, leftIndent=13,
                                 spaceAfter=3, wordWrap="CJK"),
        "step": ParagraphStyle("step", fontName=FONT_BODY_CSY, fontSize=10, leading=17,
                               textColor=COLOR_TEXT_CSY, leftIndent=18, spaceAfter=4,
                               wordWrap="CJK"),
        "code": ParagraphStyle("code", fontName=FONT_MONO_CSY, fontSize=8, leading=12.5,
                               textColor=colors.HexColor("#2E2A26"),
                               backColor=COLOR_CODE_BG_CSY, borderPadding=6,
                               leftIndent=2, spaceBefore=2, spaceAfter=8),
        "caption": ParagraphStyle("caption", fontName=FONT_BODY_CSY, fontSize=9,
                                  leading=15, textColor=COLOR_MUTED_CSY,
                                  spaceBefore=2, spaceAfter=10, wordWrap="CJK"),
        "cell": ParagraphStyle("cell", fontName=FONT_BODY_CSY, fontSize=8.5,
                               leading=14, textColor=COLOR_TEXT_CSY, wordWrap="CJK"),
        "cell_head": ParagraphStyle("cell_head", fontName=FONT_BOLD_CSY, fontSize=8.5,
                                    leading=14, textColor=COLOR_TEXT_CSY, wordWrap="CJK"),
    }


def escape_csy(text: str) -> str:
    """转义 XML 特殊字符，供 Paragraph 解析。"""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# bullet 与 code 有各自独立的处理分支，不能放进这张表
STYLE_FOR_KIND_CSY = {"h1": "h1", "h2": "h2", "h3": "h3", "p": "body",
                      "step": "step", "caption": "caption"}


def make_code_paragraph_csy(text: str, styles: dict) -> Paragraph:
    """代码块：保留缩进与换行。"""
    lines = []
    for line in escape_csy(text).split("\n"):
        indent = len(line) - len(line.lstrip(" "))
        lines.append("&nbsp;" * indent + line[indent:])
    return Paragraph("<br/>".join(lines), styles["code"])


def make_table_csy(spec: dict, styles: dict) -> Table:
    """按 spec 生成一张三线风格的表格。"""
    head = [Paragraph(escape_csy(cell), styles["cell_head"]) for cell in spec["header"]]
    rows = [[Paragraph(escape_csy(cell), styles["cell"]) for cell in row]
            for row in spec["rows"]]
    table = Table([head] + rows, colWidths=spec.get("widths"), repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEAD_BG_CSY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_CODE_BG_CSY]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, COLOR_LINE_CSY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, COLOR_LINE_CSY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def make_flowables_csy(blocks: list, styles: dict) -> list:
    """把 (类型, 内容) 序列翻译成 reportlab 的排版元素。

    小标题和紧随其后的代码块或连续条目绑成一组，避免标题留在页尾。
    """
    groups = []
    index = 0
    total = len(blocks)
    while index < total:
        kind, payload = blocks[index]
        heading = None
        if (kind in ("h2", "h3") and index + 1 < total
                and blocks[index + 1][0] in ("code", "bullet")):
            heading = Paragraph(escape_csy(payload), styles[kind])
            index += 1
            kind, payload = blocks[index]

        if kind == "code":
            groups.append([KeepTogether(([heading] if heading else [])
                                        + [make_code_paragraph_csy(payload, styles)])])
            index += 1
        elif kind == "bullet":
            run = []
            while index < total and blocks[index][0] == "bullet":
                run.append(Paragraph("•&nbsp;" + escape_csy(blocks[index][1]),
                                     styles["bullet"]))
                index += 1
            groups.append([KeepTogether(([heading] if heading else []) + run)])
        else:
            if kind in STYLE_FOR_KIND_CSY:
                groups.append([Paragraph(escape_csy(payload),
                                         styles[STYLE_FOR_KIND_CSY[kind]])])
            elif kind == "table":
                groups.append([Spacer(1, 2), make_table_csy(payload, styles),
                               Spacer(1, 10)])
            elif kind == "space":
                groups.append([Spacer(1, payload)])
            elif kind == "pagebreak":
                groups.append([PageBreak()])
            index += 1
    return [item for group in groups for item in group]


def decorate_page_csy(canvas, doc, title: str) -> None:
    """页眉画文档名，页脚画页码与分隔线。"""
    canvas.saveState()
    canvas.setFont(FONT_BODY_CSY, 8)
    canvas.setFillColor(COLOR_MUTED_CSY)
    canvas.drawString(20 * mm, A4[1] - 14 * mm, title)
    canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 14 * mm, SYSTEM_SHORT_CSY)
    canvas.setStrokeColor(COLOR_LINE_CSY)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, A4[1] - 16 * mm, A4[0] - 20 * mm, A4[1] - 16 * mm)
    canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
    canvas.drawCentredString(A4[0] / 2, 10 * mm, "- %d -" % doc.page)
    canvas.restoreState()


def make_rule_csy(width, thickness=1.6) -> Table:
    """一条装饰横线，用于封面。"""
    table = Table([[""]], colWidths=[width], rowHeights=[thickness])
    table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), thickness, COLOR_ACCENT_CSY),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def make_cover_csy(title: str, subtitle: str, meta: list, styles: dict) -> list:
    """封面页：标题、副标题、装饰线与一张信息表。"""
    flow = [Spacer(1, 54 * mm), Paragraph(escape_csy(title), styles["cover_title"]),
            Spacer(1, 5 * mm), make_rule_csy(58 * mm), Spacer(1, 7 * mm),
            Paragraph(escape_csy(subtitle), styles["cover_sub"]), Spacer(1, 38 * mm)]
    rows = [[Paragraph(escape_csy(label), styles["cell"]),
             Paragraph(escape_csy(value), styles["cell"])] for label, value in meta]
    table = Table(rows, colWidths=[30 * mm, 96 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_MUTED_CSY),
    ]))
    flow.append(table)
    return flow


def build_document_csy(path: Path, title: str, cover: list, blocks: list,
                       styles: dict) -> None:
    """渲染一份 PDF：封面一页 + 正文若干页。"""
    document = BaseDocTemplate(
        str(path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=title, author="csy", subject="Python 课程设计")
    document.addPageTemplates([
        PageTemplate(id="cover",
                     frames=[Frame(20 * mm, 20 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm)]),
        PageTemplate(id="body",
                     frames=[Frame(20 * mm, 18 * mm, A4[0] - 40 * mm, A4[1] - 38 * mm)],
                     onPage=lambda canvas, doc: decorate_page_csy(canvas, doc, title)),
    ])
    story = list(cover)
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())
    story.extend(make_flowables_csy(blocks, styles))
    document.build(story)


# --------------------------------------------------------------------- 开发文档内容

DOC_DEV_CSY = [
    ("h1", "一、项目概述"),
    ("h2", "1.1 选题背景"),
    ("p", "升学与就业是每个在校大学生都要面对的选择。但学生在做选择时，"
          "面对的信息是分散且不完整的：招生政策在省级考试院网站，"
          "分数线在研招网，毕业生的真实去向在各校每年发布的就业质量报告里，"
          "而社会上的培训机构与经验帖往往只给结论、不给依据。"),
    ("p", "对专科学生来说，这个问题更突出。专科想读研并不只有「专插本」一条路，"
          "还可以在毕业满两年后以同等学力身份直接报考，但后者要加试本科主干课程，"
          "且不少院校专业明确不接收。这些关键事实在网络上很少被系统整理，"
          "学生只能靠零散经验判断。"),
    ("p", "本项目把四块公开数据整合到一个桌面程序里：广东省普通专升本数据、"
          "广州商学院毕业生就业质量数据、全国硕士研究生招生考试国家线与广东省考数据。"
          "系统按「专科 / 本科」两个学历层次组织信息，让学生用数据而不是话术做判断。"),
    ("h2", "1.2 系统目标"),
    ("bullet", "用官方公开数据回答学生最关心的三个问题：能报什么、考什么、往届去了哪。"),
    ("bullet", "把专科到硕士的几条路径放在一起，比较时间成本与可报考范围。"),
    ("bullet", "每条数据都标明来源与覆盖范围，结论可追溯。"),
    ("bullet", "界面按学历层次与问题场景组织，而不是堆砌报表。"),
    ("bullet", "打包为免安装的 Windows 可执行程序，双击即用。"),
    ("p", "地域边界：现阶段聚焦广东省。核心数据为广东省普通专升本政策、"
          "广州商学院就业质量报告、全国考研国家线与广东省考公务员公告。"
          "系统不覆盖全国各省的专升本政策、其他高校的就业报告，"
          "也不包含各校考研复试线与录取数据。"),
    ("h2", "1.3 开发与运行环境"),
    ("table", {"header": ["项目", "说明"],
               "widths": [38 * mm, 118 * mm],
               "rows": [
                   ["操作系统", "Windows 10 / 11"],
                   ["开发语言", "Python 3.12 + TypeScript 5"],
                   ["桌面壳", "pywebview（Windows 11 自带 WebView2）"],
                   ["前端框架", "React 18 + Vite 5"],
                   ["数据可视化", "ECharts 5"],
                   ["数据库", "SQLite 3（Python 标准库 sqlite3）"],
                   ["文档生成", "reportlab"],
                   ["数据采集", "urllib、pypdf、rapidocr-onnxruntime、poppler"],
                   ["打包工具", "PyInstaller 6.22"],
                   ["测试框架", "pytest"],
               ]}),

    ("h1", "二、需求分析"),
    ("h2", "2.1 功能性需求"),
    ("table", {"header": ["编号", "功能", "说明"],
               "widths": [14 * mm, 34 * mm, 108 * mm],
               "rows": [
                   ["F1", "数据总览", "展示数据来源、覆盖范围与记录规模，支持溯源"],
                   ["F2", "专插本专业查询", "按关键词或学科门类查专业，给出四门考试科目"],
                   ["F3", "省控线走势", "按专业基础课查看历年省控线，辅助判断难度"],
                   ["F4", "考研国家线", "按学科门类与 A/B 类考生查看五年走势"],
                   ["F5", "就业去向", "按届别查看毕业生规模、落实率、升学明细与流向"],
                   ["F6", "跨层次对比", "分别展示本科与专科的升学率、落实率，不直接比较优劣"],
                   ["F7", "升学与招考对比", "展示近五年考研国家线和广东省考报名、招录与报录比"],
                   ["F8", "数据来源说明", "集中展示每处数据的发布单位、覆盖范围与局限"],
                   ["F9", "使用偏好记忆", "记住上次停留的页面，下次启动直接回到原处"],
                   ["F10", "登录与注册", "本地账号体系，密码加盐哈希保存，不联网；另提供游客体验入口"],
                   ["F11", "首次使用引导", "四步填写学历、年级、目标、专业，生成个性化建议"],
                   ["F12", "个性化建议", "按档案给出「先看什么」，每条建议可一键跳转"],
                   ["F13", "考公线", "广东省考近三年报名人数、招录人数、报录比与合格线"],
                   ["F14", "决策链第一步", "填写学历、专业、年级、成绩、预算、地区、职业目标"],
                   ["F15", "资格诊断", "按政策判断专插本/考研/考公「可报、需核实、暂不适用」"],
                   ["F16", "数据可视化", "就业规模、落实率、国家线、省考招录和报录比图表"],
                   ["F17", "招考日历", "专插本、考研、考公的报名与考试节点及官方链接"],
                   ["F18", "考公职位表", "9344 个职位，可按学历、城市和职位条件筛选"],
                   ["F19", "收藏新增", "收藏专插本专业、考研学科或考公职位"],
                   ["F20", "收藏查询与筛选", "在个人信息页按类型查看收藏"],
                   ["F21", "收藏备注修改", "为收藏填写或修改目标、待核实条件等备注"],
                   ["F22", "收藏删除", "删除当前用户不再关注的项目"],
                   ["F23", "用户数据隔离", "游客不可写入收藏，不同账号的收藏互相隔离"],
               ]}),
    ("h2", "2.2 非功能性需求"),
    ("bullet", "易用性：七个页面对应不同问题，左侧导航一键切换，无需培训。"),
    ("bullet", "可追溯：每条数据都能查到来源，界面内直接展示数据来源说明。"),
    ("bullet", "健壮性：数据库缺失、配置文件损坏、查询无结果都要给出可读提示，不能崩溃。"),
    ("bullet", "可维护性：数据查询集中在数据访问层，统计逻辑集中在分析层，界面只负责展示。"),
    ("bullet", "可移植性：全部数据随程序分发，不依赖网络与外部服务。"),
    ("h2", "2.3 典型使用场景"),
    ("p", "场景一：专科大二学生想了解升学。他打开「升学路径对比」页，"
          "查看近五年考研国家线，并对照自身专业和目标判断需要达到的分数水平。"
          "系统明确说明国家线只是复试最低要求，不把国家线包装成录取率。"),
    ("p", "场景二：学生决定专插本，但不知道该考什么。他打开「专插本」页，"
          "输入「计算机」，系统列出三个相关专业，每个都给出公共课、专业基础课、"
          "专业综合课；下方联动显示高等数学近三年的三科总分线和专业综合课线，他据此判断难度。"),
    ("p", "场景三：学生想筛选广东省内某地市的可报职位。他在考公区域选择地市，"
          "查看职位、招录人数和报名期间最后公开的报录比，并收藏目标职位。"
          "之后在个人信息页补充备注，形成自己的关注清单。"),

    ("h1", "三、系统总体设计"),
    ("h2", "3.1 设计原则"),
    ("bullet", "数据先于界面：先把四块公开数据整理成结构化表，再设计页面。"),
    ("bullet", "分层清晰：界面只调用分析层，分析层只调用数据访问层，SQL 不散落在界面里。"),
    ("bullet", "口径可解释：所有对比都写明统计口径，例如升学率包含哪些去向。"),
    ("bullet", "局限显式化：数据由学校自行统计、PDF 经 OCR 提取等局限，直接在界面上说明。"),
    ("h2", "3.2 分层架构"),
    ("table", {"header": ["层次", "模块", "职责"],
               "widths": [24 * mm, 44 * mm, 88 * mm],
               "rows": [
                     ["前端层", "frontend/（React + TypeScript + ECharts）",
                      "首页、专科、本科、升学路径对比、考试时间、数据总览、个人信息七页"],
                     ["桌面壳", "main.py + pywebview",
                      "承载前端，并把 window.pywebview.api 调用转发给 Python"],
                     ["界面层（旧）", "window / dialogs / theme / widgets",
                      "Tkinter 备用界面，保留在 main_tk.py"],
                   ["账号层", "auth / login / onboarding",
                    "本地账号、密码哈希、登录注册窗口、四步引导"],
                     ["接口层", "web_api",
                      "把数据库与分析结果组装成前端需要的 JSON"],
                   ["分析层", "analysis",
                    "跨学历层次对比、路径时间成本、就业去向排名"],
                   ["数据层", "database / config / paths",
                    "SQLite 查询封装、使用偏好读写、开发与打包路径适配"],
                   ["采集层", "scripts/",
                    "数据采集、PDF 解析、OCR、建库、文档生成"],
               ]}),
    ("h2", "3.3 模块划分"),
    ("table", {"header": ["文件", "职责", "关键函数"],
               "widths": [34 * mm, 66 * mm, 56 * mm],
               "rows": [
                   ["main.py", "程序入口", "main_csy"],
                   ["main_tk.py", "旧版 Tkinter 入口（备用）", "main_csy"],
                   ["paths.py", "区分只读资源目录与可写目录", "database_file_csy"],
                    ["web_api.py", "React 接口、收藏 CRUD 与数据组装", "WebApi"],
                    ["auth.py", "账号注册登录、个人档案与收藏 CRUD", "UserStore"],
                   ["login.py", "登录 / 注册窗口", "LoginWindow"],
                   ["onboarding.py", "首次使用四步引导", "OnboardingWindow"],
                   ["config.py", "使用偏好读写与默认值回退", "load_config_csy"],
                   ["database.py", "封装对 pathway.db 的全部查询", "PathwayDatabase"],
                   ["analysis.py", "跨层次对比与路径分析", "PathAnalysis"],
                   ["eligibility.py", "资格诊断规则（专插本/考研/考公）", "diagnose_all_csy"],
                   ["canvas_charts.py", "自绘环形图/柱状图/折线图", "DonutChart / BarChart"],
                   ["theme.py", "配色、字体、图标与 ttk 样式", "apply_theme_csy"],
                   ["widgets.py", "圆角卡片、统计块、悬停提示", "RoundedCard"],
                   ["dialogs.py", "数据来源说明框、关于框", "DataSourceDialog"],
                    ["window.py", "旧版 Tkinter 主窗口", "MainWindow"],
                    ["frontend/App.tsx", "React 七个页面、图表、筛选和收藏交互", "App"],
                   ["frontend/api.ts", "前端 API 封装与 pywebview 就绪等待", "api"],
               ]}),
    ("h2", "3.4 关键流程"),
    ("h3", "3.4.1 启动流程"),
    ("code", "程序启动\n"
             "  -> 显示登录 / 注册窗口\n"
             "  -> 登录成功，读取个人档案\n"
             "  -> 若尚未完成引导：四步填写学历、年级、目标、专业\n"
             "  -> 主界面根据档案在「数据总览」顶部生成「给你的建议」\n"
             "  -> 每条建议附带「去看看」按钮，直接跳到对应页面"),
    ("h3", "3.4.2 数据从采集到展示"),
    ("code", "官方公开数据（网页 / PDF）\n"
             "  -> 采集脚本下载原始文件，留档到 data/raw/\n"
             "  -> 解析 / OCR，整理成结构化 CSV（data/processed/）\n"
             "  -> build_database.py 汇入 SQLite（data/pathway.db）\n"
             "  -> PathwayDatabase 提供业务查询\n"
             "  -> PathAnalysis 做跨层次对比与路径计算\n"
             "  -> React 渲染七个页面，通过 pywebview API 调用 Python"),
    ("h3", "3.4.3 页面切换"),
    ("p", "React 主界面采用「左侧导航 + 右侧内容区」结构。点击导航项时，"
          "通过 PageKey 状态切换页面；Python 侧的 WebApi 负责组织数据并返回 JSON。"),

    ("h1", "四、数据设计"),
    ("h2", "4.1 数据来源"),
    ("table", {"header": ["数据", "发布单位", "覆盖范围"],
               "widths": [56 * mm, 58 * mm, 42 * mm],
               "rows": [
                   ["普通专升本招生最低控制分数线", "广东省教育考试院", "2024-2026 年"],
                   ["普通专升本招生专业目录及考试要求", "广东省教育考试院", "2026 年"],
                   ["毕业生就业质量年度报告", "广州商学院信息公开网", "2021-2024 届"],
                   ["硕士研究生招生考试国家线", "中国研究生招生信息网", "2022-2026 年"],
                   ["广东省考试录用公务员公告与职位表", "中共广东省委组织部", "2024-2026 年"],
                   ["广东省考报名阶段公开人数汇总", "广东中公教育", "2024-2026 年"],
               ]}),
    ("caption", "官方数据原始文件保留在 data/raw/。报名人数采用报名阶段最后一次公开值，"
                "不标注为官方最终报名人数。"),
    ("h2", "4.2 数据库表结构"),
    ("table", {"header": ["表名", "内容", "行数"],
               "widths": [50 * mm, 78 * mm, 28 * mm],
               "rows": [
                   ["zsb_score_line", "专升本省控线（按考生类别与专业基础课）", "54"],
                   ["zsb_major_subject", "专升本专业与公共课、专业基础课对应", "264"],
                   ["zsb_major_comprehensive", "专升本专业与专业综合课对应", "65"],
                   ["emp_scale", "毕业生规模与落实率等总量指标", "27"],
                   ["emp_advance", "升学与深造明细（研究生 / 专升本 / 出国）", "26"],
                   ["emp_level", "分学历（本科 / 专科）的就业统计与落实率", "14"],
                   ["emp_college", "分学院毕业生人数", "12"],
                   ["emp_flow", "就业流向（地区 / 城市 / 单位性质 / 行业）", "17"],
                   ["kaoyan_national_line", "考研国家线（A/B 类、总分与单科）", "250"],
                   ["kaogong", "广东省考公务员（招录人数、合格线、报名和考试时间）", "3"],
                   ["kaogong_job_summary", "2026 年职位表汇总（按系统/学历/应届限制）", "14"],
                   ["kaogong_job_detail", "2026 年职位表明细（逐条职位）", "9344"],
                   ["data_source", "数据来源登记表，用于追溯", "5"],
               ]}),
    ("caption", "pathway.db 由 scripts/build_database.py 生成，共 13 张表、10095 行数据。"
                "用户账号与收藏保存在独立的 users.db 中，不参与 pathway.db 重建。"),
    ("h2", "4.3 数据采集与清洗"),
    ("bullet", "专升本：爬取省考试院三个栏目，下载 40 篇公文与 21 个附件；"
               "PDF 按列位置切分表格；附件 5 的门类列有合并单元格，"
               "改用附件 4 按专业代码反查补全。"),
    ("bullet", "就业报告：四份 PDF 均为图片型、没有文字层，"
               "先用 poppler 渲染成 150 DPI 图片，再用 OCR 识别；"
               "OCR 会按行输出，关键词可能被换行拆开，匹配时同时尝试「有空格」与「去空格」。"),
    ("bullet", "国家线：页面数据写在内联 JavaScript 变量里，"
               "用括号配对截出数组后按 JSON 解析；"
               "趋势数组按年份升序、单科线按年份降序，对齐时以单科线的年份为准。"),
    ("bullet", "考公：采集广东组织工作网的考试录用公务员公告与资格审核公告，"
               "用正则提取计划招录人数、合格分数线、报名时间与笔试时间；"
               "报名人数补充报名阶段最后一次公开汇总值，报录比由报名人数除以计划招录人数计算。"),
    ("h2", "4.4 数据质量与已知局限"),
    ("bullet", "2024、2025 年的专升本招生工作规定 PDF 是扫描件，没有文字层，"
               "因此专业目录只有 2026 年一份完整数据。"),
    ("bullet", "2022、2023 届就业报告的网页打印版右侧被裁，每行末尾的数字丢失；"
               "部分落实率和升学率按报告可确认人数计算，并在数据文件中标注。"),
    ("p", "对于 2022、2023 届缺失的落实率，系统改用「已落实人数 ÷ 毕业生总数」计算，"
          "并在数据里标注为「按人数计算」：2022 届 3576 ÷ 3951 = 90.51%，"
          "2023 届 6918 ÷ 7512 = 92.09%。这与报告原文口径可能有细微差异，"
          "界面与数据文件都保留了这一标注。"),
    ("bullet", "高校就业质量报告由学校自行统计发布，未经第三方核验，"
               "系统已在界面与文档中明确标注。"),
    ("bullet", "研招网的硕士招生专业目录是私有接口 + 登录墙，本项目只采集了全国统一国家线，"
               "未包含各校各专业的招生人数与复试线。"),
    ("bullet", "广东省考职位明细目前只有 2026 年；报名人数为报名期间最后公开值，"
               "不是官方最终报名人数，也不能直接当作最终录取率。"),
    ("bullet", "广州商学院 2024 届报告未取得分学历升学率，系统不补造缺失值。"),

    ("h1", "五、关键技术实现"),
    ("h2", "5.1 专升本 PDF 表格解析"),
    ("p", "招生工作规定的附件里有两张关键表格：附件 4 是「专业 → 公共课 + 专业基础课」，"
          "附件 5 是「专业 → 专业综合课」。pypdf 默认提取会把表格压成一行，"
          "这里改用 layout 模式，保留列对齐后再按表头位置切分。"),
    ("code", "page = reader.pages[i]\n"
             "text = page.extract_text(extraction_mode=\"layout\")   # 保留列对齐\n"
             "# 表头里找到各列起始下标，再按区间切每一行\n"
             "positions = {\"专业代码\": line.find(\"专业代码\"), ...}"),
    ("p", "附件 5 的门类列存在合并单元格，解析出来的门类不可靠。"
          "解决办法是用专业代码从附件 4 反查——附件 4 的门类来自章节标题，准确度高。"),
    ("h2", "5.2 就业报告的 OCR"),
    ("p", "四份就业质量报告是网页打印出来的图片型 PDF，文字层为空。"
          "处理流程是先渲染、再识别："),
    ("code", "pdftoppm -png -r 150 report.pdf pages/page\n"
             "-> RapidOCR 逐页识别\n"
             "-> 按页保存为 txt，保留页码分隔标记"),
    ("p", "OCR 会按视觉行切分，导致「研究生」被拆成「研究 生」这样的形式。"
          "因此匹配时同时准备两个版本：压平空白的文本，以及完全去掉空白的文本，"
          "先用前者匹配，失败再用后者。"),
    ("h2", "5.3 研招网国家线解析"),
    ("p", "国家线页面是 Vue 单页应用，表格里只有模板占位符，真实数据写在内联 JavaScript 中。"
          "这里不引入浏览器，而是直接按 JavaScript 对象的括号配对截出数组，"
          "再交给 json.loads 解析，避开了对前端渲染的依赖。"),
    ("code", "def extract_var_json_csy(html, var_name):\n"
             "    start = html.find(\"var \" + var_name)\n"
             "    bracket = html.find(\"[\", start)\n"
             "    depth = 0\n"
             "    for index in range(bracket, len(html)):\n"
             "        if html[index] == \"[\": depth += 1\n"
             "        elif html[index] == \"]\":\n"
             "            depth -= 1\n"
             "            if depth == 0:\n"
             "                return json.loads(html[bracket:index + 1])"),
    ("h2", "5.4 跨学历层次分析"),
    ("p", "这是系统最核心的分析。就业报告里同时给出本科升学率与专科升学率，"
          "把两者按年份组织起来，就能看出两类学生的路径差异："),
    ("table", {"header": ["届别", "本科升学率", "专科升学率", "总体升学率", "倍数"],
               "widths": [30 * mm, 34 * mm, 34 * mm, 34 * mm, 24 * mm],
               "rows": [
                   ["2021 届", "4.38%", "85.52%", "9.82%", "19.5 倍"],
                   ["2022 届", "4.76%", "—", "8.38%", "—"],
                   ["2023 届", "—", "81.92%", "—", "—"],
               ]}),
    ("caption", "2022、2023 届部分数值因原始 PDF 右侧被裁而缺失，2024 届未取得分学历升学率，"
                "系统均如实显示为「—」。"),
    ("p", "结论很明确：同一所学校里，专科生的升学率远高于本科生。"
          "原因是专科生的主力升学方向是专插本，而本科生的主力方向是直接就业。"
          "这组数据支撑了系统「按学历层次分别给建议」的设计。"),
    ("h2", "5.5 路径时间成本模型"),
    ("p", "系统把「从专科毕业到硕士毕业」拆成三条路径，各自累加年限："),
    ("table", {"header": ["路径", "步骤", "所需时间", "起算口径"],
               "widths": [30 * mm, 66 * mm, 22 * mm, 38 * mm],
               "rows": [
                   ["专插本后再考研", "大三备考专插本 → 本科 2 年 → 本科第二年同步备考考研 → 硕士 3 年",
                    "6 年", "从大三备考起算，本硕无缝衔接"],
                   ["同等学力直考", "专科毕业 → 等待 2 年并同步备考 → 硕士 3 年",
                    "5-6 年", "从专科毕业起算"],
                   ["自考本科再考研", "专科毕业 → 自考约 2 年并同步备考 → 硕士 3 年",
                    "5-6 年", "从专科毕业起算，自考周期因人而异"],
               ]}),
    ("caption", "年限按常规节奏估算，实际因个人情况而异；表中不含备考失败重来的时间。"),
    ("p", "模型算出的结论与直觉相反：同等学力直考在时间上比专插本后再考研少半年到一年，"
          "还省掉两年本科学费。但它的代价是可报考范围窄——复试要加试两门本科主干课程，"
          "部分院校热门专业明确不接收同等学力考生。系统把这两面都摆出来，"
          "而不是只给一个「更快」的结论。"),
    ("p", "除了升学，系统还把「考公」作为一条并列去向：采集广东省考试录用公务员公告，"
          "给出近三年的计划招录人数、报名阶段最后公开人数、报录比和合格线。"
          "报录比统一按「最后公开报名人数 ÷ 计划招录人数」计算，并明确不是最终录取率。"),
    ("h2", "5.6 界面实现"),
    ("p", "界面采用 React 18 + TypeScript + Vite 构建，通过 pywebview 嵌入桌面窗口。"
          "Python 负责数据与分析，前端负责展示与交互。"),
    ("bullet", "左侧深色导航 + 右侧内容区，导航为：首页、专科、本科、升学路径对比、"
               "考试时间、数据总览、个人信息。"),
    ("bullet", "专科与本科是两个独立入口：专科展示专插本、同等学力、自考与专科可报岗位；"
               "本科展示考研、保研、就业与本科可报岗位，并区分普通四年制本科与专插本本科。"),
    ("bullet", "前端通过 window.pywebview.api 调用 Python 接口层，"
               "业务逻辑仍复用 database / analysis / eligibility，没有重写数据层。"),
    ("bullet", "为什么不用 Tauri：本机没有 Rust，且 crates.io 不可访问；"
               "pywebview 同样能承载现代 Web 界面，同时保留 Python 数据层。"),
    ("h2", "5.7 决策链与资格诊断"),
    ("p", "React 主界面按「首页 → 专科 / 本科 → 升学与招考对比 → 考试时间 → 个人信息」"
          "组织，不使用替用户制定学习计划的设计。"),
    ("p", "个人信息收集学历、本科类型、专业、年级、成绩、预算、地区和职业目标；"
          "资格规则判断专插本、考研、考公分别属于「可报」「需核实」还是「暂不适用」，"
          "每条结论附政策依据与适用年份。招考日历只整理官方报名、考试节点和来源链接。"),
    ("p", "2027 考研按研招网官方日程显示：预报名为 2026-10-09 至 10-12，"
          "正式报名为 2026-10-15 至 10-24，初试为 2026-12-19 至 12-20。"),
    ("p", "资格诊断只回答「能不能报」，不计算录取概率。"
          "缺少各院校招生人数、复试线和录取数据时，系统不会给出虚假的精确推荐，"
          "而是把无法确认的条件列入「待核实项」。"),
    ("h2", "5.8 账号与个性化引导"),
    ("p", "系统启动后先进入登录 / 注册页，登录成功才进入主界面。"
          "账号保存在独立的可写数据库 users.db 中，与随程序分发的只读参考数据 pathway.db 分开，"
          "避免程序升级时覆盖用户数据。"),
    ("p", "密码不存明文，使用 PBKDF2-HMAC-SHA256 加盐哈希：每个账号生成独立随机盐，"
          "迭代 12 万次后保存哈希值。登录时用同一盐重新计算并比对。"),
    ("code", "salt = os.urandom(16).hex()\n"
             "digest = hashlib.pbkdf2_hmac(\"sha256\", password.encode(),\n"
             "                             bytes.fromhex(salt), 120000)\n"
             "# 数据库只保存 digest.hex() 与 salt，不保存 password"),
    ("p", "新用户注册后进入四步引导：学历层次、年级、目标、专业。"
          "结果写入个人档案，主界面据此在总览页顶部生成「给你的建议」。"
          "例如专科且目标为升学的用户，会被建议先看「路径对比」再查「专插本」；"
          "本科且目标为就业的用户，会被建议先看「就业去向」。每条建议都带「去看看」按钮，"
          "点击直接跳到对应页面。"),
    ("p", "收藏功能保存到 users.db 的 user_favorites 表。专业、考研学科和考公职位均可收藏；"
          "同一用户重复收藏会更新备注而不产生重复记录，不同账号的数据互相隔离。"
          "游客只读，不能写入收藏。"),
    ("h2", "5.9 数据可视化"),
    ("p", "图表使用 ECharts 5，而不是 matplotlib。ECharts 支持悬停提示、"
          "图例筛选、平滑动画与响应式布局，视觉上更接近现代数据产品。"),
    ("p", "首页用柱状图和折线图展示 2021-2024 届本科、专科人数、毕业生总数与落实率；"
          "专科页用双折线展示三科总分线和专业综合课线；本科页展示五年考研国家线；"
          "升学与招考对比页展示广东省考报名人数、招录人数及报录比。"
          "所有图表都有坐标轴名称、单位与数据来源说明。"),
    ("h2", "5.10 收藏 CRUD 与用户隔离"),
    ("p", "收藏表采用 user_id、item_type、item_key 唯一约束实现幂等新增。"
          "查询支持按类型筛选；修改只更新 note 和 updated_at；删除 SQL 同时校验收藏编号与 user_id，"
          "防止不同账号越权操作。"),

    ("h1", "六、系统测试"),
    ("h2", "6.1 测试环境与方法"),
    ("p", "使用 pytest 编写单元测试，当前共收集 82 个用例，全部在本地运行，不依赖网络与外部服务。"
          "数据库测试直接连项目自带的 pathway.db，界面测试使用隐藏的 Tk 根窗口，"
          "WebApi 测试覆盖学历分流、考公报名数据、收藏 CRUD 与游客限制。"),
    ("h2", "6.2 测试用例分类"),
    ("table", {"header": ["测试文件", "用例数", "覆盖内容"],
               "widths": [38 * mm, 20 * mm, 102 * mm],
               "rows": [
                   ["test_database.py", "14", "数据来源登记、学科与专业查询、省控线走势、"
                                              "跨层次数据齐全性、A/B 类国家线比较、"
                                              "考公数据与职位表、分学院与学历合计校验、缺库处理"],
                    ["test_analysis.py", "9", "跨层次倍数计算、路径排序、"
                                             "同等学力最短结论、路径年限与起算口径、"
                                              "本专科路径分流、专业考试信息、流向排名"],
                    ["test_eligibility.py", "15", "专插本/考研/考公状态、"
                                                "广东地区判断、专科毕业年级与待核实项"],
                   ["test_canvas_charts.py", "3", "环形图、柱状图、折线图能正常绘制"],
                   ["test_config.py", "5", "默认值、读写往返、损坏文件回退、局部更新、未知字段过滤"],
                    ["test_auth.py", "14", "注册登录、密码安全、档案读写、本科类型迁移、"
                                          "收藏 CRUD、幂等收藏与用户隔离"],
                    ["test_ui.py", "9", "旧版主窗口构建、页面切换、专插本查询、"
                                       "数据来源框与关于框、个性化建议、登录与引导窗口"],
                    ["test_web_api.py", "13", "学历分流、考试日期、四年就业数据、"
                                             "考公城市与报录比、科目筛选、收藏接口"],
               ]}),
    ("h2", "6.3 测试结论"),
    ("p", "全部 82 个用例通过。其中几条断言值得说明："
          "一是 test_analysis.py 断言「同等学力直考是时间最短路径」，"
          "这条结论由模型计算得出而不是写死文案；"
          "二是 test_database.py 断言 B 类国家线不高于 A 类，"
          "用来防止数据导入时行错位；"
          "三是 test_auth.py 直接查询数据库，断言里面不存在明文密码；"
          "四是收藏测试同时覆盖重复收藏、游客拒绝和跨用户越权。"),

    ("h1", "七、部署与打包"),
    ("h2", "7.1 源码运行"),
    ("code", "python -m venv .venv\n"
             ".venv\\Scripts\\activate\n"
             "pip install -r requirements.txt\n"
             "python main.py"),
    ("h2", "7.2 打包为可执行文件"),
    ("code", "python -m venv .build-venv\n"
             ".build-venv\\Scripts\\activate\n"
             "pip install pyinstaller\n"
             "pyinstaller --noconfirm 学径.spec"),
    ("caption", "建议使用干净的小虚拟环境打包。在 Anaconda 这类大环境里，"
                "PyInstaller 分析依赖时会扫描大量 DLL，速度会慢到不可接受。"),
    ("h2", "7.3 路径约定"),
    ("table", {"header": ["内容", "位置", "说明"],
               "widths": [38 * mm, 56 * mm, 66 * mm],
               "rows": [
                   ["数据库", "data/pathway.db", "随程序分发，只读使用"],
                   ["用户数据", "程序目录下 users.db", "账号、个人档案和收藏，可写"],
                   ["配置文件", "程序目录下 config.json", "记录使用偏好，首次运行时自动创建"],
                   ["前端资源", "frontend/dist/", "React 构建产物，打包时复制到 exe 目录"],
                   ["原始数据", "data/raw/", "采集到的原始公文、报告与网页"],
                   ["结构化数据", "data/processed/", "解析后的 CSV"],
               ]}),

    ("h1", "八、总结与展望"),
    ("h2", "8.1 完成情况"),
    ("p", "本项目完成了普通专升本、就业质量、考研国家线和广东省考四块公开数据的整理，"
          "建成一个包含 13 张表、10095 行数据的 SQLite 参考数据库；"
          "在此基础上实现了 React 七个页面的桌面程序，覆盖专科、本科、路径与招考、考试日历、个人信息；"
          "并用数据算出了「专科升学率远高于本科」与「同等学力直考时间更短但范围更窄」"
          "两个需要谨慎解释的结论。配套 82 个自动化测试、收藏 CRUD 与两份交付文档。"),
    ("h2", "8.2 不足与改进方向"),
    ("bullet", "就业数据目前只有一所学校，可扩展到同层次多所院校做横向对比。"),
    ("bullet", "研招网的招生目录与复试线尚未采集，无法给出「某校某专业招多少人、多少分」。"),
    ("bullet", "视频型 PDF 的 OCR 依赖版式，个别数字会丢失，可引入版面分析提高准确率。"),
    ("bullet", "推荐功能目前以规则与统计对比为主，后续可引入相似样本匹配与分位分档。"),

    ("pagebreak", None),
    ("h1", "附录：课程知识点覆盖对照"),
    ("p", "下表说明本课程所学知识点在项目中的具体落点，便于对照检查。"),
    ("p", "命名规范：按课程要求，项目中每一个自定义函数与方法的名称均以 csy 结尾，"
          "唯一的例外是 Python 规定不能改名的 __init__ 构造方法。"
          "本文档中的模块划分、测试统计与数据规模均取自项目代码与数据库。"),
    ("table", {"header": ["课程知识点", "项目中的体现", "所在文件"],
               "widths": [32 * mm, 82 * mm, 46 * mm],
               "rows": [
                   ["基础语法与流程", "条件分支、循环、推导式贯穿查询与解析逻辑，"
                                      "如按年份分组、缺失值过滤", "analysis.py / database.py"],
                   ["函数", "全部功能以函数或方法实现，共 100 余个自定义函数",
                    "pathway/ 全部"],
                   ["组合数据类型", "字典组织分组统计，列表承载查询结果，集合用于去重与比对",
                    "analysis.py / database.py"],
                   ["面向对象编程", "PathwayDatabase、PathAnalysis、MainWindow 等四个类，"
                                    "界面控件也封装为类", "pathway/ 全部"],
                   ["文件读写处理", "config.json 读写、CSV 读取、原始网页与 PDF 落盘",
                    "config.py / scripts/"],
                   ["异常处理", "配置损坏回退、缺库检测、查询无结果提示、"
                                "采集失败重试", "config.py / database.py / scripts/"],
                   ["标准库", "tkinter 图形界面、sqlite3 数据库、json 配置、re 正则解析、"
                              "hashlib 密码哈希、csv 读写、pathlib 路径处理", "pathway/ 全部"],
                   ["第三方模块与包", "pypdf 解析 PDF、xlrd 解析职位表、"
                                      "rapidocr 识别图片、reportlab 生成文档", "scripts/"],
               ]}),
]


# --------------------------------------------------------------------- 使用说明书内容

DOC_MANUAL_CSY = [
    ("h1", "一、软件简介"),
    ("p", "本系统是一款面向在校学生（专科与本科）的升学就业数据工具。"
          "它把广东省普通专升本、广州商学院毕业生就业质量报告、"
          "全国硕士研究生招生考试国家线和广东省考公开数据整合在一起，"
          "用七个页面回答学生最关心的几个问题。"),
    ("p", "系统的特点是：核心数据来自官方公开渠道，每条都能追溯；"
          "省考报名人数使用报名阶段公开汇总，并明确标注不是最终值；"
          "按专科、本科两个学历层次分别组织信息；"
          "不提供录取承诺，只展示往届真实情况与各条路径的代价。"),
    ("h1", "二、运行环境"),
    ("table", {"header": ["项目", "要求"],
               "widths": [40 * mm, 118 * mm],
               "rows": [
                   ["操作系统", "Windows 10 / 11"],
                   ["运行方式一", "直接运行打包好的 exe，无需安装 Python"],
                   ["运行方式二", "源码运行，需要 Python 3.10 及以上"],
                   ["网络", "不需要联网，数据随程序分发"],
                    ["磁盘", "整个程序目录约 42 MB，其中数据库约 3 MB"],
               ]}),
    ("h1", "三、安装与启动"),
    ("h2", "3.1 免安装运行（推荐）"),
    ("step", "第一步：找到 dist/学径/ 目录。"),
    ("step", "第二步：双击目录中的「学径.exe」。"),
    ("step", "第三步：在登录窗口输入用户名与密码；第一次使用点「注册」创建账号。"),
    ("step", "第四步：新用户会进入四步引导，填写学历、年级、目标和专业。"),
    ("step", "第五步：完成后进入主界面，左上角会显示「你好，用户名」。"),
    ("caption", "整个目录需要一起拷贝，不能只单独拿走 exe 文件。"),
    ("h2", "3.2 源码运行"),
    ("code", "python -m venv .venv\n"
             ".venv\\Scripts\\activate\n"
             "pip install -r requirements.txt\n"
             "python main.py"),
    ("h1", "四、界面说明"),
    ("h2", "4.1 整体布局"),
    ("p", "窗口由左侧深色导航栏、顶部标题栏与右侧内容区组成。"
          "导航为：首页、专科、本科、升学路径对比、考试时间、数据总览、个人信息。"),
    ("h2", "4.2 顶部标题栏"),
    ("bullet", "显示「你好，用户名」，不提供无法工作的搜索框。"),
    ("bullet", "「数据来源」：弹窗展示发布单位、覆盖范围、已知局限和官方链接。"),
    ("bullet", "「关于」：显示系统名称、版本号 v1.1、定位与使用边界。"),
    ("h2", "4.3 左侧导航"),
    ("bullet", "专科、本科是两个独立入口，分别展示各自相关的升学、招考与就业信息。"),
    ("bullet", "当前学历对应的导航项会显示「当前」标记。"),
    ("h2", "4.4 右侧内容区"),
    ("p", "每页由统计卡片、图表与表格组成，内容较多时可上下滚动。"),

    ("h1", "五、操作指南"),
    ("h2", "5.1 登录与注册"),
    ("step", "首次使用：在登录窗口点击「注册」，输入用户名和密码（至少 6 位），"
             "再次输入确认密码，点击「注册并开始」。"),
    ("step", "已有账号：输入用户名与密码，点击「登录」。"),
    ("step", "只想先看看：点击表单底部的「游客体验」，用预设档案直接进入主界面，"
             "不需要注册，也不会写入任何账号数据。"),
    ("step", "提示「用户名不存在」或「密码不正确」时，请检查后重试；"
             "忘记密码目前需要重新注册一个账号。"),
    ("caption", "账号只保存在本机的 users.db 中，不会上传到任何服务器；"
                "密码使用加盐哈希保存，数据库里没有明文。"),
    ("h2", "5.2 首次使用引导"),
    ("step", "注册成功后进入四步引导，顶部进度点显示当前是第几步。"),
    ("step", "第一步选学历层次（专科 / 本科）；第二步选年级；第三步选倾向（升学 / 就业 / 还没想好）。"),
    ("step", "第四步填写专业，也可以点下方常见方向快速填入。"),
    ("step", "点「下一步」继续，点「上一步」可以回去修改；最后一步按钮会变成「完成」。"),
    ("caption", "引导结果保存在个人档案里，首页与专科 / 本科页会据此展示。"),
    ("h2", "5.3 首页"),
    ("p", "首页包含：专科 / 本科入口、数据概览、广州商学院 2021-2024 届毕业生规模图、"
          "毕业去向落实率图、核心数据来源和考试节点。"),
    ("caption", "毕业生总数折线用于核对本科与专科人数之和。升学、就业、收入是不同维度，不能直接判断路径优劣。"),
    ("h2", "5.4 专科"),
    ("p", "专科入口展示专插本、同等学力直考、自考本科后考研、直接就业、考公五条路径，"
          "并提供专业基础课下拉筛选、专插本专业与考试科目查询、"
          "三科总分线与专业综合课线双折线图，以及专科可报的考公岗位。"),
    ("h2", "5.5 本科"),
    ("p", "本科入口展示考研、保研、直接就业、考公四条路径，"
          "并区分普通四年制本科与专插本本科。"
          "考研国家线区域可下拉切换学科门类，展示 2022-2026 年总分线和两类单科线。"
          "专插本本科生同样属于本科，但部分岗位、推免政策或院校条件可能有额外要求。"),
    ("h2", "5.6 升学路径对比"),
    ("p", "左侧展示近五年考研国家线；右侧展示广东省考 2024-2026 年报名人数、"
          "计划招录人数与报录比。考研学科门类可通过下拉框切换。"),
    ("caption", "广东省考报名人数采用报名阶段最后一次公开值，不是最终报名人数；"
                "报录比 = 最后公开报名人数 ÷ 计划招录人数。"),
    ("h2", "5.7 考试时间"),
    ("p", "通过下拉框按专插本 / 考研 / 考公筛选时间线，每条记录包含报名起止、考试日期、"
          "适用人群、发布单位、状态、说明与官方链接。2027 考研按研招网官方日程显示。"),
    ("caption", "往年时间只作为历史记录，不能直接当作下一年度的报名时间；"
                "尚未发布的日期显示「暂未公布」。"),
    ("h2", "5.8 数据总览"),
    ("p", "展示数据概况、全部数据来源、已知缺口和官方入口。"),
    ("h2", "5.9 个人信息"),
    ("p", "维护学历层次、本科类型、专业、年级、成绩水平、可接受预算、地区与职业目标。"
          "信息只保存在本机，不替用户决定走哪条路。"),
    ("h2", "5.10 我的关注（增删查改）"),
    ("step", "增：在专插本专业、考研学科或考公职位旁点击「收藏」。"),
    ("step", "查：在个人信息页的「我的关注」中查看，并按类型下拉筛选。"),
    ("step", "改：点击「改备注」，填写目标、待核实条件等信息并保存。"),
    ("step", "删：点击「删除」移除当前收藏。"),
    ("caption", "游客只能浏览，不能保存收藏；收藏按账号隔离，保存在 users.db。"),

    ("h1", "六、常见问题"),
    ("h3", "问题一：表格里显示「—」是什么意思？"),
    ("p", "表示该年份该指标没有取得数据，通常是原始报告文件不完整或 OCR 未能识别，"
          "不是数值为零。"),
    ("h3", "问题二：为什么专插本专业只有 2026 年？"),
    ("p", "2024、2025 年的招生工作规定 PDF 是扫描件，没有可提取的文字层，"
          "因此专业目录只有 2026 年一份完整数据。省控线则有 2024-2026 三年。"),
    ("h3", "问题三：就业数据为什么只有广州商学院？"),
    ("p", "本项目以广州商学院作为主样本，数据来自该校历年就业质量年度报告。"
          "扩展到更多院校需要逐校采集，属于后续改进方向。"),
    ("h3", "问题四：国家线为什么不是具体学校的分数线？"),
    ("p", "国家线是教育部统一划定的最低要求，各招生单位会在此基础上划定自己的复试线。"
          "本项目采集的是全国统一国家线，未包含各校复试线。"),
    ("h3", "问题五：程序需要联网吗？"),
    ("p", "不需要。数据库与原始数据随程序分发，全部查询在本地完成。"),
    ("h3", "问题六：忘记密码怎么办？"),
    ("p", "账号保存在本机，目前没有找回功能，需要重新注册一个账号。"
          "如果只是想换一个专业继续看数据，也可以不重新注册，直接在「专插本」页输入新的专业查询。"),
    ("h3", "问题七：考研表里的「单科线（满分100分科目）」是什么意思？"),
    ("p", "考研初试中，政治、英语满分 100 分，数学、专业课满分 150 分。"
          "国家线对这两类科目分别划最低单科线，任何一科低于对应分数线都不能进入复试。"),
    ("h3", "问题八：资格诊断说「可报」是不是就能录取？"),
    ("p", "不是。「可报」只代表符合基本报考条件，系统不做录取概率预测。"
          "是否录取取决于招生计划、报考人数、考试成绩和院校复试规则，"
          "这些数据目前并不完整，所以系统只给条件式建议，并把不确定的部分列为待核实项。"),
    ("h3", "问题九：广东省考报录比是最终录取率吗？"),
    ("p", "不是。广东省考官方系统没有公开最终报名人数，系统采用报名期间最后一次公开缴费人数，"
          "再除以计划招录人数得到报录比。页面已标明统计时点，不能把它理解为最终录取率。"),
    ("h3", "问题十：为什么收藏按钮提示需要登录？"),
    ("p", "收藏属于用户数据，必须按账号隔离保存。游客模式只提供只读浏览，"
          "登录后才能新增收藏、修改备注和删除。"),

    ("pagebreak", None),
    ("h1", "七、数据来源与使用说明"),
    ("caption", "核心数据来自官方公开渠道；省考报名人数采用公开汇总的最后值，"
                "就业报告由学校自行统计并经 OCR 提取。"),
    ("table", {"header": ["数据", "发布单位", "覆盖范围"],
               "widths": [56 * mm, 58 * mm, 42 * mm],
               "rows": [
                   ["普通专升本招生最低控制分数线", "广东省教育考试院", "2024-2026 年"],
                   ["普通专升本招生专业目录", "广东省教育考试院", "2026 年"],
                   ["毕业生就业质量年度报告", "广州商学院信息公开网", "2021-2024 届"],
                   ["硕士研究生招生考试国家线", "中国研究生招生信息网", "2022-2026 年"],
                    ["广东省考试录用公务员公告与职位表", "中共广东省委组织部", "2024-2026 年"],
                    ["广东省考报名阶段公开人数汇总", "广东中公教育", "2024-2026 年"],
               ]}),
    ("p", "使用边界：本系统只提供公开数据整理与条件式参考，不预测录取概率，"
          "也不替代学校就业部门、考试院或招录单位的正式公告。报考、择校和岗位选择请以当年官方文件为准。"),
]


def make_meta_csy() -> list:
    """两份文档共用的封面信息。"""
    return [
        ("项目名称", SYSTEM_FULL_CSY),
        ("课程名称", "Python 程序设计 课程设计"),
        ("姓名", "____________"),
        ("学号", "____________"),
        ("姓名代号", "csy（自定义函数命名后缀）"),
        ("版本", "v1.1"),
        ("日期", "2026-10-26"),
    ]


def main_csy() -> int:
    """生成两份交付文档。"""
    register_fonts_csy()
    styles = build_styles_csy()
    OUTPUT_DIR_CSY.mkdir(parents=True, exist_ok=True)

    dev_path = OUTPUT_DIR_CSY / "系统开发文档.pdf"
    manual_path = OUTPUT_DIR_CSY / "系统使用说明书.pdf"

    build_document_csy(
        dev_path, "系统开发文档",
        make_cover_csy(SYSTEM_FULL_CSY, "系统开发文档", make_meta_csy(), styles),
        DOC_DEV_CSY, styles)
    build_document_csy(
        manual_path, "系统使用说明书",
        make_cover_csy(SYSTEM_FULL_CSY, "系统使用说明书", make_meta_csy(), styles),
        DOC_MANUAL_CSY, styles)

    print("已生成文档：")
    print("  %s" % dev_path)
    print("  %s" % manual_path)
    return 0


if __name__ == "__main__":
    sys.exit(main_csy())
