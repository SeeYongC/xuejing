export type Profile = {
  username?: string
  education_level: '专科' | '本科' | ''
  undergrad_type?: string
  major: string
  grade: string
  score: string
  budget: string
  region: string
  goal: string
}

export type Source = { name: string; publisher: string; coverage: string; note: string }
export type CalendarEvent = {
  year: string
  category: string
  event: string
  start_date: string
  end_date: string
  exam_date: string
  audience: string
  publisher: string
  status: string
  source_url: string
  note: string
}

type PyApi = {
  bootstrap: () => Promise<any>
  save_profile: (profile: Profile) => Promise<any>
  diagnose: (profile: Profile) => Promise<any>
  personal_analysis_csy: (profile: Profile) => Promise<any>
  compare_paths: (level: string) => Promise<any>
  level_summary: (level: string) => Promise<any>
  zsb_majors: (level: string, keyword: string, discipline: string, basic_subject: string) => Promise<any>
  zsb_score: (subject: string) => Promise<any>
  kaoyan_lines: (discipline: string, candidate_class: string) => Promise<any>
  employment: (year: number) => Promise<any>
  kaogong: (level: string, city: string) => Promise<any>
  calendar: (level: string, category: string) => Promise<any>
  list_favorites_csy: (itemType: string) => Promise<any>
  add_favorite_csy: (itemType: string, itemKey: string, itemTitle: string, note: string) => Promise<any>
  update_favorite_csy: (favoriteId: number, note: string) => Promise<any>
  delete_favorite_csy: (favoriteId: number) => Promise<any>
}

declare global {
  interface Window {
    pywebview?: { api: PyApi }
  }
}

const mockProfile: Profile = {
  username: '游客',
  education_level: '专科',
  undergrad_type: '',
  major: '计算机',
  grade: '大三',
  score: '专业前 30%',
  budget: '3-6 万',
  region: '广州',
  goal: '升学（专插本 / 考研）',
}

const mockBootstrap = {
  profile: mockProfile,
  sources: [
    { name: '广东省普通专升本招生最低控制分数线', publisher: '广东省教育考试院', coverage: '2024-2026 年', note: '' },
    { name: '广东省普通专升本招生专业目录', publisher: '广东省教育考试院', coverage: '2026 年', note: '' },
    { name: '广州商学院毕业生就业质量年度报告', publisher: '广州商学院信息公开网', coverage: '2021-2024 届', note: '学校自行统计，未经第三方核验' },
    { name: '全国硕士研究生招生考试国家线', publisher: '中国研究生招生信息网', coverage: '2022-2026 年', note: '' },
    { name: '广东省考试录用公务员公告与职位表', publisher: '中共广东省委组织部', coverage: '2024-2026 年', note: '' },
  ],
  stats: [
    { label: '数据来源', value: '5 处' },
    { label: '专升本专业', value: '264 个' },
    { label: '考研学科门类', value: '14 个' },
    { label: '就业届别', value: '4 届' },
    { label: '考公年份', value: '3 年' },
  ],
  source_links: [
    { name: '中国研究生招生信息网', label: '考研国家线与报名公告', url: 'https://yz.chsi.com.cn/kyzx/zt/lnfsx.shtml' },
    { name: '广东组织工作网', label: '广东省考公告与职位表', url: 'https://www.gdzz.gov.cn/gwygz/lypytzgg/' },
  ],
  employment_overview: [
    { year: 2021, total: 4430, undergrad: 4133, college: 297, placement_rate: 92.75 },
    { year: 2022, total: 3951, undergrad: 3780, college: 171, placement_rate: 90.51 },
    { year: 2023, total: 7512, undergrad: 7335, college: 177, placement_rate: 92.09 },
    { year: 2024, total: 8800, undergrad: 8605, college: 195, placement_rate: 90.19 },
  ],
  data_gaps: ['离线演示数据仅用于界面检查，实际数据以本地数据库为准。'],
  cross_level: [
    { year: 2021, 本科: 4.38, 专科: 85.52, 总体: 9.82 },
    { year: 2022, 本科: 4.76, 总体: 8.38 },
    { year: 2023, 专科: 81.92 },
  ],
  upcoming: [
    { date: '10-20', title: '广东省考 报名时间', desc: '2025-10-20 至 2025-10-24' },
    { date: '12-07', title: '广东省考 笔试时间', desc: '2025-12-07' },
    { date: '12-21', title: '考研 初试时间', desc: '2025-12-21 至 2025-12-22' },
    { date: '03-01', title: '专插本 报名时间', desc: '2026-03-01 至 2026-03-06' },
  ],
}

