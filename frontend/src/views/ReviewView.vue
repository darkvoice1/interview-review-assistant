<template>
  <div class="review-page">
    <div v-if="loading" class="card review-empty">
      <p class="review-empty__title">正在加载今日题单...</p>
      <p class="review-empty__desc">后端会根据复习计划返回今天需要处理的题目。</p>
    </div>

    <div v-else-if="errorMessage" class="card review-empty review-empty--error">
      <p class="review-empty__title">加载失败</p>
      <p class="review-empty__desc">{{ errorMessage }}</p>
      <button class="btn btn--primary" @click="loadTodayReview">重新加载</button>
    </div>

    <div v-else-if="questions.length === 0" class="card review-empty">
      <p class="review-empty__title">今天没有待复习题目</p>
      <p class="review-empty__desc">说明你今天的题单已经清空，或者还没有上传并生成题目。</p>
    </div>

    <template v-else>
      <div class="review-progress">
        <div class="review-progress__info">
          <span class="review-progress__label">复习进度</span>
          <span class="review-progress__count">{{ currentIndex + 1 }} / {{ questions.length }}</span>
        </div>
        <div class="review-progress__bar">
          <div class="review-progress__fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
      </div>

      <Transition name="card-slide" mode="out-in">
        <article class="question-card card" :key="currentQuestion.question_id">
          <div class="question-card__source">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span>{{ currentQuestion.source_title }}</span>
            <span class="question-card__tag badge badge--accent">{{ formatDifficulty(currentQuestion.difficulty) }}</span>
          </div>

          <h2 class="question-card__title">{{ currentQuestion.question }}</h2>
          <p class="question-card__due">计划时间：{{ formatDateTime(currentQuestion.due_at) }}</p>

          <div class="question-card__actions">
            <button
              class="review-btn review-btn--dont-know"
              :class="{ selected: selectedAnswer === '不会' }"
              :disabled="submitting"
              @click="handleAnswer('不会')"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              <span>不会</span>
            </button>
            <button
              class="review-btn review-btn--fuzzy"
              :class="{ selected: selectedAnswer === '模糊' }"
              :disabled="submitting"
              @click="handleAnswer('模糊')"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12.01" y2="16"/><line x1="12" y1="8" x2="12" y2="12"/></svg>
              <span>模糊</span>
            </button>
            <button
              class="review-btn review-btn--know"
              :class="{ selected: selectedAnswer === '会' }"
              :disabled="submitting"
              @click="handleAnswer('会')"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>
              <span>会</span>
            </button>
          </div>

          <div class="question-card__answer-toggle" @click="toggleAnswer">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
              stroke-linejoin="round"
              :style="{ transform: showAnswer ? 'rotate(180deg)' : '' }"
            >
              <polyline points="6 9 12 15 18 9"/>
            </svg>
            <span>{{ showAnswer ? '收起答案' : '查看答案' }}</span>
          </div>

          <Transition name="fade">
            <div v-if="showAnswer" class="question-card__answer">
              <div class="answer-divider"></div>
              <div v-if="questionDetailLoading" class="answer-placeholder">正在加载答案...</div>
              <div v-else-if="questionDetail" class="answer-content">
                <div v-html="questionDetail.answer"></div>
                <div v-if="questionDetail.analysis" class="answer-analysis">
                  <h3>补充分析</h3>
                  <p>{{ questionDetail.analysis }}</p>
                </div>
                <div class="answer-source">
                  <span class="badge badge--accent">{{ questionDetail.section_title }}</span>
                  <p>{{ questionDetail.chunk_content }}</p>
                </div>
              </div>
              <div v-else class="answer-placeholder">暂无答案详情。</div>
            </div>
          </Transition>

          <div v-if="submitMessage" class="submit-message">{{ submitMessage }}</div>
        </article>
      </Transition>

      <div class="review-nav">
        <button class="btn btn--ghost" :disabled="currentIndex === 0 || submitting" @click="prevQuestion">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          上一题
        </button>

        <button class="btn btn--primary" @click="nextQuestion" :disabled="currentIndex === questions.length - 1 || submitting">
          下一题
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiGet, apiPost } from '../lib/api'
import { formatDateTime, formatDifficulty } from '../lib/format'

const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const submitMessage = ref('')
const showAnswer = ref(false)
const selectedAnswer = ref(null)
const currentIndex = ref(0)
const questions = ref([])
const questionDetail = ref(null)
const questionDetailLoading = ref(false)

