/**
 * useDialog — 通用对话框 composable
 * 替代 window.prompt / confirm，提供统一的 UI
 */
import { ref, reactive } from 'vue'

const state = reactive({
  show: false,
  title: '',
  placeholder: '',
  defaultValue: '',
  confirmText: '确认',
  cancelText: '取消',
  type: 'prompt', // prompt | confirm
  resolve: null,
})

const inputValue = ref('')

export function useDialog() {
  function prompt(title, defaultValue = '', placeholder = '') {
    return new Promise((resolve) => {
      state.show = true
      state.title = title
      state.placeholder = placeholder || title
      state.defaultValue = defaultValue
      state.type = 'prompt'
      state.resolve = resolve
      inputValue.value = defaultValue
    })
  }

  function confirm(title) {
    return new Promise((resolve) => {
      state.show = true
      state.title = title
      state.type = 'confirm'
      state.resolve = resolve
    })
  }

  function handleConfirm() {
    if (state.type === 'prompt') {
      state.resolve?.(inputValue.value.trim() || null)
    } else {
      state.resolve?.(true)
    }
    state.show = false
  }

  function handleCancel() {
    state.resolve?.(state.type === 'confirm' ? false : null)
    state.show = false
  }

  return {
    state,
    inputValue,
    prompt,
    confirm,
    handleConfirm,
    handleCancel,
  }
}
