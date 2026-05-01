<template>
  <div class="dashboard">
    <section class="stats-grid">
      <article class="stat-card card" v-for="stat in stats" :key="stat.label">
        <div class="stat-card__icon" v-html="stat.icon"></div>
        <div class="stat-card__body">
          <span class="stat-card__value">{{ stat.value }}</span>
          <span class="stat-card__label">{{ stat.label }}</span>
        </div>
        <div class="stat-card__trend" :class="stat.trend">
          <span>{{ stat.trendLabel }}</span>
        </div>
      </article>
    </section>

    <div class="dashboard__cols">
      <section class="card weak-section">
        <div class="card__header">
          <h2 class="card__title">薄弱知识点</h2>
          <span class="card__action" @click="$router.push('/wrong-questions')">查看错题 →</span>
        </div>
        <div v-if="loading" class="empty-state">
          <p class="empty-state__text">正在加载首页数据...</p>
        </div>
        <div v-else-if="weakPoints.length === 0" class="empty-state">
          <p class="empty-state__text">还没有错题记录，继续保持。</p>
        </div>
        <div v-else class="weak-list">
          <div v-for="item in weakPoints" :key="item.topic" class="weak-item">
            <div class="weak-item__info">
              <span class="weak-item__topic">{{ item.topic }}</span>
              <span class="weak-item__count">{{ item.count }} 题需要关注</span>
            </div>
            <div class="weak-item__bar">
              <div class="weak-item__fill" :style="{ width: item.rate + '%' }"></div>
            </div>
            <span class="weak-item__rate">{{ item.rate }}%</span>
          </div>
        </div>
      </section>

      <section class="card progress-section">
        <div class="card__header">
          <h2 class="card__title">今日复习进度</h2>
          <span class="card__action badge badge--accent">{{ reviewProgress.remaining }} 题待完成</span>
        </div>
        <div v-if="loading" class="empty-state">
          <p class="empty-state__text">正在加载今日题单...</p>
        </div>
        <template v-else>
          <div class="progress-ring-wrapper">
            <div class="progress-ring">
              <svg viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="var(--color-border)" stroke-width="6" />
                <circle
                  cx="60"
                  cy="60"
                  r="52"
                  fill="none"
                  stroke="var(--color-accent)"
                  stroke-width="6"
                  stroke-linecap="round"
                  :stroke-dasharray="circumference"
                  :stroke-dashoffset="progressOffset"
                  transform="rotate(-90 60 60)"
                  class="progress-circle"
                />
              </svg>
              <div class="progress-ring__center">
                <span class="progress-ring__pct">{{ reviewProgress.percentage }}%</span>
                <span class="progress-ring__label">完成</span>
              </div>
            </div>
            <div class="progress-breakdown">
              <div class="breakdown-item">
                <span class="breakdown-dot" style="background: var(--color-know)"></span>
                <span class="breakdown-label">今日待复习</span>
                <span class="breakdown-value">{{ reviewProgress.remaining }}</span>
              </div>
              <div class="breakdown-item">
                <span class="breakdown-dot" style="background: var(--color-fuzzy)"></span>
                <span class="breakdown-label">已复习</span>
                <span class="breakdown-value">{{ reviewProgress.completed }}</span>
              </div>
              <div class="breakdown-item">
                <span class="breakdown-dot" style="background: var(--color-dont-know)"></span>
                <span class="breakdown-label">总题目数</span>
                <span class="breakdown-value">{{ reviewProgress.total }}</span>
              </div>
            </div>
          </div>
          <button class="btn btn--primary start-review-btn" @click="$router.push('/review')" :disabled="reviewProgress.remaining === 0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            开始今日复习
          </button>
        </template>
      </section>
    </div>

    <section class="card recent-docs">
      <div class="card__header">
        <h2 class="card__title">最近导入</h2>
        <span class="card__action" @click="$router.push('/documents')">管理文档 →</span>
      </div>
      <div v-if="loading" class="empty-state">
        <p class="empty-state__text">正在加载文档...</p>
      </div>
      <div v-else-if="recentDocs.length === 0" class="empty-state">
        <p class="empty-state__text">还没有导入文档，先去上传一个 Markdown 文件吧。</p>
      </div>
      <div v-else class="doc-list">
        <div v-for="doc in recentDocs" :key="doc.id" class="doc-item">
          <div class="doc-item__icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div class="doc-item__info">
            <span class="doc-item__name">{{ doc.name }}</span>
            <span class="doc-item__meta">{{ doc.date }}</span>
          </div>
          <span class="badge badge--accent">已导入</span>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="page-error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiGet } from '../lib/api'
import { formatShortDate } from '../lib/format'

const loading = ref(true)
const errorMessage = ref('')
const statsResponse = ref(null)
const wrongQuestions = ref([])
const documents = ref([])

