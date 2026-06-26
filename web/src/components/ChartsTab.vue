<script setup>
import TypePieChart from '@/components/TypePieChart.vue'
import RatingChart from '@/components/RatingChart.vue'
import YearlyCompare from '@/components/YearlyCompare.vue'
</script>

<template>
  <div>
    <div class="charts-grid reveal">
      <div class="chart-card">
        <h3>媒体类型分布</h3>
        <TypePieChart />
      </div>
      <div class="chart-card">
        <h3>评分分布</h3>
        <RatingChart />
      </div>
    </div>
    <div class="card reveal">
      <h2><span class="icon">📅</span> 年度数据对比</h2>
      <YearlyCompare />
    </div>
  </div>
</template>

<style scoped>
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.chart-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
}
.chart-card h3 { font-size: 1rem; color: var(--text-bright); margin-bottom: 16px; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 28px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  transition: border-color var(--transition);
}
.card:hover { border-color: var(--border-bright); }
.card h2 {
  font-size: 1.15rem; font-weight: 700; color: var(--text-bright);
  margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
}
.card h2 .icon { font-size: 1.2rem; }
.reveal { opacity: 0; transform: translateY(24px); transition: opacity 0.6s ease, transform 0.6s ease; }
.reveal.visible { opacity: 1; transform: translateY(0); }

@media (max-width: 768px) {
  .charts-grid { grid-template-columns: 1fr; }
  .card { padding: 20px; }
}
</style>
