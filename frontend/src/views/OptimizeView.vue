<template>
  <div class="view">
    <div class="view__header">
      <h2 class="view__title">批量优化</h2>
      <p class="view__subtitle">批量上传多个SKU搜索词报表，一键全流程优化并导出结果</p>
    </div>

    <!-- ==================== 上传区 ==================== -->
    <MacCard>
      <!-- 拖拽区 -->
      <div
        class="batch-upload-zone"
        :class="{ 'batch-upload-zone--dragover': isDragover }"
        @dragover.prevent="isDragover = true"
        @dragleave.prevent="isDragover = false"
        @drop.prevent="onDrop"
        @click="openFileDialog"
      >
        <div class="batch-upload-zone__icon">📦</div>
        <p class="batch-upload-zone__text">
          {{ files.length ? `已选择 ${files.length} 个文件` : '拖拽多个搜索词报表文件到此处' }}
        </p>
        <p class="batch-upload-zone__hint">
          支持批量选择 .xlsx / .xls 文件，每个文件对应一个SKU
        </p>
      </div>

      <input
        ref="fileInputRef"
        type="file"
        accept=".xlsx,.xls"
        multiple
        class="upload-hidden"
        @change="onFileSelect"
      />

      <!-- 文件列表 -->
      <div v-if="files.length" class="file-list">
        <div class="file-list__header">
          <span class="file-list__count">共 {{ files.length }} 个文件</span>
          <button class="file-list__clear" @click="clearAll">全部清除</button>
        </div>
        <div
          v-for="(f, i) in files"
          :key="f.name + i"
          class="file-item"
        >
          <span class="file-item__icon">📄</span>
          <div class="file-item__info">
            <span class="file-item__name">{{ f.name }}</span>
            <span class="file-item__size">{{ formatFileSize(f.size) }}</span>
          </div>
          <button class="file-item__remove" @click="removeFile(i)">✕</button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div v-if="files.length" class="batch-actions">
        <MacButton variant="primary" :loading="processing" @click="runOptimize">
          {{ processing ? '处理中...' : '🚀 一键批量优化' }}
        </MacButton>
        <MacButton
          v-if="batchResult && batchResult.success > 0"
          variant="secondary"
          :loading="exporting"
          @click="runExport"
        >
          {{ exporting ? '导出中...' : '📥 导出 Excel' }}
        </MacButton>
      </div>
    </MacCard>

    <!-- ==================== Toast ==================== -->
    <transition name="toast-fade">
      <div v-if="toastMsg" class="toast" :class="toastType">
        <span class="toast__icon">{{ toastType === 'toast--success' ? '✅' : '⚠️' }}</span>
        <span class="toast__text">{{ toastMsg }}</span>
        <button class="toast__close" @click="toastMsg = ''">✕</button>
      </div>
    </transition>

    <!-- ==================== 结果汇总 ==================== -->
    <MacCard v-if="batchResult" class="summary-bar">
      <div class="batch-summary">
        <div class="batch-summary__item">
          <span class="batch-summary__value">{{ batchResult.total }}</span>
          <span class="batch-summary__label">总计</span>
        </div>
        <div class="batch-summary__divider" />
        <div class="batch-summary__item batch-summary__item--success">
          <span class="batch-summary__value">{{ batchResult.success }}</span>
          <span class="batch-summary__label">成功</span>
        </div>
        <div class="batch-summary__divider" />
        <div class="batch-summary__item batch-summary__item--fail" v-if="batchResult.failed > 0">
          <span class="batch-summary__value">{{ batchResult.failed }}</span>
          <span class="batch-summary__label">失败</span>
        </div>
      </div>
    </MacCard>

    <!-- ==================== 结果表格 ==================== -->
    <MacCard v-if="batchResult && batchResult.results.length" class="result-table-card">
      <MacTable
        :columns="tableColumns"
        :data="batchResult.results"
        row-key="sku_name"
        clickable
        @row-click="onRowClick"
      >
        <!-- SKU名 -->
        <template #cell-sku_name="{ value, row }">
          <span class="cell-sku">
            {{ value }}
            <span v-if="row.error" class="cell-error-badge">错误</span>
          </span>
        </template>
        <!-- 标题（截断） -->
        <template #cell-title="{ value, row }">
          <span v-if="row.error" class="cell-error-text">{{ row.error }}</span>
          <span v-else class="cell-title">{{ value || '-' }}</span>
        </template>
        <!-- 质量得分 -->
        <template #cell-score="{ value, row }">
          <span v-if="!row.error" class="cell-score" :class="scoreClass(value)">
            {{ value.toFixed(1) }}
          </span>
          <span v-else>-</span>
        </template>
        <!-- 曝光量（千分位） -->
        <template #cell-total_impressions="{ value }">
          <span>{{ formatNumber(value) }}</span>
        </template>
        <!-- 成交金额 -->
        <template #cell-total_amount="{ value }">
          <span>¥{{ formatAmount(value) }}</span>
        </template>
        <!-- 风险数 -->
        <template #cell-risk_count="{ value, row }">
          <span v-if="!row.error" :class="{ 'text-danger': value > 0 }">
            {{ value }}
          </span>
          <span v-else>-</span>
        </template>
      </MacTable>
    </MacCard>

    <!-- ==================== SKU 详情弹窗 ==================== -->
    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="detailSku" class="detail-overlay" @click.self="detailSku = null">
          <div class="detail-modal">
            <div class="detail-modal__header">
              <div>
                <h3 class="detail-modal__title">{{ detailSku.sku_name }}</h3>
                <p class="detail-modal__subtitle">SKU 优化详情</p>
              </div>
              <button class="detail-modal__close" @click="detailSku = null">✕</button>
            </div>
            <div class="detail-modal__body">
              <div v-if="detailSku.error" class="detail-error">
                ⚠️ {{ detailSku.error }}
              </div>
              <template v-else>
                <div class="detail-section">
                  <span class="detail-section__label">优化后标题</span>
                  <p class="detail-title">{{ detailSku.title }}</p>
                </div>
                <div class="detail-metrics">
                  <div class="dm"><span class="dm__v">{{ detailSku.core_count }}</span><span class="dm__l">核心词</span></div>
                  <div class="dm"><span class="dm__v">{{ detailSku.potential_count }}</span><span class="dm__l">潜力词</span></div>
                  <div class="dm"><span class="dm__v">{{ detailSku.risk_count }}</span><span class="dm__l">风险数</span></div>
                  <div class="dm"><span class="dm__v">{{ detailSku.score.toFixed(1) }}</span><span class="dm__l">质量分</span></div>
                  <div class="dm"><span class="dm__v">{{ formatNumber(detailSku.total_keywords) }}</span><span class="dm__l">总词数</span></div>
                  <div class="dm"><span class="dm__v">{{ formatNumber(detailSku.total_impressions) }}</span><span class="dm__l">总曝光</span></div>
                  <div class="dm"><span class="dm__v">¥{{ formatAmount(detailSku.total_amount) }}</span><span class="dm__l">总成交</span></div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MacCard from '@/components/MacCard.vue'
