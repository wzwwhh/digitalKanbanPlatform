<script setup>
/**
 * 智能问数 — 对话式数据分析
 *
 * 流程：
 * 1. 用户输入自然语言问题
 * 2. 后端 SSE 流式返回：
 *    - Phase 1: AI 生成查询方案（选数据源 + SQL）
 *    - Phase 2: 执行查询 → 返回真实数据表格
 *    - Phase 3: AI 流式分析 → 文字逐字打出 + 图表/KPI
 * 3. 前端渐进渲染：步骤条 → 数据表格 → 文字 → 图表
 */
import { ref, reactive, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import AskChatMessage from '../components/AskChatMessage.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const dataSources = computed(() => projectStore.currentProject?.dataSources || [])

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

// 快捷问题（根据数据源动态生成 + 固定示例）
const suggestions = computed(() => {
  const ds = dataSources.value
  const items = []
  // 根据已有数据源生成
  for (const d of ds.slice(0, 2)) {
    const fields = d.fields || []
    if (fields.length >= 2) {
      items.push(`${d.name}的整体情况如何？`)
    }
  }
  // 补充通用问题
  const generic = ['销售额趋势如何？', '哪个产品销量最高？', '各地区销售占比？', '最近的订单情况？']
  for (const g of generic) {
    if (items.length < 4 && !items.includes(g)) items.push(g)
  }
  return items.slice(0, 4)
})

/**
 * SSE 解析器：从 chunk 文本中解析出 {event, data} 事件
 */
function parseSSEChunk(chunk, buffer) {
  const text = buffer + chunk
  const events = []
  const lines = text.split('\n')
  let currentEvent = null
  let currentData = null
  let remaining = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // 最后一行如果不以换行结尾，说明是不完整的，缓存下来
    if (i === lines.length - 1 && !text.endsWith('\n')) {
      remaining = line
      break
    }

    if (line.startsWith('event: ')) {
      currentEvent = line.slice(7).trim()
    } else if (line.startsWith('data: ')) {
      currentData = line.slice(6)
    } else if (line === '' && currentEvent && currentData !== null) {
      try {
        events.push({ event: currentEvent, data: JSON.parse(currentData) })
      } catch {
        events.push({ event: currentEvent, data: currentData })
      }
      currentEvent = null
      currentData = null
    }
  }
  return { events, remaining }
}