let mockFavorites: any[] = []
let mockFavoriteId = 1

let pyRuntimeMode: 'unknown' | 'desktop' | 'browser' = 'unknown'

// pywebview 注入 api 对象和方法是两步：对象先出现，方法后挂上。
// 必须检查具体方法，否则可能在其他方法尚未挂载时调用到 undefined。
const hasPyMethod = (method: keyof PyApi) =>
  typeof window !== 'undefined' &&
  !!window.pywebview?.api &&
  typeof (window.pywebview.api as any)[method] === 'function'

/**
 * pywebview 注入 window.pywebview 是异步的，而且对象先出现、方法后挂上。
 * 用轮询而不是只监听 pywebviewready：事件可能在 React 挂载前就已经触发。
 */
function waitForPy(method: keyof PyApi = 'bootstrap'): Promise<boolean> {
  if (hasPyMethod(method)) {
    pyRuntimeMode = 'desktop'
    return Promise.resolve(true)
  }
  if (pyRuntimeMode === 'browser') return Promise.resolve(false)
  return new Promise((resolve) => {
    const started = Date.now()
    const timer = window.setInterval(() => {
      if (hasPyMethod(method)) {
        pyRuntimeMode = 'desktop'
        window.clearInterval(timer)
        resolve(true)
      } else if (Date.now() - started > 6000) {
        pyRuntimeMode = window.pywebview ? 'desktop' : 'browser'
        window.clearInterval(timer)
        resolve(hasPyMethod(method))
      }
    }, 100)
  })
}

async function callPy(method: keyof PyApi, args: unknown[], fallback: any): Promise<any> {
  const ready = await waitForPy(method)
  if (ready) {
    const fn = (window.pywebview!.api as any)[method]
    return fn(...args)
  }
  if (pyRuntimeMode === 'desktop') {
    throw new Error(`本地接口 ${method} 尚未就绪`)
  }
  return fallback
}

