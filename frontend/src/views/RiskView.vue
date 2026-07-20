<template>
  <div class="view">
    <div class="view__header">
      <h2 class="view__title">风险检测</h2>
      <p class="view__subtitle">智能检测标题中的六大降权风险：属性冲突、年份冲突、规格冲突、语义重复、关键词堆砌、无意义垃圾词</p>
    </div>

    <!-- ==================== 标题输入区 ==================== -->
    <MacCard>
      <div class="input-area">
        <div class="input-area__body">
          <!-- 可高亮文本编辑区（contenteditable overlay） -->
          <div class="title-input-wrapper">
            <!-- 高亮层（绝对定位，只读） -->
            <div
              v-if="highlightedTitle"
              class="title-highlight"
              aria-hidden="true"
              v-html="highlightedTitle"
            />
            <!-- 实际输入层（透明背景） -->
            <textarea
              ref="titleInput"
              v-model="titleText"
              class="title-textarea"
              :class="{ 'title-textarea--transparent': !!highlightedTitle }"
              placeholder="粘贴现有商品标题，例如：【标准版】2024新款无线蓝牙耳机 10件套礼盒装 包邮免运费 双头充电"
              rows="3"
              @input="onTitleInput"
            />
          </div>

          <!-- 关键词列表（可选） -->
          <div class="word-list-section">
            <div class="word-list-section__header" @click="showWordInput = !showWordInput">
              <span class="word-list-section__label">
                📋 关键词列表（可选，用于堆砌检测）
              </span>
              <span class="word-list-section__toggle">{{ showWordInput ? '收起 ▴' : '展开 ▾' }}</span>
            </div>
            <div v-if="showWordInput" class="word-list-section__body">
              <div class="word-tags">
                <span
                  v-for="(w, i) in wordList"
                  :key="i"
                  class="word-tag"
                >
                  {{ w }}
                  <button class="word-tag__remove" @click="removeWord(i)">✕</button>
                </span>
              </div>
              <div class="word-input-row">
                <input
                  v-model="newWord"
                  class="word-input"
                  placeholder="输入关键词后回车添加"
                  @keydown.enter.prevent="addWord"
                />
                <MacButton variant="secondary" size="small" @click="addWord">
                  添加
                </MacButton>
                <MacButton
                  v-if="wordList.length > 0"
                  variant="secondary"
                  size="small"
                  @click="loadFromSession"
                >
                  从报表导入
                </MacButton>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area__footer">
          <div class="input-area__info">
            <span v-if="titleText.length > 0" class="char-count">
              {{ titleText.length }} 字
            </span>
          </div>
          <MacButton
            variant="primary"
            :loading="checking"
            :disabled="!titleText.trim()"
            @click="runCheck"
          >
            {{ checking ? '检测中...' : '🔍 开始检测' }}
          </MacButton>
        </div>
      </div>
    </MacCard>

    <!-- ==================== Toast 错误提示 ==================== -->
    <transition name="toast-fade">
      <div v-if="errorMsg" class="toast toast--error">
        <span class="toast__icon">⚠️</span>
        <span class="toast__text">{{ errorMsg }}</span>
        <button class="toast__close" @click="errorMsg = ''">✕</button>
      </div>
    </transition>

    <!-- ==================== 检测结果区 ==================== -->
    <template v-if="result">
      <!-- 风险总览卡片 -->
      <MacCard class="overview-card">
        <div class="risk-overview">
          <!-- 风险评分环 -->
          <div class="risk-score-ring">
            <svg viewBox="0 0 100 100" class="risk-score-ring__svg">
              <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-border)" stroke-width="6" />
              <circle
                cx="50" cy="50" r="42"
                fill="none"
                :stroke="scoreColor"
                stroke-width="6"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="scoreOffset"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div class="risk-score-ring__text">
              <span class="risk-score-ring__value" :style="{ color: scoreColor }">
                {{ result.risk_score }}
              </span>
              <span class="risk-score-ring__label">风险分</span>
            </div>
          </div>

          <!-- 分类计数 -->
          <div class="risk-counts">
            <div class="risk-count risk-count--high" :class="{ 'risk-count--active': activeLevel === 'high' }" @click="activeLevel = activeLevel === 'high' ? '' : 'high'">
              <span class="risk-count__value">{{ result.high_count }}</span>
              <span class="risk-count__label">高风险</span>
            </div>
            <div class="risk-count risk-count--medium" :class="{ 'risk-count--active': activeLevel === 'medium' }" @click="activeLevel = activeLevel === 'medium' ? '' : 'medium'">
              <span class="risk-count__value">{{ result.medium_count }}</span>
              <span class="risk-count__label">中风险</span>
            </div>
            <div class="risk-count risk-count--low" :class="{ 'risk-count--active': activeLevel === 'low' }" @click="activeLevel = activeLevel === 'low' ? '' : 'low'">
              <span class="risk-count__value">{{ result.low_count }}</span>
              <span class="risk-count__label">低风险</span>
            </div>
          </div>

          <!-- 评估结论 -->
          <div class="risk-verdict" :style="{ color: scoreColor }">
            {{ verdictText }}
          </div>
        </div>
      </MacCard>

      <!-- 风险列表 -->
      <MacCard v-if="filteredRisks.length > 0" class="risk-list-card">
        <template #header>
          <div class="risk-list__header">
            <span>风险详情（{{ filteredRisks.length }} 条）</span>
            <span v-if="activeLevel" class="filter-badge" @click="activeLevel = ''">
              {{ RISK_LEVEL_LABEL[activeLevel].text }} × 清除筛选
            </span>
          </div>
        </template>

        <div class="risk-list">
          <div
            v-for="(risk, idx) in filteredRisks"
            :key="idx"
            class="risk-item"
            :class="{ 'risk-item--active': activeRiskIdx === idx }"
            :style="riskItemStyle(risk.risk_level)"
            @click="highlightRisk(risk, idx)"
          >
            <div class="risk-item__left">
              <span class="risk-item__icon">{{ RISK_TYPE_ICON[risk.type] || '⚠️' }}</span>
            </div>
            <div class="risk-item__center">
              <div class="risk-item__header">
                <span class="risk-item__type">{{ risk.type }}</span>
                <span
                  class="risk-item__level"
                  :style="levelBadgeStyle(risk.risk_level)"
                >
                  {{ RISK_LEVEL_LABEL[risk.risk_level].text }}
                </span>
              </div>
              <p class="risk-item__content">
                违规内容：<strong>{{ risk.content }}</strong>
              </p>
              <p class="risk-item__suggestion">
                💡 {{ risk.suggestion }}
              </p>
            </div>
          </div>
        </div>
      </MacCard>

      <!-- 无风险（理想标题） -->
      <MacCard v-else>
        <div class="clean-state">
          <span class="clean-state__icon">✅</span>
          <p class="clean-state__text">未检测到风险，标题质量良好</p>
        </div>
      </MacCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import MacCard from '@/components/MacCard.vue'