async function askQuestion() {
  const q = question.value.trim()
  if (!q || loading.value) return

  // 用户消息
  chatHistory.value.push({ role: 'user', content: q })
  question.value = ''
  loading.value = true
  scrollToBottom()

  // 创建 AI 消息占位
  const aiMsg = reactive({
    role: 'assistant',
    steps: [],
    queries: [],
    tables: [],
    text: '',
    kpi: null,
    chart: null,
    widgetConfig: null,
    error: null,
    done: false,
  })
  chatHistory.value.push(aiMsg)
  scrollToBottom()

  try {
    // 传完整数据源配置（后端需要 url/sql/headers 等来执行查询）
    const body = JSON.stringify({
      question: q,
      allDataSources: dataSources.value.map(d => ({
        id: d.id,
        name: d.name,
        type: d.type || 'api',
        url: d.url,
        method: d.method,
        headers: d.headers,
        dataPath: d.dataPath,
        table: d.table,
        sql: d.sql,
        fields: d.fields,
        fieldAnnotations: d.fieldAnnotations,
        sample: (d.sample || []).slice(0, 3),
      })),
      projectId: projectId.value,
    })

    const resp = await fetch('/api/ai/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })

    if (!resp.ok) {
      aiMsg.error = `请求失败: HTTP ${resp.status}`
      aiMsg.done = true
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let sseBuffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const { events, remaining } = parseSSEChunk(chunk, sseBuffer)
      sseBuffer = remaining

      for (const evt of events) {
        switch (evt.event) {
          case 'step':
            // 更新或追加步骤
            const existingStep = aiMsg.steps.find(s => s.phase === evt.data.phase)
            if (existingStep) {
              Object.assign(existingStep, evt.data)
            } else {
              aiMsg.steps.push({ ...evt.data })
            }
            break

          case 'query':
            aiMsg.queries.push(evt.data)
            break

          case 'table':
            // 给 table 加 _expanded 响应式属性
            aiMsg.tables.push(reactive({ ...evt.data, _expanded: false }))
            break

          case 'text':
            aiMsg.text += evt.data.delta || ''
            break

          case 'result':
            if (evt.data.kpi) aiMsg.kpi = evt.data.kpi
            if (evt.data.chart) aiMsg.chart = evt.data.chart
            if (evt.data.widgetConfig) aiMsg.widgetConfig = evt.data.widgetConfig
            break

          case 'error':
            aiMsg.error = evt.data.message || '未知错误'
            break

          case 'done':
            aiMsg.done = true
            break
        }
        scrollToBottom()
      }
    }

    // 确保标记完成
    aiMsg.done = true

  } catch (err) {
    aiMsg.error = `请求失败: ${err.message}`
    aiMsg.done = true
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function useSuggestion(text) {
  question.value = text
  askQuestion()
}

function addToDashboard(widgetConfig) {
  if (!widgetConfig || !widgetConfig.type) return

  const dashboards = projectStore.getDashboards(projectId.value)
  if (dashboards.length === 0) {
    alert('请先创建一个看板')
    return
  }

  const db = dashboards[0]
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

  router.push({
    name: 'dashboard-edit',
    params: { projectId: projectId.value, dashboardId: db.id },
  })
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    askQuestion()
  }
}
</script>

<template>
  <div class="ask-page">
    <!-- 简洁 Header -->
    <div class="ask-header">
      <div class="header-title">
        <span class="header-icon">🤖</span>
        <h1>智能问数</h1>
      </div>
      <p class="ask-desc" v-if="dataSources.length">
        基于 {{ dataSources.length }} 个数据源，用自然语言探索数据
      </p>
    </div>

    <!-- 没有数据源提示 -->
    <div v-if="dataSources.length === 0" class="ds-empty">
      <div class="empty-big-icon">📦</div>
      <p>暂无数据源</p>
      <p class="empty-hint">请先添加数据源，AI 才能查询真实数据为你分析</p>
      <button class="go-ds-btn" @click="router.push({ name: 'datasources', params: { projectId } })">
        前往数据源管理 →
      </button>
    </div>

    <template v-else>
      <!-- 对话区 -->
      <div class="chat-area" ref="chatAreaRef">
        <!-- 空状态 -->
        <div v-if="chatHistory.length === 0" class="empty-chat">
          <div class="empty-icon">💬</div>
          <p class="empty-title">有什么想了解的？</p>
          <p class="empty-subtitle">AI 会查询真实数据，生成图表和分析为你解答</p>
          <div class="suggestion-grid">
            <button
              v-for="(s, i) in suggestions"
              :key="i"
              class="suggestion-btn"
              @click="useSuggestion(s)"
            >
              <span class="sug-icon">💡</span>
              {{ s }}
            </button>
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
            <!-- 用户消息 -->
            <template v-if="msg.role === 'user'">
              <div class="msg-body user-body">
                <div class="msg-text user-text">{{ msg.content }}</div>
              </div>
              <div class="msg-avatar user-avatar">👤</div>
            </template>

            <!-- AI 消息 -->
            <template v-else>
              <div class="msg-avatar ai-avatar">🤖</div>
              <div class="msg-body ai-body">
                <AskChatMessage
                  :msg="msg"
                  @addToDashboard="addToDashboard"
                />
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            v-model="question"
            class="ask-input"
            placeholder="输入你的问题，例如：各品类的总销售额对比？"
            @keydown="handleKeydown"
            :disabled="loading"
            rows="1"
          ></textarea>
          <button class="ask-btn" @click="askQuestion" :disabled="loading || !question.trim()">
            <template v-if="loading"><span class="send-spinner"></span></template>
            <template v-else>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </template>
          </button>
        </div>
        <div class="input-hint">Enter 发送 · Shift+Enter 换行</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ask-page {
  max-width: 840px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  padding: 0 16px;
}

/* Header */
.ask-header {
  text-align: center;
  padding: 20px 0 12px;
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.header-icon {
  font-size: 28px;
}

.ask-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #e0e6ff);
  margin: 0;
}

.ask-desc {
  color: var(--text-muted, #4a5578);
  font-size: 13px;
  margin-top: 4px;
}

/* 空数据源 */
.ds-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.empty-big-icon { font-size: 48px; }

.ds-empty p {
  margin: 0;
  color: var(--text-secondary, #8892b0);
  font-size: 14px;
}

.empty-hint {
  color: var(--text-muted, #4a5578) !important;
  font-size: 13px !important;
}

.go-ds-btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.go-ds-btn:hover { opacity: 0.85; }

/* 对话区 */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  scroll-behavior: smooth;
}

/* 空状态 */
.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0 40px;
}

.empty-icon { font-size: 48px; margin-bottom: 12px; }

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin: 0 0 4px;
}

.empty-subtitle {
  font-size: 13px;
  color: var(--text-muted, #4a5578);
  margin: 0 0 24px;
}

.suggestion-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  max-width: 480px;
  width: 100%;
}

.suggestion-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  color: var(--text-secondary, #8892b0);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.suggestion-btn:hover {
  border-color: var(--accent, #00d4ff);
  color: var(--accent, #00d4ff);
  background: rgba(0, 212, 255, 0.04);
  transform: translateY(-1px);
}

.sug-icon { font-size: 14px; flex-shrink: 0; }

/* 消息 */
.messages {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.msg.user {
  justify-content: flex-end;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, rgba(123, 97, 255, 0.2), rgba(0, 212, 255, 0.15));
  border: 1px solid rgba(123, 97, 255, 0.3);
}

.user-avatar {
  background: rgba(0, 212, 255, 0.12);
  border: 1px solid rgba(0, 212, 255, 0.25);
}

.msg-body {
  max-width: 85%;
  min-width: 60px;
}

.user-text {
  padding: 10px 16px;
  border-radius: 16px 16px 4px 16px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(123, 97, 255, 0.1));
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  line-height: 1.5;
}

.ai-body {
  padding: 14px 18px;
  border-radius: 4px 16px 16px 16px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
}

/* 输入区 */
.input-area {
  flex-shrink: 0;
  padding: 12px 0 8px;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 14px;
  padding: 6px 6px 6px 16px;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--accent, #00d4ff);
}

.ask-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  outline: none;
  resize: none;
  min-height: 24px;
  max-height: 120px;
  padding: 6px 0;
  font-family: inherit;
  line-height: 1.5;
}

.ask-input::placeholder {
  color: var(--text-muted, #4a5578);
}

.ask-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.ask-btn:hover { opacity: 0.85; }

.ask-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.send-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted, #4a5578);
  margin-top: 4px;
  opacity: 0.6;
}
</style>