import MacButton from '@/components/MacButton.vue'
import MacTable, { type TableColumn } from '@/components/MacTable.vue'
import { apiClient, type BatchOptimizeData, type BatchSkuResultItem } from '@/api/client'
import { formatNumber, formatAmount, formatFileSize } from '@/utils/format'

// ---- 文件状态 ----
const fileInputRef = ref<HTMLInputElement>()
const files = ref<File[]>([])
const isDragover = ref(false)
const processing = ref(false)
const exporting = ref(false)
const toastMsg = ref('')
const toastType = ref<'toast--success' | 'toast--error'>('toast--success')

// ---- 结果 ----
const batchResult = ref<BatchOptimizeData | null>(null)
const detailSku = ref<BatchSkuResultItem | null>(null)

// ---- 表格 ----
const tableColumns: TableColumn[] = [
  { key: 'sku_name', title: 'SKU/文件名', width: '180px' },
  { key: 'title', title: '优化后标题' },
  { key: 'core_count', title: '核心词', align: 'center', width: '70px' },
  { key: 'potential_count', title: '潜力词', align: 'center', width: '70px' },
  { key: 'risk_count', title: '风险', align: 'center', width: '60px' },
  { key: 'score', title: '得分', align: 'center', width: '70px' },
  { key: 'total_impressions', title: '曝光量', align: 'right', width: '100px' },
  { key: 'total_amount', title: '成交金额', align: 'right', width: '100px' },
]

