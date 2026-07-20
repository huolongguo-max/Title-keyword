<template>
  <div class="view">
    <div class="view__header">
      <div class="view__header-row">
        <div>
          <h2 class="view__title">词池分类</h2>
          <p class="view__subtitle">自动四层级分类 + 质量得分计算，精准定位核心词与淘汰词</p>
        </div>
        <MacButton
          variant="primary"
          :loading="classifying"
          :disabled="!hasData"
          @click="runClassify"
        >
          {{ classifying ? '分类中...' : '一键分类' }}
        </MacButton>
      </div>
    </div>

    <!-- 无数据提示 -->
    <MacCard v-if="!hasData && !classifyResult" class="empty-state-card">
      <div class="empty-state">
        <div class="empty-state__icon">🏷️</div>
        <p class="empty-state__text">暂无搜索词数据</p>
        <p class="empty-state__hint">
          请先在「上传解析」页面上传京东商智搜索词报表，再返回此处进行分类
        </p>
        <MacButton variant="secondary" @click="$router.push('/upload')">
          前往上传
        </MacButton>
      </div>
    </MacCard>

    <!-- 分类结果 Toast -->
    <transition name="toast-fade">
      <div v-if="toastMsg" class="toast" :class="toastType">
        <span class="toast__icon">{{ toastType === 'toast--success' ? '✅' : '⚠️' }}</span>
        <span class="toast__text">{{ toastMsg }}</span>
        <button class="toast__close" @click="toastMsg = ''">✕</button>
      </div>
    </transition>

    <!-- 四词池宫格 -->
    <div v-if="classifyResult" class="pool-grid">
      <WordPoolCard
        v-for="poolKey in poolKeys"
        :key="poolKey"
        :pool="classifyResult[poolKey]"
        :icon="POOL_META[poolKey].icon"
        :name="POOL_META[poolKey].name"
        :tag="classifyResult[poolKey].tag"
        :accent-color="POOL_META[poolKey].color"
        :default-collapsed="POOL_META[poolKey].collapsed"
      />
    </div>

    <!-- 分类统计摘要 -->
    <MacCard v-if="classifyResult && totalWords > 0" class="summary-card">
      <div class="summary">
        <div class="summary__item">
          <span class="summary__value">{{ totalWords }}</span>
          <span class="summary__label">总词数</span>
        </div>
        <div class="summary__divider" />
        <div class="summary__item">
          <span class="summary__value summary__value--blue">
            {{ classifyResult.core_transaction.count }}
          </span>
          <span class="summary__label">核心成交</span>
        </div>
        <div class="summary__divider" />
        <div class="summary__item">
          <span class="summary__value summary__value--green">
            {{ classifyResult.potential_growth.count }}
          </span>
          <span class="summary__label">潜力增长</span>
        </div>
        <div class="summary__divider" />
        <div class="summary__item">
          <span class="summary__value summary__value--gray">
            {{ classifyResult.invalid_weak.count }}
          </span>
          <span class="summary__label">无效弱词</span>
        </div>
        <div class="summary__divider" />
        <div class="summary__item">
          <span class="summary__value summary__value--orange">
            {{ classifyResult.conflict_risk.count }}
          </span>
          <span class="summary__label">冲突违规</span>
        </div>
      </div>
    </MacCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import MacCard from '@/components/MacCard.vue'
import MacButton from '@/components/MacButton.vue'
import WordPoolCard from '@/components/WordPoolCard.vue'
import { apiClient, type ClassifyResponseData, POOL_META, type PoolKey } from '@/api/client'

// ---- 状态 ----
const classifying = ref(false)
const classifyResult = ref<ClassifyResponseData | null>(null)
const toastMsg = ref('')
const toastType = ref<'toast--success' | 'toast--error'>('toast--success')

// ---- 从 sessionStorage 恢复上传数据 ----
const SESSION_KEY = 'search_word_keywords'

/** 是否有上传的搜索词数据 */
const hasData = computed(() => {
  const stored = sessionStorage.getItem(SESSION_KEY)
  if (stored) {
    try {
      return JSON.parse(stored).length > 0
    } catch {
      return false
    }
  }
  return false
})

/** 获取存储的搜索词 */
function getStoredKeywords() {
  const stored = sessionStorage.getItem(SESSION_KEY)
  if (!stored) return []
  try {
    return JSON.parse(stored)
  } catch {
    return []
  }
}

/** 词池键列表（用于 v-for 渲染） */
const poolKeys: PoolKey[] = ['core_transaction', 'potential_growth', 'invalid_weak', 'conflict_risk']

const totalWords = computed(() => {
  if (!classifyResult.value) return 0
  const pools = classifyResult.value
  return pools.core_transaction.count + pools.potential_growth.count +
    pools.invalid_weak.count + pools.conflict_risk.count
})

// ---- 执行分类 ----
async function runClassify() {
  const keywords = getStoredKeywords()
  if (keywords.length === 0) {
    toastMsg.value = '没有可分类的关键词数据'
    toastType.value = 'toast--error'
    return
  }

  classifying.value = true
  toastMsg.value = ''

  try {
    const res = await apiClient.classifyWords(keywords)
    if (res.data) {
      classifyResult.value = res.data
      toastMsg.value = res.message
      toastType.value = 'toast--success'

      // 持久化分类结果到 sessionStorage，供后续模块使用
      sessionStorage.setItem('word_classify_result', JSON.stringify(res.data))
    }
  } catch (err: any) {
    toastMsg.value = err.message || '分类失败，请重试'
    toastType.value = 'toast--error'
  } finally {
    classifying.value = false
  }
}

// ---- 页面挂载时尝试恢复之前的分类结果 ----
const storedResult = sessionStorage.getItem('word_classify_result')
if (storedResult) {
  try {
    classifyResult.value = JSON.parse(storedResult)
  } catch { /* ignore */ }
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

.view__header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg);
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

/* ==================== 空态 ==================== */
.empty-state-card {
  text-align: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) 0;
}

.empty-state__icon {
  font-size: 48px;
  opacity: 0.6;
}

.empty-state__text {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.empty-state__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  max-width: 360px;
  text-align: center;
}

/* ==================== Toast ==================== */
.toast {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  line-height: 1.4;
}

.toast--success {
  background: rgba(52, 199, 89, 0.08);
  color: var(--color-success);
  border: 1px solid rgba(52, 199, 89, 0.20);
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
  color: inherit;
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

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ==================== 四宫格 ==================== */
.pool-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

/* ==================== 摘要栏 ==================== */
.summary-card {
  margin-top: 0;
}

.summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.summary__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.summary__value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: 1.2;
}

.summary__value--blue { color: var(--color-primary); }
.summary__value--green { color: var(--color-success); }
.summary__value--gray { color: var(--color-text-tertiary); }
.summary__value--orange { color: var(--color-warning); }

.summary__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.summary__divider {
  width: 1px;
  height: 32px;
  background: var(--color-border);
}

/* ==================== 响应式 ==================== */
@media (max-width: 900px) {
  .pool-grid {
    grid-template-columns: 1fr;
  }

  .view__header-row {
    flex-direction: column;
    gap: var(--space-md);
  }
}
</style>