export const api = {
  async bootstrap() {
    return callPy('bootstrap', [], mockBootstrap)
  },
  async saveProfile(profile: Profile) {
    return callPy('save_profile', [profile], { success: true })
  },
  async diagnose(profile: Profile) {
    return callPy('diagnose', [profile], [
      {
        path: '专插本', status: '可报', policy_year: '2026',
        source: '广东省2026年普通高等学校专升本招生工作规定',
        reasons: ['学历：专科（符合）', '地区：广州（在广东范围内）'],
        todo: ['往届生需户籍连续满 3 年，具体以当年文件为准'],
        summary: '你的地区在广东范围内，符合基本条件。',
      },
      {
        path: '考研', status: '暂不适用', policy_year: '2026',
        source: '教育部全国硕士研究生招生工作管理规定',
        reasons: [], todo: ['比较专插本后再考研与同等学力直考两条路'],
        summary: '专科生需要毕业满 2 年才能以同等学力报考。',
      },
      {
        path: '考公（广东省考）', status: '暂不适用', policy_year: '2026',
        source: '广东省2026年考试录用公务员公告',
        reasons: [], todo: ['关注广东省考公告与职位表'],
        summary: '省考一般在大四上学期报名、年底笔试。',
      },
    ])
  },
  async personalAnalysis(profile: Profile) {
    return callPy('personal_analysis_csy', [profile], {
      profile_ready: Boolean(profile.education_level && profile.major && profile.grade && profile.region && profile.goal),
      summary: `${profile.education_level || '未填写'} · ${profile.major || '专业未填写'} · ${profile.grade || '年级未填写'}`,
      profile_gaps: profile.education_level ? [] : ['请补充学历层次'],
      recommendations: profile.education_level ? [
        {
          key: profile.education_level === '专科' ? 'zsb' : 'kaoyan',
          title: profile.education_level === '专科' ? '专插本' : '本科毕业后考研',
          status: '可报',
          match_level: '优先了解',
          score: 86,
          reasons: ['资格符合基本条件', '与你的升学目标一致'],
          evidence: ['示例数据：请运行桌面版读取本地 SQLite'],
          gaps: [],
          next_checks: ['查看对应公开数据，并以当年官方公告为准'],
          page: profile.education_level === '专科' ? 'college' : 'undergrad',
        },
      ] : [],
      rules_version: '1.0',
      calculated_at: new Date().toISOString().slice(0, 10),
      note: '匹配分只表示资料与公开数据的适配程度，不是录取概率。',
    })
  },
  async comparePaths(level: string) {
    return callPy('compare_paths', [level], [])
  },
  async levelSummary(level: string) {
    return callPy('level_summary', [level], {
      cross_level: mockBootstrap.cross_level,
      subjects: level === '专科' ? ['高等数学', '管理学'] : [],
      major_subjects: level === '专科'
        ? [{ subject: '高等数学', major_count: 105 }]
        : [],
    })
  },
  async zsbMajors(level: string, keyword: string, discipline: string, basicSubject = '') {
    return callPy('zsb_majors', [level, keyword, discipline, basicSubject], [])
  },
  async zsbScore(subject: string) {
    return callPy('zsb_score', [subject], { trend: [], subjects: [] })
  },
  async kaoyanLines(discipline: string, cls: string) {
    return callPy('kaoyan_lines', [discipline, cls], { trend: [], disciplines: [] })
  },
  async employment(year: number) {
    return callPy('employment', [year], { scale: [], advance: [], flow: [], years: [] })
  },
  async kaogong(level: string, city = '全部') {
    return callPy('kaogong', [level, city], {
      rows: [],
      total: 0,
      city_options: [],
      summary: [],
      education: [],
      years: [
        { year: 2026, recruit_count: 11779, applicants: 270194, competition_ratio: 22.94 },
        { year: 2025, recruit_count: 17419, applicants: 157100, competition_ratio: 9.02 },
        { year: 2024, recruit_count: 17307, applicants: 170203, competition_ratio: 9.83 },
      ],
    })
  },
  async calendar(level: string, category: string) {
    return callPy('calendar', [level, category], [])
  },
  async listFavorites(itemType = '全部') {
    const result = await callPy('list_favorites_csy', [itemType], null)
    if (result !== null) return result
    return {
      success: true,
      rows: itemType === '全部'
        ? mockFavorites
        : mockFavorites.filter((item) => item.item_type === itemType),
    }
  },
  async addFavorite(itemType: string, itemKey: string, itemTitle: string, note = '') {
    const result = await callPy('add_favorite_csy', [itemType, itemKey, itemTitle, note], null)
    if (result !== null) return result
    const existing = mockFavorites.find(
      (item) => item.item_type === itemType && item.item_key === itemKey)
    if (existing) {
      existing.item_title = itemTitle
      existing.note = note
      existing.updated_at = new Date().toISOString()
      return { success: true, id: existing.id }
    }
    const id = mockFavoriteId++
    mockFavorites.unshift({
      id,
      item_type: itemType,
      item_key: itemKey,
      item_title: itemTitle,
      note,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    return { success: true, id }
  },
  async updateFavorite(favoriteId: number, note: string) {
    const result = await callPy('update_favorite_csy', [favoriteId, note], null)
    if (result !== null) return result
    const item = mockFavorites.find((favorite) => favorite.id === favoriteId)
    if (!item) return { success: false, error: '收藏不存在' }
    item.note = note
    item.updated_at = new Date().toISOString()
    return { success: true }
  },
  async deleteFavorite(favoriteId: number) {
    const result = await callPy('delete_favorite_csy', [favoriteId], null)
    if (result !== null) return result
    const index = mockFavorites.findIndex((favorite) => favorite.id === favoriteId)
    if (index < 0) return { success: false, error: '收藏不存在' }
    mockFavorites.splice(index, 1)
    return { success: true }
  },
}
