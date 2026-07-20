<template>
  <div class="view">
    <div class="view__header">
      <h2 class="view__title">标题生成</h2>
      <p class="view__subtitle">基于词池分类结果，一键生成符合京东规范的最优标题，支持新旧标题权重对比</p>
    </div>

    <!-- ==================== 无数据提示 ==================== -->
    <MacCard v-if="!hasData && !result" class="empty-card">
      <div class="empty-state">
        <div class="empty-state__icon">✨</div>
        <p class="empty-state__text">暂无词池分类数据</p>
        <p class="empty-state__hint">请先在「词池分类」页面完成一键分类，再返回生成标题</p>
        <MacButton variant="secondary" @click="$router.push('/keywords')">前往分类</MacButton>
      </div>
    </MacCard>

    <!-- ==================== 控制区 ==================== -->
    <MacCard v-if="hasData">
      <div class="control-bar">
        <div class="control-bar__left">
          <label class="slider-label">
            <span class="slider-label__text">字数上限</span>
            <span class="slider-label__value">{{ maxLength }} 字</span>
          </label>
          <input
            v-model.number="maxLength"
            type="range"
            min="20"
            max="50"
            step="1"
            class="slider"
          />
        </div>
        <div class="control-bar__right">
          <div class="control-bar__toggle">
            <span class="toggle-label">原标题对比</span>
            <button
              class="toggle-switch"
              :class="{ 'toggle-switch--on': showCompare }"
              @click="showCompare = !showCompare"
            >
              <span class="toggle-switch__dot" />
            </button>
          </div>
          <MacButton variant="primary" :loading="generating" @click="runGenerate">
            {{ generating ? '生成中...' : '✨ 一键生成' }}
          </MacButton>
        </div>
      </div>

      <!-- 原标题输入（对比模式） -->
      <div v-if="showCompare" class="original-input-row">
        <input
          v-model="originalTitle"
          class="original-input"
          placeholder="输入原标题进行对比（可选）"
        />
      </div>
    </MacCard>

    <!-- ==================== Toast ==================== -->
    <transition name="toast-fade">
      <div v-if="toastMsg" class="toast" :class="toastType">
        <span class="toast__text">{{ toastMsg }}</span>
        <button class="toast__close" @click="toastMsg = ''">✕</button>
      </div>
    </transition>

    <!-- ==================== 生成结果 ==================== -->
    <template v-if="result">
      <!-- 标题展示 -->
      <MacCard class="result-card">
        <div class="title-display">
          <h1 class="title-display__text">{{ result.new_title }}</h1>
          <div class="title-display__actions">
            <MacButton variant="primary" @click="copyTitle">
              {{ copied ? '✅ 已复制' : '📋 一键复制' }}
            </MacButton>
          </div>
        </div>
        <div class="title-meta">
          <span class="title-meta__item">{{ result.chinese_count }} 汉字</span>
          <span class="title-meta__divider">·</span>
          <span class="title-meta__item">{{ result.total_chars }} 字符</span>
          <span class="title-meta__divider">·</span>
          <span class="title-meta__item">{{ result.word_detail.length }} 个词</span>
        </div>
      </MacCard>

      <!-- 词权重明细 -->
      <MacCard title="词权重明细">
        <div class="word-breakdown">
          <div class="word-flow">
            <span
              v-for="wd in result.word_detail"
              :key="wd.position"
              class="word-chip"
              :style="wordChipStyle(wd.source_type)"
            >
              {{ wd.word }}
              <small class="word-chip__label">{{ sourceLabel(wd.source_type) }}</small>
            </span>
          </div>
          <div class="word-table">
            <div class="word-table__row word-table__row--header">
              <span class="word-table__cell word-table__cell--pos">#</span>
              <span class="word-table__cell">关键词</span>
              <span class="word-table__cell">来源词池</span>
              <span class="word-table__cell">类型</span>
              <span class="word-table__cell word-table__cell--num">得分</span>
            </div>
            <div
              v-for="wd in result.word_detail"
              :key="wd.position"
              class="word-table__row"
            >
              <span class="word-table__cell word-table__cell--pos">{{ wd.position + 1 }}</span>
              <span class="word-table__cell word-table__cell--word">{{ wd.word }}</span>
              <span class="word-table__cell word-table__cell--pool">{{ wd.source_pool }}</span>
              <span class="word-table__cell">
                <span class="type-badge" :style="wordChipStyle(wd.source_type)">
                  {{ sourceLabel(wd.source_type) }}
                </span>
              </span>
              <span class="word-table__cell word-table__cell--num">
                {{ wd.score != null ? wd.score.toFixed(1) : '-' }}
              </span>
            </div>
          </div>
        </div>
      </MacCard>

      <!-- 新旧对比 -->
      <template v-if="result.compare">
        <!-- 权重提升 -->
        <MacCard class="improvement-card">
          <div class="improvement">
            <div class="improvement__header">
              <span class="improvement__label">预估权重提升</span>
              <span class="improvement__value" :style="{ color: improvementColor }">
                +{{ result.compare.weight_improvement }}%
              </span>
            </div>
            <div class="improvement__bar">
              <div
                class="improvement__bar-fill"
                :style="{ width: result.compare.weight_improvement + '%', background: improvementColor }"
              />
            </div>
            <div class="improvement__reasons">
              <p v-for="(reason, i) in result.compare.traffic_reasons" :key="i" class="improvement__reason">
                📈 {{ reason }}
              </p>
            </div>
          </div>
        </MacCard>

        <!-- 左右对比卡片 -->
        <div class="compare-grid">
          <!-- 原标题 -->
          <MacCard>
            <template #header>
              <div class="compare-header">
                <span class="compare-header__icon">📝</span>
                <span class="compare-header__title">原标题</span>
                <span class="compare-header__risk" :style="riskBadgeStyle(result.compare.original_title.risk_score)">
                  风险 {{ result.compare.original_title.risk_score }} 分
                </span>
              </div>
            </template>
            <p class="compare-title-text">{{ result.compare.original_title.title }}</p>
            <div class="compare-metrics">
              <div class="compare-metric">
                <span class="compare-metric__value">{{ result.compare.original_title.core_count }}</span>
                <span class="compare-metric__label">核心词</span>
              </div>
              <div class="compare-metric compare-metric--bad">
                <span class="compare-metric__value">{{ result.compare.original_title.invalid_count }}</span>
                <span class="compare-metric__label">无效词</span>
              </div>
              <div class="compare-metric compare-metric--bad">
                <span class="compare-metric__value">{{ result.compare.original_title.conflict_count }}</span>
                <span class="compare-metric__label">冲突词</span>
              </div>
              <div class="compare-metric compare-metric--bad">
                <span class="compare-metric__value">{{ result.compare.original_title.risk_count }}</span>
                <span class="compare-metric__label">风险项</span>
              </div>
            </div>
          </MacCard>

          <!-- 分隔箭头 -->
          <div class="compare-arrow">→</div>

          <!-- 新标题 -->
          <MacCard class="compare-new-card">
            <template #header>
              <div class="compare-header">
                <span class="compare-header__icon">✨</span>
                <span class="compare-header__title">新标题</span>
                <span class="compare-header__risk compare-header__risk--good">
                  风险 {{ result.compare.new_title.risk_score }} 分
                </span>
              </div>
            </template>
            <p class="compare-title-text compare-title-text--new">{{ result.compare.new_title.title }}</p>
            <div class="compare-metrics">
              <div class="compare-metric compare-metric--good">
                <span class="compare-metric__value">{{ result.compare.new_title.core_count }}</span>
                <span class="compare-metric__label">核心词</span>
              </div>
              <div class="compare-metric compare-metric--good">
                <span class="compare-metric__value">{{ result.compare.new_title.potential_count }}</span>
                <span class="compare-metric__label">潜力词</span>
              </div>
              <div class="compare-metric compare-metric--good">
                <span class="compare-metric__value">{{ result.compare.new_title.invalid_removed }}</span>
                <span class="compare-metric__label">已剔除无效</span>
              </div>
              <div class="compare-metric compare-metric--good">
                <span class="compare-metric__value">{{ result.compare.new_title.risk_count }}</span>
                <span class="compare-metric__label">风险项</span>
              </div>
            </div>
          </MacCard>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import MacCard from '@/components/MacCard.vue'
