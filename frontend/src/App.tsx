import { useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { api, Profile } from './api'

type PageKey = 'home' | 'college' | 'undergrad' | 'compare' | 'calendar' | 'overview' | 'profile'

const NAV: { key: PageKey; label: string; icon: string }[] = [
  { key: 'home', label: '首页', icon: 'home' },
  { key: 'college', label: '专科', icon: 'book' },
  { key: 'undergrad', label: '本科', icon: 'cap' },
  { key: 'compare', label: '升学路径对比', icon: 'chart' },
  { key: 'calendar', label: '考试时间', icon: 'calendar' },
  { key: 'overview', label: '数据总览', icon: 'data' },
  { key: 'profile', label: '个人信息', icon: 'user' },
]

const EMPTY_PROFILE: Profile = {
  username: '游客',
  education_level: '',
  undergrad_type: '',
  major: '',
  grade: '',
  score: '',
  budget: '',
  region: '',
  goal: '',
}

const PALETTE = ['#2f6f5e', '#d9822b', '#54758a', '#b45f4a', '#7b6b8f']

function errorText(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return String(error || '未知错误')
}

const FAVORITE_TYPE_LABELS: Record<string, string> = {
  zsb_major: '专插本专业',
  kaoyan_discipline: '考研学科',
  kaogong_job: '考公职位',
}

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  }
  const paths: Record<string, JSX.Element> = {
    home: <><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" /></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v18H6.5A2.5 2.5 0 0 1 4 18.5z" /><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20" /></>,
    cap: <><path d="m2 9 10-5 10 5-10 5z" /><path d="M6 11.5V17c0 1.5 2.7 3 6 3s6-1.5 6-3v-5.5" /></>,
    chart: <><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M22 20H2" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18" /></>,
    data: <><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5" /><path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" /></>,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
    arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    warn: <><path d="M12 3 2 21h20z" /><path d="M12 9v5M12 17h.01" /></>,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
    star: <><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9z" /></>,
  }
  return <svg {...common}>{paths[name] ?? paths.info}</svg>
}

function Sidebar({ page, onNavigate, profile }: { page: PageKey; onNavigate: (p: PageKey) => void; profile: Profile }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">径</div>
        <div>
          <div className="brand-name">学径</div>
          <div className="brand-sub">学历与升学数据平台</div>
        </div>
      </div>
      <nav className="nav">
        {NAV.map((item) => (
          <button
            key={item.key}
            className={`nav-item ${page === item.key ? 'active' : ''}`}
            onClick={() => onNavigate(item.key)}
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
            {item.key === 'college' && profile.education_level === '专科' && <em className="nav-badge">当前</em>}
            {item.key === 'undergrad' && profile.education_level === '本科' && <em className="nav-badge">当前</em>}
          </button>
        ))}
      </nav>
      <div className="sidebar-foot">
        <div className="foot-user">
          <div className="avatar">{(profile.username || '游').slice(0, 1)}</div>
          <div>
            <div className="foot-name">{profile.username || '游客'}</div>
            <div className="foot-role">{profile.education_level || '未填写学历'}</div>
          </div>
        </div>
      </div>
    </aside>
  )
}

function Topbar({ profile, bootstrap }: { profile: Profile; bootstrap: any }) {
  const [dialog, setDialog] = useState<'sources' | 'about' | null>(null)

  return (
    <header className="topbar">
      <div>
        <div className="topbar-title">你好，{profile.username || '同学'} 👋</div>
        <div className="topbar-sub">欢迎使用学径 · 学历与升学数据平台</div>
      </div>
      <div className="topbar-actions">
        <button className="ghost-btn" onClick={() => setDialog('sources')}><Icon name="data" size={16} />数据来源</button>
        <button className="ghost-btn" onClick={() => setDialog('about')}><Icon name="info" size={16} />关于</button>
      </div>
      {dialog && (
        <div className="modal-mask" onClick={() => setDialog(null)}>
          <section className="modal-card" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="modal-head">
              <div>
                <h3>{dialog === 'sources' ? '数据来源' : '关于学径'}</h3>
                <p>{dialog === 'sources' ? '仅展示系统实际使用的公开数据渠道' : '学历与升学数据平台 · v1.2'}</p>
              </div>
              <button className="icon-btn" aria-label="关闭" onClick={() => setDialog(null)}><Icon name="close" /></button>
            </div>
            {dialog === 'sources' ? (
              <div className="modal-body">
                <div className="source-list">
                  {(bootstrap?.sources || []).map((source: any) => (
                    <div className="modal-source" key={source.name}>
                      <b>{source.name}</b>
                      <span>{source.publisher} · {source.coverage}</span>
                      {source.note && <small>{source.note}</small>}
                    </div>
                  ))}
                </div>
                <div className="source-links">
                  {(bootstrap?.source_links || []).map((link: any) => (
                    <a key={link.name} href={link.url} target="_blank" rel="noreferrer">{link.name}：{link.label}</a>
                  ))}
                </div>
              </div>
            ) : (
              <div className="modal-body about-copy">
                <p><b>基于公开数据的本专科学历路径分析与推荐系统</b></p>
                <p>面向广东省专科、本科在校生，整理升学、考研、考公和就业公开数据，帮助用户查看路径差异、报名节点与数据来源。</p>
                <p>系统只做资格与信息展示，不预测录取概率，也不以升学率直接判断路径优劣。</p>
                <p className="muted">版本 1.2 · 本地离线运行</p>
              </div>
            )}
          </section>
        </div>
      )}
    </header>
  )
}

function StatCards({ stats }: { stats: { label: string; value: string }[] }) {
  return (
    <div className="stat-grid">
      {stats.map((s) => (
        <div className="stat-card" key={s.label}>
          <div className="stat-value">{s.value}</div>
          <div className="stat-label">{s.label}</div>
        </div>
      ))}
    </div>
  )
}

function SectionCard({ title, extra, children }: { title: string; extra?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="card">
      <div className="card-head">
        <h3>{title}</h3>
        {extra}
      </div>
      {children}
    </section>
  )
}

