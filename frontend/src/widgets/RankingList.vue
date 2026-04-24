<template>
  <div class="placeholder-widget">
    <div class="placeholder-icon">{{ icon }}</div>
    <div class="placeholder-label">{{ label }}</div>
  </div>
</template>
<script setup>
defineProps({ props: { type: Object, default: () => ({}) } })
const icon = '🚧'
const label = '开发中'
</script>
<style scoped>
.placeholder-widget { width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:var(--bg-card); border-radius:8px; border:1px solid var(--border-color); color:var(--text-muted); }
.placeholder-icon { font-size:32px; margin-bottom:8px; }
.placeholder-label { font-size:13px; }
</style>