import MacButton from '@/components/MacButton.vue'
import { apiClient, type TitleGenerateData, SOURCE_TYPE_CONFIG } from '@/api/client'

// ---- 状态 ----
const maxLength = ref(30)
const originalTitle = ref('')
const showCompare = ref(false)
const generating = ref(false)
const copied = ref(false)
const toastMsg = ref('')
const toastType = ref<'toast--success' | 'toast--error'>('toast--success')
const result = ref<TitleGenerateData | null>(null)

// ---- 数据可用性 ----
const hasData = computed(() => {
  try { return !!sessionStorage.getItem('word_classify_result') }
  catch { return false }
})

function getClassifyData() {
  try {
    const stored = sessionStorage.getItem('word_classify_result')
    return stored ? JSON.parse(stored) : null
  } catch { return null }
}

// ---- 计算 ----
const improvementColor = computed(() => {
  const v = result.value?.compare?.weight_improvement ?? 0
  if (v >= 50) return '#34C759'
  if (v >= 20) return '#FF9500'
  return '#FF3B30'
})

// ---- 操作 ----
async function runGenerate() {
  const pools = getClassifyData()
  if (!pools) {
    toastMsg.value = '请先在词池分类页面完成一键分类'
    toastType.value = 'toast--error'
    return
  }

  generating.value = true
  toastMsg.value = ''

  try {
    const res = await apiClient.generateTitle({
      word_pools: pools,
      original_title: showCompare.value && originalTitle.value.trim()
        ? originalTitle.value.trim()
        : undefined,
      max_length: maxLength.value,
    })
    result.value = res.data
    if (res.data) {
      toastMsg.value = res.message
      toastType.value = 'toast--success'
    }
  } catch (err: any) {
    toastMsg.value = err.message || '生成失败'
    toastType.value = 'toast--error'
  } finally {
    generating.value = false
  }
}