function HomePage({ bootstrap, onNavigate }: { bootstrap: any; onNavigate: (p: PageKey) => void }) {
  const employment: any[] = bootstrap?.employment_overview || []

  const countOption = useMemo(() => ({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: {
      data: ['本科毕业生', '专科毕业生', '毕业生总数'],
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#6b7280', fontSize: 11 },
    },
    grid: { left: 48, right: 14, top: 38, bottom: 30 },
    xAxis: {
      type: 'category',
      name: '届别',
      data: employment.map((item) => `${item.year}届`),
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280' },
    },
    yAxis: {
      type: 'value',
      name: '人数',
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f2f6' } },
      axisLabel: { color: '#9ca3af' },
    },
    series: [
      { name: '本科毕业生', type: 'bar', data: employment.map((item) => item.undergrad), barWidth: 18, itemStyle: { borderRadius: [5, 5, 0, 0], color: '#7fa691' } },
      { name: '专科毕业生', type: 'bar', data: employment.map((item) => item.college), barWidth: 18, itemStyle: { borderRadius: [5, 5, 0, 0], color: PALETTE[1] } },
      { name: '毕业生总数', type: 'line', data: employment.map((item) => item.total), symbolSize: 7, lineStyle: { width: 2, color: PALETTE[2] }, itemStyle: { color: PALETTE[2] } },
    ],
  }), [employment])

  const placementOption = useMemo(() => ({
    tooltip: { trigger: 'axis', formatter: (items: any[]) => `${items[0]?.axisValue}<br/>${items[0]?.value}%` },
    grid: { left: 48, right: 18, top: 24, bottom: 30 },
    xAxis: {
      type: 'category',
      name: '届别',
      data: employment.map((item) => `${item.year}届`),
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280' },
    },
    yAxis: {
      type: 'value',
      name: '落实率（%）',
      min: 80,
      max: 100,
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f2f6' } },
      axisLabel: { color: '#9ca3af' },
    },
    series: [{
      type: 'line',
      data: employment.map((item) => item.placement_rate),
      smooth: true,
      symbolSize: 7,
      lineStyle: { width: 3, color: PALETTE[0] },
      itemStyle: { color: PALETTE[0] },
      label: { show: true, formatter: '{c}%', color: '#5b665f', fontSize: 11 },
      areaStyle: { color: 'rgba(47,111,94,0.10)' },
    }],
  }), [employment])

  return (
    <div className="page">
      <section className="hero">
        <div className="hero-copy">
          <h1>你的学历，能通往多少种可能？</h1>
          <p>整合官方数据 · 解析升学路径 · 直观呈现选择</p>
          <div className="hero-chips">
            {['专插本', '考研', '就业', '考公'].map((t) => <span key={t}>{t}</span>)}
          </div>
        </div>
        <div className="hero-art" aria-hidden>
          <div className="hero-sun" />
          <div className="hero-hill h1" />
          <div className="hero-hill h2" />
          <div className="hero-person" />
        </div>
      </section>

      <div className="home-grid">
        <div className="home-main">
          <SectionCard title="专科 / 本科" extra={<span className="muted">选择你的学历层次</span>}>
            <div className="level-grid">
              <button className="level-card college" onClick={() => onNavigate('college')}>
                <div className="level-icon">专</div>
                <div className="level-title">专科</div>
                <div className="level-desc">查看专科的升学路径、考试科目、可报考的考公岗位等信息。</div>
                <span className="level-arrow"><Icon name="arrow" /></span>
              </button>
              <button className="level-card undergrad" onClick={() => onNavigate('undergrad')}>
                <div className="level-icon">本</div>
                <div className="level-title">本科</div>
                <div className="level-desc">查看本科的升学路径（考研、保研、普通本科）、就业去向、考公岗位等信息。</div>
                <span className="level-arrow"><Icon name="arrow" /></span>
              </button>
            </div>
          </SectionCard>

          <SectionCard title="广州商学院就业数据" extra={<span className="muted">2021–2024 届公开就业报告</span>}>
            <div className="chart-grid">
              <div>
                <div className="chart-title">2021–2024 届毕业生规模</div>
                <ReactECharts option={countOption} style={{ height: 260 }} />
              </div>
              <div>
                <div className="chart-title">2021–2024 届毕业去向落实率</div>
                <ReactECharts option={placementOption} style={{ height: 260 }} />
              </div>
            </div>
            <p className="footnote">毕业生人数与落实率来自四份广州商学院就业质量报告。升学率因 2022、2023 年 OCR 缺项和 2024 年报告未取得，只在有完整依据的页面展示。</p>
          </SectionCard>
        </div>

        <div className="home-side">
          <SectionCard title="数据概览" extra={<button className="link-btn" onClick={() => onNavigate('overview')}>查看更多</button>}>
            <StatCards stats={bootstrap?.stats || []} />
          </SectionCard>

          <SectionCard title="考试节点参考" extra={<button className="link-btn" onClick={() => onNavigate('calendar')}>查看更多</button>}>
            <div className="timeline">
              {(bootstrap?.upcoming || []).map((item: any) => (
                <div className="timeline-item" key={item.title}>
                  <div className="timeline-date"><span>{item.date.split('-')[0]}</span><em>{item.date.split('-')[1]}</em></div>
                  <div className="timeline-body">
                    <div className="timeline-title">{item.title}</div>
                    <div className="timeline-desc">{item.desc}</div>
                  </div>
                  <Icon name="arrow" size={14} />
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="核心数据来源">
            <div className="source-list">
              {(bootstrap?.sources || []).slice(0, 4).map((s: any) => (
                <div className="source-item" key={s.name}>
                  <div className="source-dot" />
                  <div>
                    <div className="source-name">{s.publisher}</div>
                    <div className="source-sub">{s.name}</div>
                  </div>
                  <span className="source-year">{s.coverage}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>

      <section className="bottom-banner">
        <div>
          <h3>数据驱动 · 看见更多可能</h3>
          <p>用真实的数据，帮你做出更清晰的选择</p>
        </div>
        <button onClick={() => onNavigate('compare')}>开始探索 <Icon name="arrow" size={16} /></button>
      </section>
    </div>
  )
}

function LevelPage({ level, profile, onNavigate }: { level: '专科' | '本科'; profile: Profile; onNavigate: (p: PageKey) => void }) {
  const [summary, setSummary] = useState<any>({})
  const [subjects, setSubjects] = useState<string[]>([])
  const [majorSubjects, setMajorSubjects] = useState<any[]>([])
  const [subject, setSubject] = useState('')
  const [trend, setTrend] = useState<any[]>([])
  const [majors, setMajors] = useState<any[]>([])
  const [keyword, setKeyword] = useState(level === '专科' ? '计算机' : '')
  const [basicSubject, setBasicSubject] = useState('')
  const [kaogong, setKaogong] = useState<any>({ rows: [], summary: [], education: [] })
  const [kaogongCity, setKaogongCity] = useState('全部')
  const [kaoyanDisciplines, setKaoyanDisciplines] = useState<string[]>([])
  const [discipline, setDiscipline] = useState('工学')
  const [kaoyanTrend, setKaoyanTrend] = useState<any[]>([])
  const [error, setError] = useState('')
  const [favoriteNotice, setFavoriteNotice] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const addFavorite = async (
    itemType: string, itemKey: string, itemTitle: string, note = '',
  ) => {
    const result = await api.addFavorite(itemType, itemKey, itemTitle, note)
    if (result?.success) {
      setFavoriteNotice({ type: 'success', text: `已收藏：${itemTitle}` })
    } else {
      setFavoriteNotice({ type: 'error', text: result?.error || '收藏失败' })
    }
    setTimeout(() => setFavoriteNotice(null), 2400)
  }

  useEffect(() => {
    setError('')
    setKaogongCity('全部')
    api.levelSummary(level)
      .then((data) => {
        setSummary(data || {})
        const nextSubjects: string[] = data?.subjects || []
        const nextMajorSubjects: any[] = data?.major_subjects || []
        setSubjects(nextSubjects)
        setMajorSubjects(nextMajorSubjects)
        setSubject(nextSubjects.length ? nextSubjects[nextSubjects.length - 1] : '')
        setBasicSubject(nextMajorSubjects.length ? nextMajorSubjects[0].subject : '')
      })
      .catch((reason) => setError(`学历数据加载失败：${errorText(reason)}`))
  }, [level])

  useEffect(() => {
    api.kaogong(level, kaogongCity)
      .then(setKaogong)
      .catch((reason) => setError(`考公岗位加载失败：${errorText(reason)}`))
  }, [level, kaogongCity])

  useEffect(() => {
    if (level !== '专科' || !subject) {
      setTrend([])
      return
    }
    api.zsbScore(subject)
      .then((data) => setTrend(data?.trend || []))
      .catch((reason) => setError(`省控线加载失败：${errorText(reason)}`))
  }, [level, subject])

  useEffect(() => {
    if (level !== '专科') {
      setMajors([])
      return
    }
    api.zsbMajors('专科', keyword, '', basicSubject)
      .then(setMajors)
      .catch((reason) => setError(`专业数据加载失败：${errorText(reason)}`))
  }, [level, keyword, basicSubject])

  useEffect(() => {
    if (level !== '本科') {
      setKaoyanTrend([])
      return
    }
    api.kaoyanLines(discipline, 'A类考生')
      .then((data) => {
        setKaoyanTrend(data?.trend || [])
        setKaoyanDisciplines(data?.disciplines || [])
      })
      .catch((reason) => setError(`考研国家线加载失败：${errorText(reason)}`))
  }, [level, discipline])

  const scoreOption = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['三科总分线', '专业综合课线'],
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#6b7280', fontSize: 11 },
    },
    grid: { left: 52, right: 20, top: 42, bottom: 34 },
    xAxis: { type: 'category', name: '年份', data: trend.map((t) => String(t.year)), nameTextStyle: { color: '#9ca3af', fontSize: 11 }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisLabel: { color: '#6b7280' } },
    yAxis: { type: 'value', name: '分数线（分）', nameTextStyle: { color: '#9ca3af', fontSize: 11 }, splitLine: { lineStyle: { color: '#f0f2f6' } }, axisLabel: { color: '#9ca3af' } },
    series: [
      { name: '三科总分线', type: 'line', data: trend.map((t) => t.total_line), smooth: true, symbolSize: 7, lineStyle: { width: 3, color: PALETTE[0] }, itemStyle: { color: PALETTE[0] } },
      { name: '专业综合课线', type: 'line', data: trend.map((t) => t.comprehensive_line), smooth: true, symbolSize: 7, lineStyle: { width: 2, color: PALETTE[1] }, itemStyle: { color: PALETTE[1] } },
    ],
  }), [trend])

  const kaoyanOption = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['总分线', '单科满分 100', '单科满分 > 100'],
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#6b7280', fontSize: 11 },
    },
    grid: { left: 52, right: 20, top: 42, bottom: 34 },
    xAxis: { type: 'category', name: '年份', data: kaoyanTrend.map((item) => String(item.year)), nameTextStyle: { color: '#9ca3af', fontSize: 11 }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisLabel: { color: '#6b7280' } },
    yAxis: { type: 'value', name: '分数线（分）', nameTextStyle: { color: '#9ca3af', fontSize: 11 }, splitLine: { lineStyle: { color: '#f0f2f6' } }, axisLabel: { color: '#9ca3af' } },
    series: [
      { name: '总分线', type: 'line', data: kaoyanTrend.map((item) => item.total_line), smooth: true, symbolSize: 6, lineStyle: { width: 3, color: PALETTE[0] }, itemStyle: { color: PALETTE[0] } },
      { name: '单科满分 100', type: 'line', data: kaoyanTrend.map((item) => item.single_subject_100), smooth: true, symbolSize: 5, lineStyle: { width: 2, color: PALETTE[1] }, itemStyle: { color: PALETTE[1] } },
      { name: '单科满分 > 100', type: 'line', data: kaoyanTrend.map((item) => item.single_subject_150), smooth: true, symbolSize: 5, lineStyle: { width: 2, color: PALETTE[2] }, itemStyle: { color: PALETTE[2] } },
    ],
  }), [kaoyanTrend])

  const profileSuffix = level === '本科' && profile.undergrad_type ? ` · ${profile.undergrad_type}` : ''

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>{level}数据入口{profileSuffix}</h2>
          <p>{level === '专科'
            ? '专科的升学路径、考试科目、可报考的考公岗位'
            : '本科的考研方向、可报考的考公岗位与升学路径'}</p>
        </div>
        <button className="primary-btn" onClick={() => onNavigate('profile')}>
          修改个人信息 <Icon name="arrow" size={16} />
        </button>
      </div>

      {level === '本科' && (
        <div className="notice info">
          <Icon name="info" size={16} />
          <span>本科包含「普通四年制本科」与「专插本本科」。专插本本科生同样属于本科，
            但部分岗位、推免政策或院校条件可能有额外要求，请以具体公告为准。</span>
        </div>
      )}

      {error && <div className="notice error"><Icon name="warn" size={16} /><span>{error}</span></div>}
      {favoriteNotice && (
        <div className={`notice ${favoriteNotice.type === 'success' ? 'info' : 'error'}`} aria-live="polite">
          <Icon name={favoriteNotice.type === 'success' ? 'check' : 'warn'} size={16} />
          <span>{favoriteNotice.text}</span>
        </div>
      )}

      <div className="two-col">
        <SectionCard title="升学路径" extra={<span className="muted">{level === '专科' ? '专插本 · 同等学力 · 自考' : '考研 · 推免（需核实） · 就业 · 考公'}</span>}>
          <div className="path-list">
            {(summary.paths || []).map((p: any) => (
              <div className="path-row" key={p.name}>
                <div className="path-name">{p.name}</div>
                <div className="path-meta">{p.time} · {p.note}</div>
              </div>
            ))}
            {!summary.paths?.length && <div className="empty">暂无数据</div>}
          </div>
        </SectionCard>

        <SectionCard
          title="可报考公岗位"
          extra={(
            <div className="card-tools">
              <select value={kaogongCity} onChange={(e) => setKaogongCity(e.target.value)}>
                <option value="全部">全部地市</option>
                {(kaogong.city_options || []).map((item: any) => (
                  <option key={item.city} value={item.city}>{item.city}（{item.headcount} 人）</option>
                ))}
              </select>
            </div>
          )}
        >
          <div className="job-summary">
            当前筛选：{kaogong.total || 0} 个职位，计划招录 {kaogong.headcount || 0} 人
            <span>官方报录比：暂缺</span>
          </div>
          <div className="job-list">
            {(kaogong.rows || []).slice(0, 6).map((r: any, i: number) => (
              <div className="job-row" key={`${r.unit}-${r.position}-${i}`}>
                <div className="job-unit"><b>{r.unit}</b><span>{r.position || '职位名称未提供'}</span></div>
                <div className="job-edu">{r.education}</div>
                <div className="job-count">{r.headcount} 人</div>
                <button
                  className="favorite-btn"
                  title="收藏职位"
                  onClick={() => addFavorite(
                    'kaogong_job',
                    [r.system, r.unit, r.position, r.education, r.headcount].join('|'),
                    `${r.unit} · ${r.position || '职位'}`,
                    `城市：${r.city || '未标注'}；学历：${r.education || '未注明'}`,
                  )}
                >
                  <Icon name="star" size={14} />收藏
                </button>
              </div>
            ))}
            {!kaogong.rows?.length && <div className="empty">暂无数据</div>}
          </div>
          <p className="footnote">{kaogong.ratio_note || '职位表未公开报名人数，暂无法计算报录比。'} 城市按招考单位名称中明确出现的广东地级市归类。</p>
          <a className="source-link" href="https://www.gdzz.gov.cn/gwygz/lypytzgg/" target="_blank" rel="noreferrer">前往广东组织工作网查看完整职位表</a>
        </SectionCard>
      </div>

      {level === '专科' && (
        <>
          <SectionCard
            title="专插本专业与考试科目"
            extra={(
              <div className="card-tools">
                <span className="muted">专业基础课</span>
                <select value={basicSubject} onChange={(e) => setBasicSubject(e.target.value)}>
                  {majorSubjects.map((item: any) => (
                    <option key={item.subject} value={item.subject}>{item.subject}（{item.major_count} 个专业）</option>
                  ))}
                </select>
              </div>
            )}
          >
            <div className="filter-row">
              <input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="例如：计算机、会计" />
              <button className="ghost-btn" onClick={() => api.zsbMajors('专科', keyword, '', basicSubject).then(setMajors).catch((reason) => setError(`专业数据加载失败：${errorText(reason)}`))}>查询</button>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>专业代码</th><th>专业名称</th><th>学科门类</th><th>公共课</th><th>专业基础课</th><th>专业综合课</th><th>操作</th></tr></thead>
                <tbody>
                  {majors.slice(0, 20).map((m: any) => (
                    <tr key={m.major_code}>
                      <td>{m.major_code}</td><td>{m.major_name}</td><td>{m.discipline}</td>
                      <td>{m.common_subjects}</td><td>{m.basic_subject}</td><td>{m.comprehensive_subject || '院校自命题'}</td>
                      <td>
                        <button
                          className="favorite-btn"
                          onClick={() => addFavorite(
                            'zsb_major',
                            `${m.year || ''}|${m.major_code}`,
                            m.major_name,
                            `专业基础课：${m.basic_subject || '未注明'}`,
                          )}
                        >
                          <Icon name="star" size={14} />收藏
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>

          <SectionCard title="省控线走势" extra={<select value={subject} onChange={(e) => setSubject(e.target.value)}>{subjects.map((s) => <option key={s}>{s}</option>)}</select>}>
            <ReactECharts option={scoreOption} notMerge style={{ height: 280 }} />
            {!trend.length && <div className="empty">当前专业基础课暂无可展示的省控线数据</div>}
          </SectionCard>
        </>
      )}

      {level === '本科' && (
        <SectionCard
          title="考研国家线（复试最低线）"
          extra={<select value={discipline} onChange={(e) => setDiscipline(e.target.value)}>{kaoyanDisciplines.map((item) => <option key={item}>{item}</option>)}</select>}
        >
          <ReactECharts option={kaoyanOption} notMerge style={{ height: 300 }} />
          {!kaoyanTrend.length && <div className="empty">正在读取国家线数据，若持续为空请检查本地数据库</div>}
          <p className="footnote">A 类考生适用于广东。国家线是进入复试的最低要求，不代表具体院校录取线。</p>
          <div className="inline-actions">
            <button
              className="favorite-btn"
              onClick={() => addFavorite(
                'kaoyan_discipline',
                discipline,
                `${discipline}考研国家线`,
                'A 类考生；关注近五年国家线变化',
              )}
            >
              <Icon name="star" size={14} />收藏该学科
            </button>
            <a className="source-link" href="https://yz.chsi.com.cn/kyzx/zt/lnfsx.shtml" target="_blank" rel="noreferrer">前往研招网查看历年国家线</a>
          </div>
        </SectionCard>
      )}

      <div className="notice warn">
        <Icon name="warn" size={16} />
        <span>以上数据来自官方公开渠道，具体报考条件与时间以当年公告为准。</span>
      </div>
    </div>
  )
}

function ComparePage({ profile }: { profile: Profile }) {
  const [kaoyanRows, setKaoyanRows] = useState<any[]>([])
  const [disciplines, setDisciplines] = useState<string[]>([])
  const [discipline, setDiscipline] = useState('工学')
  const [kaogong, setKaogong] = useState<any>({ years: [] })
  const [error, setError] = useState('')
  const level = profile.education_level || '专科'

  useEffect(() => {
    setError('')
    api.kaoyanLines(discipline, 'A类考生')
      .then((data) => {
        setKaoyanRows(data?.trend || [])
        setDisciplines(data?.disciplines || [])
      })
      .catch((reason) => setError(`考研国家线加载失败：${errorText(reason)}`))
  }, [discipline])

  useEffect(() => {
    api.kaogong(level, '全部')
      .then(setKaogong)
      .catch((reason) => setError(`考公数据加载失败：${errorText(reason)}`))
  }, [level])

  const kaoyanOption = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['总分线', '单科满分 100', '单科满分 > 100'],
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#6b7280', fontSize: 11 },
    },
    grid: { left: 52, right: 20, top: 42, bottom: 46 },
    xAxis: {
      type: 'category',
      name: '年份',
      nameLocation: 'middle',
      nameGap: 28,
      data: kaoyanRows.map((item) => String(item.year)),
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280' },
    },
    yAxis: {
      type: 'value',
      name: '国家线（分）',
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f2f6' } },
      axisLabel: { color: '#9ca3af' },
    },
    series: [
      { name: '总分线', type: 'line', data: kaoyanRows.map((item) => item.total_line), smooth: true, symbolSize: 7, lineStyle: { width: 3, color: PALETTE[0] }, itemStyle: { color: PALETTE[0] } },
      { name: '单科满分 100', type: 'line', data: kaoyanRows.map((item) => item.single_subject_100), smooth: true, symbolSize: 6, lineStyle: { width: 2, color: PALETTE[1] }, itemStyle: { color: PALETTE[1] } },
      { name: '单科满分 > 100', type: 'line', data: kaoyanRows.map((item) => item.single_subject_150), smooth: true, symbolSize: 6, lineStyle: { width: 2, color: PALETTE[2] }, itemStyle: { color: PALETTE[2] } },
    ],
  }), [kaoyanRows])

  const kaogongYears = useMemo(
    () => [...(kaogong?.years || [])].sort((a: any, b: any) => a.year - b.year),
    [kaogong],
  )

  const kaogongOption = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['最后公布报名人数', '计划招录人数', '报录比'],
      right: 0,
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#6b7280', fontSize: 11 },
    },
    grid: { left: 58, right: 54, top: 42, bottom: 46 },
    xAxis: {
      type: 'category',
      name: '年份',
      nameLocation: 'middle',
      nameGap: 28,
      data: kaogongYears.map((item: any) => String(item.year)),
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280' },
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        nameTextStyle: { color: '#9ca3af', fontSize: 11 },
        splitLine: { lineStyle: { color: '#f0f2f6' } },
        axisLabel: { color: '#9ca3af' },
      },
      {
        type: 'value',
        name: '报录比（:1）',
        min: 0,
        nameTextStyle: { color: '#9ca3af', fontSize: 11 },
        splitLine: { show: false },
        axisLabel: { color: '#9ca3af' },
      },
    ],
    series: [
      { name: '最后公布报名人数', type: 'bar', data: kaogongYears.map((item: any) => item.applicants), barWidth: 24, itemStyle: { borderRadius: [5, 5, 0, 0], color: '#8fb2a3' } },
      { name: '计划招录人数', type: 'bar', data: kaogongYears.map((item: any) => item.recruit_count), barWidth: 24, itemStyle: { borderRadius: [5, 5, 0, 0], color: PALETTE[0] } },
      { name: '报录比', type: 'line', yAxisIndex: 1, data: kaogongYears.map((item: any) => item.competition_ratio), symbolSize: 7, lineStyle: { width: 2, color: PALETTE[1] }, itemStyle: { color: PALETTE[1] }, tooltip: { valueFormatter: (value: any) => `${value}:1` } },
    ],
  }), [kaogongYears])

  return (
    <div className="page">
      <div className="page-head">
        <div><h2>升学与招考数据对比</h2><p>用可核实的公开数据查看考研门槛和广东省考招录规模</p></div>
      </div>
      {error && <div className="notice error"><Icon name="warn" size={16} /><span>{error}</span></div>}
      <div className="two-col">
        <SectionCard
          title="近 5 年考研国家线"
          extra={(
            <select value={discipline} onChange={(e) => setDiscipline(e.target.value)}>
              {disciplines.map((item) => <option key={item}>{item}</option>)}
            </select>
          )}
        >
          <ReactECharts option={kaoyanOption} notMerge style={{ height: 320 }} />
          {!kaoyanRows.length && <div className="empty">暂无可展示的考研国家线数据</div>}
          <p className="footnote">国家线是进入复试的最低要求，不是最终录取率。录取率还需报名人数和实际录取人数，本系统不编造。</p>
        </SectionCard>
        <SectionCard title="广东省考报名与招录对比" extra={<span className="muted">当前数据库 2024–2026 年</span>}>
          <ReactECharts option={kaogongOption} notMerge style={{ height: 320 }} />
          {!kaogongYears.length && <div className="empty">暂无可展示的广东省考数据</div>}
          <p className="footnote">官方系统未公布最终报名人数，图中采用报名期间最后一次公开数据：2024-01-20、2025-01-12、2026-10-22。报录比 = 最后公布报名人数 ÷ 计划招录人数。</p>
          <a className="source-link" href="https://m.gd.offcn.com/zw/tongji/" target="_blank" rel="noreferrer">查看报名人数公开统计来源（中公教育汇总）</a>
        </SectionCard>
      </div>
      <div className="notice info">
        <Icon name="info" size={16} />
        <span>考研国家线与考公招录规模是不同指标，不能直接换算成同一种“录取率”，也不能据此得出哪条路更好。</span>
      </div>
    </div>
  )
}

