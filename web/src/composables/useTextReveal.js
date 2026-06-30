import { ref, onMounted, watch } from 'vue'

/**
 * 逐字浮现动画
 * 将文本拆分为单个字符，依次延迟浮现
 */
export function useTextReveal() {
  const containerRef = ref(null)
  const isVisible = ref(false)

  function splitText(text) {
    return text.split('').map((char, i) => ({
      char: char === ' ' ? '\u00A0' : char,
      delay: i * 0.04,
    }))
  }

  function observe() {
    if (!containerRef.value) return
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          isVisible.value = true
          obs.disconnect()
        }
      })
    }, { threshold: 0.3 })
    obs.observe(containerRef.value)
  }

  onMounted(() => observe())

  return { containerRef, isVisible, splitText }
}

/**
 * 数字递增动画
 */
export function useCountUp() {
  function animate(el, target, duration = 1500, suffix = '') {
    if (!el) return
    const start = 0
    const startTime = performance.now()
    function step(now) {
      const progress = Math.min((now - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const val = Math.floor(start + (target - start) * eased)
      el.textContent = val.toLocaleString() + suffix
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }
  return { animate }
}