const ALLOWED = ['.xlsx', '.xls']

function isValid(f: File) {
  const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase()
  return ALLOWED.includes(ext)
}

// ---- 文件操作 ----
function openFileDialog() { fileInputRef.value?.click() }
function onFileSelect(e: Event) {
  const selected = (e.target as HTMLInputElement).files
  if (!selected) return
  for (let i = 0; i < selected.length; i++) {
    const f = selected[i]
    if (isValid(f) && !files.value.some(x => x.name === f.name)) {
      files.value.push(f)
    }
  }
  if (fileInputRef.value) fileInputRef.value.value = ''
}
function onDrop(e: DragEvent) {
  isDragover.value = false
  if (e.dataTransfer?.files) {
    for (let i = 0; i < e.dataTransfer.files.length; i++) {
      const f = e.dataTransfer.files[i]
      if (isValid(f) && !files.value.some(x => x.name === f.name)) {
        files.value.push(f)
      }
    }
  }
}
function removeFile(i: number) { files.value.splice(i, 1) }
function clearAll() {
  files.value = []
  batchResult.value = null
}

// ---- 优化 / 导出 ----
async function runOptimize() {
  if (!files.value.length) return
  processing.value = true
  toastMsg.value = ''
  try {
    const res = await apiClient.batchOptimize(files.value)
    batchResult.value = res.data
    toastMsg.value = res.message
    toastType.value = 'toast--success'
  } catch (e: any) {
    toastMsg.value = e.message || '处理失败'
    toastType.value = 'toast--error'
  } finally {
    processing.value = false
  }
}

async function runExport() {
  if (!batchResult.value?.results) return
  exporting.value = true
  try {
    const blob = await apiClient.batchExport(batchResult.value.results)
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'SKU优化结果.xlsx'
    a.click()
    URL.revokeObjectURL(a.href)
    toastMsg.value = '导出成功'
    toastType.value = 'toast--success'
  } catch (e: any) {
    toastMsg.value = e.message || '导出失败'
    toastType.value = 'toast--error'
  } finally {
    exporting.value = false
  }
}

function onRowClick(row: BatchSkuResultItem) {
  detailSku.value = row
}

function scoreClass(s: number) {
  if (s >= 70) return 'cell-score--high'
  if (s >= 40) return 'cell-score--mid'
  return 'cell-score--low'
}
</script>

<style scoped>
.view { display: flex; flex-direction: column; gap: var(--space-lg); }
.view__header { margin-bottom: var(--space-sm); }
.view__title { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); color: var(--color-text-primary); }
.view__subtitle { margin-top: var(--space-xs); font-size: var(--font-size-sm); color: var(--color-text-secondary); }

/* ---- 上传区 ---- */
.batch-upload-zone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: var(--space-xl); border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg); cursor: pointer; transition: all var(--transition-normal);
}
.batch-upload-zone:hover, .batch-upload-zone--dragover { border-color: var(--color-primary); background: var(--color-primary-light); }
.batch-upload-zone__icon { font-size: 36px; margin-bottom: var(--space-sm); }
.batch-upload-zone__text { font-size: var(--font-size-md); font-weight: var(--font-weight-medium); color: var(--color-text-primary); }
.batch-upload-zone__hint { margin-top: var(--space-xs); font-size: var(--font-size-sm); color: var(--color-text-tertiary); }
.upload-hidden { display: none; }

