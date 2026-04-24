<template>
  <div class="text-block" :style="textStyle">
    {{ props.content }}
  </div>
</template>

<script setup>
import { computed } from 'vue'

const p = defineProps({
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

const textStyle = computed(() => ({
  fontSize: `${p.props.fontSize}px`,
  textAlign: p.props.align,
  color: p.props.color || 'var(--text-primary)',
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
