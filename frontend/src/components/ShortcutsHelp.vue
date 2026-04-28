<template>
  <Transition name="help-fade">
    <div v-if="visible" class="help-overlay" @click.self="$emit('close')">
      <div class="help-panel">
        <div class="help-header">
          <h2>⌨️ 快捷键</h2>
          <button class="help-close" @click="$emit('close')">✕</button>
        </div>
        <div class="help-body">
          <div v-for="group in shortcuts" :key="group.title" class="shortcut-group">
            <h3>{{ group.title }}</h3>
            <div v-for="item in group.items" :key="item.key" class="shortcut-item">
              <kbd>{{ item.key }}</kbd>
              <span>{{ item.desc }}</span>
            </div>
          </div>
        </div>
        <div class="help-footer">
          <span>按 <kbd>?</kbd> 关闭</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
})
defineEmits(['close'])

const shortcuts = [
  {
    title: '编辑操作',
    items: [
      { key: 'Ctrl + S', desc: '保存看板' },
      { key: 'Ctrl + Z', desc: '撤销' },
      { key: 'Ctrl + Y', desc: '重做' },
      { key: 'Ctrl + D', desc: '复制选中组件' },
      { key: 'Delete', desc: '删除选中组件' },
    ]
  },
  {
    title: '画布操作',
    items: [
      { key: '滚轮', desc: '缩放画布' },
      { key: '右键', desc: '上下文菜单' },
      { key: '拖拽', desc: '移动组件' },
      { key: '角点拖拽', desc: '调整大小' },
    ]
  },
  {
    title: '预览',
    items: [
      { key: 'ESC', desc: '退出预览' },
      { key: 'F', desc: '全屏切换' },
      { key: '?', desc: '打开/关闭快捷键面板' },
    ]
  },
]
</script>

<style scoped>
.help-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
}

.help-panel {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 16px;
  width: 420px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
}

.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.help-header h2 {
  font-size: 18px;
  color: var(--text-primary, #e0e6ff);
  margin: 0;
}

.help-close {
  background: none;
  border: none;
  color: var(--text-muted, #4a5578);
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  transition: color 0.15s;
}

.help-close:hover {
  color: var(--text-primary, #e0e6ff);
}

.help-body {
  padding: 16px 24px;
}

.shortcut-group {
  margin-bottom: 16px;
}

.shortcut-group h3 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted, #4a5578);
  margin: 0 0 8px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.shortcut-item span {
  font-size: 13px;
  color: var(--text-secondary, #8892b0);
}

kbd {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  font-family: 'Inter', monospace;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 4px;
  color: var(--text-primary, #e0e6ff);
  min-width: 32px;
  text-align: center;
}

.help-footer {
  padding: 12px 24px;
  border-top: 1px solid var(--border-color, #2a3560);
  text-align: center;
  font-size: 12px;
  color: var(--text-muted, #4a5578);
}

.help-footer kbd {
  margin: 0 2px;
}

.help-fade-enter-active { transition: all 0.2s ease; }
.help-fade-leave-active { transition: all 0.15s ease; }
.help-fade-enter-from, .help-fade-leave-to { opacity: 0; }
.help-fade-enter-from .help-panel { transform: scale(0.95); }
</style>