async function copyTitle() {
  if (!result.value?.new_title) return
  try {
    await navigator.clipboard.writeText(result.value.new_title)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback
    const ta = document.createElement('textarea')
    ta.value = result.value.new_title
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

function sourceLabel(type: string): string {
  return SOURCE_TYPE_CONFIG[type]?.label || type
}

function wordChipStyle(type: string) {
  const cfg = SOURCE_TYPE_CONFIG[type]
  return {
    background: (cfg?.color || '#999') + '18',
    borderColor: (cfg?.color || '#999') + '30',
    color: cfg?.color || '#666',
  }
}

function riskBadgeStyle(score: number) {
  if (score >= 60) return { color: '#FF3B30', background: 'rgba(255,59,48,0.10)' }
  if (score >= 30) return { color: '#FF9500', background: 'rgba(255,149,0,0.10)' }
  return { color: '#34C759', background: 'rgba(52,199,89,0.10)' }
}
</script>

<style scoped>
.view { display: flex; flex-direction: column; gap: var(--space-lg); }
.view__header { margin-bottom: var(--space-sm); }
.view__title { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); color: var(--color-text-primary); }
.view__subtitle { margin-top: var(--space-xs); font-size: var(--font-size-sm); color: var(--color-text-secondary); }

/* ---- 空态 ---- */
.empty-card { text-align: center; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: var(--space-md); padding: var(--space-lg) 0; }
.empty-state__icon { font-size: 48px; opacity: 0.6; }
.empty-state__text { font-size: var(--font-size-md); font-weight: var(--font-weight-medium); color: var(--color-text-primary); }
.empty-state__hint { font-size: var(--font-size-sm); color: var(--color-text-secondary); max-width: 320px; text-align: center; }

/* ---- 控制栏 ---- */
.control-bar { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-lg); flex-wrap: wrap; }
.control-bar__left { flex: 1; min-width: 200px; }
.control-bar__right { display: flex; align-items: center; gap: var(--space-md); flex-shrink: 0; }
.control-bar__toggle { display: flex; align-items: center; gap: var(--space-sm); }
.slider-label { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--space-xs); }
.slider-label__text { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.slider-label__value { font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); color: var(--color-primary); }
.slider { width: 100%; height: 4px; -webkit-appearance: none; appearance: none; border-radius: 2px; background: var(--color-border); outline: none; }
.slider::-webkit-slider-thumb { -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%; background: var(--color-primary); cursor: pointer; box-shadow: 0 1px 3px rgba(0,122,255,0.3); }
.toggle-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.toggle-switch { position: relative; width: 36px; height: 20px; border-radius: 10px; background: var(--color-border); border: none; cursor: pointer; transition: background var(--transition-fast); }
.toggle-switch--on { background: var(--color-primary); }
.toggle-switch__dot { position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: transform var(--transition-fast); box-shadow: 0 1px 2px rgba(0,0,0,0.12); }
.toggle-switch--on .toggle-switch__dot { transform: translateX(16px); }
.original-input-row { margin-top: var(--space-md); padding-top: var(--space-md); border-top: 1px solid var(--color-border); }
.original-input { width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-family: var(--font-family); font-size: var(--font-size-sm); outline: none; transition: border-color var(--transition-fast); }
.original-input:focus { border-color: var(--color-primary); }

/* ---- Toast ---- */
.toast { display: flex; align-items: center; gap: var(--space-sm); padding: 12px 16px; border-radius: var(--radius-md); font-size: var(--font-size-sm); }
.toast--success { background: rgba(52,199,89,0.08); color: var(--color-success); border: 1px solid rgba(52,199,89,0.20); }
.toast--error { background: rgba(255,59,48,0.08); color: var(--color-danger); border: 1px solid rgba(255,59,48,0.20); }
.toast__text { flex: 1; }
.toast__close { flex-shrink: 0; background: none; border: none; color: inherit; cursor: pointer; font-size: var(--font-size-base); padding: 2px 6px; border-radius: var(--radius-sm); opacity: 0.6; }
.toast__close:hover { opacity: 1; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateY(-6px); }

