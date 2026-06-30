<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  colors: {
    type: Array,
    default: () => [
      'rgba(168,197,160,0.08)',
      'rgba(212,168,87,0.06)',
      'rgba(107,140,175,0.07)',
      'rgba(154,138,175,0.05)',
    ],
  },
})

const canvas = ref(null)
let ctx, raf, t = 0

function draw() {
  if (!ctx) return
  const c = canvas.value
  const w = c.width
  const h = c.height
  ctx.clearRect(0, 0, w, h)

  const n = props.colors.length
  for (let i = 0; i < n; i++) {
    const phase = t * 0.0003 + i * (Math.PI * 2 / n)
    const x = w * (0.5 + Math.cos(phase) * 0.35)
    const y = h * (0.5 + Math.sin(phase * 1.3) * 0.35)
    const r = Math.max(100, Math.min(w, h) * (0.4 + Math.sin(phase * 0.7) * 0.15))

    const grad = ctx.createRadialGradient(x, y, 0, x, y, r)
    grad.addColorStop(0, props.colors[i])
    grad.addColorStop(1, 'transparent')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, w, h)
  }

  t++
  raf = requestAnimationFrame(draw)
}

function resize() {
  const c = canvas.value
  if (!c) return
  const dpr = window.devicePixelRatio || 1
  const rect = c.getBoundingClientRect()
  c.width = rect.width * dpr
  c.height = rect.height * dpr
  ctx.scale(dpr, dpr)
  c.style.width = rect.width + 'px'
  c.style.height = rect.height + 'px'
}

onMounted(() => {
  const c = canvas.value
  if (!c) return
  ctx = c.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const rect = c.getBoundingClientRect()
  c.width = rect.width * dpr
  c.height = rect.height * dpr
  ctx.scale(dpr, dpr)
  c.style.width = rect.width + 'px'
  c.style.height = rect.height + 'px'
  draw()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  if (raf) cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
})
</script>

<template>
  <canvas ref="canvas" class="dynamic-bg" />
</template>

<style scoped>
.dynamic-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
