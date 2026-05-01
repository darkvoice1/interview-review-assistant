<template>
  <div class="stats-page">
    <section class="metrics-grid">
      <div class="card metric-card" v-for="m in metrics" :key="m.label">
        <div class="metric-card__icon" v-html="m.icon"></div>
        <div class="metric-card__body">
          <span class="metric-card__value">{{ m.value }}</span>
          <span class="metric-card__label">{{ m.label }}</span>
        </div>
        <div class="metric-card__change" :class="m.changeType">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline v-if="m.changeType === 'up'" points="18 15 12 9 6 15"/>
            <polyline v-else points="6 9 12 15 18 9"/>
          </svg>
          {{ m.change }}
        </div>
      </div>
    </section>

    <div v-if="loading" class="card panel-empty">
      正在加载统计数据...
    </div>
    <div v-else-if="errorMessage" class="card panel-empty panel-empty--error">
      {{ errorMessage }}
    </div>
    <template v-else>
      <div class="stats__cols">
        <section class="card chart-card">
          <div class="card__header">
            <h2 class="card__title">掌握程度分布</h2>
          </div>
          <div class="distribution-wrapper">
            <div class="distribution-bar">
              <div
                v-for="item in masteryDistribution"
                :key="item.label"
                class="distribution-segment"
                :style="{ width: item.percent + '%', background: item.color }"
              ></div>
            </div>
            <div class="distribution-legend">
              <div v-for="item in masteryDistribution" :key="item.label" class="legend-item">
                <span class="legend-dot" :style="{ background: item.color }"></span>
                <span class="legend-label">{{ item.label }}</span>
                <span class="legend-value">{{ item.percent }}%</span>
              </div>
            </div>
          </div>
        </section>

        <section class="card chart-card">
          <div class="card__header">
            <h2 class="card__title">复习数据概览</h2>
            <span class="card__trend badge badge--accent">实时</span>
          </div>
          <div class="weekly-chart">
            <div class="chart-summary">
              <div class="chart-stat">
                <span class="chart-stat__value">{{ dueReviewCount }}</span>
                <span class="chart-stat__label">待复习题目</span>
              </div>
              <div class="chart-stat">
                <span class="chart-stat__value">{{ reviewedTodayCount }}</span>
                <span class="chart-stat__label">今日已复习</span>
              </div>
              <div class="chart-stat">
                <span class="chart-stat__value">{{ reviewRecordCount }}</span>
                <span class="chart-stat__label">累计复习次数</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="card topic-card">
        <div class="card__header">
          <h2 class="card__title">专题掌握详情</h2>
        </div>
        <div v-if="topicMastery.length === 0" class="empty-state">
          <p class="empty-state__text">还没有题目或复习记录，暂时无法生成专题统计。</p>
        </div>
        <div v-else class="topic-table">
          <div class="topic-row topic-row--header">
            <span class="topic-cell topic-cell--name">专题</span>
            <span class="topic-cell topic-cell--count">题目数</span>
            <span class="topic-cell topic-cell--rate">掌握率</span>
            <span class="topic-cell topic-cell--status">状态</span>
          </div>
          <div v-for="topic in topicMastery" :key="topic.name" class="topic-row">
            <span class="topic-cell topic-cell--name">{{ topic.name }}</span>
            <span class="topic-cell topic-cell--count">{{ topic.count }}</span>
            <span class="topic-cell topic-cell--rate">
              <div class="rate-bar">
                <div class="rate-bar__fill" :style="{ width: topic.rate + '%', background: getRateColor(topic.rate) }"></div>
              </div>
              <span class="rate-value">{{ topic.rate }}%</span>
            </span>
            <span class="topic-cell topic-cell--status">
              <span class="badge" :class="getStatusBadge(topic.rate)">{{ getStatusLabel(topic.rate) }}</span>
            </span>
          </div>
        </div>
      </section>

      <section class="card summary-stats-card">
        <div class="summary-stats-grid">
          <div class="summary-stat">
            <span class="summary-stat__icon">文</span>
            <div class="summary-stat__body">
              <span class="summary-stat__value">{{ documentCount }}</span>
              <span class="summary-stat__label">文档数</span>
            </div>
          </div>
          <div class="summary-stat">
            <span class="summary-stat__icon">题</span>
            <div class="summary-stat__body">
              <span class="summary-stat__value">{{ questionCount }}</span>
              <span class="summary-stat__label">累计题目</span>
            </div>
          </div>
          <div class="summary-stat">
            <span class="summary-stat__icon">错</span>
            <div class="summary-stat__body">
              <span class="summary-stat__value">{{ wrongQuestionCount }}</span>
              <span class="summary-stat__label">错题数</span>
            </div>
          </div>
          <div class="summary-stat">
            <span class="summary-stat__icon">今</span>
            <div class="summary-stat__body">
              <span class="summary-stat__value">{{ reviewedTodayCount }}</span>
              <span class="summary-stat__label">今日已复习</span>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiGet } from '../lib/api'

