<template>
  <div class="text-block" :style="textStyle">
    {{ widgetProps.content }}
  </div>
</template>

<script setup>
import { computed } from 'vue'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
    props: {
    type: Object,
    default: () => ({
      content: '标题文本',
      fontSize: 24,
      align: 'center',
      color: '',
    })
  }
})

// 用 widgetProps 避免 props.props 混淆
const widgetProps = computed(() => p.props || {})

const textStyle = computed(() => ({
  fontSize: `${widgetProps.value.fontSize || 24}px`,
  textAlign: widgetProps.value.align || 'center',
  color: widgetProps.value.color || 'var(--text-primary)',
}))
</script>

<style scoped>
.text-block {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  padding: 8px 16px;
  box-sizing: border-box;
  word-break: break-word;
}
</style>
