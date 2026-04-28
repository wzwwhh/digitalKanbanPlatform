<template>
  <div class="ai-chat">
    <!-- 消息列表 -->
    <div class="chat-messages" ref="messageListRef">
      <div class="welcome-msg" v-if="messages.length === 0">
        <div class="welcome-icon">🤖</div>
        <div class="welcome-title">AI 助手</div>
        <div class="welcome-text">试试说："做一个电商看板"</div>
        <div class="quick-actions">
          <button
            v-for="(action, i) in quickActions"
            :key="i"
            class="quick-btn"
            @click="sendQuick(action.text)"
          >{{ action.label }}</button>
        </div>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-msg"
        :class="msg.role"
      >
        <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="msg-bubble">
          <div class="msg-text">{{ msg.content }}</div>
          <div v-if="msg.commandCount" class="msg-badge">
            执行了 {{ msg.commandCount }} 个操作
          </div>
        </div>
      </div>

      <div v-if="loading" class="chat-msg assistant">
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">
          <div class="msg-text thinking">{{ loadingText }}<span class="dots">...</span></div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input-area">
      <input
        ref="inputRef"
        v-model="inputText"
        class="chat-input"
        placeholder="输入指令，如：做一个销售看板"
        @keydown.enter="sendMessage"
        :disabled="loading"
      />
      <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">
        {{ loading ? '⏳' : '➤' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed, onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useProjectStore } from '../stores/project'
import { useThemeStore } from '../stores/theme'
import { useHistoryStore } from '../stores/history'
import { executeCommand, createCommand, CommandType, undo, redo } from '../core/command'

const p = defineProps({
  initialPrompt: { type: String, default: '' },
})

const dashboardStore = useDashboardStore()
const projectStore = useProjectStore()
const themeStore = useThemeStore()
const historyStore = useHistoryStore()

const inputText = ref('')
const messages = ref([])
const loading = ref(false)
const loadingStage = ref(0)
let loadingTimer = null

const loadingTexts = ['正在理解需求', 'AI 生成中', '组件创建中']
const loadingText = computed(() => loadingTexts[loadingStage.value] || 'AI 正在思考')

function startLoadingAnim() {
  loadingStage.value = 0
  loadingTimer = setInterval(() => {
    if (loadingStage.value < loadingTexts.length - 1) loadingStage.value++
  }, 2000)
}
function stopLoadingAnim() {
  clearInterval(loadingTimer)
  loadingTimer = null
  loadingStage.value = 0
}
const messageListRef = ref(null)
const inputRef = ref(null)
const initialPromptUsed = ref(false)

// 动态快捷按钮：根据数据源状态推荐不同操作
const quickActions = computed(() => {
  const hasDatasources = (projectStore.currentProject?.dataSources || []).length > 0
  const hasWidgets = dashboardStore.widgets.length > 0

  if (hasDatasources && !hasWidgets) {
    // 有数据源，无组件 → 推荐基于数据生成
    return [
      { label: '🚀 基于数据生成看板', text: '用现有的数据源做一个看板' },
      { label: '📊 电商看板', text: '做一个电商销售看板' },
      { label: '📈 运营看板', text: '做一个运营数据看板' },
    ]
  }
  if (hasWidgets && hasDatasources) {
    // 有组件有数据源 → 推荐增量操作
    return [
      { label: '✨ 补充图表', text: '再补充几个合适的图表' },
      { label: '🎨 调整风格', text: '换一个暗色科技风格' },
      { label: '➕ 加指标卡', text: '加一个KPI指标卡' },
    ]
  }
  // 默认
  return [
    { label: '📊 电商看板', text: '做一个电商销售看板' },
    { label: '📈 运营看板', text: '做一个运营数据看板' },
    { label: '➕ 加指标卡', text: '加一个KPI指标卡' },
  ]
})

// 自动触发 AI 生成（新建看板时选了"AI 生成"）
onMounted(() => {
  if (p.initialPrompt && !initialPromptUsed.value) {
    initialPromptUsed.value = true
    // 稍作延迟确保组件加载完成
    setTimeout(() => {
      inputText.value = p.initialPrompt
      sendMessage()
    }, 500)
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function sendQuick(text) {
  inputText.value = text
  sendMessage()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  startLoadingAnim()
  scrollToBottom()

  try {
    // 构建上下文（精简版，减少 HTTP body 体积）
    const context = {
      widgets: dashboardStore.widgets.map(w => ({
        id: w.id,
        type: w.type,
        props: { title: w.props?.title },  // 只发标题，不发全部 props
        position: w.position,
        size: w.size,
        dataSource: w.dataSource ? {
          sourceId: w.dataSource.sourceId,
          mapping: w.dataSource.mapping,
        } : null,
      })),
      dataSources: (projectStore.currentProject?.dataSources || []).map(ds => ({
        id: ds.id,
        name: ds.name,
        type: ds.type,
        fields: ds.fields,
        // 不发 sample 数据，避免几 KB 膨胀
      })),
      selectedId: dashboardStore.selectedId,
      theme: themeStore.currentBoardStyle,
    }

    // 调用后端（30 秒超时）
    const controller = new AbortController()
    // AI 处理可能需要较长时间，将超时时间延长至 300 秒
    const timeout = setTimeout(() => controller.abort(new Error("AI 请求超时，请重试（复杂指令可能需要更长处理时间）")), 300000)
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, context }),
      signal: controller.signal,
    })
    clearTimeout(timeout)

    if (!response.ok) {
      throw new Error(`服务器错误: ${response.status}`)
    }

    const data = await response.json()

    // 执行 commands
    let commandCount = 0
    if (data.commands && data.commands.length > 0) {
      for (const cmd of data.commands) {
        applyCommand(cmd)
        commandCount++
      }
    }

    // 添加 AI 回复
    messages.value.push({
      role: 'assistant',
      content: data.message || '操作已完成',
      commandCount,
    })

  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: `请求失败: ${err.message}`,
    })
  } finally {
    loading.value = false
    stopLoadingAnim()
    scrollToBottom()
    nextTick(() => inputRef.value?.focus())
  }
}