const loading = ref(true)
const errorMessage = ref('')
const statsResponse = ref(null)
const questions = ref([])
const wrongQuestions = ref([])

const documentCount = computed(() => statsResponse.value?.document_count ?? 0)
const questionCount = computed(() => statsResponse.value?.question_count ?? 0)
const dueReviewCount = computed(() => statsResponse.value?.due_review_count ?? 0)
const wrongQuestionCount = computed(() => statsResponse.value?.wrong_question_count ?? 0)
const reviewRecordCount = computed(() => statsResponse.value?.review_record_count ?? 0)
const reviewedTodayCount = computed(() => statsResponse.value?.reviewed_today_count ?? 0)

const masteredPercent = computed(() => {
  if (questionCount.value === 0) {
    return 0
  }
  return Math.round(((questionCount.value - wrongQuestionCount.value) / questionCount.value) * 100)
})

const metrics = computed(() => [
  {
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    value: String(reviewRecordCount.value),
    label: '累计复习次数',
    change: reviewedTodayCount.value > 0 ? `今日 ${reviewedTodayCount.value}` : '今日 0',
    changeType: 'up',
  },
  {
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>',
    value: `${masteredPercent.value}%`,
    label: '整体掌握率',
    change: wrongQuestionCount.value > 0 ? `错题 ${wrongQuestionCount.value}` : '状态良好',
    changeType: wrongQuestionCount.value > 0 ? 'down' : 'up',
  },
  {
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>',
    value: String(wrongQuestionCount.value),
    label: '当前错题量',
    change: dueReviewCount.value > 0 ? `待复习 ${dueReviewCount.value}` : '已清空',
    changeType: wrongQuestionCount.value > 0 ? 'down' : 'up',
  },
  {
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    value: String(questionCount.value),
    label: '题库总量',
    change: `${documentCount.value} 份文档`,
    changeType: 'up',
  },
])

const masteryDistribution = computed(() => {
  if (questions.value.length === 0) {
    return [
      { label: '已掌握', percent: 0, color: 'var(--color-know)' },
      { label: '需加强', percent: 0, color: 'var(--color-dont-know)' },
    ]
  }

  const mastered = Math.max(0, questionCount.value - wrongQuestionCount.value)
  const weak = wrongQuestionCount.value

  return [
    { label: '已掌握', percent: Math.round((mastered / questionCount.value) * 100), color: 'var(--color-know)' },
    { label: '需加强', percent: Math.round((weak / questionCount.value) * 100), color: 'var(--color-dont-know)' },
  ]
})

const topicMastery = computed(() => {
  const bucket = new Map()

  for (const question of questions.value) {
    const key = question.section_title || '未分类'
    const current = bucket.get(key) ?? { name: key, count: 0, wrong: 0 }
    current.count += 1
    bucket.set(key, current)
  }

  for (const wrong of wrongQuestions.value) {
    const key = wrong.section_title || '未分类'
    const current = bucket.get(key) ?? { name: key, count: 0, wrong: 0 }
    current.wrong += 1
    bucket.set(key, current)
  }

  return [...bucket.values()]
    .map((item) => ({
      name: item.name,
      count: item.count,
      rate: item.count === 0 ? 0 : Math.max(0, Math.round(((item.count - item.wrong) / item.count) * 100)),
    }))
    .sort((a, b) => a.rate - b.rate)
})