import MacButton from '@/components/MacButton.vue'
import { apiClient, type RiskCheckData, type RiskItem, RISK_LEVEL_LABEL, RISK_TYPE_ICON } from '@/api/client'

// ---- 输入状态 ----
const titleText = ref('')
const titleInput = ref<HTMLTextAreaElement>()
const wordList = ref<string[]>([])
const newWord = ref('')
const showWordInput = ref(false)
const checking = ref(false)
const errorMsg = ref('')

// ---- 检测结果 ----
const result = ref<RiskCheckData | null>(null)
const activeRiskIdx = ref<number | null>(null)
const activeLevel = ref<string>('')  // 按等级筛选

// ---- 高亮文本 ----
const highlightedTitle = ref('')
const activeHighlight = ref<{ start: number; end: number } | null>(null)

// ---- SVG 环参数 ----
const circumference = 2 * Math.PI * 42

// ---- 计算 ----
const scoreColor = computed(() => {
  const s = result.value?.risk_score ?? 0
  if (s >= 60) return '#FF3B30'
  if (s >= 30) return '#FF9500'
  return '#34C759'
})

const scoreOffset = computed(() => {
  const pct = Math.min(result.value?.risk_score ?? 0, 100) / 100
  return circumference * (1 - pct)
})

const verdictText = computed(() => {
  const s = result.value?.risk_score ?? 0
  if (s >= 60) return '⚠️ 标题存在较多风险，建议优先处理高/中风险项'
  if (s >= 30) return '🔶 标题存在一定风险，建议针对性优化'
  if (s > 0) return '🔹 标题质量可接受，可进一步优化低风险项'
  return '✅ 标题质量良好，未发现明显降权风险'
})

