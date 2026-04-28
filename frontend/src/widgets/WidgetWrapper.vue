<template>
  <div
    class="widget-wrapper"
    :class="{ selected }"
    :style="wrapperStyle"
    @mousedown.stop="onMouseDown"
  >
    <!-- 如果有边框样式，用 BorderBox 包裹 -->
    <BorderBox 
      v-if="widget.props.borderStyle && widget.props.borderStyle !== 'none'" 
      :props="{ style: widget.props.borderStyle, glowing: true }"
      class="widget-content"
    >
      <component
        :is="widgetComponent"
        :props="widget.props"
        :widget="widget"
        style="width:100%; height:100%;"
      />
    </BorderBox>

    <!-- 动态渲染组件 -->
    <component
      v-else
      :is="widgetComponent"
      :props="widget.props"
      :widget="widget"
      class="widget-content"
    />

    <!-- 选中时的缩放手柄 -->
    <template v-if="selected">
      <div class="resize-handle nw" @mousedown.stop="onResizeStart('nw', $event)"></div>
      <div class="resize-handle ne" @mousedown.stop="onResizeStart('ne', $event)"></div>
      <div class="resize-handle sw" @mousedown.stop="onResizeStart('sw', $event)"></div>
      <div class="resize-handle se" @mousedown.stop="onResizeStart('se', $event)"></div>
    </template>
  </div>
</template>

<script setup>
import { computed, shallowRef, watch } from 'vue'
import { getWidget } from '../core/registry'
import BorderBox from './BorderBox.vue'

const props = defineProps({
  widget: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  scale: { type: Number, default: 1 },
})

const emit = defineEmits(['select', 'move', 'resize'])

// 动态加载组件
const widgetComponent = shallowRef(null)

watch(() => props.widget.type, async (type) => {
  const def = getWidget(type)
  if (def && def.component) {
    const mod = await def.component()
    widgetComponent.value = mod.default
  } else {
    widgetComponent.value = null
  }
}, { immediate: true })

const wrapperStyle = computed(() => ({
  left: `${props.widget.position.x}px`,
  top: `${props.widget.position.y}px`,
  width: `${props.widget.size.w}px`,
  height: `${props.widget.size.h}px`,
}))

// 拖拽移动
let startX = 0, startY = 0, startPos = { x: 0, y: 0 }

function onMouseDown(e) {
  emit('select')

  startX = e.clientX
  startY = e.clientY
  startPos = { ...props.widget.position }
  const wrapperEl = e.currentTarget

  const onMouseMove = (e) => {
    const dx = (e.clientX - startX) / props.scale
    const dy = (e.clientY - startY) / props.scale
    if (wrapperEl && wrapperEl.classList) {
      wrapperEl.style.left = `${startPos.x + dx}px`
      wrapperEl.style.top = `${startPos.y + dy}px`
    }
  }

  const onMouseUp = (e) => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)

    const dx = (e.clientX - startX) / props.scale
    const dy = (e.clientY - startY) / props.scale
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
      emit('move', {
        x: Math.max(0, Math.round(startPos.x + dx)),
        y: Math.max(0, Math.round(startPos.y + dy)),
      })
    }
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// 缩放
function onResizeStart(corner, e) {
  const startX = e.clientX
  const startY = e.clientY
  const startSize = { ...props.widget.size }
  const startPos = { ...props.widget.position }

  const resizeEl = e.currentTarget.parentElement || e.currentTarget

  const onMouseMove = (e) => {
    const dx = (e.clientX - startX) / props.scale
    const dy = (e.clientY - startY) / props.scale
    let newW = startSize.w, newH = startSize.h
    let newX = startPos.x, newY = startPos.y

    if (corner.includes('e')) newW = Math.max(80, startSize.w + dx)
    if (corner.includes('w')) { newW = Math.max(80, startSize.w - dx); newX = startPos.x + dx }
    if (corner.includes('s')) newH = Math.max(60, startSize.h + dy)
    if (corner.includes('n')) { newH = Math.max(60, startSize.h - dy); newY = startPos.y + dy }

    if (resizeEl && resizeEl.classList) {
      resizeEl.style.width = `${newW}px`
      resizeEl.style.height = `${newH}px`
      resizeEl.style.left = `${newX}px`
      resizeEl.style.top = `${newY}px`
    }
  }

  const onMouseUp = (e) => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)

    const dx = (e.clientX - startX) / props.scale
    const dy = (e.clientY - startY) / props.scale
    let newW = startSize.w, newH = startSize.h

    if (corner.includes('e')) newW = Math.max(80, Math.round(startSize.w + dx))
    if (corner.includes('w')) newW = Math.max(80, Math.round(startSize.w - dx))
    if (corner.includes('s')) newH = Math.max(60, Math.round(startSize.h + dy))
    if (corner.includes('n')) newH = Math.max(60, Math.round(startSize.h - dy))

    emit('resize', { w: newW, h: newH })

    if (corner.includes('w') || corner.includes('n')) {
      let newX = startPos.x, newY = startPos.y
      if (corner.includes('w')) newX = startPos.x + (startSize.w - newW)
      if (corner.includes('n')) newY = startPos.y + (startSize.h - newH)
      emit('move', { x: Math.max(0, newX), y: Math.max(0, newY) })
    }
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
</script>

<style scoped>
.widget-wrapper {
  position: absolute;
  cursor: move;
  transition: box-shadow 0.15s ease;
}

.widget-wrapper.selected {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
  box-shadow: var(--shadow-glow);
  z-index: 10;
}

.widget-content {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 缩放手柄 */
.resize-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--accent);
  border: 2px solid var(--bg-primary);
  border-radius: 2px;
  z-index: 20;
}

.resize-handle.nw { top: -5px; left: -5px; cursor: nw-resize; }
.resize-handle.ne { top: -5px; right: -5px; cursor: ne-resize; }
.resize-handle.sw { bottom: -5px; left: -5px; cursor: sw-resize; }
.resize-handle.se { bottom: -5px; right: -5px; cursor: se-resize; }
</style>
