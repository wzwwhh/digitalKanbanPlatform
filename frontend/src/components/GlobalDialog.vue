<template>
  <Transition name="dialog">
    <div v-if="dialog.state.show" class="dialog-overlay" @click.self="dialog.handleCancel">
      <div class="dialog-box">
        <h3 class="dialog-title">{{ dialog.state.title }}</h3>
        <input
          v-if="dialog.state.type === 'prompt'"
          ref="inputRef"
          v-model="dialog.inputValue.value"
          class="dialog-input"
          :placeholder="dialog.state.placeholder"
          @keydown.enter="dialog.handleConfirm"
          autofocus
        />
        <div class="dialog-actions">
          <button class="btn-cancel" @click="dialog.handleCancel">取消</button>
          <button class="btn-confirm" @click="dialog.handleConfirm">
            {{ dialog.state.type === 'confirm' ? '确认' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useDialog } from '../composables/useDialog'

const dialog = useDialog()
const inputRef = ref(null)

// 自动聚焦
watch(() => dialog.state.show, (show) => {
  if (show && dialog.state.type === 'prompt') {
    nextTick(() => inputRef.value?.focus())
  }
})
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
}

.dialog-box {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 14px;
  padding: 24px;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
}

.dialog-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin: 0 0 16px;
}

.dialog-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-primary, #0a0e27);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
  margin-bottom: 16px;
}

.dialog-input:focus {
  border-color: var(--accent, #00d4ff);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-cancel {
  padding: 8px 18px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #2a3560);
  background: none;
  color: var(--text-secondary, #8892b0);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: var(--text-secondary, #8892b0);
}

.btn-confirm {
  padding: 8px 18px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-confirm:hover {
  opacity: 0.9;
}

/* Transitions */
.dialog-enter-active { transition: all 0.25s ease; }
.dialog-leave-active { transition: all 0.15s ease; }
.dialog-enter-from { opacity: 0; }
.dialog-enter-from .dialog-box { transform: scale(0.95) translateY(10px); }
.dialog-leave-to { opacity: 0; }
.dialog-leave-to .dialog-box { transform: scale(0.98); }
</style>
