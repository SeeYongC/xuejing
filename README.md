# 基于公开数据的本专科学历路径分析与推荐系统

面向在校学生（**专科与本科**）的升学就业数据工具。用官方公开数据回答三个问题：

1. 我这个专业在广东能报什么？要考哪几门、历年分数线多少？
2. 专科想读研有几条路？各自要几年、门槛差在哪？
3. 往届毕业生的真实去向是什么？升学率和落实率到底多少？

## 解决什么问题

学生升学择校时面临的信息问题有三个：

| 问题 | 具体表现 |
|---|---|
| 信息分散 | 招生政策在考试院网站、分数线在研招网、就业数据在各校就业报告里，格式还不统一 |
| 跨层次信息缺失 | 专科生想读研，网上大多只讲专插本，同等学力直考的真实门槛没人系统整理 |
| 只给结论不给依据 | 机构和经验帖给的是话术，学生需要的是"往届和我条件相近的人最后去了哪" |

本系统把三块官方数据整合起来，标清来源与样本范围，让结论可以追溯。

## 地域边界

**现阶段聚焦广东省。** 核心数据是广东省普通专升本政策、广州商学院就业质量报告、
全国考研国家线与广东省考公务员公告。系统**不覆盖**全国各省的专升本政策、
其他高校的就业报告、各校考研复试线与录取数据。

因此当前定位是「广东省专科、本科学生的升学与发展规划工具」，
不是全国性的升学平台。

## 功能

程序启动后先进入**登录 / 注册**页，登录成功才进入主界面。新用户会走四步引导
（学历、年级、目标、专业），系统据此在首页生成「给你的建议」。

界面是左侧导航 + 右侧内容区的桌面程序，五个页面：

| 页面 | 内容 |
|---|---|
| 数据总览 | 数据来源、覆盖范围、记录规模，以及最值得注意的一组数据（跨层次升学率对比） |
| 专插本 | 按关键词或学科门类查专业，给出四门考试科目；按专业基础课看省控线走势 |
| 考研 | 按学科门类看国家线走势，A 类 / B 类可切换；最新一年国家线总览 |
| 就业去向 | 按届别看毕业生规模、落实率、升学明细与单位性质分布 |
| 路径对比 | 从专科到硕士的三条路径，比较时间成本与可报考范围 |

## 账号与引导

- 账号保存在本地 `users.db`，不联网；密码用 PBKDF2-HMAC-SHA256 加盐哈希保存，数据库里没有明文
- 不想注册可以点「游客体验」，用预设档案（专科 / 计算机 / 大二 / 升学）直接进入主界面
- 新用户注册后进入四步引导：学历层次 → 年级 → 倾向（升学 / 就业 / 还没想好）→ 专业
- 主界面顶部显示「你好，用户名」，首页按档案生成「给你的建议」，每条建议带「去看看」按钮直接跳转
- 例如：专科 + 升学 → 建议先看「路径对比」再查「专插本」；本科 + 就业 → 建议先看「就业去向」

## 数据来源

全部为官方公开渠道，系统内每条记录都保留来源：

| 数据 | 来源 | 覆盖 |
|---|---|---|
| 普通专升本招生最低控制分数线 | 广东省教育考试院 | 2024-2026 年 |
| 普通专升本招生专业目录 | 广东省教育考试院（招生工作规定附件） | 2026 年 |
| 毕业生就业质量年度报告 | 广州商学院信息公开网 | 2021-2024 届 |
| 硕士研究生招生考试国家线 | 中国研究生招生信息网 | 2022-2026 年 |

已知局限：高校就业质量报告由学校自行统计发布，未经第三方核验；原始文件为网页打印版 PDF，
经 OCR 提取，个别数值可能缺失。系统内已标注。

## 运行

```bash
# 1. 构建前端（首次运行需要）
cd frontend
npm install --cache "..\.npm-cache"
npm run build
cd ..

# 2. 启动桌面程序
python main.py
```

程序界面是 **React + TypeScript + ECharts**，通过 **pywebview** 嵌入桌面窗口；
Python 负责数据与分析逻辑。Windows 11 自带 WebView2，不需要额外安装。

旧版纯 Tkinter 界面保留在 `main_tk.py`，可作备用。

**为什么不用 Tauri**：本机没有安装 Rust，且 crates.io 不可访问。
pywebview 同样能承载现代 Web 界面，同时保留 Python 数据层。

## 数据管道

原始数据一律留档在 `data/raw/`，处理后的 CSV 在 `data/processed/`，
最后汇入 SQLite 数据库 `data/pathway.db`。

```bash
# 1. 广东省专升本（专插本）——采集省考试院的公开通知与附件
python scripts/collect_zsb.py
python scripts/build_zsb_dataset.py      # 省控线
python scripts/parse_zsb_majors.py       # 专业目录与考试科目

# 2. 广州商学院就业质量报告——图片型 PDF，需先 OCR
python scripts/ocr_gcc_reports.py
python scripts/build_gcc_dataset.py

# 3. 考研国家线
python scripts/collect_yz_lines.py

# 4. 汇总入库
python scripts/build_database.py
```

几点说明：

- 2024、2025 年的招生工作规定 PDF 是扫描件没有文字层，只有 2026 年那份能直接提取
- 就业报告是图片型 PDF，用 poppler 渲染后交给 `rapidocr-onnxruntime` 识别
- 研招网的国家线写在内联 JS 变量里，用括号配对截出数组后解析

## 测试

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
```

## 打包成 exe

建议用干净的虚拟环境打包，在 Anaconda 这类大环境里 PyInstaller 分析阶段会非常慢：

```bash
python -m venv .build-venv
.build-venv\Scripts\activate
pip install matplotlib pyinstaller
pyinstaller --noconfirm --windowed --name 学历路径分析 --add-data "data;data" main.py
```

## 生成交付文档

```bash
python scripts/build_docs.py
```

在 `docs/` 下生成《系统开发文档.pdf》与《系统使用说明书.pdf》。

## 项目结构

```
.
├── main.py                  程序入口
├── pathway/                 核心代码包
│   ├── paths.py             路径工具，兼容开发环境与打包后的 exe
│   ├── auth.py              本地账号与个人档案（密码加盐哈希）
│   ├── login.py             登录 / 注册窗口
│   ├── onboarding.py        首次使用四步引导
│   ├── config.py            使用偏好的读写
│   ├── database.py          数据访问层：封装对 pathway.db 的全部查询
│   ├── analysis.py          路径分析：跨层次对比、时间成本、去向画像
│   ├── charts.py            图表绘制
│   ├── theme.py             设计规范：配色、字体、图标、样式
│   ├── widgets.py           自绘控件：圆角卡片、统计块、悬停提示
│   ├── dialogs.py           数据来源说明框、关于框
│   └── window.py            主窗口与五个页面
├── frontend/                React + TypeScript + ECharts
│   ├── src/App.tsx          首页、专科、本科、路径对比、考试时间、总览、个人信息
│   └── src/styles.css       现代数据产品风格
├── data/
│   ├── raw/                 原始数据（40 篇公文、4 份报告、网页存档）
│   ├── processed/           结构化 CSV
│   └── pathway.db           汇总后的 SQLite 数据库
├── scripts/                 数据采集、解析、建库、文档生成
├── tests/                   单元测试
└── docs/                    交付文档
```

## 编码约定

按课程要求，项目中每一个自定义函数与方法的名称均以 `csy` 结尾，
例如 `load_config_csy`、`cross_level_rates_csy`、`build_database` 里各导入函数。
唯一的例外是 Python 规定不能改名的 `__init__` 构造方法。