const filteredRisks = computed(() => {
  if (!result.value) return []
  if (!activeLevel.value) return result.value.risk_list
  return result.value.risk_list.filter(r => r.risk_level === activeLevel.value)
})

// ---- 高亮生成 ----
function buildHighlightText(title: string, positions: { start: number; end: number }[]) {
  if (!positions.length) return ''
  // 合并重叠区间
  const sorted = [...positions].sort((a, b) => a.start - b.start)
  const merged: { start: number; end: number }[] = []
  for (const p of sorted) {
    if (merged.length && p.start <= merged[merged.length - 1].end) {
      merged[merged.length - 1].end = Math.max(merged[merged.length - 1].end, p.end)
    } else {
      merged.push({ ...p })
    }
  }

  let html = ''
  let cursor = 0
  for (const m of merged) {
    html += escapeHtml(title.slice(cursor, m.start))
    html += `<mark>${escapeHtml(title.slice(m.start, m.end))}</mark>`
    cursor = m.end
  }
  html += escapeHtml(title.slice(cursor))
  return html
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function onTitleInput() {
  // 用户手动输入时清除风险相关的所有状态
  resetHighlight()
}

function resetHighlight() {
  highlightedTitle.value = ''
  activeHighlight.value = null
  activeRiskIdx.value = null
}

// ---- 操作 ----
function addWord() {
  const w = newWord.value.trim()
  if (w && !wordList.value.includes(w)) {
    wordList.value.push(w)
  }
  newWord.value = ''
}

function removeWord(idx: number) {
  wordList.value.splice(idx, 1)
}

function loadFromSession() {
  const stored = sessionStorage.getItem('search_word_keywords')
  if (stored) {
    try {
      const keywords = JSON.parse(stored)
      const names: string[] = keywords.map((k: any) => k.keyword)
      for (const n of names) {
        if (!wordList.value.includes(n)) {
          wordList.value.push(n)
        }
      }
    } catch { /* ignore */ }
  }
}

async function runCheck() {
  if (!titleText.value.trim()) return

  checking.value = true
  errorMsg.value = ''
  resetHighlight()
  result.value = null

  try {
    const res = await apiClient.checkTitleRisk(titleText.value.trim(), wordList.value)
    if (res.data) {
      result.value = res.data
    }
  } catch (err: any) {
    errorMsg.value = err.message || '检测失败，请重试'
  } finally {
    checking.value = false
  }
}

function highlightRisk(risk: RiskItem, idx: number) {
  if (activeRiskIdx.value === idx) {
    // 取消高亮
    resetHighlight()
    return
  }
  activeRiskIdx.value = idx
  // 构建高亮映射
  const allPositions = risk.positions.map(p => ({ start: p.start, end: p.end }))
  highlightedTitle.value = buildHighlightText(titleText.value, allPositions)
}

function riskItemStyle(level: string) {
  const meta = RISK_LEVEL_LABEL[level]
  return { borderLeftColor: meta?.color || '#AEAEB2' }
}

function levelBadgeStyle(level: string) {
  const meta = RISK_LEVEL_LABEL[level]
  return { color: meta?.color, background: meta?.bg }
}
</script>

<style scoped>
.view {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.view__header { margin-bottom: var(--space-sm); }
.view__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}
.view__subtitle {
  margin-top: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* ==================== 输入区 ==================== */
.input-area__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* 高亮输入框 */
.title-input-wrapper {
  position: relative;
}

.title-highlight {
  position: absolute;
  inset: 0;
  padding: 12px 14px;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: transparent;
  pointer-events: none;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
}

.title-highlight :deep(mark) {
  background: rgba(255, 59, 48, 0.22);
  border-radius: 3px;
  color: transparent;
}

.title-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: 1.6;
  color: var(--color-text-primary);
  background: var(--color-bg-white);
  resize: vertical;
  transition: border-color var(--transition-fast);
  outline: none;
}

.title-textarea--transparent {
  color: transparent;
  caret-color: var(--color-text-primary);
  background: transparent;
  position: relative;
  z-index: 1;
}

.title-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.title-textarea::placeholder {
  color: var(--color-text-tertiary);
}

/* 关键词列表 */
.word-list-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: var(--space-sm) 0;
  user-select: none;
}

