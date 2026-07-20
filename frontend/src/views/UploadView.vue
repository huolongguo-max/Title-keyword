<template>
  <div class="view">
    <div class="view__header">
      <h2 class="view__title">上传解析</h2>
      <p class="view__subtitle">上传京东商智-搜索词报表（.xlsx / .xls），自动解析并预览数据</p>
    </div>

    <!-- ==================== 上传区域 ==================== -->
    <MacCard class="upload-card">
      <div
        class="upload-zone"
        :class="{ 'upload-zone--dragover': isDragover, 'upload-zone--has-file': !!selectedFile }"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
        @click="openFileDialog"
      >
        <template v-if="!selectedFile">
          <div class="upload-zone__icon">📂</div>
          <p class="upload-zone__text">点击或拖拽京东商智搜索词报表到此处</p>
          <p class="upload-zone__hint">仅支持 .xlsx / .xls 格式，最大 20MB</p>
        </template>
        <template v-else>
          <div class="upload-zone__icon">📄</div>
          <p class="upload-zone__text">{{ selectedFile.name }}</p>
          <p class="upload-zone__hint">{{ formatFileSize(selectedFile.size) }} — 点击重新选择</p>
        </template>
      </div>

      <input
        ref="fileInput"
        type="file"
        accept=".xlsx,.xls"
        class="upload-input-hidden"
        @change="onFileSelect"
      />

      <!-- 操作按钮 -->
      <div v-if="selectedFile" class="upload-actions">
        <MacButton variant="primary" :loading="uploading" @click="handleUpload">
          {{ uploading ? '解析中...' : '开始解析' }}
        </MacButton>
        <MacButton variant="secondary" :disabled="uploading" @click="clearFile">
          移除
        </MacButton>
      </div>
    </MacCard>

    <!-- ==================== 错误提示 Toast ==================== -->
    <transition name="toast-fade">
      <div v-if="errorMsg" class="toast toast--error">
        <span class="toast__icon">⚠️</span>
        <span class="toast__text">{{ errorMsg }}</span>
        <button class="toast__close" @click="errorMsg = ''">✕</button>
      </div>
    </transition>

    <!-- ==================== 数据概览卡片 ==================== -->
    <div v-if="overview" class="overview-grid">
      <MacCard class="overview-card">
        <div class="stat-item">
          <span class="stat-item__value">{{ formatNumber(overview.total_keywords) }}</span>
          <span class="stat-item__label">总词数</span>
        </div>
      </MacCard>
      <MacCard class="overview-card">
        <div class="stat-item">
          <span class="stat-item__value">{{ formatNumber(overview.transaction_keywords) }}</span>
          <span class="stat-item__label">有成交词数</span>
        </div>
      </MacCard>
      <MacCard class="overview-card">
        <div class="stat-item">
          <span class="stat-item__value">{{ formatNumber(overview.total_impressions) }}</span>
          <span class="stat-item__label">总曝光量</span>
        </div>
      </MacCard>
      <MacCard class="overview-card">
        <div class="stat-item">
          <span class="stat-item__value">¥{{ formatAmount(overview.total_amount) }}</span>
          <span class="stat-item__label">总成交金额</span>
        </div>
      </MacCard>
    </div>

    <!-- ==================== 数据表格 ==================== -->
    <MacCard v-if="keywords.length > 0" class="table-card">
      <template #header>
        <div class="table-header">
          <span class="table-header__count">
            共 <strong>{{ formatNumber(keywords.length) }}</strong> 个关键词
          </span>
        </div>
      </template>

      <MacTable :columns="tableColumns" :data="pagedData" row-key="keyword">
        <!-- 关键词列 -->
        <template #cell-keyword="{ value }">
          <span class="cell-keyword">{{ value }}</span>
        </template>
        <!-- CTR 列：百分比 -->
        <template #cell-ctr="{ value }">
          <span>{{ formatPercent(value) }}</span>
        </template>
        <!-- 成交金额列 -->
        <template #cell-amount="{ value }">
          <span>¥{{ formatAmount(value) }}</span>
        </template>
        <!-- 数值列：千分位 -->
        <template #cell-impressions="{ value }">
          <span>{{ formatNumber(value) }}</span>
        </template>
        <template #cell-clicks="{ value }">
          <span>{{ formatNumber(value) }}</span>
        </template>
        <template #cell-cart_adds="{ value }">
          <span>{{ formatNumber(value) }}</span>
        </template>
        <template #cell-orders="{ value }">
          <span>{{ formatNumber(value) }}</span>
        </template>
        <template #cell-traffic="{ value }">
          <span>{{ formatNumber(value) }}</span>
        </template>
      </MacTable>

      <!-- 分页控件 -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          class="pagination__btn"
          :disabled="currentPage <= 1"
          @click="currentPage = 1"
        >
          ««
        </button>
        <button
          class="pagination__btn"
          :disabled="currentPage <= 1"
          @click="currentPage--"
        >
          ‹
        </button>

        <template v-for="p in visiblePages" :key="p">
          <span v-if="p === -1" class="pagination__ellipsis">…</span>
          <button
            v-else
            class="pagination__btn"
            :class="{ 'pagination__btn--active': p === currentPage }"
            @click="currentPage = p"
          >
            {{ p }}
          </button>
        </template>

        <button
          class="pagination__btn"
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
        >
          ›
        </button>
        <button
          class="pagination__btn"
          :disabled="currentPage >= totalPages"
          @click="currentPage = totalPages"
        >
          »»
        </button>
      </div>
    </MacCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import MacCard from '@/components/MacCard.vue'
