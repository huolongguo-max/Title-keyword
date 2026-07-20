/**
 * API 请求封装
 * 基于 fetch，统一处理请求/响应拦截、错误处理
 */

// 后端基础地址（开发环境通过 Vite proxy 代理）
const BASE_URL = '/api'

// 通用响应结构
interface ApiResponse<T = any> {
  message: string
  data?: T
  detail?: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(error.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('网络连接异常')
    }
  }

  /** GET 请求 */
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  /** POST 请求（JSON） */
  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /** 文件上传 */
  async upload<T>(endpoint: string, file: File): Promise<ApiResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '上传失败' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /** 健康检查 */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const res = await this.get<{ status: string; version: string }>('/health')
    return res as unknown as { status: string; version: string }
  }

  /** 上传京东商智搜索词报表 */
  async uploadSearchWord(file: File): Promise<SearchWordUploadResult> {
    const res = await this.upload<SearchWordUploadData>('/upload/search-word', file)
    return {
      message: res.message ?? '',
      data: res.data ?? null,
    }
  }

  /** 词池分类 */
  async classifyWords(keywords: SearchWordItem[]): Promise<ClassifyResult> {
    const res = await this.post<ClassifyResponseData>('/word/classify', { keywords })
    return {
      message: res.message ?? '',
      data: res.data ?? null,
    }
  }

  /** 标题风险检测 */
  async checkTitleRisk(title: string, wordList: string[]): Promise<RiskCheckResult> {
    const res = await this.post<RiskCheckData>('/title/check-risk', {
      title,
      word_list: wordList,
    })
    return {
      message: res.message ?? '',
      data: res.data ?? null,
    }
  }

  /** 标题生成 + 新旧对比 */
  async generateTitle(req: TitleGenerateRequest): Promise<TitleGenerateResult> {
    const res = await this.post<TitleGenerateData>('/titles/generate', req)
    return {
      message: res.message ?? '',
      data: res.data ?? null,
    }
  }

  /** 批量优化（多文件） */
  async batchOptimize(files: File[]): Promise<BatchOptimizeResult> {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    const url = `${this.baseUrl}/batch/optimize`
    const response = await fetch(url, { method: 'POST', body: formData })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '批量处理失败' }))
      throw new Error(err.detail || `HTTP ${response.status}`)
    }
    const json = await response.json()
    return { message: json.message ?? '', data: json.data ?? null }
  }

  /** 导出结果 */
  async batchExport(results: BatchSkuResultItem[]): Promise<Blob> {
    const url = `${this.baseUrl}/batch/export`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results }),
    })
    if (!response.ok) throw new Error('导出失败')
    return response.blob()
  }
}

// ============================================================
// 搜索词报表类型定义
// ============================================================

/** 单条搜索词 */
export interface SearchWordItem {
  keyword: string
  impressions: number
  clicks: number
  ctr: number
  cart_adds: number
  orders: number
  amount: number
  traffic: number
}

/** 数据概览 */
export interface SearchWordOverview {
  total_keywords: number
  transaction_keywords: number
  total_impressions: number
  total_amount: number
}

/** 上传返回的数据体 */
export interface SearchWordUploadData {
  overview: SearchWordOverview
  keywords: SearchWordItem[]
}

/** 上传接口完整响应 */
export interface SearchWordUploadResult {
  message: string
  data: SearchWordUploadData | null
}

// ============================================================
// 词池分类类型定义
// ============================================================

/** 分类后的单条关键词（含得分 + 归属） */
export interface ClassifiedWord extends SearchWordItem {
  score: number
  pool: string
  pool_label: string
  pool_tag: string
}

/** 单个词池 */
export interface WordPool {
  name: string
  tag: string
  count: number
  keywords: ClassifiedWord[]
}

/** 分类响应数据体 */
export interface ClassifyResponseData {
  core_transaction: WordPool
  potential_growth: WordPool
  invalid_weak: WordPool
  conflict_risk: WordPool
}

/** 分类接口完整响应 */
export interface ClassifyResult {
  message: string
  data: ClassifyResponseData | null
}

/** 词池键名 */
export type PoolKey = 'core_transaction' | 'potential_growth' | 'invalid_weak' | 'conflict_risk'

