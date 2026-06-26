import { ref, onMounted, onBeforeUnmount, watch, shallowRef, nextTick } from 'vue'
import * as echarts from 'echarts'

export function useECharts(getOptionFn, watchSources = []) {
  const chartRef = ref(null)
  const chart = shallowRef(null)
  const ready = ref(false)

  function render() {
    if (!chart.value) return
    const opt = getOptionFn()
    if (opt) chart.value.setOption(opt, true)
  }

  function resize() {
    chart.value?.resize()
  }

  onMounted(async () => {
    await nextTick()
    if (chartRef.value) {
      chart.value = echarts.init(chartRef.value, null, { renderer: 'canvas' })
      ready.value = true
      render()
    }
  })

  onBeforeUnmount(() => {
    chart.value?.dispose()
    chart.value = null
  })

  watch(watchSources, () => {
    if (ready.value) render()
  }, { deep: true })

  watch(chartRef, async (el) => {
    if (el && !chart.value) {
      await nextTick()
      chart.value = echarts.init(el, null, { renderer: 'canvas' })
      ready.value = true
      render()
    }
  })

  return { chartRef, ready, render, resize }
}

export const TOOLTIP_STYLE = {
  backgroundColor: 'rgba(22,27,36,0.95)',
  borderColor: 'rgba(48,54,61,0.6)',
  textStyle: { color: '#c9d1d9', fontSize: 13 },
}