const currentQuestion = computed(() => questions.value[currentIndex.value] ?? null)

const progressPercent = computed(() => {
  if (questions.value.length === 0) {
    return 0
  }
  return ((currentIndex.value + 1) / questions.value.length) * 100
})

async function loadTodayReview() {
  loading.value = true
  errorMessage.value = ''

  try {
    const data = await apiGet('/review/today')
    questions.value = data.items
    currentIndex.value = 0
    resetCard()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function loadQuestionDetail() {
  if (!currentQuestion.value) {
    return
  }

  questionDetailLoading.value = true
  try {
    questionDetail.value = await apiGet(`/questions/${currentQuestion.value.question_id}`)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    questionDetailLoading.value = false
  }
}

async function toggleAnswer() {
  showAnswer.value = !showAnswer.value
  if (showAnswer.value && !questionDetail.value) {
    await loadQuestionDetail()
  }
}

async function handleAnswer(feedback) {
  if (!currentQuestion.value || submitting.value) {
    return
  }

  selectedAnswer.value = feedback
  submitting.value = true
  submitMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await apiPost('/review/submit', {
      question_id: currentQuestion.value.question_id,
      user_feedback: feedback,
    })

    submitMessage.value = `已记录“${result.user_feedback}”，下次复习时间：${formatDateTime(result.next_review_at)}`

    setTimeout(() => {
      if (currentIndex.value < questions.value.length - 1) {
        nextQuestion()
      } else {
        void loadTodayReview()
      }
    }, 500)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value += 1
    resetCard()
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value -= 1
    resetCard()
  }
}

function resetCard() {
  showAnswer.value = false
  selectedAnswer.value = null
  submitMessage.value = ''
  questionDetail.value = null
}

onMounted(loadTodayReview)
</script>

<style scoped>
.review-page {
  max-width: 720px;
  margin: 0 auto;
  display: grid;
  gap: var(--space-6);
}

.review-empty {
  padding: var(--space-8);
  text-align: center;
  display: grid;
  gap: var(--space-3);
}

.review-empty--error {
  background: var(--color-danger-subtle);
}

.review-empty__title {
  font-size: var(--text-xl);
  font-weight: 700;
}

.review-empty__desc {
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
}

.review-progress {
  display: grid;
  gap: var(--space-2);
}

.review-progress__info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-progress__label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.review-progress__count {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.review-progress__bar {
  height: 8px;
  background: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.review-progress__fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
}

.question-card {
  padding: var(--space-6);
  display: grid;
  gap: var(--space-5);
}

.question-card__source {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  flex-wrap: wrap;
}

.question-card__tag {
  margin-left: auto;
}

.question-card__title {
  font-size: var(--text-2xl);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.question-card__due {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

.question-card__actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}

.review-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  background: var(--color-surface-subtle);
  transition: all var(--transition-fast);
  font-weight: 600;
}

.review-btn:hover {
  border-color: var(--color-border-active);
  color: var(--color-text-primary);
}

.review-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.review-btn.selected {
  color: var(--color-text-inverse);
  border-color: transparent;
}

.review-btn--dont-know.selected {
  background: var(--color-dont-know);
}

.review-btn--fuzzy.selected {
  background: var(--color-fuzzy);
}

.review-btn--know.selected {
  background: var(--color-know);
}

.question-card__answer-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 600;
}

.question-card__answer {
  overflow: hidden;
}

.answer-divider {
  height: 1px;
  background: var(--color-border);
  margin-bottom: var(--space-4);
}

.answer-placeholder {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

.answer-content {
  display: grid;
  gap: var(--space-4);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
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
  color: var(--color-accent);
}

.answer-analysis {
  padding: var(--space-4);
  background: var(--color-surface-subtle);
  border-radius: var(--radius-md);
}

.answer-analysis h3 {
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
}

.answer-source {
  display: grid;
  gap: var(--space-2);
}

.answer-source p {
  color: var(--color-text-secondary);
}

.submit-message {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-size: var(--text-sm);
}

.review-nav {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
}

.review-nav .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.card-slide-enter-active,
.card-slide-leave-active,
.fade-enter-active,
.fade-leave-active {
  transition: all var(--transition-normal);
}

.card-slide-enter-from,
.card-slide-leave-to,
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 640px) {
  .question-card__actions {
    grid-template-columns: 1fr;
  }

  .review-nav {
    flex-direction: column;
  }
}
</style>