/* ---- 标题展示 ---- */
.title-display { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-lg); }
.title-display__text { font-size: 22px; font-weight: var(--font-weight-bold); color: var(--color-text-primary); line-height: 1.5; flex: 1; word-break: break-all; }
.title-display__actions { flex-shrink: 0; }
.title-meta { display: flex; align-items: center; gap: 6px; margin-top: var(--space-md); padding-top: var(--space-md); border-top: 1px solid var(--color-border); }
.title-meta__item, .title-meta__divider { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

/* ---- 词权重明细 ---- */
.word-breakdown { display: flex; flex-direction: column; gap: var(--space-lg); }
.word-flow { display: flex; flex-wrap: wrap; gap: 6px; }
.word-chip { display: inline-flex; align-items: center; gap: 4px; padding: 5px 10px; border-radius: var(--radius-full); border: 1px solid; font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); }
.word-chip__label { font-size: 10px; font-weight: var(--font-weight-regular); opacity: 0.7; }
.word-table { border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; }
.word-table__row { display: grid; grid-template-columns: 32px 1fr 1fr 72px 50px; align-items: center; padding: 6px 12px; border-bottom: 1px solid var(--color-border); font-size: var(--font-size-sm); }
.word-table__row:last-child { border-bottom: none; }
.word-table__row--header { background: rgba(0,0,0,0.02); font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.3px; }
.word-table__cell--pos { text-align: center; color: var(--color-text-tertiary); }
.word-table__cell--num { text-align: center; }
.word-table__cell--word { font-weight: var(--font-weight-medium); }
.word-table__cell--pool { color: var(--color-text-secondary); }
.type-badge { display: inline-block; padding: 1px 6px; border-radius: var(--radius-full); font-size: var(--font-size-xs); }

/* ---- 权重提升 ---- */
.improvement-card { padding: 0; }
.improvement { display: flex; flex-direction: column; gap: var(--space-md); }
.improvement__header { display: flex; align-items: baseline; justify-content: space-between; }
.improvement__label { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.improvement__value { font-size: 36px; font-weight: var(--font-weight-bold); line-height: 1; }
.improvement__bar { height: 8px; border-radius: 4px; background: var(--color-border); overflow: hidden; }
.improvement__bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.improvement__reasons { display: flex; flex-direction: column; gap: 4px; }
.improvement__reason { font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: 1.5; }

/* ---- 对比卡片 ---- */
.compare-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: var(--space-md); align-items: start; }
.compare-arrow { display: flex; align-items: center; justify-content: center; padding-top: 40px; font-size: 24px; color: var(--color-primary); font-weight: var(--font-weight-bold); }
.compare-header { display: flex; align-items: center; gap: var(--space-sm); width: 100%; }
.compare-header__icon { font-size: 16px; }
.compare-header__title { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); color: var(--color-text-primary); }
.compare-header__risk { margin-left: auto; padding: 2px 8px; border-radius: var(--radius-full); font-size: var(--font-size-xs); font-weight: var(--font-weight-medium); }
.compare-header__risk--good { color: #34C759; background: rgba(52,199,89,0.10); }
.compare-title-text { font-size: var(--font-size-base); line-height: 1.6; color: var(--color-text-primary); margin-bottom: var(--space-md); word-break: break-all; padding: var(--space-sm) 0; }
.compare-title-text--new { color: var(--color-primary); }
.compare-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-sm); }
.compare-metric { display: flex; flex-direction: column; align-items: center; padding: var(--space-sm); border-radius: var(--radius-md); background: rgba(0,0,0,0.02); }
.compare-metric--bad .compare-metric__value { color: #FF3B30; }
.compare-metric--good .compare-metric__value { color: #34C759; }
.compare-metric__value { font-size: var(--font-size-lg); font-weight: var(--font-weight-bold); line-height: 1.2; }
.compare-metric__label { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-top: 2px; }
.compare-new-card :deep(.mac-card__header) { border-left: 3px solid var(--color-primary); }

@media (max-width: 800px) {
  .compare-grid { grid-template-columns: 1fr; }
  .compare-arrow { transform: rotate(90deg); padding-top: 0; }
  .title-display { flex-direction: column; }
  .word-table__row { grid-template-columns: 24px 1fr 1fr; }
  .word-table__row .word-table__cell:nth-child(4),
  .word-table__row .word-table__cell:nth-child(5) { display: none; }
}
</style>