function getRateColor(rate) {
  if (rate >= 80) return 'var(--color-know)'
  if (rate >= 60) return 'var(--color-know-light)'
  if (rate >= 40) return 'var(--color-fuzzy)'
  return 'var(--color-dont-know)'
}

function getStatusBadge(rate) {
  if (rate >= 80) return 'badge--know'
  if (rate >= 60) return 'badge--know-light'
  if (rate >= 40) return 'badge--fuzzy'
  return 'badge--danger'
}

function getStatusLabel(rate) {
  if (rate >= 80) return '良好'
  if (rate >= 60) return '稳定'
  if (rate >= 40) return '需加强'
  return '薄弱'
}

async function loadStats() {
  loading.value = true
  errorMessage.value = ''

  try {
    const [statsData, questionData, wrongData] = await Promise.all([
      apiGet('/review/stats'),
      apiGet('/questions'),
      apiGet('/questions/wrong'),
    ])

    statsResponse.value = statsData
    questions.value = questionData
    wrongQuestions.value = wrongData
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.stats-page {
  display: grid;
  gap: var(--space-5);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

@media (max-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

.metric-card {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.metric-card__icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.metric-card__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-card__value {
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  line-height: 1;
  color: var(--color-text-primary);
}

.metric-card__label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.metric-card__change {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: var(--text-xs);
  font-weight: 600;
}

.metric-card__change.up {
  color: var(--color-know);
}

.metric-card__change.down {
  color: var(--color-dont-know);
}

.panel-empty {
  padding: var(--space-8);
  text-align: center;
}

.panel-empty--error {
  color: var(--color-danger);
  background: var(--color-danger-subtle);
}

.stats__cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

@media (max-width: 768px) {
  .stats__cols {
    grid-template-columns: 1fr;
  }
}

.chart-card,
.topic-card,
.summary-stats-card {
  padding: var(--space-6);
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
}

.card__trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: var(--text-xs);
  font-weight: 600;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
}

.distribution-wrapper {
  display: grid;
  gap: var(--space-5);
}

.distribution-bar {
  display: flex;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-border);
}

.distribution-segment {
  transition: width var(--transition-slow);
}

.distribution-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.legend-value {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text-primary);
}

.weekly-chart,
.chart-summary {
  display: flex;
  gap: var(--space-6);
}

.chart-summary {
  flex-wrap: wrap;
}

.chart-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chart-stat__value {
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  color: var(--color-text-primary);
}

.chart-stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.topic-table {
  display: grid;
  gap: var(--space-2);
}

.topic-row {
  display: grid;
  grid-template-columns: 1.5fr 80px 1.2fr 80px;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.topic-row--header {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: var(--space-2) var(--space-4);
}

.topic-row:not(.topic-row--header):hover {
  background: var(--color-surface-subtle);
}

.topic-cell--name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.topic-cell--count {
  color: var(--color-text-secondary);
}

.topic-cell--rate {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.rate-bar {
  flex: 1;
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.rate-bar__fill {
  height: 100%;
  border-radius: 2px;
  transition: width var(--transition-slow);
}

.rate-value {
  font-weight: 600;
  color: var(--color-text-primary);
  min-width: 36px;
  text-align: right;
}

.summary-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

@media (max-width: 768px) {
  .summary-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .topic-row {
    grid-template-columns: 1fr 60px 80px;
  }

  .topic-cell--status,
  .topic-row--header .topic-cell--status {
    display: none;
  }
}

.summary-stat {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-subtle);
}

.summary-stat__icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-weight: 700;
}

.summary-stat__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-stat__value {
  font-size: var(--text-xl);
  font-weight: 700;
}

.summary-stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.badge--know {
  background: var(--color-know-light);
  color: var(--color-know);
}

.badge--know-light {
  background: var(--color-know-light);
  color: var(--color-know);
}

.badge--fuzzy {
  background: var(--color-fuzzy-light);
  color: var(--color-fuzzy);
}
</style>
