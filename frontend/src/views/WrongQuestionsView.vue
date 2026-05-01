<template>
  <div class="wrong-page">
    <section class="card summary-card">
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-value">{{ totalWrong }}</span>
          <span class="summary-label">总错题</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ weakTopics }}</span>
          <span class="summary-label">薄弱专题</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ suggestions }}</span>
          <span class="summary-label">建议优先复习</span>
        </div>
        <div class="summary-item">
          <span class="summary-value summary-value--trend">{{ accuracy }}%</span>
          <span class="summary-label">估算掌握度</span>
        </div>
      </div>
    </section>

    <section class="filters">
      <div class="filter-tabs">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          class="filter-tab"
          :class="{ active: activeFilter === tab.key }"
          @click="activeFilter = tab.key"
        >
          {{ tab.label }}
          <span class="filter-tab__count">{{ tab.count }}</span>
        </button>
      </div>
      <div class="filter-tags">
        <button
          v-for="tag in topicTags"
          :key="tag"
          class="tag-btn"
          :class="{ active: activeTag === tag }"
          @click="activeTag = activeTag === tag ? '' : tag"
        >
          {{ tag }}
        </button>
      </div>
    </section>

    <section class="card wrong-list-card">
      <div class="card__header">
        <h2 class="card__title">
          错题列表
          <span class="card__count">{{ filteredQuestions.length }} 题</span>
        </h2>
        <button class="btn btn--ghost" @click="$router.push('/review')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          进入今日复习
        </button>
      </div>

      <div v-if="loading" class="empty-state">
        <p class="empty-state__text">正在加载错题列表...</p>
      </div>
      <div v-else-if="errorMessage" class="empty-state">
        <p class="empty-state__text">{{ errorMessage }}</p>
      </div>
      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <div class="empty-state__icon">🎉</div>
        <p class="empty-state__text">当前筛选条件下没有错题。</p>
      </div>

      <TransitionGroup v-else name="list" tag="div" class="wrong-list">
        <article v-for="q in filteredQuestions" :key="q.id" class="wrong-item">
          <div class="wrong-item__header">
            <div class="wrong-item__source">
              <span class="badge badge--accent">{{ q.section_title || '未分类' }}</span>
              <span class="wrong-item__origin">{{ q.source_title }}</span>
            </div>
            <div class="wrong-item__meta">
              <span class="wrong-item__wrong-count">已复习 {{ q.review_count }} 次</span>
              <span class="wrong-item__date">下次：{{ formatDateTime(q.next_review_at) }}</span>
            </div>
          </div>
          <p class="wrong-item__question">{{ q.question }}</p>
          <div class="wrong-item__actions">
            <button class="btn btn--ghost" @click="toggleExpand(q.id)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
              {{ expandedIds.has(q.id) ? '收起' : '查看答案' }}
            </button>
            <button class="btn btn--ghost review-btn-sm" @click="$router.push('/review')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              去复习
            </button>
          </div>

          <Transition name="fade">
            <div v-if="expandedIds.has(q.id)" class="wrong-item__answer">
              <div class="answer-divider"></div>
              <div class="answer-content">
                <div v-html="q.answer"></div>
                <div v-if="q.analysis" class="answer-analysis">
                  <strong>补充分析：</strong>
                  <p>{{ q.analysis }}</p>
                </div>
              </div>
            </div>
          </Transition>
        </article>
      </TransitionGroup>
    </section>

    <section class="card suggestion-card" v-if="suggestionsList.length > 0">
      <div class="suggestion-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <h2 class="card__title">复习建议</h2>
      </div>
      <div class="suggestion-list">
        <div class="suggestion-item" v-for="s in suggestionsList" :key="s.topic">
          <div class="suggestion-item__info">
            <span class="suggestion-item__topic">{{ s.topic }}</span>
            <span class="suggestion-item__desc">建议优先处理该专题中的错题</span>
          </div>
          <div class="suggestion-item__count">
            <span class="badge badge--danger">{{ s.count }} 题</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiGet } from '../lib/api'
import { formatDateTime } from '../lib/format'

const activeFilter = ref('all')
const activeTag = ref('')
const expandedIds = ref(new Set())
const loading = ref(true)
const errorMessage = ref('')
const wrongQuestions = ref([])

const filterTabs = computed(() => {
  const recentCount = wrongQuestions.value.filter((item) => item.review_count >= 1 && item.review_count <= 2).length
  const suggestionCount = wrongQuestions.value.filter((item) => item.mastery_level <= 1).length

  return [
    { key: 'all', label: '全部', count: wrongQuestions.value.length },
    { key: 'recent', label: '近期', count: recentCount },
    { key: 'suggestion', label: '建议优先', count: suggestionCount },
  ]
})

