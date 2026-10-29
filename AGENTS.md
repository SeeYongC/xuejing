# AGENTS.md — 学历路径分析与推荐系统

课程设计项目：**基于公开数据的本专科学历路径分析与推荐系统**（Tkinter 桌面程序）。
面向专科与本科在校生，用官方公开数据展示升学与就业路径。
旧版（问数通 / DataAsk，大模型问数系统）已整体移除，可在 git 历史中查看。

## 运行与测试

```powershell
python main.py                       # 启动桌面程序（React + pywebview 版）
python main_tk.py                    # 启动旧版 Tkinter 界面（备用）
python -m pytest tests -q            # 单元测试
python scripts/build_database.py     # 由 processed/*.csv 重建 pathway.db
python scripts/build_docs.py         # 生成 docs/ 下的两份交付 PDF
```

## 前端（React + ECharts + pywebview）

```powershell
cd frontend
npm install --cache "..\.npm-cache"   # npm 默认缓存目录可能没有写权限
npm run build                         # 产物在 frontend/dist
cd ..
python main.py                        # pywebview 加载 frontend/dist
```

- 技术栈：React 18 + TypeScript + Vite + ECharts
- 桌面壳：pywebview（Windows 11 自带 WebView2，无需额外安装）
- **不要用 Tauri**：本机没有 Rust，且 crates.io 不可访问
- 前端通过 `window.pywebview.api.<method>()` 调用 Python；
  **方法名必须是下划线命名**，与 `pathway/web_api.py` 一致
- pywebview 注入 API 分两步：对象先出现、方法后挂上；
  判断是否就绪要看 `typeof api.bootstrap === 'function'`，不能只看对象存在

## 结构

- `main.py` — 入口，调用 `pathway.window.launch_csy()`
- `pathway/paths.py` — 资源目录与可写目录的区分，兼容 PyInstaller（`sys._MEIPASS`）；
  `APP_NAME_CSY` 是窗口与 exe 用的简称，`APP_FULL_NAME_CSY` 是完整题目
- `pathway/auth.py` — `UserStore`，本地账号与个人档案；
  账号存**可写的 users.db**（与只读的 pathway.db 分开），密码用 PBKDF2 加盐哈希
- `pathway/login.py` — 登录 / 注册窗口，程序启动的第一个界面
- `pathway/onboarding.py` — 四步引导（学历 / 年级 / 目标 / 专业），结果写入个人档案
- `pathway/web_api.py` — pywebview 暴露给 React 的接口层（`WebApi`）
- `pathway/eligibility.py` — 资格诊断规则：专插本 / 考研 / 考公的「可报 / 需核实 / 暂不适用」
- `pathway/database.py` — `PathwayDatabase`，封装对 `pathway.db` 的**全部**查询；
  界面层不直接拼 SQL，新增查询在这里加方法
- `pathway/analysis.py` — `PathAnalysis`，跨学历层次对比、路径时间成本、就业去向画像
- `pathway/config.py` — 使用偏好（`last_page` / `last_year` / `last_discipline`）
- `pathway/canvas_charts.py` — 自绘环形图 / 柱状图 / 折线图，不依赖 matplotlib 或 pyecharts
- `pathway/theme.py` — 设计规范：配色、字体、图标字形、ttk 样式，改外观只动这里
- `pathway/widgets.py` — 自绘控件：`RoundedCard`、`RoundedBox`、`StatBox`、`SegmentedControl`、`Tooltip`
- `pathway/dialogs.py` — 数据来源说明框、关于框
- `pathway/window.py` — 主窗口（左侧导航 + 右侧内容区），
  决策链四步 + 数据查询四页 + 数据总览，共 9 个页面
- `frontend/src/App.tsx` — React 主界面：首页、专科、本科、升学路径对比、
  考试时间、数据总览、个人信息
- `frontend/src/api.ts` — 前端 API 封装与 pywebview 就绪等待

## 数据管道

三条数据线，脚本可重跑，原始数据留档在 `data/raw/`，最终汇入 `data/pathway.db`。

### 1. 广东省专升本（专插本）

```powershell
python scripts/collect_zsb.py        # 采集省考试院公开通知与附件 -> data/raw/eea/
python scripts/build_zsb_dataset.py  # 省控线 -> 专升本省控线.csv
python scripts/parse_zsb_majors.py   # 专业目录 -> 专升本专业与*.csv
```

