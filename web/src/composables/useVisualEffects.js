import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 鼠标跟随光晕 + 点击涟漪 + 3D卡片倾斜
 */
export function useVisualEffects() {
  const mouseX = ref(0)
  const mouseY = ref(0)
  const glowVisible = ref(false)

  function onMouseMove(e) {
    mouseX.value = e.clientX
    mouseY.value = e.clientY
    if (!glowVisible.value) glowVisible.value = true
  }

  function createRipple(e) {
    const target = e.currentTarget || e.target
    if (!target || !target.getBoundingClientRect) return

    const rect = target.getBoundingClientRect()
    const x = (e.clientX || rect.left + rect.width / 2) - rect.left
    const y = (e.clientY || rect.top + rect.height / 2) - rect.top

    const ripple = document.createElement('span')
    ripple.className = 'ripple-effect'
    ripple.style.left = x + 'px'
    ripple.style.top = y + 'px'
    target.appendChild(ripple)

    setTimeout(() => ripple.remove(), 800)
  }

  function bindRipple(el) {
    if (!el) return
    el.style.position = el.style.position || 'relative'
    el.style.overflow = 'hidden'
    el.addEventListener('click', createRipple)
  }

  function bindTilt(el, maxDeg = 12) {
    if (!el) return
    el.style.transformStyle = 'preserve-3d'
    el.style.transition = 'transform 0.1s ease'

    function onMove(e) {
      const rect = el.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const cy = rect.top + rect.height / 2
      const dx = (e.clientX - cx) / (rect.width / 2)
      const dy = (e.clientY - cy) / (rect.height / 2)
      const rx = -dy * maxDeg
      const ry = dx * maxDeg
      el.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.03)`
    }

    function onLeave() {
      el.style.transform = 'perspective(800px) rotateX(0) rotateY(0) scale(1)'
    }

    el.addEventListener('mousemove', onMove)
    el.addEventListener('mouseleave', onLeave)
    el._tiltCleanup = () => {
      el.removeEventListener('mousemove', onMove)
      el.removeEventListener('mouseleave', onLeave)
    }
  }

  onMounted(() => {
    window.addEventListener('mousemove', onMouseMove, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('mousemove', onMouseMove)
  })

  return { mouseX, mouseY, glowVisible, createRipple, bindRipple, bindTilt }
}