/** 词池元信息（名称、图标、默认折叠状态） */
export const POOL_META: Record<PoolKey, { name: string; icon: string; collapsed: boolean; color: string }> = {
  core_transaction: {
    name: '核心成交词池',
    icon: '💎',
    collapsed: false,
    color: '#007AFF',
  },
  potential_growth: {
    name: '潜力增长词池',
    icon: '📈',
    collapsed: false,
    color: '#34C759',
  },
  invalid_weak: {
    name: '无效弱词池',
    icon: '🗑️',
    collapsed: true,
    color: '#AEAEB2',
  },
  conflict_risk: {
    name: '冲突违规词池',
    icon: '⚠️',
    collapsed: true,
    color: '#FF9500',
  },
}

// ============================================================
// 风险检测类型定义
// ============================================================

/** 风险词位置 */
export interface RiskPosition {
  word: string
  start: number
  end: number
}

/** 单条风险 */
export interface RiskItem {
  type: string
  risk_level: 'high' | 'medium' | 'low'
  content: string
  positions: RiskPosition[]
  suggestion: string
}

/** 风险检测数据体 */
export interface RiskCheckData {
  risk_list: RiskItem[]
  risk_score: number
  high_count: number
  medium_count: number
  low_count: number
}

/** 风险检测完整响应 */
export interface RiskCheckResult {
  message: string
  data: RiskCheckData | null
}

/** 风险等级 → 显示标签映射 */
export const RISK_LEVEL_LABEL: Record<string, { text: string; color: string; bg: string }> = {
  high:   { text: '高风险', color: '#FF3B30', bg: 'rgba(255,59,48,0.08)' },
  medium: { text: '中风险', color: '#FF9500', bg: 'rgba(255,149,0,0.08)' },
  low:    { text: '低风险', color: '#AEAEB2', bg: 'rgba(174,174,178,0.08)' },
}

/** 风险类型 → 图标映射 */
export const RISK_TYPE_ICON: Record<string, string> = {
  '属性冲突': '⚡',
  '年份冲突': '📅',
  '规格冲突': '📏',
  '语义重复': '🔄',
  '关键词堆砌': '📌',
  '无意义垃圾词': '🗑️',
}

// ============================================================
// 标题生成类型定义
// ============================================================

/** 标题生成请求 */
export interface TitleGenerateRequest {
  word_pools: Record<string, WordPool>
  original_title?: string
  max_length?: number
}

/** 词权重明细 */
export interface WordDetail {
  word: string
  position: number
  source_pool: string
  source_type: string
  score?: number
  impressions?: number
}

/** 原标题对比指标 */
export interface CompareTitleInfo {
  title: string
  core_count: number
  invalid_count: number
  conflict_count: number
  risk_count: number
  risk_score: number
}

/** 新标题对比指标 */
export interface CompareNewTitleInfo {
  title: string
  core_count: number
  potential_count: number
  invalid_removed: number
  risk_count: number
  risk_score: number
}

/** 新旧对比数据 */
export interface CompareData {
  original_title: CompareTitleInfo
  new_title: CompareNewTitleInfo
  weight_improvement: number
  traffic_reasons: string[]
}

/** 标题生成数据体 */
export interface TitleGenerateData {
  new_title: string
  chinese_count: number
  total_chars: number
  word_detail: WordDetail[]
  compare: CompareData | null
}

/** 标题生成响应 */
export interface TitleGenerateResult {
  message: string
  data: TitleGenerateData | null
}

/** 来源类型配置 */
export const SOURCE_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  '前置核心词': { label: '前置核心', color: '#007AFF' },
  '中段属性词': { label: '中段属性', color: '#34C759' },
  '尾部热搜词': { label: '尾部热搜', color: '#FF9500' },
}

// ============================================================
// 批量优化类型定义
// ============================================================

export interface BatchSkuResultItem {
  sku_name: string
  title: string
  core_count: number
  potential_count: number
  risk_count: number
  score: number
  total_keywords: number
  total_impressions: number
  total_amount: number
  error: string | null
}

export interface BatchOptimizeData {
  results: BatchSkuResultItem[]
  total: number
  success: number
  failed: number
}

export interface BatchOptimizeResult {
  message: string
  data: BatchOptimizeData | null
}

export const apiClient = new ApiClient(BASE_URL)
export default apiClient