function CalendarPage({ profile }: { profile: Profile }) {
  const [category, setCategory] = useState('全部')
  const [events, setEvents] = useState<any[]>([])
  const [error, setError] = useState('')
  const level = profile.education_level || '专科'
  const categories = level === '本科' ? ['全部', '考研', '考公'] : ['全部', '专插本', '考研', '考公']

  useEffect(() => {
    if (!categories.includes(category)) setCategory('全部')
  }, [level, category])

  useEffect(() => {
    setError('')
    api.calendar(level, category)
      .then(setEvents)
      .catch((reason) => setError(`考试日历加载失败：${errorText(reason)}`))
  }, [level, category])

  const statusClass = (s: string) => s === '已公布' ? 'green' : s === '暂未公布' ? 'gray' : s === '已结束' ? 'muted' : 'amber'

  return (
    <div className="page">
      <div className="page-head">
        <div><h2>考试时间</h2><p>{level}适用考试节点，往年日期仅作为历史记录</p></div>
      </div>
      {error && <div className="notice error"><Icon name="warn" size={16} /><span>{error}</span></div>}
      <div className="filter-row">
        <label className="inline-filter">考试类别
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
      </div>
      <SectionCard title="招考时间线" extra={<span className="muted">{events.length} 条记录</span>}>
        <div className="event-list">
          {events.map((e, i) => (
            <div className="event-row" key={i}>
              <div className="event-date"><b>{e.year}</b><span>{e.start_date || '—'}</span></div>
              <div className="event-main">
                <div className="event-title">{e.event}</div>
                <div className="event-meta">{e.audience} · {e.publisher}</div>
                {e.start_date && <div className="event-meta">报名：{e.start_date} 至 {e.end_date}</div>}
                {e.exam_date && <div className="event-meta">考试：{e.exam_date}</div>}
                {e.note && <div className="event-note">{e.note}</div>}
                {e.source_url && <a className="source-link" href={e.source_url} target="_blank" rel="noreferrer">查看官方公告</a>}
              </div>
              <span className={`pill ${statusClass(e.status)}`}>{e.status}</span>
            </div>
          ))}
          {!events.length && <div className="empty">暂无记录</div>}
        </div>
      </SectionCard>
      <div className="notice warn">
        <Icon name="warn" size={16} />
        <span>往年时间只作为历史记录，不能直接当作下一年度的报名时间；尚未发布的日期显示「暂未公布」。</span>
      </div>
    </div>
  )
}

