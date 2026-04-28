<template>
  <div class="border-box" :class="[styleClass, { glowing: p.props.glowing !== false }]">
    <div class="corner tl"></div>
    <div class="corner tr"></div>
    <div class="corner bl"></div>
    <div class="corner br"></div>
    <div v-if="p.props.title" class="border-title">
      <span class="title-decoration"></span>
      {{ p.props.title }}
    </div>
    <div class="border-content" :class="{ 'has-title': !!p.props.title }">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const styleClass = computed(() => p.props.style || 'tech-1')
</script>

<style scoped>
.border-box {
  width: 100%; height: 100%;
  position: relative;
  background: transparent;
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 4px;
  box-sizing: border-box;
  padding: 12px;
}

/* 四角装饰 */
.corner {
  position: absolute;
  width: 12px;
  height: 12px;
  border-color: var(--accent, #00d4ff);
}

.corner.tl { top: -1px; left: -1px; border-top: 2px solid; border-left: 2px solid; }
.corner.tr { top: -1px; right: -1px; border-top: 2px solid; border-right: 2px solid; }
.corner.bl { bottom: -1px; left: -1px; border-bottom: 2px solid; border-left: 2px solid; }
.corner.br { bottom: -1px; right: -1px; border-bottom: 2px solid; border-right: 2px solid; }

/* 发光效果 */
.border-box.glowing {
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.08), inset 0 0 12px rgba(0, 212, 255, 0.03);
}

/* 科技风 1 */
.border-box.tech-1 {
  border-color: rgba(0, 212, 255, 0.3);
}

/* 科技风 2 */
.border-box.tech-2 {
  border-color: rgba(123, 97, 255, 0.3);
}
.border-box.tech-2 .corner { border-color: #7b61ff; }
.border-box.tech-2.glowing {
  box-shadow: 0 0 12px rgba(123, 97, 255, 0.08), inset 0 0 12px rgba(123, 97, 255, 0.03);
}

/* 简洁 */
.border-box.simple {
  border-color: var(--border-color, #2a3560);
  border-radius: 8px;
}
.border-box.simple .corner { display: none; }

.border-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #e0e6ff);
  margin-bottom: 8px;
}

.title-decoration {
  width: 3px;
  height: 14px;
  background: var(--accent, #00d4ff);
  border-radius: 2px;
}

.border-content {
  width: 100%;
  height: 100%;
}
.border-content.has-title {
  height: calc(100% - 30px);
}
</style>
