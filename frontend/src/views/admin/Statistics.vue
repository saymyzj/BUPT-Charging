<template>
  <div class="page">
    <div class="page-head">
      <h1>报表统计</h1>
      <p>按日/周/月维度查看各桩充电数据</p>
    </div>

    <div class="toolbar">
      <div class="tab-group">
        <button class="tab-btn" :class="{ active: granularity === 'day' }" @click="switchTab('day')">日报</button>
        <button class="tab-btn" :class="{ active: granularity === 'week' }" @click="switchTab('week')">周报</button>
        <button class="tab-btn" :class="{ active: granularity === 'month' }" @click="switchTab('month')">月报</button>
      </div>
      <button class="btn btn-primary" @click="loadData">刷新</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

    <template v-if="!loading && reports.length">
      <!-- Summary -->
      <div class="stats-row">
        <div class="stat"><span class="s-label">总充电次数</span><span class="s-val">{{ sumField('total_charge_count') }}</span></div>
        <div class="stat"><span class="s-label">总充电电量</span><span class="s-val">{{ sumField('total_charge_energy').toFixed(1) }} kWh</span></div>
        <div class="stat"><span class="s-label">总充电费</span><span class="s-val">¥{{ sumField('total_charge_fee').toFixed(2) }}</span></div>
        <div class="stat"><span class="s-label">总服务费</span><span class="s-val">¥{{ sumField('total_service_fee').toFixed(2) }}</span></div>
        <div class="stat"><span class="s-label">总费用</span><span class="s-val">¥{{ sumField('total_fee').toFixed(2) }}</span></div>
      </div>

      <!-- Table -->
      <div class="card">
        <div class="card-head"><h3>详细报表</h3></div>
        <div class="card-body" style="padding:0;overflow-x:auto;">
          <table class="t">
            <thead>
              <tr>
                <th>时段</th>
                <th>充电桩</th>
                <th>充电次数</th>
                <th>充电时长</th>
                <th>充电电量</th>
                <th>充电费</th>
                <th>服务费</th>
                <th>总费用</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in reports" :key="i">
                <td>{{ r.time_key }}</td>
                <td><strong>{{ r.station_code }}</strong></td>
                <td>{{ r.total_charge_count }}</td>
                <td>{{ fmtDuration(r.total_charge_seconds) }}</td>
                <td>{{ (r.total_charge_energy || 0).toFixed(1) }}</td>
                <td>¥{{ (r.total_charge_fee || 0).toFixed(2) }}</td>
                <td>¥{{ (r.total_service_fee || 0).toFixed(2) }}</td>
                <td><strong>¥{{ (r.total_fee || 0).toFixed(2) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-row">
        <div class="chart-card">
          <div class="chart-title">各桩充电电量 (kWh)</div>
          <div class="bar-chart">
            <div class="bar-item" v-for="c in chartData" :key="c.code">
              <div class="bar-val">{{ c.energy.toFixed(0) }}</div>
              <div class="bar" :style="{ height: barH(c.energy, maxEnergy) + '%', background: '#34d399' }"></div>
              <div class="bar-label">{{ c.code }}</div>
            </div>
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-title">各桩总费用 (¥)</div>
          <div class="bar-chart">
            <div class="bar-item" v-for="c in chartData" :key="c.code + 'fee'">
              <div class="bar-val">{{ c.fee.toFixed(0) }}</div>
              <div class="bar" :style="{ height: barH(c.fee, maxFee) + '%', background: '#fbbf24' }"></div>
              <div class="bar-label">{{ c.code }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="!loading && !reports.length" class="empty-text">暂无数据</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReports } from '@/api/charging'

const granularity = ref('day')
const reports = ref([])
const loading = ref(false)

function fmtDuration(s) {
  if (!s && s !== 0) return '--'
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function sumField(field) {
  return reports.value.reduce((acc, r) => acc + (r[field] || 0), 0)
}

// Aggregate per station for charts
const chartData = computed(() => {
  const map = {}
  reports.value.forEach(r => {
    if (!map[r.station_code]) map[r.station_code] = { code: r.station_code, energy: 0, fee: 0 }
    map[r.station_code].energy += r.total_charge_energy || 0
    map[r.station_code].fee += r.total_fee || 0
  })
  return Object.values(map)
})

const maxEnergy = computed(() => Math.max(...chartData.value.map(c => c.energy), 1))
const maxFee = computed(() => Math.max(...chartData.value.map(c => c.fee), 1))

function barH(val, max) { return Math.max((val / max) * 100, 2) }

async function loadData() {
  loading.value = true
  try {
    const res = await getReports(granularity.value)
    const payload = res?.data ?? res
    reports.value = payload?.rows || payload?.reports || []
  } catch (_) { /* silent */ }
  loading.value = false
}

function switchTab(g) { granularity.value = g; loadData() }

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 20px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.tab-group { display: flex; gap: 2px; background: #f3f4f6; border-radius: 8px; padding: 3px; }
.tab-btn { padding: 6px 16px; border: none; border-radius: 6px; background: transparent; font-size: 13px; font-weight: 500; cursor: pointer; color: #6b7280; transition: 0.15s; }
.tab-btn.active { background: white; color: #059669; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.btn { padding: 8px 18px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.12s; }
.btn-primary { background: #10b981; color: white; }
.btn-primary:hover { background: #059669; }
.loading-text, .empty-text { color: #9ca3af; font-size: 14px; padding: 40px 0; text-align: center; }

.stats-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.stat { background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; }
.s-label { display: block; font-size: 11px; color: #9ca3af; font-weight: 500; text-transform: uppercase; letter-spacing: 0.3px; }
.s-val { display: block; font-size: 20px; font-weight: 700; color: #111827; margin-top: 6px; }

.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; margin-bottom: 16px; }
.card-head { padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-body { padding: 20px; }
table.t { width: 100%; border-collapse: collapse; }
table.t th { text-align: left; padding: 10px 14px; font-size: 11px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e5e7eb; }
table.t td { padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f3f4f6; color: #374151; }
table.t td strong { color: #111827; }
table.t tr:last-child td { border-bottom: none; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.chart-card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; }
.chart-title { font-size: 13px; font-weight: 600; color: #111827; margin-bottom: 16px; }
.bar-chart { display: flex; align-items: flex-end; gap: 8px; height: 180px; padding-top: 24px; border-bottom: 1px solid #e5e7eb; }
.bar-item { display: flex; flex-direction: column; align-items: center; flex: 1; }
.bar { width: 100%; max-width: 36px; border-radius: 4px 4px 0 0; transition: 0.3s; min-height: 2px; }
.bar-label { font-size: 10px; color: #9ca3af; margin-top: 8px; font-weight: 500; }
.bar-val { font-size: 10px; font-weight: 700; color: #111827; margin-bottom: 4px; }
</style>
