<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvas = ref(null)
let ctx = null
let raf = null
let particles = []
let w = 0, h = 0

const props = defineProps({
  density: { type: Number, default: 60 },
  color: { type: String, default: 'rgba(168, 197, 160, ' },
  speed: { type: Number, default: 0.3 },
})

function resize() {
  const c = canvas.value
  if (!c) return
  const dpr = window.devicePixelRatio || 1
  const rect = c.getBoundingClientRect()
  w = rect.width
  h = rect.height
  c.width = w * dpr
  c.height = h * dpr
  ctx.scale(dpr, dpr)
}

function initParticles() {
  particles = []
  for (let i = 0; i < props.density; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * props.speed,
      vy: (Math.random() - 0.5) * props.speed,
      r: Math.random() * 2 + 0.5,
      o: Math.random() * 0.4 + 0.1,
      tw: Math.random() * Math.PI * 2,
    })
  }
}

function draw() {
  if (!ctx) return
  ctx.clearRect(0, 0, w, h)

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i]
    p.x += p.vx
    p.y += p.vy
    p.tw += 0.02

    if (p.x < 0) p.x = w
    if (p.x > w) p.x = 0
    if (p.y < 0) p.y = h
    if (p.y > h) p.y = 0

    const flicker = 0.5 + Math.sin(p.tw) * 0.3
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = props.color + (p.o * flicker).toFixed(2) + ')'
    ctx.fill()

    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j]
      const dx = p.x - q.x
      const dy = p.y - q.y
      const dist = dx * dx + dy * dy
      if (dist < 8000) {
        const alpha = (1 - dist / 8000) * 0.08
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(q.x, q.y)
        ctx.strokeStyle = props.color + alpha.toFixed(2) + ')'
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }

  raf = requestAnimationFrame(draw)
}

onMounted(() => {
  const c = canvas.value
  if (!c) return
  ctx = c.getContext('2d')
  resize()
  initParticles()
  draw()
  window.addEventListener('resize', () => { resize(); initParticles() })
})

onUnmounted(() => {
  if (raf) cancelAnimationFrame(raf)
})
</script>

<template>
  <canvas ref="canvas" class="particle-bg" />
</template>

<style scoped>
.particle-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