const topicTags = computed(() => {
  return [...new Set(wrongQuestions.value.map((item) => item.section_title).filter(Boolean))]
})

const filteredQuestions = computed(() => {
  let list = wrongQuestions.value

  if (activeTag.value) {
    list = list.filter((item) => item.section_title === activeTag.value)
  }
  if (activeFilter.value === 'recent') {
    list = list.filter((item) => item.review_count <= 2)
  }
  if (activeFilter.value === 'suggestion') {
    list = list.filter((item) => item.mastery_level <= 1)
  }

  return list
})

const totalWrong = computed(() => wrongQuestions.value.length)

const weakTopics = computed(() => {
  return new Set(wrongQuestions.value.map((item) => item.section_title || item.source_title)).size
})

const suggestions = computed(() => wrongQuestions.value.filter((item) => item.mastery_level <= 1).length)

const accuracy = computed(() => {
  if (wrongQuestions.value.length === 0) {
    return 100
  }

  const sum = wrongQuestions.value.reduce((acc, item) => acc + item.mastery_level, 0)
  return Math.round((sum / (wrongQuestions.value.length * 4)) * 100)
})

const suggestionsList = computed(() => {
  const bucket = new Map()

  for (const item of wrongQuestions.value.filter((question) => question.mastery_level <= 1)) {
    const topic = item.section_title || item.source_title || '未分类'
    bucket.set(topic, (bucket.get(topic) ?? 0) + 1)
  }

  return [...bucket.entries()].map(([topic, count]) => ({ topic, count }))
})

function toggleExpand(id) {
  const newSet = new Set(expandedIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  expandedIds.value = newSet
}

async function loadWrongQuestions() {
  loading.value = true
  errorMessage.value = ''

  try {
    wrongQuestions.value = await apiGet('/questions/wrong')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

onMounted(loadWrongQuestions)
</script>

<style scoped>
.wrong-page {
  display: grid;
  gap: var(--space-5);
}

.summary-card {
  padding: var(--space-6);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  text-align: center;
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-5);
  }
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.summary-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  line-height: 1;
  color: var(--color-text-primary);
}

.summary-value--trend {
  color: var(--color-warning);
}

.summary-label {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.filters {
  display: grid;
  gap: var(--space-4);
}

.filter-tabs,
.filter-tags {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.filter-tab,
.tag-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border);
  transition: all var(--transition-fast);
}

.tag-btn {
  font-size: var(--text-xs);
  background: var(--color-surface-subtle);
}

.filter-tab:hover,
.tag-btn:hover {
  border-color: var(--color-border-active);
  color: var(--color-text-primary);
}

.filter-tab.active,
.tag-btn.active {
  background: var(--color-accent-subtle);
  border-color: var(--color-accent-border);
  color: var(--color-accent);
}

.filter-tab__count {
  font-size: var(--text-xs);
  opacity: 0.7;
}

.wrong-list-card,
.suggestion-card {
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
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
}

.card__count {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.wrong-list,
.suggestion-list {
  display: grid;
  gap: var(--space-3);
}

.wrong-item {
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.wrong-item:hover {
  border-color: var(--color-border-active);
  background: var(--color-surface-subtle);
}

.wrong-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
}

.wrong-item__source,
.wrong-item__meta,
.wrong-item__actions,
.suggestion-header,
.suggestion-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.wrong-item__origin,
.wrong-item__meta {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.wrong-item__wrong-count {
  color: var(--color-danger);
  font-weight: 600;
}

.wrong-item__question {
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: var(--leading-relaxed);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.review-btn-sm {
  font-size: var(--text-xs) !important;
}

.wrong-item__answer {
  overflow: hidden;
}

.answer-divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-4) 0;
}

.answer-content {
  display: grid;
  gap: var(--space-3);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text-primary);
}

.answer-content :deep(ul) {
  padding-left: var(--space-5);
  margin: var(--space-2) 0;
  list-style: disc;
}

.answer-content :deep(li) {
  margin-bottom: var(--space-1);
}

.answer-content :deep(strong) {
  font-weight: 600;
  color: var(--color-accent);
}

.answer-analysis {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-subtle);
}

.suggestion-item {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-subtle);
  border: 1px solid var(--color-border-light);
}

.suggestion-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.suggestion-item__topic {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.suggestion-item__desc {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.list-enter-active,
.list-leave-active,
.fade-enter-active,
.fade-leave-active {
  transition: all var(--transition-normal);
}

.list-enter-from,
.list-leave-to,
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 600px) {
  .wrong-item__header,
  .card__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
