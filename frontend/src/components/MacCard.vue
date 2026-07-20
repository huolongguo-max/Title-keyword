<template>
  <div :class="['mac-card', { 'mac-card--hover': hoverable }]">
    <div v-if="title || $slots.header" class="mac-card__header">
      <h3 v-if="title" class="mac-card__title">{{ title }}</h3>
      <slot name="header" />
    </div>
    <div class="mac-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="mac-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * MacCard - macOS 毛玻璃风格内容卡片
 * 支持标题、header/footer 插槽、悬停效果
 */
withDefaults(
  defineProps<{
    title?: string
    hoverable?: boolean
  }>(),
  {
    title: '',
    hoverable: false,
  }
)
</script>

<style scoped>
.mac-card {
  background: var(--color-bg-card);
  backdrop-filter: var(--blur-card);
  -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  overflow: hidden;
}

.mac-card--hover:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: rgba(0, 0, 0, 0.12);
}

.mac-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.mac-card__title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.mac-card__body {
  padding: var(--space-lg);
}

.mac-card__footer {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-border);
  background: rgba(0, 0, 0, 0.02);
}
</style>
