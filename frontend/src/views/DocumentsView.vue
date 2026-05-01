<template>
  <div class="documents-page">
    <section class="card upload-card">
      <div
        class="dropzone"
        :class="{ 'dropzone--active': isDragging || uploading }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="triggerUpload"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".md,.markdown"
          multiple
          class="dropzone__input"
          @change="handleFileSelect"
        />
        <div class="dropzone__content">
          <div class="dropzone__icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <p class="dropzone__title">{{ uploading ? '正在上传并生成题目...' : '导入 Markdown 面经' }}</p>
          <p class="dropzone__hint">拖拽文件到这里，或点击选择文件。上传后会自动解析并生成题目。</p>
        </div>
      </div>
      <div class="upload-card__info">
        <span class="badge badge--accent">支持 .md / .markdown</span>
        <span class="upload-card__tip">接口层只负责接收文件，真正的解析与生成逻辑都在后端服务层。</span>
      </div>
      <div v-if="uploadMessage" class="upload-card__message upload-card__message--success">{{ uploadMessage }}</div>
      <div v-if="errorMessage" class="upload-card__message upload-card__message--error">{{ errorMessage }}</div>
    </section>

    <section class="card list-card">
      <div class="card__header">
        <div class="card__header-left">
          <h2 class="card__title">已导入文档</h2>
          <span class="card__count">{{ filteredDocs.length }} 个文档</span>
        </div>
        <div class="card__header-right">
          <div class="search-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input v-model="searchQuery" type="text" placeholder="搜索文档..." class="search-input" />
          </div>
          <button class="btn btn--outline" @click="sortDescending = !sortDescending">
            {{ sortDescending ? '最新优先' : '最早优先' }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="empty-state">
        <p class="empty-state__text">正在加载文档列表...</p>
      </div>
      <div v-else-if="filteredDocs.length === 0" class="empty-state">
        <p class="empty-state__text">{{ searchQuery ? '没有匹配的文档。' : '还没有导入文档，先上传一个 Markdown 文件吧。' }}</p>
      </div>

      <TransitionGroup v-else name="list" tag="div" class="doc-table">
        <div v-for="doc in filteredDocs" :key="doc.id" class="doc-row">
          <div class="doc-row__main">
            <div class="doc-row__icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            </div>
            <div class="doc-row__info">
              <span class="doc-row__name">{{ doc.title }}</span>
              <span class="doc-row__meta">创建时间 {{ formatDateTime(doc.created_at) }}</span>
            </div>
          </div>
          <span class="badge badge--accent doc-row__status">已入库</span>
        </div>
      </TransitionGroup>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiGet, apiPost, apiUpload } from '../lib/api'
import { formatDateTime } from '../lib/format'

const isDragging = ref(false)
const fileInput = ref(null)
const searchQuery = ref('')
const sortDescending = ref(true)
const uploading = ref(false)
const loading = ref(true)
const documents = ref([])
const uploadMessage = ref('')
const errorMessage = ref('')

const filteredDocs = computed(() => {
  let list = documents.value
  if (searchQuery.value) {
    const keyword = searchQuery.value.trim().toLowerCase()
    list = list.filter((item) => item.title.toLowerCase().includes(keyword))
  }

  const sorted = [...list].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  return sortDescending.value ? sorted.reverse() : sorted
})

function triggerUpload() {
  if (!uploading.value) {
    fileInput.value?.click()
  }
}

function handleFileSelect(event) {
  const files = [...(event.target.files ?? [])]
  if (files.length > 0) {
    void handleFiles(files)
  }
  event.target.value = ''
}

function handleDrop(event) {
  isDragging.value = false
  const files = [...(event.dataTransfer?.files ?? [])]
  if (files.length > 0) {
    void handleFiles(files)
  }
}

async function loadDocuments() {
  loading.value = true
  try {
    documents.value = await apiGet('/documents')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function handleFiles(files) {
  const markdownFiles = files.filter((file) => file.name.endsWith('.md') || file.name.endsWith('.markdown'))
  if (markdownFiles.length === 0) {
    errorMessage.value = '只支持上传 .md 或 .markdown 文件。'
    return
  }

  uploading.value = true
  uploadMessage.value = ''
  errorMessage.value = ''

  try {
    for (const file of markdownFiles) {
      const document = await apiUpload('/documents/upload', file)
      await apiPost(`/questions/generate/${document.id}`)
    }

    uploadMessage.value = `成功上传 ${markdownFiles.length} 个文件，并已自动生成题目。`
    await loadDocuments()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    uploading.value = false
  }
}

onMounted(loadDocuments)
</script>

<style scoped>
.documents-page {
  display: grid;
  gap: var(--space-5);
}

.upload-card {
  padding: var(--space-6);
}

.dropzone {
  position: relative;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-subtle);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dropzone:hover,
.dropzone--active {
  border-color: var(--color-accent);
  background: var(--color-accent-subtle);
}

.dropzone__input {
  display: none;
}

.dropzone__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-8);
  text-align: center;
}

.dropzone__icon {
  color: var(--color-text-tertiary);
}

.dropzone__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
}

.dropzone__hint {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

.upload-card__info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-4);
  flex-wrap: wrap;
}

.upload-card__tip {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.upload-card__message {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.upload-card__message--success {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.upload-card__message--error {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.list-card {
  padding: var(--space-6);
}

.card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}

.card__header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.card__title {
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
}

.card__count {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.card__header-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
}

.search-box:focus-within {
  border-color: var(--color-border-active);
}

.search-input {
  width: 180px;
  padding: var(--space-1) 0;
  font-size: var(--text-sm);
  background: transparent;
  color: var(--color-text-primary);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

@media (max-width: 600px) {
  .card__header {
    flex-direction: column;
    align-items: stretch;
  }

  .card__header-right {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box,
  .search-input {
    width: 100%;
  }
}

.doc-table {
  display: grid;
  gap: var(--space-2);
}

.doc-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.doc-row:hover {
  background: var(--color-surface-subtle);
}

.doc-row__main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.doc-row__icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-subtle);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.doc-row__info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.doc-row__name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-row__meta {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.doc-row__status {
  flex-shrink: 0;
}

.list-enter-active,
.list-leave-active {
  transition: all var(--transition-normal);
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
