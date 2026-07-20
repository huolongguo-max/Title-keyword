<template>
  <button
    :class="['mac-btn', `mac-btn--${variant}`, { 'mac-btn--loading': loading }]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="mac-btn__spinner" />
    <span class="mac-btn__text">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
/**
 * MacButton - macOS 风格按钮
 * @variant primary | secondary | danger
 * 三种样式：主按钮（蓝色）、次按钮（灰色边框）、危险按钮（红色）
 */
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'danger'
    disabled?: boolean
    loading?: boolean
  }>(),
  {
    variant: 'primary',
    disabled: false,
    loading: false,
  }
)

defineEmits<{
  click: []
}>()
</script>

<style scoped>
.mac-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  height: 32px;
  padding: 0 16px;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  user-select: none;
  transition: all var(--transition-fast);
  outline: none;
  white-space: nowrap;
}

.mac-btn:active {
  transform: scale(0.97);
}

.mac-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ---- 主按钮（苹果蓝） ---- */
.mac-btn--primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  box-shadow: 0 1px 3px rgba(0, 122, 255, 0.3);
}
.mac-btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  box-shadow: 0 2px 6px rgba(0, 122, 255, 0.35);
}
.mac-btn--primary:active:not(:disabled) {
  background: var(--color-primary-active);
}

/* ---- 次按钮（灰色边框） ---- */
.mac-btn--secondary {
  background: var(--color-bg-white);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}
.mac-btn--secondary:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.16);
}
.mac-btn--secondary:active:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
}

/* ---- 危险按钮（苹果红） ---- */
.mac-btn--danger {
  background: var(--color-danger);
  color: var(--color-text-inverse);
  box-shadow: 0 1px 3px rgba(255, 59, 48, 0.3);
}
.mac-btn--danger:hover:not(:disabled) {
  background: var(--color-danger-hover);
  box-shadow: 0 2px 6px rgba(255, 59, 48, 0.35);
}

/* ---- 加载动画 ---- */
.mac-btn__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