import MacButton from '@/components/MacButton.vue'
import MacTable, { type TableColumn } from '@/components/MacTable.vue'
import { apiClient, type SearchWordItem, type SearchWordOverview } from '@/api/client'
import { formatNumber, formatAmount, formatPercent, formatFileSize } from '@/utils/format'

// ---- 文件上传状态 ----
const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const isDragover = ref(false)
const uploading = ref(false)
const errorMsg = ref('')

// ---- 解析结果 ----
const overview = ref<SearchWordOverview | null>(null)
const keywords = ref<SearchWordItem[]>([])

// ---- 分页 ----
const PAGE_SIZE = 50
const currentPage = ref(1)

const totalPages = computed(() => Math.ceil(keywords.value.length / PAGE_SIZE))

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return keywords.value.slice(start, start + PAGE_SIZE)
})

/** 可见的页码按钮（带省略号） */
const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: number[] = []
  // 始终显示第1页
  pages.push(1)
  if (cur > 3) pages.push(-1) // 省略号
  // 当前页附近的页码
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) {
    pages.push(i)
  }
  if (cur < total - 2) pages.push(-1)
  pages.push(total)
  return pages
})

// ---- 表格列定义 ----
const tableColumns: TableColumn[] = [
  { key: 'keyword', title: '关键词', width: 'auto' },
  { key: 'impressions', title: '曝光', align: 'right' },
  { key: 'clicks', title: '点击', align: 'right' },
  { key: 'ctr', title: 'CTR', align: 'right' },
  { key: 'cart_adds', title: '加购', align: 'right' },
  { key: 'orders', title: '成交单量', align: 'right' },
  { key: 'amount', title: '成交金额', align: 'right' },
  { key: 'traffic', title: '引流人数', align: 'right' },
]

// ---- 允许的扩展名 ----
const ALLOWED_EXTS = ['.xlsx', '.xls']

/** 校验文件扩展名 */
function isValidExt(filename: string): boolean {
  const ext = filename.substring(filename.lastIndexOf('.')).toLowerCase()
  return ALLOWED_EXTS.includes(ext)
}

// ---- 拖拽处理 ----
function onDragOver(e: DragEvent) {
  isDragover.value = true
}

function onDragLeave() {
  isDragover.value = false
}

function onDrop(e: DragEvent) {
  isDragover.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    selectFile(file)
  }
}

// ---- 文件选择 ----
function openFileDialog() {
  if (uploading.value) return
  fileInput.value?.click()
}

function onFileSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    selectFile(file)
  }
}

function selectFile(file: File) {
  errorMsg.value = ''

  // 客户端格式拦截
  if (!isValidExt(file.name)) {
    errorMsg.value = `不支持的文件格式，请上传 .xlsx 或 .xls 格式的搜索词报表`
    return
  }

  // 大小检查 (20MB)
  if (file.size > 20 * 1024 * 1024) {
    errorMsg.value = `文件过大（${formatFileSize(file.size)}），请上传不超过 20MB 的报表`
    return
  }

  selectedFile.value = file
  overview.value = null
  keywords.value = []
  // 重置 input 以便重复选择同一文件
  if (fileInput.value) fileInput.value.value = ''
}

// ---- 上传解析 ----
async function handleUpload() {
  if (!selectedFile.value) return

  uploading.value = true
  errorMsg.value = ''

  try {
    const res = await apiClient.uploadSearchWord(selectedFile.value)
    if (res.data) {
      overview.value = res.data.overview
      keywords.value = res.data.keywords
      currentPage.value = 1

      // 持久化到 sessionStorage，供词池分类等后续模块直接调用
      sessionStorage.setItem('search_word_keywords', JSON.stringify(res.data.keywords))
      sessionStorage.setItem('search_word_overview', JSON.stringify(res.data.overview))
    }
  } catch (err: any) {
    errorMsg.value = err.message || '上传失败，请重试'
  } finally {
    uploading.value = false
  }
}

// ---- 清除 ----
function clearFile() {
  selectedFile.value = null
  overview.value = null
  keywords.value = []
  errorMsg.value = ''
  currentPage.value = 1
}
</script>

<style scoped>
.view {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.view__header {
  margin-bottom: var(--space-sm);
}

.view__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.view__subtitle {
  margin-top: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* ==================== 上传区域 ==================== */
.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) var(--space-lg);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-normal);
  user-select: none;
}

.upload-zone:hover,
.upload-zone--dragover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.upload-zone--has-file {
  border-style: solid;
  border-color: var(--color-border);
  background: rgba(0, 0, 0, 0.01);
}

.upload-zone__icon {
  font-size: 40px;
  margin-bottom: var(--space-md);
}

.upload-zone__text {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.upload-zone__hint {
  margin-top: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.upload-input-hidden {
  display: none;
}

.upload-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  justify-content: center;
}

/* ==================== Toast 错误提示 ==================== */
.toast {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  line-height: 1.4;
}

.toast--error {
  background: rgba(255, 59, 48, 0.08);
  color: var(--color-danger);
  border: 1px solid rgba(255, 59, 48, 0.20);
}

.toast__icon {
  flex-shrink: 0;
  font-size: 16px;
}

.toast__text {
  flex: 1;
}

.toast__close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--color-danger);
  cursor: pointer;
  font-size: var(--font-size-base);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  opacity: 0.6;
  transition: opacity var(--transition-fast);
}

.toast__close:hover {
  opacity: 1;
}

/* Toast 动画 */
.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ==================== 数据概览卡片 ==================== */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
}

.overview-card {
  padding: 0;
}

.overview-card :deep(.mac-card__body) {
  padding: var(--space-lg);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
}

.stat-item__value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  line-height: 1.2;
}

.stat-item__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* ==================== 表格区域 ==================== */
.table-card {
  margin-top: 0;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.table-header__count {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.table-header__count strong {
  color: var(--color-text-primary);
}

.cell-keyword {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

/* ==================== 分页 ==================== */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.pagination__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 6px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-primary);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.pagination__btn:hover:not(:disabled):not(.pagination__btn--active) {
  background: rgba(0, 0, 0, 0.06);
}

.pagination__btn--active {
  background: var(--color-primary);
  color: #fff;
  font-weight: var(--font-weight-semibold);
}

.pagination__btn:disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

.pagination__ellipsis {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

/* ==================== 响应式：概览卡片折行 ==================== */
@media (max-width: 900px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
