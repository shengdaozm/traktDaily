import { ref, watch, onMounted, onUnmounted } from 'vue'

export function useBackgroundLayer(sectionBackgrounds, activeSection) {
  const layerA = ref('')
  const layerB = ref('')
  const activeLayer = ref('A')
  const rotationIdx = ref(0)
  let rotationTimer = null
  let loadToken = 0

  function preload(url) {
    return new Promise((resolve) => {
      if (!url) { resolve(); return }
      const img = new Image()
      img.onload = () => resolve()
      img.onerror = () => resolve()
      img.src = url
    })
  }

  function getActiveUrl() {
    const bgs = sectionBackgrounds.value
    if (!bgs || !bgs.length) return ''
    const idx = Math.min(activeSection.value, bgs.length - 1)
    const bg = bgs[idx]
    if (!bg) return ''
    if (Array.isArray(bg)) {
      return bg[rotationIdx.value % bg.length] || ''
    }
    return bg
  }

  async function updateBackground() {
    const url = getActiveUrl()
    if (!url) return

    const next = activeLayer.value === 'A' ? 'B' : 'A'
    const nextRef = next === 'A' ? layerA : layerB

    if (nextRef.value === url) {
      activeLayer.value = next
      return
    }

    nextRef.value = url
    const token = ++loadToken
    await preload(url)
    if (token !== loadToken) return

    requestAnimationFrame(() => {
      activeLayer.value = next
    })
  }

  function startRotation() {
    stopRotation()
    const bgs = sectionBackgrounds.value
    if (!bgs || !bgs.length) return
    const idx = Math.min(activeSection.value, bgs.length - 1)
    const bg = bgs[idx]
    if (Array.isArray(bg) && bg.length > 1) {
      rotationTimer = setInterval(() => {
        rotationIdx.value++
        updateBackground()
      }, 8000)
    }
  }

  function stopRotation() {
    if (rotationTimer) {
      clearInterval(rotationTimer)
      rotationTimer = null
    }
  }

  watch(activeSection, () => {
    rotationIdx.value = 0
    updateBackground()
    startRotation()
  })

  watch(sectionBackgrounds, () => {
    rotationIdx.value = 0
    updateBackground()
    startRotation()
  }, { deep: true })

  onMounted(() => {
    updateBackground()
    startRotation()
  })

  onUnmounted(stopRotation)

  return { layerA, layerB, activeLayer }
}
