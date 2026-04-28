<template>
  <div class="theme-pickers">
    <div class="theme-group" v-if="showSystemTheme">
      <div class="theme-picker-title">主题</div>
      <div class="theme-dropdown" @click="open = !open" ref="dropdownRef">
        <span class="theme-current">
          <span class="mini-swatch" :style="{ background: currentAccent }"></span>
          {{ currentLabel }}
        </span>
        <span class="dropdown-arrow">{{ open ? '▲' : '▼' }}</span>
      </div>
      <Transition name="dropdown">
        <div v-if="open" class="theme-options">
          <div
            v-for="t in themeList"
            :key="t.id"
            class="theme-option"
            :class="{ active: currentSystemTheme === t.id }"
            @click="selectTheme(t.id)"
          >
            <span class="mini-swatch" :style="{ background: t.accent }"></span>
            <span>{{ t.label }}</span>
            <span v-if="currentSystemTheme === t.id" class="check">✓</span>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useThemeStore } from '../stores/theme'

const props = defineProps({
  currentSystemTheme: { type: String, default: 'dark-tech' },
  currentBoardStyle: { type: String, default: 'dark-tech' },
  showSystemTheme: { type: Boolean, default: true },
  showBoardStyle: { type: Boolean, default: true },
})

const emit = defineEmits(['change-system', 'change-board'])
const open = ref(false)
const dropdownRef = ref(null)

const tStore = useThemeStore()
const themeList = computed(() =>
  tStore.allThemes.map(t => ({
    id: t.id,
    label: t.label || t.id,
    accent: t.vars?.['--accent'] || '#00d4ff',
  }))
)

const currentLabel = computed(() => {
  const t = themeList.value.find(t => t.id === props.currentSystemTheme)
  return t?.label || props.currentSystemTheme
})

const currentAccent = computed(() => {
  const t = themeList.value.find(t => t.id === props.currentSystemTheme)
  return t?.accent || '#00d4ff'
})

function selectTheme(id) {
  emit('change-system', id)
  open.value = false
}

function handleClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
.theme-pickers {
  display: flex;
  gap: 12px;
  align-items: center;
}

.theme-group {
  display: flex;
  gap: 6px;
  align-items: center;
  position: relative;
}

.theme-picker-title {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.theme-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-primary, #e0e6ff);
  transition: border-color 0.15s;
  user-select: none;
}

.theme-dropdown:hover {
  border-color: var(--accent, #00d4ff);
}

.theme-current {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dropdown-arrow {
  font-size: 8px;
  color: var(--text-muted);
}

.theme-options {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  min-width: 160px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  padding: 4px;
  z-index: 1000;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary, #8892b0);
  cursor: pointer;
  transition: all 0.15s;
}

.theme-option:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary, #e0e6ff);
}

.theme-option.active {
  color: var(--accent, #00d4ff);
}

.mini-swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.check {
  margin-left: auto;
  font-size: 12px;
  color: var(--accent, #00d4ff);
}

/* Transitions */
.dropdown-enter-active { transition: all 0.15s ease; }
.dropdown-leave-active { transition: all 0.1s ease; }
.dropdown-enter-from { opacity: 0; transform: translateY(-4px); }
.dropdown-leave-to { opacity: 0; }
</style>
