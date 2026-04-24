<template>
  <div class="prop-editor" v-if="widget">
    <div class="editor-section">
      <div class="section-label">组件类型</div>
      <div class="type-badge">{{ widgetDef?.label || widget.type }}</div>
    </div>

    <!-- Schema 驱动的属性表单 -->
    <div class="editor-section" v-for="(field, key) in schema" :key="key">
      <label class="field-label">{{ field.label }}</label>

      <!-- 字符串 -->
      <input
        v-if="field.type === 'string'"
        type="text"
        class="field-input"
        :value="widget.props[key]"
        @input="updateProp(key, $event.target.value)"
      />

      <!-- 数字 -->
      <input
        v-if="field.type === 'number'"
        type="number"
        class="field-input"
        :value="widget.props[key]"
        @input="updateProp(key, Number($event.target.value))"
      />

      <!-- 布尔 -->
      <label v-if="field.type === 'boolean'" class="field-switch">
        <input
          type="checkbox"
          :checked="widget.props[key]"
          @change="updateProp(key, $event.target.checked)"
        />
        <span class="switch-slider"></span>
        <span class="switch-label">{{ widget.props[key] ? '开' : '关' }}</span>
      </label>

      <!-- 下拉选择 -->
      <select
        v-if="field.type === 'select'"
        class="field-input"
        :value="widget.props[key]"
        @change="updateProp(key, $event.target.value)"
      >
        <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
      </select>

      <!-- 颜色 -->
      <div v-if="field.type === 'color'" class="field-color">
        <input
          type="color"
          :value="widget.props[key] || '#00d4ff'"
          @input="updateProp(key, $event.target.value)"
          class="color-picker"
        />
        <input
          type="text"
          class="field-input color-text"
          :value="widget.props[key]"
          @input="updateProp(key, $event.target.value)"
          placeholder="默认"
        />
      </div>
    </div>

    <!-- 位置和尺寸 -->
    <div class="editor-section">
      <div class="section-label">位置与尺寸</div>
      <div class="pos-grid">
        <div class="pos-field">
          <label>X</label>
          <input type="number" :value="widget.position.x" @input="updatePosition('x', $event)" />
        </div>
        <div class="pos-field">
          <label>Y</label>
          <input type="number" :value="widget.position.y" @input="updatePosition('y', $event)" />
        </div>
        <div class="pos-field">
          <label>W</label>
          <input type="number" :value="widget.size.w" @input="updateSize('w', $event)" />
        </div>
        <div class="pos-field">
          <label>H</label>
          <input type="number" :value="widget.size.h" @input="updateSize('h', $event)" />
        </div>
      </div>
    </div>

    <!-- 删除 -->
    <div class="editor-section">
      <button class="btn-delete" @click="deleteWidget">🗑️ 删除组件</button>
    </div>
  </div>

  <div v-else class="prop-empty">
    <div class="empty-icon">👆</div>
    <p>点击画布上的组件</p>
    <p>查看和编辑属性</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { executeCommand, createCommand, CommandType } from '../core/command'
import { getWidget } from '../core/registry'

const dashboardStore = useDashboardStore()

const widget = computed(() => dashboardStore.selectedWidget)
const widgetDef = computed(() => widget.value ? getWidget(widget.value.type) : null)
const schema = computed(() => widgetDef.value?.schema || {})

function updateProp(key, value) {
  if (!widget.value) return
  executeCommand(createCommand(CommandType.UPDATE_WIDGET, {
    id: widget.value.id,
    props: { [key]: value },
  }))
}

function updatePosition(axis, event) {
  if (!widget.value) return
  const val = Number(event.target.value)
  executeCommand(createCommand(CommandType.MOVE_WIDGET, {
    id: widget.value.id,
    position: {
      ...widget.value.position,
      [axis]: Math.max(0, val),
    },
  }))
}

function updateSize(dim, event) {
  if (!widget.value) return
  const val = Number(event.target.value)
  executeCommand(createCommand(CommandType.RESIZE_WIDGET, {
    id: widget.value.id,
    size: {
      ...widget.value.size,
      [dim]: Math.max(dim === 'w' ? 80 : 60, val),
    },
  }))
}

function deleteWidget() {
  if (!widget.value) return
  if (confirm('确定删除这个组件？')) {
    executeCommand(createCommand(CommandType.DELETE_WIDGET, { id: widget.value.id }))
  }
}
</script>

<style scoped>
.prop-editor {
  padding: 12px;
}

.editor-section {
  margin-bottom: 16px;
}

.section-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.type-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 13px;
  color: var(--accent);
}

.field-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.field-input {
  width: 100%;
  padding: 6px 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}

.field-input:focus {
  border-color: var(--accent);
}

/* Switch */
.field-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.field-switch input {
  display: none;
}

.switch-slider {
  width: 36px;
  height: 20px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  position: relative;
  transition: all 0.2s;
}

.switch-slider::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: var(--text-muted);
  border-radius: 50%;
  top: 1px;
  left: 1px;
  transition: all 0.2s;
}

.field-switch input:checked + .switch-slider {
  background: var(--accent);
  border-color: var(--accent);
}

.field-switch input:checked + .switch-slider::after {
  left: 17px;
  background: #fff;
}

.switch-label {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Color */
.field-color {
  display: flex;
  gap: 8px;
  align-items: center;
}

.color-picker {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
  background: transparent;
}

.color-text {
  flex: 1;
}

/* Position grid */
.pos-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.pos-field {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pos-field label {
  font-size: 11px;
  color: var(--text-muted);
  width: 16px;
  flex-shrink: 0;
}

.pos-field input {
  width: 100%;
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
}

.pos-field input:focus {
  border-color: var(--accent);
}

/* Delete */
.btn-delete {
  width: 100%;
  padding: 8px;
  background: transparent;
  border: 1px solid var(--accent-danger);
  border-radius: 6px;
  color: var(--accent-danger);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-delete:hover {
  background: rgba(255, 69, 96, 0.1);
}

/* Empty state */
.prop-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.8;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
  opacity: 0.5;
}
</style>