/* ---- 文件列表 ---- */
.file-list { margin-top: var(--space-md); }
.file-list__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-sm); }
.file-list__count { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.file-list__clear { background: none; border: none; color: var(--color-danger); font-size: var(--font-size-sm); cursor: pointer; }
.file-item { display: flex; align-items: center; gap: var(--space-sm); padding: 8px 0; border-bottom: 1px solid var(--color-border); }
.file-item:last-child { border-bottom: none; }
.file-item__icon { font-size: 20px; flex-shrink: 0; }
.file-item__info { flex: 1; min-width: 0; }
.file-item__name { display: block; font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-item__size { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.file-item__remove { background: none; border: none; color: var(--color-text-tertiary); cursor: pointer; font-size: 14px; padding: 2px 6px; border-radius: var(--radius-sm); }
.file-item__remove:hover { color: var(--color-danger); background: rgba(255,59,48,0.06); }

/* ---- 操作按钮 ---- */
.batch-actions { display: flex; gap: var(--space-sm); margin-top: var(--space-md); padding-top: var(--space-md); border-top: 1px solid var(--color-border); }

/* ---- Toast ---- */
.toast { display: flex; align-items: center; gap: var(--space-sm); padding: 12px 16px; border-radius: var(--radius-md); font-size: var(--font-size-sm); }
.toast--success { background: rgba(52,199,89,0.08); color: var(--color-success); border: 1px solid rgba(52,199,89,0.20); }
.toast--error { background: rgba(255,59,48,0.08); color: var(--color-danger); border: 1px solid rgba(255,59,48,0.20); }
.toast__icon { flex-shrink: 0; font-size: 16px; }
.toast__text { flex: 1; }
.toast__close { flex-shrink: 0; background: none; border: none; color: inherit; cursor: pointer; font-size: var(--font-size-base); padding: 2px 6px; border-radius: var(--radius-sm); opacity: 0.6; }
.toast__close:hover { opacity: 1; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateY(-6px); }

/* ---- 汇总 ---- */
.batch-summary { display: flex; align-items: center; justify-content: center; gap: var(--space-xl); flex-wrap: wrap; }
.batch-summary__item { display: flex; flex-direction: column; align-items: center; }
.batch-summary__value { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); line-height: 1.2; }
.batch-summary__item--success .batch-summary__value { color: var(--color-success); }
.batch-summary__item--fail .batch-summary__value { color: var(--color-danger); }
.batch-summary__label { font-size: var(--font-size-xs); color: var(--color-text-secondary); }
.batch-summary__divider { width: 1px; height: 28px; background: var(--color-border); }

/* ---- 表格样式 ---- */
.cell-sku { font-weight: var(--font-weight-medium); }
.cell-error-badge { display: inline-block; margin-left: 6px; padding: 1px 6px; border-radius: var(--radius-full); background: rgba(255,59,48,0.12); color: var(--color-danger); font-size: var(--font-size-xs); }
.cell-title { display: block; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell-error-text { color: var(--color-danger); font-size: var(--font-size-xs); }
.cell-score { font-weight: var(--font-weight-semibold); }
.cell-score--high { color: var(--color-primary); }
.cell-score--mid { color: var(--color-success); }
.cell-score--low { color: var(--color-text-tertiary); }
.text-danger { color: var(--color-danger); font-weight: var(--font-weight-semibold); }

/* ---- 详情弹窗 ---- */
.detail-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.detail-modal { background: var(--color-bg-white); border-radius: var(--radius-xl); box-shadow: var(--shadow-lg); width: 420px; max-height: 80vh; overflow-y: auto; animation: pop-in 0.25s ease; }
@keyframes pop-in { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.detail-modal__header { display: flex; align-items: flex-start; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--color-border); }
.detail-modal__title { font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); }
.detail-modal__subtitle { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: 2px; }
.detail-modal__close { width: 28px; height: 28px; border-radius: 50%; border: none; background: rgba(0,0,0,0.06); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; color: var(--color-text-secondary); }
.detail-modal__close:hover { background: rgba(0,0,0,0.12); }
.detail-modal__body { padding: 20px; }
.detail-error { padding: var(--space-md); border-radius: var(--radius-md); background: rgba(255,59,48,0.06); color: var(--color-danger); font-size: var(--font-size-sm); }
.detail-section { margin-bottom: var(--space-lg); }
.detail-section__label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.3px; }
.detail-title { margin-top: 4px; font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); color: var(--color-primary); line-height: 1.6; }
.detail-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-sm); }
.dm { display: flex; flex-direction: column; align-items: center; padding: var(--space-sm); border-radius: var(--radius-md); background: rgba(0,0,0,0.02); }
.dm__v { font-size: var(--font-size-md); font-weight: var(--font-weight-bold); }
.dm__l { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: 1px; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

@media (max-width: 600px) { .detail-modal { width: 90vw; } }
</style>
