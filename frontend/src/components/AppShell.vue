<template>
  <div class="shell">
    <header class="mobile-header">
      <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="菜单">
        <span class="hamburger" :class="{ open: mobileMenuOpen }">
          <span></span><span></span><span></span>
        </span>
      </button>
      <span class="mobile-logo">面经复习助手</span>
    </header>

    <div
      v-if="mobileMenuOpen"
      class="overlay"
      @click="mobileMenuOpen = false"
    ></div>

    <aside class="sidebar" :class="{ open: mobileMenuOpen }">
      <div class="sidebar__brand">
        <div class="sidebar__logo">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="2" width="24" height="24" rx="6" fill="#1a6d5e" opacity="0.12" />
            <path
              d="M8 10h12M8 14h8M8 18h10"
              stroke="#1a6d5e"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <circle cx="22" cy="9" r="3.5" fill="#1a6d5e" opacity="0.2" />
          </svg>
        </div>
        <span class="sidebar__title">面经复习助手</span>
      </div>

      <nav class="sidebar__nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          @click="mobileMenuOpen = false"
        >
          <span class="nav-item__icon" v-html="item.icon"></span>
          <span class="nav-item__label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-item__badge">{{ item.badge }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar__footer">
        <div class="sidebar__status">
          <span class="status-dot"></span>
          <span class="status-text">已就绪</span>
        </div>
      </div>
    </aside>

    <main class="main">
      <div class="main__header">
        <h1 class="main__title">{{ currentPageTitle }}</h1>
        <p class="main__subtitle">{{ currentPageSubtitle }}</p>
      </div>
      <div class="main__content">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, RouterLink, RouterView } from 'vue-router'

const route = useRoute()
const mobileMenuOpen = ref(false)

const navItems = [
  {
    path: '/',
    label: '总览',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  },
  {
    path: '/documents',
    label: '文档',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
  },
  {
    path: '/review',
    label: '今日复习',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  },
  {
    path: '/wrong-questions',
    label: '错题',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  },
  {
    path: '/statistics',
    label: '统计',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  },
  {
    path: '/settings',
    label: '设置',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
  },
]

const pageMeta = {
  '/': { title: '总览', subtitle: '复习驾驶舱 · 今日学习状态一览' },
  '/documents': { title: '文档管理', subtitle: '导入和管理你的面经笔记' },
  '/review': { title: '今日复习', subtitle: '一次一题 · 专注复习' },
  '/wrong-questions': { title: '错题复盘', subtitle: '回顾薄弱知识点' },
  '/statistics': { title: '学习统计', subtitle: '复习数据与趋势概览' },
  '/settings': { title: '模型设置', subtitle: '管理厂商配置并测试连接状态' },
}

const currentPageTitle = computed(() => {
  const meta = pageMeta[route.path]
  return meta ? meta.title : '面经复习助手'
})

const currentPageSubtitle = computed(() => {
  const meta = pageMeta[route.path]
  return meta ? meta.subtitle : ''
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}

.mobile-header {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 56px;
  padding: 0 var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  align-items: center;
  gap: var(--space-3);
}

.mobile-logo {
  font-weight: 700;
  font-size: var(--text-base);
  letter-spacing: var(--tracking-tight);
  color: var(--color-text-primary);
}

.mobile-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
}

.mobile-menu-btn:hover {
  background: var(--color-surface-subtle);
}

.hamburger {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 18px;
}

.hamburger span {
  display: block;
  height: 2px;
  background: var(--color-text-primary);
  border-radius: 1px;
  transition: all var(--transition-fast);
}

.hamburger.open span:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}

.hamburger.open span:nth-child(2) {
  opacity: 0;
}

.hamburger.open span:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

.overlay {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(28, 28, 30, 0.3);
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 50;
  width: 220px;
  padding: var(--space-6) var(--space-3);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: transform var(--transition-normal);
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3) var(--space-8);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-4);
}

.sidebar__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar__title {
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  color: var(--color-text-primary);
}

.sidebar__nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
}

.nav-item:hover {
  background: var(--color-surface-subtle);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-weight: 600;
}

.nav-item__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-item__label {
  flex: 1;
}

.nav-item__badge {
  padding: 1px 7px;
  border-radius: var(--radius-full);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-size: var(--text-xs);
  font-weight: 700;
}

.sidebar__footer {
  padding: var(--space-4) var(--space-3) 0;
  border-top: 1px solid var(--color-border-light);
  margin-top: auto;
}

.sidebar__status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent);
}

.status-text {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.main {
  flex: 1;
  margin-left: 220px;
  padding: var(--space-10) var(--space-8);
  min-height: 100vh;
}

.main__header {
  margin-bottom: var(--space-8);
}

.main__title {
  font-size: var(--text-3xl);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-tight);
  color: var(--color-text-primary);
}

.main__subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-1);
  font-weight: 400;
}

.main__content {
  animation: contentEnter var(--transition-slow) ease-out;
}

@keyframes contentEnter {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .mobile-header {
    display: flex;
  }

  .overlay {
    display: block;
  }

  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .main {
    margin-left: 0;
    padding: 72px var(--space-4) var(--space-8);
  }

  .main__header {
    margin-bottom: var(--space-5);
  }

  .main__title {
    font-size: var(--text-2xl);
  }
}
</style>