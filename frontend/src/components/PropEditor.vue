<template>
  <div class="prop-editor" v-if="widget">
    <div class="editor-section">
      <div class="section-label">组件类型</div>
      <div class="type-badge">{{ widgetDef?.label || widget.type }}</div>
    </div>

    <!-- Sub Tabs -->
    <div class="sub-tabs">
      <button class="sub-tab" :class="{ active: subTab === 'style' }" @click="subTab = 'style'">🎨 样式</button>
      <button class="sub-tab" :class="{ active: subTab === 'data' }" @click="subTab = 'data'">📊 数据</button>
    </div>

    <!-- ===== 样式 Tab ===== -->
    <div v-if="subTab === 'style'">
      <!-- 全局外边框样式 -->
      <div class="editor-section">
        <div class="section-label">外框装饰</div>
        <select
          class="field-input"
          :value="widget.props.borderStyle || 'none'"
          @change="updateProp('borderStyle', $event.target.value)"
        >
          <option value="none">无边框</option>
          <option value="tech-1">科幻蓝 (Tech 1)</option>
          <option value="tech-2">科幻紫 (Tech 2)</option>
          <option value="simple">实线框 (Simple)</option>
        </select>
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

        <!-- 多行文本 / JSON -->
        <textarea
          v-if="field.type === 'textarea'"
          class="field-input field-textarea"
          :value="widget.props[key]"
          @input="updateProp(key, $event.target.value)"
          rows="6"
          :placeholder="field.label"
          spellcheck="false"
        ></textarea>
      </div>

      <!-- 位置和尺寸 -->
      <div class="editor-section">
        <div class="section-label">位置与尺寸</div>
        <div class="pos-grid">
          <div class="pos-field">
            <label>X</label>
            <input type="number" :value="widget.position.x" @change="updatePosition('x', $event)" />
          </div>
          <div class="pos-field">
            <label>Y</label>
            <input type="number" :value="widget.position.y" @change="updatePosition('y', $event)" />
          </div>
          <div class="pos-field">
            <label>W</label>
            <input type="number" :value="widget.size.w" @change="updateSize('w', $event)" />
          </div>
          <div class="pos-field">
            <label>H</label>
            <input type="number" :value="widget.size.h" @change="updateSize('h', $event)" />
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 数据 Tab ===== -->
    <div v-if="subTab === 'data'">
      <!-- 数据源选择 -->
      <div class="editor-section">
        <div class="section-label">数据源</div>
        <select class="field-input" :value="widget.dataSource?.sourceId || ''" @change="onSelectDataSource($event.target.value)">
          <option value="">不绑定（使用默认数据）</option>
          <option v-for="ds in dataSources" :key="ds.id" :value="ds.id">
            {{ ds.name }} ({{ (ds.fields || []).length }}字段)
          </option>
        </select>
      </div>

      <!-- 已绑定数据源时显示字段映射 -->
      <template v-if="boundDataSource">
        <div class="editor-section">
          <div class="section-label">字段映射</div>
          <div class="ds-info">
            <span class="ds-badge">{{ boundDataSource.name }}</span>
            <span class="ds-structure">{{ boundDataSource.structure }}</span>
          </div>
        </div>

        <!-- 根据组件类型显示不同的映射字段 -->
        <template v-if="mappingSchema.length > 0">
          <div class="editor-section" v-for="mf in mappingSchema" :key="mf.key">
            <label class="field-label">{{ mf.label }}</label>
            <select class="field-input" :value="currentMapping[mf.key] || ''" @change="updateMappingField(mf.key, $event.target.value)">
              <option value="">-- 选择字段 --</option>
              <option v-for="f in boundDataSource.fields" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
        </template>
      </template>

      <!-- 无可用数据源提示 -->
      <div v-if="dataSources.length === 0" class="data-hint">
        <div class="hint-icon">🔗</div>
        <p>尚未添加数据源</p>
        <p class="hint-sub">请到侧边栏「数据源」页面添加</p>
      </div>
    </div>

    <!-- 删除 -->
    <div class="editor-section" style="margin-top: 16px;">
      <button class="btn-delete" @click="deleteWidget">🗑️ 删除组件</button>
    </div>
  </div>

  <!-- 未选中任何组件时：显示看板属性 -->
  <div v-else class="prop-editor dashboard-props">
    <div class="editor-section">
      <div class="section-label">看板属性</div>
      <div class="field-label">主题风格</div>
      <ThemePicker
        :current-board-style="themeStore.currentBoardStyle"
        :show-system-theme="false"
        @change-board="themeStore.applyBoardStyle"
      />
      <p class="hint">看板风格将影响当前大屏的配色方案</p>
    </div>
    
    <div class="prop-empty" style="height: auto; margin-top: 40px;">
      <div class="empty-icon">👆</div>
      <p>点击画布上的组件</p>
      <p>查看和编辑组件属性</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useProjectStore } from '../stores/project'
