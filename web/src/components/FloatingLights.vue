<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  count: { type: Number, default: 5 },
  colors: { type: Array, default: () => ['rgba(168,197,160,0.12)', 'rgba(212,168,87,0.08)', 'rgba(107,140,175,0.1)'] },
})

const orbs = ref([])

function generateOrbs() {
  orbs.value = Array.from({ length: props.count }, (_, i) => ({
    id: i,
    size: Math.random() * 300 + 150,
    x: Math.random() * 100,
    y: Math.random() * 100,
    duration: Math.random() * 15 + 15,
    delay: Math.random() * -20,
    color: props.colors[i % props.colors.length],
    drift: Math.random() * 60 - 30,
  }))
}

onMounted(() => generateOrbs())
</script>

<template>
  <div class="floating-lights">
    <div
      v-for="orb in orbs"
      :key="orb.id"
      class="light-orb"
      :style="{
        width: orb.size + 'px',
        height: orb.size + 'px',
        left: orb.x + '%',
        top: orb.y + '%',
        background: orb.color,
        animationDuration: orb.duration + 's',
        animationDelay: orb.delay + 's',
        '--drift': orb.drift + 'px',
      }"
    />
  </div>
</template>

<style scoped>
.floating-lights {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}
.light-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  animation: float-orb linear infinite;
}
@keyframes float-orb {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 0.3;
  }
  33% {
    transform: translate(var(--drift), -60px) scale(1.2);
    opacity: 0.6;
  }
  66% {
    transform: translate(calc(var(--drift) * -1), 40px) scale(0.9);
    opacity: 0.4;
  }
  100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.3;
  }
}
</style>
