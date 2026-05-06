<template>
  <div class="settings-page">
    <section class="card intro-card">
      <div class="intro-card__header">
        <div>
          <h2 class="card__title">大模型厂商配置</h2>
          <p class="intro-card__sub">保存 API Key、默认模型，并决定是否用于智能 chunk 拆分和 AI 出题。</p>
        </div>
        <span class="badge badge--accent">OpenAI Compatible</span>
      </div>
      <div v-if="summaryMessage" class="intro-card__message intro-card__message--success">{{ summaryMessage }}</div>
      <div v-if="errorMessage" class="intro-card__message intro-card__message--error">{{ errorMessage }}</div>
    </section>

    <section v-if="loading" class="card state-card">
      <div class="empty-state">
        <p class="empty-state__text">正在加载厂商配置...</p>
      </div>
    </section>

    <section v-else class="providers-grid">
      <article v-for="provider in providers" :key="provider.provider_name" class="card provider-card">
        <div class="provider-card__header">
          <div>
            <h3 class="provider-card__title">{{ provider.display_name }}</h3>
            <p class="provider-card__sub">{{ provider.provider_name }}</p>
          </div>
          <div class="provider-card__badges">
            <span v-if="provider.use_for_chunking" class="badge badge--secondary">Chunking</span>
            <span v-if="provider.use_for_question_generation" class="badge badge--accent">出题</span>
          </div>
        </div>

        <div class="provider-form">
          <label class="field">
            <span class="field__label">显示名称</span>
            <input v-model="provider.display_name" type="text" class="field__input" placeholder="例如 OpenRouter" />
          </label>

          <label class="field">
            <span class="field__label">Base URL</span>
            <input v-model="provider.base_url" type="text" class="field__input" placeholder="https://openrouter.ai/api/v1" />
          </label>

          <label class="field">
            <span class="field__label">API Key</span>
            <input v-model="provider.api_key" type="password" class="field__input" placeholder="留空则沿用已保存的 API Key" />
            <span v-if="provider.api_key_masked && !provider.api_key" class="field__hint">当前已保存：{{ provider.api_key_masked }}</span>
          </label>

          <label class="field">
            <span class="field__label">默认模型</span>
            <input v-model="provider.default_model" type="text" class="field__input" placeholder="例如 openai/gpt-4.1-mini" />
          </label>

          <div class="provider-switches">
            <label class="switch-row">
              <input v-model="provider.is_enabled" type="checkbox" />
              <span>启用该厂商</span>
            </label>
            <label class="switch-row">
              <input v-model="provider.use_for_chunking" type="checkbox" />
              <span>用于智能 chunk 拆分</span>
            </label>
            <label class="switch-row">
              <input v-model="provider.use_for_question_generation" type="checkbox" />
              <span>用于 AI 出题</span>
            </label>
          </div>
        </div>

        <div class="provider-card__actions">
          <button class="btn btn--outline" :disabled="provider.testing || provider.saving" @click="handleTest(provider)">
            {{ provider.testing ? '测试中...' : '测试连接' }}
          </button>
          <button class="btn btn--primary" :disabled="provider.saving || provider.testing" @click="handleSave(provider)">
            {{ provider.saving ? '保存中...' : '保存配置' }}
          </button>
        </div>

        <div v-if="provider.testResult" class="test-result" :class="provider.testResult.success ? 'test-result--success' : 'test-result--error'">
          <div class="test-result__title">
            {{ provider.testResult.success ? '连接成功' : '连接失败' }}
          </div>
          <div class="test-result__meta">
            <span>模型：{{ provider.testResult.model || '未返回' }}</span>
            <span>地址：{{ provider.testResult.base_url || provider.base_url || '默认地址' }}</span>
          </div>
          <p class="test-result__message">{{ provider.testResult.message }}</p>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { fetchSettings, saveProviderSettings, testProviderConnection } from '../lib/api'

const loading = ref(true)
const errorMessage = ref('')
const summaryMessage = ref('')
const providers = ref([])

const defaultProviders = [
  {
    provider_name: 'openrouter',
    display_name: 'OpenRouter',
    base_url: 'https://openrouter.ai/api/v1',
    api_key: '',
    api_key_masked: '',
    default_model: 'openai/gpt-4.1-mini',
    is_enabled: false,
    use_for_chunking: false,
    use_for_question_generation: false,
  },
  {
    provider_name: 'qwen',
    display_name: 'Qwen',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key: '',
    api_key_masked: '',
    default_model: 'qwen-max',
    is_enabled: false,
    use_for_chunking: false,
    use_for_question_generation: false,
  },
  {
    provider_name: 'deepseek',
    display_name: 'DeepSeek',
    base_url: 'https://api.deepseek.com/v1',
    api_key: '',
    api_key_masked: '',
    default_model: 'deepseek-chat',
    is_enabled: false,
    use_for_chunking: false,
    use_for_question_generation: false,
  },
]

