/**
 * History Store - 撤销/重做历史栈
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const MAX_HISTORY = 50

export const useHistoryStore = defineStore('history', () => {
  const undoStack = ref([])
  const redoStack = ref([])

  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  /**
   * 推入新命令（执行后调用）
   */
  function push(cmd) {
    undoStack.value.push(cmd)
    // 新操作后清空重做栈
    redoStack.value = []
    // 限制栈大小
    if (undoStack.value.length > MAX_HISTORY) {
      undoStack.value.shift()
    }
  }

  /**
   * 弹出撤销栈顶
   */
  function popUndo() {
    return undoStack.value.pop() || null
  }

  /**
   * 推入重做栈
   */
  function pushRedo(cmd) {
    redoStack.value.push(cmd)
  }

  /**
   * 弹出重做栈顶
   */
  function popRedo() {
    return redoStack.value.pop() || null
  }

  /**
   * 清空历史
   */
  function clear() {
    undoStack.value = []
    redoStack.value = []
  }

  return {
    undoStack,
    redoStack,
    canUndo,
    canRedo,
    push,
    popUndo,
    pushRedo,
    popRedo,
    clear,
  }
})
