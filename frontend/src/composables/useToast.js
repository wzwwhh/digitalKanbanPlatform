import { reactive } from 'vue'

const state = reactive({
  show: false,
  message: '',
  type: 'success', // 'success' | 'error' | 'warning' | 'info'
})

let timer = null

export function useToast() {
  function show(msg, type = 'success', duration = 2500) {
    if (timer) clearTimeout(timer)
    state.message = msg
    state.type = type
    state.show = true
    timer = setTimeout(() => {
      state.show = false
    }, duration)
  }

  function success(msg, duration) { show(msg, 'success', duration) }
  function error(msg, duration) { show(msg, 'error', duration) }
  function warning(msg, duration) { show(msg, 'warning', duration) }
  function info(msg, duration) { show(msg, 'info', duration) }

  return {
    state,
    show,
    success,
    error,
    warning,
    info
  }
}
