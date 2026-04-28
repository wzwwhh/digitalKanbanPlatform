<script setup>
/**
 * 智能问数页面 — 基于项目数据源，用自然语言提问，AI 推荐可视化
 *
 * 流程：
 * 1. 用户选择数据源
 * 2. 输入自然语言问题（如 "哪个产品销量最高？"）
 * 3. AI 分析数据 → 推荐图表类型 → 生成配置
 * 4. 用户可以将结果快速添加到看板
 */
import { ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const dataSources = computed(() => projectStore.currentProject?.dataSources || [])
const selectedDsId = ref('')

const question = ref('')
const chatHistory = ref([])
const loading = ref(false)
const chatAreaRef = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

// 快捷问题
const suggestions = [
  '数据整体趋势如何？',
  '哪个类别占比最大？',
  '最近数据有什么异常？',
  '各项指标对比如何？',
]

async function askQuestion() {
  const q = question.value.trim()
  if (!q || loading.value) return

  const ds = dataSources.value.find(d => d.id === selectedDsId.value)

  chatHistory.value.push({ role: 'user', content: q })
  question.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(new Error("数据分析请求超时，请重试")), 300000)
    const resp = await fetch('/api/ai/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: q,
        dataSource: ds ? { id: ds.id, name: ds.name, url: ds.url, fields: ds.fields } : null,
        allDataSources: dataSources.value.map(d => ({ id: d.id, name: d.name, fields: d.fields })),
        projectId: projectId.value,
      }),
      signal: controller.signal,
    })
    clearTimeout(timeoutId)

    const data = await resp.json()
    chatHistory.value.push({
      role: 'assistant',
      content: data.answer || '抱歉，我暂时无法回答这个问题。',
      suggestion: data.chartSuggestion || null,
      widgetConfig: data.widgetConfig || null,
    })
    scrollToBottom()
  } catch (err) {
    chatHistory.value.push({
      role: 'assistant',
      content: `请求失败: ${err.message}。请确保后端服务已启动。`,
    })
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

function useSuggestion(text) {
  question.value = text
  askQuestion()
}

function goToEditor(widgetConfig) {
  const dashboards = projectStore.getDashboards(projectId.value)
  if (dashboards.length > 0) {
    const db = dashboards[0]
    
    // 如果 AI 返回了完整的图表和数据源配置，直接将组件插入看板
    if (widgetConfig && widgetConfig.type) {
      const newWidget = {
        id: 'w_' + Math.random().toString(36).substr(2, 9),
        type: widgetConfig.type,
        props: widgetConfig.props || {},
        position: { x: 50 + Math.random() * 100, y: 50 + Math.random() * 100 },
        size: { w: 400, h: 300 },
        dataSource: widgetConfig.dataSource || null
      }
      if (!db.widgets) db.widgets = []
      db.widgets.push(newWidget)
      projectStore.saveProject()
    }

    router.push({
      name: 'dashboard-edit',
      params: { projectId: projectId.value, dashboardId: db.id },
    })
  }
}
</script>

<template>
  <div class="ask-page">
    <div class="ask-header">
      <h1>🤖 智能问数</h1>
      <p class="ask-desc">选择数据源，用自然语言提问，AI 帮你分析数据</p>
    </div>

    <!-- 数据源选择 -->
    <div class="ds-selector" v-if="dataSources.length > 0">
      <label class="ds-label">数据源</label>
      <select v-model="selectedDsId" class="ds-select">
        <option value="">不指定数据源</option>
        <option v-for="ds in dataSources" :key="ds.id" :value="ds.id">
          {{ ds.name }} ({{ (ds.fields || []).length }} 个字段)
        </option>
      </select>
    </div>
    <div v-else class="ds-empty">
      <p>暂无数据源，请先到<button class="link-btn" @click="router.push({ name: 'datasources', params: { projectId } })">数据源管理</button>添加</p>
    </div>

    <!-- 对话区 -->
    <div class="chat-area" ref="chatAreaRef">
      <!-- 空状态 -->
      <div v-if="chatHistory.length === 0" class="empty-chat">
        <div class="empty-icon">💬</div>
        <p>试试问一些关于数据的问题</p>
        <div class="suggestion-grid">
          <button
            v-for="(s, i) in suggestions"
            :key="i"
            class="suggestion-btn"
            @click="useSuggestion(s)"
          >{{ s }}</button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages" v-else>
        <div
          v-for="(msg, i) in chatHistory"
          :key="i"
          class="msg"
          :class="msg.role"
        >
          <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="msg-body">
            <div class="msg-text">{{ msg.content }}</div>
            <div v-if="msg.suggestion" class="msg-suggestion">
              <span class="suggestion-tag">📊 建议图表: {{ msg.suggestion }}</span>
              <button class="action-btn" @click="goToEditor(msg.widgetConfig)">
                {{ msg.widgetConfig ? '✨ 一键生成此图表 →' : '去编辑器创建 →' }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="loading" class="msg assistant">
          <div class="msg-avatar">🤖</div>
          <div class="msg-body">
            <div class="msg-text thinking">分析中<span class="dots">...</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <input
        v-model="question"
        class="ask-input"
        placeholder="输入你的问题，如：哪个产品销量最高？"
        @keydown.enter="askQuestion"
        :disabled="loading"
      />
      <button class="ask-btn" @click="askQuestion" :disabled="loading || !question.trim()">
        {{ loading ? '⏳' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.ask-page {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
}

.ask-header {
  text-align: center;
  padding: 24px 0 16px;
}

.ask-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #e0e6ff);
  margin: 0 0 8px;
}

.ask-desc {
  color: var(--text-secondary, #8892b0);
  font-size: 14px;
}

/* 数据源选择 */
.ds-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  margin-bottom: 16px;
}

.ds-label {
  font-size: 13px;
  color: var(--text-muted, #4a5578);
  white-space: nowrap;
}

.ds-select {
  flex: 1;
  padding: 6px 10px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-primary, #e0e6ff);
  font-size: 13px;
  outline: none;
}

.ds-empty {
  text-align: center;
  padding: 12px;
  color: var(--text-muted, #4a5578);
  font-size: 13px;
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent, #00d4ff);
  cursor: pointer;
  text-decoration: underline;
  font-size: 13px;
}

/* 对话区 */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.empty-chat {
  text-align: center;
  padding: 48px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-chat p {
  color: var(--text-secondary, #8892b0);
  margin-bottom: 20px;
}

.suggestion-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  max-width: 400px;
  margin: 0 auto;
}

.suggestion-btn {
  padding: 10px 16px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-secondary, #8892b0);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.suggestion-btn:hover {
  border-color: var(--accent, #00d4ff);
  color: var(--accent, #00d4ff);
}

/* 消息 */
.messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  font-size: 20px;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary, #131837);
  border-radius: 50%;
}

.msg-body {
  max-width: 70%;
}

.msg-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.msg.user .msg-text {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(123, 97, 255, 0.15));
  color: var(--text-primary, #e0e6ff);
  border-bottom-right-radius: 4px;
}

.msg.assistant .msg-text {
  background: var(--bg-secondary, #131837);
  color: var(--text-primary, #e0e6ff);
  border: 1px solid var(--border-color, #2a3560);
  border-bottom-left-radius: 4px;
}

.msg-suggestion {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.suggestion-tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(0, 227, 150, 0.1);
  color: #00e396;
  border: 1px solid rgba(0, 227, 150, 0.2);
}

.action-btn {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid var(--accent, #00d4ff);
  background: transparent;
  color: var(--accent, #00d4ff);
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--accent, #00d4ff);
  color: #fff;
}

.thinking {
  color: var(--text-muted, #4a5578);
}

.dots {
  animation: dotPulse 1.5s infinite;
}

@keyframes dotPulse {
  0%, 60% { opacity: 1; }
  30% { opacity: 0.3; }
}

/* 输入区 */
.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 0;
  border-top: 1px solid var(--border-color, #2a3560);
  flex-shrink: 0;
}

.ask-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

.ask-input:focus {
  border-color: var(--accent, #00d4ff);
}

.ask-btn {
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.ask-btn:hover { opacity: 0.9; }
.ask-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
