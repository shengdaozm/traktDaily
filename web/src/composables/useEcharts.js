import { ref, onMounted, onBeforeUnmount, onActivated, watch, shallowRef, nextTick } from 'vue'
import * as echarts from 'echarts'

export function useECharts(getOptionFn, watchSources = []) {
  const chartRef = ref(null)
  const chart = shallowRef(null)
  const ready = ref(false)

  function initChart() {
    if (chart.value || !chartRef.value) return
    if (chartRef.value.offsetWidth === 0 || chartRef.value.offsetHeight === 0) return
    chart.value = echarts.init(chartRef.value, null, { renderer: 'canvas' })
    ready.value = true
    render()
  }

  function render() {
    if (!chart.value) return
    const opt = getOptionFn()
    if (opt) chart.value.setOption(opt, true)
  }

  function resize() {
    if (chart.value) {
      chart.value.resize()
    } else {
      initChart()
    }
  }

  function tryInit() {
    nextTick(() => {
      setTimeout(() => {
        initChart()
        if (!chart.value) {
          setTimeout(initChart, 200)
        }
      }, 50)
    })
  }

  onMounted(() => {
    tryInit()
  })

  onActivated(() => {
    tryInit()
  })

  onBeforeUnmount(() => {
    chart.value?.dispose()
    chart.value = null
  })

  watch(watchSources, () => {
    if (ready.value) {
      render()
    } else {
      tryInit()
    }
  }, { deep: true })

  return { chartRef, ready, render, resize }
}

export const TOOLTIP_STYLE = {
  backgroundColor: 'rgba(22,27,36,0.95)',
  borderColor: 'rgba(48,54,61,0.6)',
  textStyle: { color: '#c9d1d9', fontSize: 13 },
}
