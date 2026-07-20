<template>
  <div class="app-window">
    <!-- ==================== 顶部标题栏 ==================== -->
    <header class="titlebar">
      <div class="titlebar__left">
        <!-- macOS 红绿灯窗口按钮占位 -->
        <span class="traffic-light traffic-light--close" />
        <span class="traffic-light traffic-light--minimize" />
        <span class="traffic-light traffic-light--zoom" />
      </div>
      <div class="titlebar__center">
        <span class="titlebar__title">Title-Keyword 智能分析平台</span>
      </div>
      <div class="titlebar__right">
        <!-- 预留右侧操作区 -->
      </div>
    </header>

    <!-- ==================== 主体区域 ==================== -->
    <div class="app-body">
      <!-- 左侧导航栏 -->
      <aside class="sidebar">
        <nav class="sidebar__nav">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="sidebar__item"
            active-class="sidebar__item--active"
          >
            <span class="sidebar__icon">{{ item.icon }}</span>
            <span class="sidebar__label">{{ item.label }}</span>
          </router-link>
        </nav>

        <!-- 底部状态信息 -->
        <div class="sidebar__footer">
          <div class="sidebar__status">
            <span class="status-dot status-dot--online" />
            <span class="status-text">服务运行中</span>
          </div>
          <p class="sidebar__version">v1.0.0</p>
        </div>
      </aside>

      <!-- 右侧主内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * App.vue - macOS 风格应用主布局
 * 顶部标题栏 + 左侧导航 + 右侧内容区
 */

interface MenuItem {
  path: string
  label: string
  icon: string
}

const menuItems: MenuItem[] = [
  { path: '/upload', label: '上传解析', icon: '📤' },
  { path: '/keywords', label: '词池分类', icon: '🏷️' },
  { path: '/risk', label: '风险检测', icon: '🛡️' },
  { path: '/generate', label: '标题生成', icon: '✨' },
  { path: '/optimize', label: '批量优化', icon: '🚀' },
]
</script>

<style scoped>
/* ============================================================
   应用窗口布局
   ============================================================ */
.app-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg);
}

/* ==================== 标题栏 ==================== */
.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--titlebar-height);
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: var(--blur-sidebar);
  -webkit-backdrop-filter: var(--blur-sidebar);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  -webkit-app-region: drag;    /* macOS 窗口拖拽区域 */
  user-select: none;
}

.titlebar__left,
.titlebar__center,
.titlebar__right {
  display: flex;
  align-items: center;
  flex: 1;
}

.titlebar__left {
  gap: 8px;
}

.titlebar__center {
  justify-content: center;
}

.titlebar__right {
  justify-content: flex-end;
}

.titlebar__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

/* macOS 红绿灯占位 */
.traffic-light {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  -webkit-app-region: no-drag;
}

.traffic-light--close {
  background: #FF5F57;
}

.traffic-light--minimize {
  background: #FEBC2E;
}

.traffic-light--zoom {
  background: #28C840;
}

/* ==================== 主体区域 ==================== */
.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ==================== 侧边导航栏 ==================== */
.sidebar {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: var(--sidebar-width);
  padding: var(--space-md) var(--space-sm);
  background: rgba(245, 245, 247, 0.80);
  backdrop-filter: var(--blur-sidebar);
  -webkit-backdrop-filter: var(--blur-sidebar);
  border-right: 1px solid var(--color-border);
  flex-shrink: 0;
  overflow-y: auto;
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 导航菜单项 */
.sidebar__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-regular);
  color: var(--color-text-primary);
  text-decoration: none;
  transition: all var(--transition-fast);
  user-select: none;
}

.sidebar__item:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-text-primary);
}

.sidebar__item--active {
  background: rgba(0, 122, 255, 0.10);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
}

.sidebar__item--active:hover {
  background: rgba(0, 122, 255, 0.15);
  color: var(--color-primary);
}

.sidebar__icon {
  font-size: 16px;
  width: 22px;
  text-align: center;
  flex-shrink: 0;
}

.sidebar__label {
  white-space: nowrap;
}

/* 侧边栏底部 */
.sidebar__footer {
  padding: var(--space-md) var(--space-sm) var(--space-xs);
  border-top: 1px solid var(--color-border);
}

.sidebar__status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.status-dot--online {
  background: var(--color-success);
}

.status-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.sidebar__version {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* ==================== 主内容区 ==================== */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xl);
  background: var(--color-bg);
}

/* ==================== 路由切换动画 ==================== */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