.word-list-section__label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.word-list-section__toggle {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
}

.word-list-section__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.word-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.word-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(0, 122, 255, 0.06);
  border: 1px solid rgba(0, 122, 255, 0.15);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  color: var(--color-primary);
}

.word-tag__remove {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 10px;
  opacity: 0.5;
  padding: 0 2px;
  transition: opacity var(--transition-fast);
}

.word-tag__remove:hover {
  opacity: 1;
}

.word-input-row {
  display: flex;
  gap: var(--space-sm);
}

.word-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color var(--transition-fast);
}

.word-input:focus {
  border-color: var(--color-primary);
}

/* 输入区底部 */
.input-area__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.char-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* ==================== Toast ==================== */
.toast {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}
.toast--error {
  background: rgba(255, 59, 48, 0.08);
  color: var(--color-danger);
  border: 1px solid rgba(255, 59, 48, 0.20);
}
.toast__icon { flex-shrink: 0; font-size: 16px; }
.toast__text { flex: 1; }
.toast__close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: var(--font-size-base);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  opacity: 0.6;
}
.toast__close:hover { opacity: 1; }
.toast-fade-enter-active, .toast-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast-fade-enter-from, .toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ==================== 风险总览 ==================== */
.risk-overview {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xl);
  flex-wrap: wrap;
}

.risk-score-ring {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}
.risk-score-ring__svg { width: 100%; height: 100%; }
.risk-score-ring__text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.risk-score-ring__value {
  font-size: 28px;
  font-weight: var(--font-weight-bold);
  line-height: 1.1;
}
.risk-score-ring__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.risk-counts {
  display: flex;
  gap: var(--space-md);
}

.risk-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
}
.risk-count--active {
  border-color: var(--color-primary);
  background: rgba(0, 122, 255, 0.04);
}
.risk-count--high .risk-count__value { color: #FF3B30; }
.risk-count--medium .risk-count__value { color: #FF9500; }
.risk-count--low .risk-count__value { color: #AEAEB2; }
.risk-count__value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  line-height: 1.2;
}
.risk-count__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.risk-verdict {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-align: center;
  flex-basis: 100%;
}

/* ==================== 风险列表 ==================== */
.risk-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-size: var(--font-size-sm);
}

.filter-badge {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  cursor: pointer;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(0, 122, 255, 0.06);
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.risk-item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  border-left: 3px solid;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.risk-item:hover {
  background: rgba(0, 0, 0, 0.02);
}
.risk-item--active {
  background: rgba(0, 122, 255, 0.04);
}

.risk-item__left {
  flex-shrink: 0;
  padding-top: 1px;
}
.risk-item__icon {
  font-size: 18px;
}

.risk-item__center {
  flex: 1;
  min-width: 0;
}

.risk-item__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: 4px;
}

.risk-item__type {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.risk-item__level {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: 1px 6px;
  border-radius: var(--radius-full);
}

.risk-item__content {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  line-height: 1.4;
}
.risk-item__content strong {
  color: var(--color-text-primary);
}

.risk-item__suggestion {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  line-height: 1.5;
}

/* ==================== 无风险状态 ==================== */
.clean-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-lg) 0;
}
.clean-state__icon { font-size: 40px; }
.clean-state__text {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-success);
}

/* ==================== 响应式 ==================== */
@media (max-width: 700px) {
  .risk-overview {
    flex-direction: column;
    gap: var(--space-md);
  }
  .risk-counts {
    flex-direction: row;
  }
}
</style>
