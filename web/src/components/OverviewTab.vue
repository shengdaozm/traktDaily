<script setup>
import TrendChart from '@/components/TrendChart.vue'
import TopMedia from '@/components/TopMedia.vue'
import RecentList from '@/components/RecentList.vue'
</script>

<template>
  <div>
    <div class="card reveal">
      <h2><span class="icon">📈</span> 月度观影趋势</h2>
      <TrendChart />
    </div>
    <div class="card reveal">
      <h2><span class="icon">🏆</span> 观影次数排行</h2>
      <TopMedia />
    </div>
    <div class="card reveal">
      <h2><span class="icon">🕐</span> 最近观影</h2>
      <RecentList />
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 28px; margin-bottom: 24px;
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

@media (max-width: 768px) { .card { padding: 20px; } }
</style>