function OverviewPage({ bootstrap }: { bootstrap: any }) {
  return (
    <div className="page">
      <div className="page-head">
        <div><h2>数据总览</h2><p>系统用到的数据全部来自官方公开渠道，可逐条追溯</p></div>
      </div>
      <SectionCard title="数据概况">
        <StatCards stats={bootstrap?.stats || []} />
      </SectionCard>
      <SectionCard title="数据来源与覆盖范围">
        <div className="table-wrap">
          <table>
            <thead><tr><th>数据名称</th><th>发布单位</th><th>覆盖范围</th><th>说明</th></tr></thead>
            <tbody>
              {(bootstrap?.sources || []).map((s: any) => (
                <tr key={s.name}><td>{s.name}</td><td>{s.publisher}</td><td>{s.coverage}</td><td>{s.note || '—'}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
      <SectionCard title="数据缺口说明">
        <div className="data-gaps">
          {(bootstrap?.data_gaps || []).map((item: string) => <div key={item}>{item}</div>)}
        </div>
        <div className="source-links">
          {(bootstrap?.source_links || []).map((link: any) => (
            <a key={link.name} href={link.url} target="_blank" rel="noreferrer">{link.name}：{link.label}</a>
          ))}
        </div>
      </SectionCard>
      <div className="notice warn">
        <Icon name="warn" size={16} />
        <span>高校就业质量报告由学校自行统计发布，未经第三方核验；部分年份数据因原始文件不完整而缺失。</span>
      </div>
    </div>
  )
}

function PersonalAnalysisPanel({
  profile,
  refreshKey,
  onNavigate,
}: {
  profile: Profile
  refreshKey: number
  onNavigate: (p: PageKey) => void
}) {
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runAnalysis = async () => {
    setLoading(true)
    setError('')
    try {
      setAnalysis(await api.personalAnalysis(profile))
    } catch (reason) {
      setError(`个人条件分析失败：${errorText(reason)}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void runAnalysis() }, [refreshKey])

  return (
    <SectionCard
      title="个人条件分析"
      extra={(
        <div className="card-tools">
          <span className="muted">使用当前表单内容</span>
          <button className="ghost-btn" onClick={runAnalysis} disabled={loading}>
            {loading ? '分析中...' : '重新分析'}
          </button>
        </div>
      )}
    >
      {error && <div className="notice error"><Icon name="warn" size={16} /><span>{error}</span></div>}
      {loading && !analysis && <div className="empty">正在按固定流程分析个人条件...</div>}
      {analysis && (
        <div className="analysis-panel">
          <div className="analysis-summary">
            <div>
              <b>{analysis.summary}</b>
              <span>{analysis.note}</span>
            </div>
            <span className="pill gray">规则 v{analysis.rules_version} · {analysis.calculated_at}</span>
          </div>
          {!!analysis.profile_gaps?.length && (
            <div className="notice warn">
              <Icon name="warn" size={16} />
              <span>{analysis.profile_gaps.join('；')}</span>
            </div>
          )}
          {!analysis.profile_ready && <div className="empty">请先补全个人信息，再生成路径建议。</div>}
          <div className="analysis-grid">
            {(analysis.recommendations || []).map((item: any) => (
              <article className="analysis-card" key={item.key}>
                <div className="analysis-card-head">
                  <div>
                    <span className={`pill ${item.status === '可报' ? 'green' : item.status === '需核实' ? 'amber' : 'muted'}`}>{item.status}</span>
                    <h4>{item.title}</h4>
                  </div>
                  <div className="match-score">
                    <b>{item.score}</b>
                    <span>{item.match_level}</span>
                  </div>
                </div>
                <div className="analysis-detail">
                  <b>判断理由</b>
                  <span>{(item.reasons || []).join('；') || '资料不足'}</span>
                </div>
                <div className="analysis-detail">
                  <b>公开数据证据</b>
                  <span>{(item.evidence || []).join('；') || '暂无可匹配证据'}</span>
                </div>
                {!!item.gaps?.length && (
                  <div className="analysis-detail analysis-gap">
                    <b>数据缺口</b>
                    <span>{item.gaps.join('；')}</span>
                  </div>
                )}
                <div className="analysis-detail">
                  <b>下一步核实</b>
                  <span>{(item.next_checks || []).join('；')}</span>
                </div>
                <button className="link-btn analysis-link" onClick={() => onNavigate(item.page as PageKey)}>
                  查看相关数据 <Icon name="arrow" size={14} />
                </button>
              </article>
            ))}
          </div>
        </div>
      )}
    </SectionCard>
  )
}

function ProfilePage({
  profile,
  onChange,
  onNavigate,
}: {
  profile: Profile
  onChange: (p: Profile) => void
  onNavigate: (p: PageKey) => void
}) {
  const [draft, setDraft] = useState<Profile>(profile)
  const [hasUserEdited, setHasUserEdited] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [analysisVersion, setAnalysisVersion] = useState(0)
  const [favorites, setFavorites] = useState<any[]>([])
  const [favoriteFilter, setFavoriteFilter] = useState('全部')
  const [favoriteError, setFavoriteError] = useState('')
  const [favoriteLoading, setFavoriteLoading] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [noteDraft, setNoteDraft] = useState('')
  const set = (key: keyof Profile, value: string) => {
    setHasUserEdited(true)
    setDraft((current) => {
      const next = { ...current, [key]: value } as Profile
      if (key === 'education_level' && value !== '本科') next.undergrad_type = ''
      return next
    })
  }
  const dirty = JSON.stringify(draft) !== JSON.stringify(profile)

  useEffect(() => {
    if (!hasUserEdited) setDraft(profile)
  }, [profile, hasUserEdited])

  const loadFavorites = async () => {
    setFavoriteLoading(true)
    setFavoriteError('')
    try {
      const result = await api.listFavorites(favoriteFilter)
      if (!result?.success) {
        setFavorites([])
        setFavoriteError(result?.error || '收藏加载失败')
      } else {
        setFavorites(result.rows || [])
      }
    } catch (reason) {
      setFavorites([])
      setFavoriteError(`收藏加载失败：${errorText(reason)}`)
    } finally {
      setFavoriteLoading(false)
    }
  }

  useEffect(() => { void loadFavorites() }, [favoriteFilter])

  const saveFavoriteNote = async (favoriteId: number) => {
    const result = await api.updateFavorite(favoriteId, noteDraft)
    if (!result?.success) {
      setFavoriteError(result?.error || '备注修改失败')
      return
    }
    setEditingId(null)
    setNoteDraft('')
    await loadFavorites()
  }

  const deleteFavorite = async (favoriteId: number) => {
    const result = await api.deleteFavorite(favoriteId)
    if (!result?.success) {
      setFavoriteError(result?.error || '删除收藏失败')
      return
    }
    await loadFavorites()
  }

  const save = async () => {
    setSaving(true)
    setSaved(false)
    setError('')
    try {
      const result = await api.saveProfile(draft)
      if (!result?.success) throw new Error(result?.error || '个人信息保存失败')
      onChange(draft)
      setHasUserEdited(false)
      setAnalysisVersion((version) => version + 1)
      setSaved(true)
      setTimeout(() => setSaved(false), 1800)
    } catch (reason) {
      setError(`个人信息保存失败：${errorText(reason)}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <div className="page-head">
        <div><h2>个人信息</h2><p>修改后可立即重新分析；保存后会同步到账号和其他页面</p></div>
        <div className="page-status">
          {dirty && !saving && <span className="pill amber">有未保存修改</span>}
          {saved && <span className="pill green">已保存并重新分析</span>}
        </div>
      </div>
      {error && <div className="notice error" aria-live="polite"><Icon name="warn" size={16} /><span>{error}</span></div>}
      <SectionCard title="基础资料">
        <div className="form-grid">
          <label>学历层次<select value={draft.education_level} onChange={(e) => set('education_level', e.target.value)}>
            <option value="">请选择</option><option>专科</option><option>本科</option>
          </select></label>
          <label>本科类型<select value={draft.undergrad_type || ''} onChange={(e) => set('undergrad_type', e.target.value)} disabled={draft.education_level !== '本科'}>
            <option value="">不适用 / 请选择</option><option>普通四年制本科</option><option>专插本本科</option><option>其他</option>
          </select></label>
          <label>专业<input value={draft.major} onChange={(e) => set('major', e.target.value)} placeholder="例如：计算机科学与技术" /></label>
          <label>年级<select value={draft.grade} onChange={(e) => set('grade', e.target.value)}>
            <option value="">请选择</option>{['大一', '大二', '大三', '大四', '已毕业'].map((g) => <option key={g}>{g}</option>)}
          </select></label>
          <label>成绩水平<select value={draft.score} onChange={(e) => set('score', e.target.value)}>
            <option value="">请选择</option>{['专业前 10%', '专业前 30%', '专业中游', '专业后 30%', '不确定'].map((g) => <option key={g}>{g}</option>)}
          </select></label>
          <label>可接受预算<select value={draft.budget} onChange={(e) => set('budget', e.target.value)}>
            <option value="">请选择</option>{['1 万以内', '1-3 万', '3-6 万', '6 万以上', '没考虑过'].map((g) => <option key={g}>{g}</option>)}
          </select></label>
          <label>地区<select value={draft.region} onChange={(e) => set('region', e.target.value)}>
            <option value="">请选择</option>{['广州', '深圳', '珠三角其他城市', '粤东', '粤西', '粤北', '广东省外', '没想好'].map((g) => <option key={g}>{g}</option>)}
          </select></label>
          <label>职业目标<select value={draft.goal} onChange={(e) => set('goal', e.target.value)}>
            <option value="">请选择</option>{['升学（专插本 / 考研）', '直接就业', '还没想好'].map((g) => <option key={g}>{g}</option>)}
          </select></label>
        </div>
        <div className="form-actions">
          <button className="primary-btn" onClick={save} disabled={saving}>{saving ? '正在保存...' : '保存个人信息'}</button>
        </div>
      </SectionCard>

      <PersonalAnalysisPanel profile={draft} refreshKey={analysisVersion} onNavigate={onNavigate} />

      <SectionCard
        title="我的关注"
        extra={(
          <select value={favoriteFilter} onChange={(e) => setFavoriteFilter(e.target.value)}>
            <option value="全部">全部</option>
            <option value="zsb_major">专插本专业</option>
            <option value="kaoyan_discipline">考研学科</option>
            <option value="kaogong_job">考公职位</option>
          </select>
        )}
      >
        {favoriteError && <div className="notice warn"><Icon name="warn" size={16} /><span>{favoriteError}</span></div>}
        {favoriteLoading && <div className="empty">正在读取收藏...</div>}
        {!favoriteLoading && !favoriteError && favorites.length === 0 && (
          <div className="empty">暂无关注。可在专科、本科页面收藏专业、学科或考公职位。</div>
        )}
        <div className="favorite-list">
          {favorites.map((item: any) => (
            <div className="favorite-row" key={item.id}>
              <div className="favorite-main">
                <span className="pill green">{FAVORITE_TYPE_LABELS[item.item_type] || item.item_type}</span>
                <b>{item.item_title}</b>
                {editingId === item.id ? (
                  <input
                    value={noteDraft}
                    onChange={(e) => setNoteDraft(e.target.value)}
                    placeholder="填写目标、待核实条件等备注"
                  />
                ) : (
                  <span className="favorite-note">{item.note || '暂无备注'}</span>
                )}
              </div>
              <div className="favorite-actions">
                {editingId === item.id ? (
                  <>
                    <button className="link-btn" onClick={() => saveFavoriteNote(item.id)}>保存</button>
                    <button className="link-btn muted-link" onClick={() => setEditingId(null)}>取消</button>
                  </>
                ) : (
                  <button
                    className="link-btn"
                    onClick={() => {
                      setEditingId(item.id)
                      setNoteDraft(item.note || '')
                    }}
                  >
                    改备注
                  </button>
                )}
                <button className="link-btn danger-link" onClick={() => deleteFavorite(item.id)}>删除</button>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
      <div className="notice info">
        <Icon name="info" size={16} />
        <span>个人信息只保存在本机，不会上传到任何服务器。</span>
      </div>
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState<PageKey>('home')
  const [profile, setProfile] = useState<Profile>(EMPTY_PROFILE)
  const [bootstrap, setBootstrap] = useState<any>(null)
  const [bootStatus, setBootStatus] = useState('loading')
  const [bootError, setBootError] = useState('')

  const loadBootstrap = async () => {
    setBootStatus('loading')
    setBootError('')
    try {
      const data = await api.bootstrap()
      setBootstrap(data)
      if (data?.profile) setProfile({ ...EMPTY_PROFILE, ...data.profile })
      setBootStatus('ok')
    } catch (reason) {
      setBootStatus('error')
      setBootError(`系统初始化失败：${errorText(reason)}`)
    }
  }

  useEffect(() => { void loadBootstrap() }, [])

  return (
    <div className="app">
      <Sidebar page={page} onNavigate={setPage} profile={profile} />
      <main className="main">
        <Topbar profile={profile} bootstrap={bootstrap} />
        <div className="content">
          {bootStatus === 'loading' && <div className="status-banner loading" aria-live="polite">正在读取本地数据...</div>}
          {bootStatus === 'error' && (
            <div className="status-banner error" aria-live="polite">
              <span>{bootError}</span>
              <button className="ghost-btn" onClick={loadBootstrap}>重试</button>
            </div>
          )}
          {page === 'home' && <HomePage bootstrap={bootstrap} onNavigate={setPage} />}
          {page === 'college' && <LevelPage level="专科" profile={profile} onNavigate={setPage} />}
          {page === 'undergrad' && <LevelPage level="本科" profile={profile} onNavigate={setPage} />}
          {page === 'compare' && <ComparePage profile={profile} />}
          {page === 'calendar' && <CalendarPage profile={profile} />}
          {page === 'overview' && <OverviewPage bootstrap={bootstrap} />}
          {page === 'profile' && <ProfilePage profile={profile} onChange={setProfile} onNavigate={setPage} />}
        </div>
      </main>
    </div>
  )
}
