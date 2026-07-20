<template>
  <div class="pool-card" :style="{ '--pool-accent': accentColor }">
    <!-- 卡片头部 -->
    <div class="pool-card__header" @click="collapsed = !collapsed">
      <div class="pool-card__header-left">
        <span class="pool-card__icon">{{ icon }}</span>
        <div>
          <span class="pool-card__name">{{ name }}</span>
          <span class="pool-card__tag">{{ tag }}</span>
        </div>
      </div>
      <div class="pool-card__header-right">
        <span class="pool-card__count">{{ pool.count }}</span>
        <span class="pool-card__count-label">词</span>
        <span class="pool-card__chevron" :class="{ 'pool-card__chevron--open': !collapsed }">
          ▾
        </span>
      </div>
    </div>

    <!-- 卡片内容（可折叠） -->
    <transition name="pool-collapse">
      <div v-if="!collapsed" class="pool-card__body">
        <!-- 空态 -->
        <div v-if="pool.count === 0" class="pool-card__empty">
          <span class="pool-card__empty-icon">📭</span>
          <span>暂无匹配的关键词</span>
        </div>

        <!-- 词列表 -->
        <div v-else class="pool-card__list">
          <div
            v-for="(word, idx) in pool.keywords"
            :key="word.keyword"
            class="pool-word"
            :class="{ 'pool-word--selected': selectedWord === word }"
            @click="selectWord(word)"
          >
            <!-- 排名 -->
            <span class="pool-word__rank">{{ idx + 1 }}</span>

            <!-- 关键词 + 得分 -->
            <div class="pool-word__main">
              <span class="pool-word__keyword">{{ word.keyword }}</span>
              <div class="pool-word__metrics">
                <span class="pool-word__metric">曝光 {{ formatNumber(word.impressions) }}</span>
                <span class="pool-word__metric">点击 {{ formatNumber(word.clicks) }}</span>
                <span v-if="word.orders > 0" class="pool-word__metric pool-word__metric--primary">
                  成交 {{ word.orders }}单
                </span>
              </div>
            </div>

            <!-- 质量得分 -->
            <div class="pool-word__score" :class="getScoreClass(word.score)">
              <span class="pool-word__score-value">{{ word.score.toFixed(1) }}</span>
              <span class="pool-word__score-label">分</span>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 详情弹窗（macOS 风格浮层） -->
    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="selectedWord" class="detail-overlay" @click.self="selectedWord = null">
          <div class="detail-modal">
            <div class="detail-modal__header">
              <h3 class="detail-modal__title">{{ selectedWord.keyword }}</h3>
              <button class="detail-modal__close" @click="selectedWord = null">✕</button>
            </div>
            <div class="detail-modal__body">
              <!-- 得分环 -->
              <div class="detail-score-ring">
                <svg viewBox="0 0 100 100" class="detail-score-ring__svg">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-border)" stroke-width="6" />
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    :stroke="accentColor"
                    stroke-width="6"
                    stroke-linecap="round"
                    :stroke-dasharray="circumference"
                    :stroke-dashoffset="scoreOffset"
                    transform="rotate(-90 50 50)"
                    class="detail-score-ring__arc"
                  />
                </svg>
                <div class="detail-score-ring__text">
                  <span class="detail-score-ring__value">{{ selectedWord.score.toFixed(1) }}</span>
                  <span class="detail-score-ring__label">质量分</span>
                </div>
              </div>

              <!-- 全指标网格 -->
              <div class="detail-metrics">
                <div class="detail-metric">
                  <span class="detail-metric__label">曝光次数</span>
                  <span class="detail-metric__value">{{ formatNumber(selectedWord.impressions) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">点击次数</span>
                  <span class="detail-metric__value">{{ formatNumber(selectedWord.clicks) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">点击率 CTR</span>
                  <span class="detail-metric__value">{{ formatPercent(selectedWord.ctr) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">加购次数</span>
                  <span class="detail-metric__value">{{ formatNumber(selectedWord.cart_adds) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">成交订单量</span>
                  <span class="detail-metric__value">{{ formatNumber(selectedWord.orders) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">成交金额</span>
                  <span class="detail-metric__value">¥{{ formatAmount(selectedWord.amount) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">引流人数</span>
                  <span class="detail-metric__value">{{ formatNumber(selectedWord.traffic) }}</span>
                </div>
                <div class="detail-metric">
                  <span class="detail-metric__label">所属词池</span>
                  <span class="detail-metric__value detail-metric__value--pool">{{ selectedWord.pool_label }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { type WordPool, type ClassifiedWord } from '@/api/client'
import { formatNumber, formatAmount, formatPercent } from '@/utils/format'

const props = defineProps<{
  pool: WordPool
  icon: string
  name: string
  tag: string
  accentColor: string
  defaultCollapsed?: boolean
}>()

const collapsed = ref(props.defaultCollapsed ?? false)
const selectedWord = ref<ClassifiedWord | null>(null)

function selectWord(word: ClassifiedWord) {
  selectedWord.value = word
}

function getScoreClass(score: number): string {
  if (score >= 70) return 'pool-word__score--high'
  if (score >= 30) return 'pool-word__score--mid'
  return 'pool-word__score--low'
}

// ---- 得分环 SVG ----
const circumference = 2 * Math.PI * 42
const scoreOffset = computed(() => {
  const pct = Math.min(selectedWord.value?.score ?? 0, 100) / 100
  return circumference * (1 - pct)
})
</script>

<style scoped>
.pool-card {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-normal);
  display: flex;
  flex-direction: column;
}

.pool-card:hover {
  box-shadow: var(--shadow-sm);
}

/* ==================== 头部 ==================== */
.pool-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
  border-left: 3px solid var(--pool-accent);
}

.pool-card__header:hover {
  background: rgba(0, 0, 0, 0.02);
}

.pool-card__header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.pool-card__icon {
  font-size: 20px;
  flex-shrink: 0;
}

.pool-card__name {
  display: block;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.pool-card__tag {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 1px;
}

.pool-card__header-right {
  display: flex;
  align-items: baseline;
  gap: 2px;
  flex-shrink: 0;
}

.pool-card__count {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--pool-accent);
  line-height: 1;
}

.pool-card__count-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-right: 8px;
}

.pool-card__chevron {
  font-size: 12px;
  color: var(--color-text-tertiary);
  transition: transform var(--transition-fast);
  transform: rotate(-90deg);
}

.pool-card__chevron--open {
  transform: rotate(0deg);
}

/* ==================== 内容区 ==================== */
.pool-card__body {
  border-top: 1px solid var(--color-border);
  max-height: 360px;
  overflow-y: auto;
}

.pool-card__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  gap: var(--space-sm);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.pool-card__empty-icon {
  font-size: 28px;
  opacity: 0.5;
}

/* 折叠动画 */
.pool-collapse-enter-active,
.pool-collapse-leave-active {
  transition: max-height 0.3s ease, opacity 0.25s ease;
  max-height: 360px;
}

.pool-collapse-enter-from,
.pool-collapse-leave-to {
  max-height: 0;
  opacity: 0;
}

/* ==================== 词条目 ==================== */
.pool-card__list {
  padding: var(--space-xs) 0;
}

.pool-word {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.pool-word:hover {
  background: rgba(0, 0, 0, 0.03);
}

.pool-word--selected {
  background: rgba(0, 122, 255, 0.05);
}

.pool-word__rank {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.04);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.pool-word__main {
  flex: 1;
  min-width: 0;
}

.pool-word__keyword {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pool-word__metrics {
  display: flex;
  gap: 10px;
  margin-top: 2px;
}

.pool-word__metric {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.pool-word__metric--primary {
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
}

/* 得分徽章 */
.pool-word__score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.pool-word__score--high {
  background: rgba(0, 122, 255, 0.10);
  color: var(--color-primary);
}

.pool-word__score--mid {
  background: rgba(52, 199, 89, 0.10);
  color: var(--color-success);
}

.pool-word__score--low {
  background: rgba(174, 174, 178, 0.10);
  color: var(--color-text-tertiary);
}

.pool-word__score-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  line-height: 1.1;
}

.pool-word__score-label {
  font-size: 9px;
  opacity: 0.7;
}

/* ==================== 详情弹窗 ==================== */
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.detail-modal {
  background: var(--color-bg-white);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  width: 380px;
  max-height: 80vh;
  overflow-y: auto;
  animation: modal-in 0.25s ease;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.detail-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.detail-modal__title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.detail-modal__close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.06);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--transition-fast);
}

.detail-modal__close:hover {
  background: rgba(0, 0, 0, 0.12);
}

.detail-modal__body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
}

/* 得分环 */
.detail-score-ring {
  position: relative;
  width: 110px;
  height: 110px;
}

.detail-score-ring__svg {
  width: 100%;
  height: 100%;
}

.detail-score-ring__arc {
  transition: stroke-dashoffset 0.6s ease;
}

.detail-score-ring__text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.detail-score-ring__value {
  font-size: 26px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: 1.1;
}

.detail-score-ring__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

/* 指标网格 */
.detail-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
  width: 100%;
}

.detail-metric {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-md);
}

.detail-metric__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-bottom: 2px;
}

.detail-metric__value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.detail-metric__value--pool {
  color: var(--pool-accent);
}

/* 弹窗动画 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
