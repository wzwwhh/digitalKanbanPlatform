<template>
  <Transition name="toast">
    <div v-if="toast.state.show" class="global-toast" :class="toast.state.type">
      {{ toast.state.message }}
    </div>
  </Transition>
</template>

<script setup>
import { useToast } from '../composables/useToast'
const toast = useToast()
</script>

<style scoped>
.global-toast {
  position: fixed;
  top: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  z-index: 10000;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.global-toast.success { background: var(--accent-success, #00e676); }
.global-toast.error { background: var(--accent-danger, #ff1744); }
.global-toast.warning { background: var(--accent-warning, #ffb300); color: #000; }
.global-toast.info { background: var(--accent-info, #00d4ff); color: #000; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1); }
.toast-enter-from { opacity: 0; transform: translate(-50%, -20px); }
.toast-leave-to { opacity: 0; transform: translate(-50%, -20px); }
</style>