const stats = computed(() => {
  const data = statsResponse.value
  if (!data) {
    return []
  }

  return [
    {
      icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
      value: String(data.due_review_count),
      label: '今日待复习',
      trend: data.due_review_count > 0 ? 'up' : 'neutral',
      trendLabel: data.due_review_count > 0 ? '建议优先完成' : '今日已清空',
    },
    {
      icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
      value: String(data.document_count),
      label: '已导入文档',
      trend: 'neutral',
      trendLabel: `共 ${data.question_count} 道题`,
    },
    {
      icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      value: String(data.wrong_question_count),
      label: '待复习错题',
      trend: data.wrong_question_count > 0 ? 'down' : 'neutral',
      trendLabel: data.wrong_question_count > 0 ? '需要重点关注' : '暂无错题',
    },
    {
      icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
      value: String(data.review_record_count),
      label: '累计复习次数',
      trend: 'up',
      trendLabel: `今天完成 ${data.reviewed_today_count} 次`,
    },
  ]
})

const weakPoints = computed(() => {
  const bucket = new Map()

  for (const item of wrongQuestions.value) {
    const topic = item.section_title || item.source_title || '未分类'
    const current = bucket.get(topic) ?? { topic, count: 0, score: 0 }
    current.count += 1
    current.score += Math.max(0, 100 - item.mastery_level * 25)
    bucket.set(topic, current)
  }

  return [...bucket.values()]
    .map((item) => ({
      topic: item.topic,
      count: item.count,
      rate: Math.min(100, Math.max(20, Math.round(item.score / item.count))),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 4)
})

const reviewProgress = computed(() => {
  const data = statsResponse.value
  if (!data) {
    return { remaining: 0, completed: 0, total: 0, percentage: 0 }
  }

  const remaining = data.due_review_count
  const completed = data.reviewed_today_count
  const total = remaining + completed
  const percentage = total === 0 ? 0 : Math.round((completed / total) * 100)

  return { remaining, completed, total, percentage }
})

const circumference = 2 * Math.PI * 52

const progressOffset = computed(() => {
  return circumference - (reviewProgress.value.percentage / 100) * circumference
})

const recentDocs = computed(() => {
  return [...documents.value]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 4)
    .map((doc) => ({
      id: doc.id,
      name: doc.title,
      date: formatShortDate(doc.created_at),
    }))
})

async function loadDashboard() {
  loading.value = true
  errorMessage.value = ''

  try {
    const [statsData, wrongData, documentsData] = await Promise.all([
      apiGet('/review/stats'),
      apiGet('/questions/wrong'),
      apiGet('/documents'),
    ])

    statsResponse.value = statsData
    wrongQuestions.value = wrongData
    documents.value = documentsData
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: var(--space-6);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--color-accent);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-card__icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.stat-card__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-card__value {
  font-size: var(--text-3xl);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  line-height: 1;
  color: var(--color-text-primary);
}

.stat-card__label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.stat-card__trend {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-tertiary);
}

.stat-card__trend.up {
  color: var(--color-accent);
}

.stat-card__trend.down {
  color: var(--color-danger);
}

.card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
  gap: var(--space-3);
}

.card__title {
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  color: var(--color-text-primary);
}

.card__action {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: color var(--transition-fast);
  font-weight: 500;
}

.card__action:hover {
  color: var(--color-accent);
}

.dashboard__cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

@media (max-width: 768px) {
  .dashboard__cols {
    grid-template-columns: 1fr;
  }
}

.weak-section {
  padding: var(--space-6);
}

.weak-list {
  display: grid;
  gap: var(--space-4);
}

.weak-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-2) var(--space-3);
  align-items: center;
}

.weak-item__info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.weak-item__topic {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.weak-item__count {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.weak-item__bar {
  grid-column: 1 / -1;
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.weak-item__fill {
  height: 100%;
  background: var(--color-danger);
  border-radius: 2px;
  transition: width var(--transition-slow);
}

.weak-item__rate {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  justify-self: end;
}

.progress-section {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
}

.progress-ring-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-4) 0;
}

@media (max-width: 480px) {
  .progress-ring-wrapper {
    flex-direction: column;
    gap: var(--space-6);
  }
}

.progress-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.progress-ring svg {
  width: 100%;
  height: 100%;
}

.progress-circle {
  transition: stroke-dashoffset var(--transition-slow);
}

.progress-ring__center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.progress-ring__pct {
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  line-height: 1;
  color: var(--color-text-primary);
}

.progress-ring__label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.progress-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.breakdown-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.breakdown-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  flex: 1;
}

.breakdown-value {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.start-review-btn {
  margin-top: auto;
  width: 100%;
  justify-content: center;
  padding: var(--space-3);
  border-radius: var(--radius-md);
}

.start-review-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.recent-docs {
  padding: var(--space-6);
}

.doc-list {
  display: grid;
  gap: var(--space-2);
}

.doc-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
  cursor: default;
}

.doc-item:hover {
  background: var(--color-surface-subtle);
}

.doc-item__icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-subtle);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.doc-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.doc-item__name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-item__meta {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.page-error {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-danger-subtle);
  color: var(--color-danger);
  font-size: var(--text-sm);
}
</style>
