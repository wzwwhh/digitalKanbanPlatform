<script setup>
/**
 * 编辑器入口页面 — 包裹现有的 AppLayout (Workspace + PropEditor + AiChat)
 * Phase 3 中会改造为 EditorLayout
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const route = useRoute()
const projectId = computed(() => route.params.projectId)
const dashboardId = computed(() => route.params.dashboardId)
const aiPrompt = computed(() => route.query.aiPrompt || '')
</script>

<template>
  <AppLayout
    :projectId="projectId"
    :dashboardId="dashboardId"
    :aiPrompt="aiPrompt"
  />
</template>
