<script setup>
const props = defineProps({
  opacity: { type: Number, default: 0.04 },
})
</script>

<template>
  <div class="film-grain" :style="{ opacity: props.opacity }" />
</template>

<style scoped>
.film-grain {
  position: fixed;
  inset: -50%;
  width: 200%;
  height: 200%;
  pointer-events: none;
  z-index: 9998;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' /%3E%3C/svg%3E");
  animation: grain-shift 0.5s steps(4) infinite;
}
@keyframes grain-shift {
  0% { transform: translate(0, 0); }
  25% { transform: translate(-5%, 3%); }
  50% { transform: translate(3%, -5%); }
  75% { transform: translate(-3%, -3%); }
  100% { transform: translate(5%, 5%); }
}
</style>