- 数据源：广东省教育考试院 `bmbk_sksywj` / `tzgg` / `zwgk_zkgs` 三个栏目
- 2024、2025 年的招生工作规定 PDF 是**扫描件没有文字层**，只有 2026 年那份能直接提取
- PDF 用 `extract_text(extraction_mode="layout")` 保留表格列对齐，再按表头列位置切分
- 附件 5 的门类列有合并单元格，改用附件 4（门类取自章节标题）按专业代码反查补全

### 2. 广州商学院就业质量报告（图片型 PDF，走 OCR）

```powershell
python scripts/ocr_gcc_reports.py    # 渲染 + OCR -> data/raw/gcc/text/*.txt
python scripts/build_gcc_dataset.py  # 解析 -> 广州商学院_*.csv
```

- 四份报告（2021-2024 届）是**图片型 PDF，没有文字层**，必须 OCR：
  poppler `pdftoppm` 渲染（150 DPI）后交给 `rapidocr-onnxruntime` 识别
- OCR 按行输出，关键词会被换行拆开（如「研究 生」），匹配时要同时试
  「有空格」与「去空格」两个版本，见 `build_gcc_dataset.py` 的 `search_csy`
- **已知问题**：2022、2023 两份是网页打印版，右侧被裁导致落实率取不到；
  2021、2024 完整。核心发现：专科升学率（81.92%、85.52%）远高于本科（3.34%、4.38%）

### 3. 考研国家线

```powershell
python scripts/collect_yz_lines.py   # -> 研招网_历年国家线.csv
```

- 数据源：研招网「历年复试分数线」专题页 `https://yz.chsi.com.cn/kyzx/zt/lnfsx.shtml`
- 国家线是**内联 JS 变量**（`var tyhxList` / `ddhxList` / `zgzcList`），不是服务端渲染；
  用括号配对截出数组后 `json.loads` 即可
- 趋势数组 `gjx` 是**年份升序**，单科线 `dkx` 是**年份降序**，对齐以 `dkx` 的年份为准；
  各分组年数不同（少数民族组只有 3 年）；页面里有一个 name 为空的模板占位项要过滤
- 研招网的硕士专业目录（`/zsml/`）是私有接口 + 登录墙，暂未采集

### 4. 广东省考公务员

```powershell
python scripts/collect_kaogong.py       # 招录人数/合格线 -> 广东省考公务员.csv
python scripts/collect_kaogong_jobs.py  # 职位表 -> 广东省考_职位表汇总.csv / 明细.csv
```

- 数据源：广东组织工作网「公务员录用」栏目
- 职位表在公告附件的 ZIP 里，是旧版 `.xls`（需 `xlrd`）；6 个工作表共 9344 条职位
- ZIP 文件名含中文，`urllib` 请求前必须用 `quote` 做百分号编码

## 约定

- **函数命名**：每个自定义函数/方法名必须以 `csy` 结尾（课程硬性要求），新增代码必须遵守；
  测试函数写成 `test_xxx_csy`，pytest 仍能正常收集；例外只有 `__init__`
- **数据库**：`data/pathway.db` 由 `scripts/build_database.py` 生成，
  它会 **DROP 并重建**全部表，不要往库里写需要保留的数据
- **用户数据**：账号与档案存在 `users.db`（可写目录），不要写进 pathway.db；
  `build_database.py` 重建时不会影响 users.db
- **密码**：只存 PBKDF2 哈希与随机盐，任何地方都不要记录或回显明文
- **圆角卡片**：`RoundedCard` 只固定内容宽度、不固定高度，高度靠内容自然撑开；
  一旦给内容 `itemconfigure(height=...)` 就会钉死尺寸
- **图标**：统一走 `theme.icon_csy()` 取 Segoe MDL2 Assets 字形，没有该字体时自动退化为纯文字
- **界面线程**：本系统不联网，所有查询都是本地 SQLite，无需后台线程；
  新增网络调用时必须放到后台线程并用 `root.after` 回主线程
- **打包**：新增文件读取一律走 `resource_root_csy()`，不要写死相对路径
- **语言**：界面文案与代码注释用中文
- **提交**：本机无 GPG 密钥，需 `git commit --no-gpg-sign`
