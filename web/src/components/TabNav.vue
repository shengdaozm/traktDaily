<script setup>
const emit = defineEmits(['change'])
defineProps({
  tabs: { type: Array, required: true },
})
const model = defineModel({ type: String })

function select(key) {
  if (model.value !== key) {
    model.value = key
    emit('change', key)
  }
}
</script>

<template>
  <nav class="tab-nav">
    <button
      v-for="tab in tabs" :key="tab.key"
      class="tab-btn" :class="{ active: model === tab.key }"
      @click="select(tab.key)"
    >
      {{ tab.icon }} {{ tab.label }}
    </button>
  </nav>
</template>

<style scoped>
.tab-nav {
  display: flex; gap: 4px; margin-bottom: 28px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 5px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  position: sticky; top: 16px; z-index: 100;
  box-shadow: var(--shadow);
}
.tab-btn {
  flex: 1; padding: 10px 16px; border: none; background: transparent;
  color: var(--muted); font-size: 0.9rem; font-weight: 600;
  border-radius: var(--radius-sm); cursor: pointer;
  transition: all var(--transition);
}
.tab-btn:hover { color: var(--text-bright); }
.tab-btn.active { background: rgba(88, 166, 255, 0.12); color: var(--primary); }

@media (max-width: 768px) {
  .tab-btn { font-size: 0.8rem; padding: 8px 10px; }
}
</style>