import { useThemeStore } from '../stores/theme'
import { executeCommand, createCommand, CommandType } from '../core/command'
import { getWidget } from '../core/registry'
import { useDialog } from '../composables/useDialog'
import ThemePicker from './ThemePicker.vue'

const dashboardStore = useDashboardStore()
const projectStore = useProjectStore()
const themeStore = useThemeStore()
const { confirm: showConfirm } = useDialog()

const subTab = ref('style')

const widget = computed(() => dashboardStore.selectedWidget)
const widgetDef = computed(() => widget.value ? getWidget(widget.value.type) : null)
const schema = computed(() => widgetDef.value?.schema || {})

const dataSources = computed(() => projectStore.currentProject?.dataSources || [])
const boundDataSource = computed(() => {
  const sid = widget.value?.dataSource?.sourceId
  if (!sid) return null
  return dataSources.value.find(ds => ds.id === sid) || null
})
const currentMapping = computed(() => widget.value?.dataSource?.mapping || {})

// 根据组件类型定义 mapping schema
const mappingSchema = computed(() => {
  if (!widget.value) return []
  const t = widget.value.type
  if (t === 'line' || t === 'bar') {
    return [
      { key: 'x', label: 'X轴 (分类/时间)' },
      { key: 'y', label: 'Y轴 (数值)' },
    ]
  }
  if (t === 'pie') {
    return [
      { key: 'name', label: '名称字段' },
      { key: 'value', label: '数值字段' },
    ]
  }
  if (t === 'kpi' || t === 'number-flip' || t === 'gauge') {
    return [
      { key: 'value', label: '数值字段' },
    ]
  }
  if (t === 'table' || t === 'ranking') {
    return [
      { key: 'name', label: '名称字段' },
      { key: 'value', label: '数值字段' },
    ]
  }
  if (t === 'scatter') {
    return [
      { key: 'x', label: 'X轴字段' },
      { key: 'y', label: 'Y轴字段' },
    ]
  }
  return []
})

// 选中组件时自动切到样式 tab
watch(widget, () => {
  subTab.value = 'style'
})

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

function onSelectDataSource(sourceId) {
  if (!widget.value) return
  if (!sourceId) {
    // 解绑
    executeCommand(createCommand(CommandType.UPDATE_WIDGET, {
      id: widget.value.id,
      dataSource: null,
    }))
  } else {
    executeCommand(createCommand(CommandType.UPDATE_WIDGET, {
      id: widget.value.id,
      dataSource: {
        sourceId,
        mapping: widget.value.dataSource?.mapping || {},
      },
    }))
  }
}

function updateMappingField(key, value) {
  if (!widget.value) return
  const newMapping = { ...(widget.value.dataSource?.mapping || {}), [key]: value }
  executeCommand(createCommand(CommandType.UPDATE_WIDGET, {
    id: widget.value.id,
    dataSource: {
      ...(widget.value.dataSource || {}),
      mapping: newMapping,
    },
  }))
}

async function deleteWidget() {
  if (!widget.value) return
  const ok = await showConfirm('确定删除这个组件？')
  if (ok) {
    executeCommand(createCommand(CommandType.DELETE_WIDGET, { id: widget.value.id }))
    dashboardStore.deselectAll()
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

/* Sub Tabs */
.sub-tabs {
  display: flex;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
}

.sub-tab {
  flex: 1;
  padding: 8px 0;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.sub-tab:hover {
  color: var(--text-primary);
}

.sub-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
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
  box-sizing: border-box;
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

/* Textarea */
.field-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
  padding: 8px;
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

/* Data Tab */
.ds-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.ds-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 4px;
  color: var(--accent);
}

.ds-structure {
  font-size: 11px;
  color: var(--text-muted);
  font-family: monospace;
}

.data-hint {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted);
  font-size: 13px;
}

.hint-icon {
  font-size: 28px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.hint-sub {
  font-size: 11px;
  color: var(--text-muted);
  opacity: 0.7;
}

.hint {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
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