function createProviderState(provider) {
  return {
    ...provider,
    saving: false,
    testing: false,
    testResult: null,
  }
}

function mergeProviders(savedProviders) {
  const savedMap = new Map(savedProviders.map((item) => [item.provider_name, item]))
  const merged = defaultProviders.map((item) => {
    const saved = savedMap.get(item.provider_name)
    return createProviderState({
      ...item,
      ...saved,
      api_key: '',
    })
  })

  for (const saved of savedProviders) {
    if (!defaultProviders.find((item) => item.provider_name === saved.provider_name)) {
      merged.push(
        createProviderState({
          ...saved,
          api_key: '',
        }),
      )
    }
  }

  return merged
}

async function loadSettings() {
  loading.value = true
  errorMessage.value = ''

  try {
    const data = await fetchSettings()
    providers.value = mergeProviders(data.providers)
  } catch (error) {
    errorMessage.value = error.message
    providers.value = mergeProviders([])
  } finally {
    loading.value = false
  }
}

async function handleSave(provider) {
  provider.saving = true
  errorMessage.value = ''
  summaryMessage.value = ''

  try {
    const payload = {
      provider_name: provider.provider_name,
      display_name: provider.display_name,
      base_url: provider.base_url || null,
      api_key: provider.api_key.trim() || null,
      default_model: provider.default_model || null,
      is_enabled: provider.is_enabled,
      use_for_chunking: provider.use_for_chunking,
      use_for_question_generation: provider.use_for_question_generation,
    }

    const saved = await saveProviderSettings(payload)
    provider.api_key = ''
    provider.api_key_masked = saved.api_key_masked
    summaryMessage.value = `${saved.display_name} 配置已保存。`
    await loadSettings()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    provider.saving = false
  }
}

async function handleTest(provider) {
  provider.testing = true
  provider.testResult = null
  errorMessage.value = ''
  summaryMessage.value = ''

  try {
    const rawApiKey = provider.api_key.trim()
    const result = await testProviderConnection({
      provider_name: provider.provider_name,
      display_name: provider.display_name,
      base_url: provider.base_url || null,
      api_key: rawApiKey || null,
      default_model: provider.default_model || null,
      use_saved_key: !rawApiKey && Boolean(provider.api_key_masked),
    })

    provider.testResult = {
      success: result.success,
      model: result.model,
      base_url: result.base_url,
      message: result.message,
    }
  } catch (error) {
    provider.testResult = {
      success: false,
      model: provider.default_model,
      base_url: provider.base_url,
      message: error.message,
    }
  } finally {
    provider.testing = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-page {
  display: grid;
  gap: var(--space-5);
}

.intro-card,
.state-card {
  padding: var(--space-6);
}

.intro-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.card__title {
  font-size: var(--text-base);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  color: var(--color-text-primary);
}

.intro-card__sub {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.intro-card__message {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.intro-card__message--success {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.intro-card__message--error {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.providers-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

@media (max-width: 960px) {
  .providers-grid {
    grid-template-columns: 1fr;
  }
}

.provider-card {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.provider-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.provider-card__title {
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  color: var(--color-text-primary);
}

.provider-card__sub {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.provider-card__badges {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.provider-form {
  display: grid;
  gap: var(--space-4);
}

.field {
  display: grid;
  gap: var(--space-2);
}

.field__label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.field__input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-subtle);
  color: var(--color-text-primary);
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.field__input:focus {
  border-color: var(--color-border-active);
  background: var(--color-surface);
}

.field__hint {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.provider-switches {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-subtle);
  border: 1px solid var(--color-border-light);
}

.switch-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.switch-row input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-accent);
}

.provider-card__actions {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.test-result {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
}

.test-result--success {
  background: var(--color-accent-subtle);
  border-color: var(--color-accent-border);
}

.test-result--error {
  background: var(--color-danger-subtle);
  border-color: rgba(176, 74, 58, 0.15);
}

.test-result__title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text-primary);
}

.test-result__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.test-result__message {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  line-height: var(--leading-relaxed);
}
</style>