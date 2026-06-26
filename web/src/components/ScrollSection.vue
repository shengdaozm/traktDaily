<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  bg: { type: String, default: '' },
  gradient: { type: String, default: 'var(--grad-1)' },
})

const sectionRef = ref(null)
const visible = ref(false)
const bgStyle = props.bg ? { backgroundImage: `url(${props.bg})` } : {}
const gradStyle = { background: props.gradient }

let observer = null

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) visible.value = true
    })
  }, { threshold: 0.15 })
  if (sectionRef.value) observer.observe(sectionRef.value)
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <section ref="sectionRef" class="scroll-section" :style="gradStyle">
    <div v-if="bg" class="bg-blur" :style="bgStyle" />
    <div class="section-content" :class="{ visible }">
      <slot :visible="visible" />
    </div>
    <slot name="hint" />
  </section>
</template>