/**
 * 应用后端返回的 command
 */
function applyCommand(cmd) {
  switch (cmd.type) {
    case 'ADD_WIDGET':
      executeCommand(createCommand(CommandType.ADD_WIDGET, cmd.payload))
      break
    case 'UPDATE_WIDGET':
      executeCommand(createCommand(CommandType.UPDATE_WIDGET, cmd.payload, 'ai'))
      break
    case 'DELETE_WIDGET':
      executeCommand(createCommand(CommandType.DELETE_WIDGET, cmd.payload, 'ai'))
      break
    case 'MOVE_WIDGET':
      executeCommand(createCommand(CommandType.MOVE_WIDGET, cmd.payload, 'ai'))
      break
    case 'RESIZE_WIDGET':
      executeCommand(createCommand(CommandType.RESIZE_WIDGET, cmd.payload, 'ai'))
      break
    case 'CHANGE_THEME':
      themeStore.applyBoardStyle(cmd.payload.theme)
      break
    case 'UNDO':
      undo()
      break
    case 'REDO':
      redo()
      break
    case 'BATCH':
      if (cmd.payload?.commands) {
        cmd.payload.commands.forEach(sub => applyCommand(sub))
      }
      break
  }
}
</script>

<style scoped>
.ai-chat {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* 欢迎 */
.welcome-msg {
  text-align: center;
  padding: 32px 16px;
}

.welcome-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.welcome-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.welcome-text {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quick-btn {
  padding: 8px 14px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.quick-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

/* 消息 */
.chat-msg {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 28px;
  height: 28px;
  font-size: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg-bubble {
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-msg.user .msg-bubble {
  background: var(--accent);
  color: #fff;
  border-bottom-right-radius: 2px;
}

.chat-msg.assistant .msg-bubble {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-bottom-left-radius: 2px;
}

.msg-badge {
  margin-top: 4px;
  padding: 2px 8px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 4px;
  font-size: 11px;
  color: var(--accent);
}

/* Thinking animation */
.thinking .dots {
  animation: dots 1.2s steps(3, end) infinite;
}

@keyframes dots {
  0% { content: ''; opacity: 0.3; }
  33% { opacity: 0.6; }
  66% { opacity: 0.9; }
  100% { opacity: 0.3; }
}

/* 输入区 */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.chat-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  font-family: inherit;
}

.chat-input:focus {
  border-color: var(--accent);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--accent);
  color: #fff;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
