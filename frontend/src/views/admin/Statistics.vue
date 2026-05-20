<template>
  <div class="page">
    <div class="page-head">
      <h1>报表统计</h1>
      <p>多维度分析充电桩电量、收益及设备使用率</p>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="tab-group">
        <button class="tab-btn" :class="{ active: granularity === 'day' }" @click="switchTab('day')">日报</button>
        <button class="tab-btn" :class="{ active: granularity === 'week' }" @click="switchTab('week')">周报</button>
        <button class="tab-btn" :class="{ active: granularity === 'month' }" @click="switchTab('month')">月报</button>
      </div>
      <button class="btn-refresh" :disabled="loading" @click="loadData">
        <span class="material-icons">refresh</span>刷新
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载中…</div>

    <template v-else-if="reports.length">
      <!-- KPI Cards -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">总收益 (¥)</div>
            <div class="kpi-val mono">¥{{ sumField('total_fee').toFixed(2) }}</div>
          </div>
          <div class="kpi-icon purple"><span class="material-icons">account_balance_wallet</span></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">总充电量 (kWh)</div>
            <div class="kpi-val mono">{{ sumField('total_charge_energy').toFixed(2) }}</div>
          </div>
          <div class="kpi-icon blue"><span class="material-icons">bolt</span></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">总服务次数</div>
            <div class="kpi-val mono">{{ sumField('total_charge_count') }}<span class="kpi-unit">次</span></div>
          </div>
          <div class="kpi-icon green"><span class="material-icons">ev_station</span></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">总充电时长</div>
            <div class="kpi-val">{{ fmtDuration(sumField('total_charge_seconds')) }}</div>
          </div>
          <div class="kpi-icon gold"><span class="material-icons">schedule</span></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">服务费合计 (¥)</div>
            <div class="kpi-val mono">¥{{ sumField('total_service_fee').toFixed(2) }}</div>
          </div>
          <div class="kpi-icon red"><span class="material-icons">payments</span></div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid-2">
        <!-- Vertical bar chart: Energy -->
        <div class="chart-box">
          <div class="chart-title">各桩充电电量 (kWh)</div>
          <div class="bars">
            <div class="y-axis">
              <span v-for="v in yAxisEnergy" :key="v">{{ v }}</span>
            </div>
            <div class="bar-item" v-for="c in chartData" :key="c.code">
              <div class="bar"><span :style="{ height: barH(c.energy, yAxisEnergyMax) + '%' }"></span></div>
              <div class="bar-value mono">{{ fmtEnergy(c.energy) }}</div>
              <div class="bar-label">{{ c.code }}</div>
            </div>
          </div>
        </div>

        <!-- Vertical bar chart: Fee + Donut -->
        <div class="chart-box">
          <div class="chart-title">各桩总费用 (¥)</div>
          <div class="chart-wrap">
            <div class="bars" style="height:260px">
              <div class="y-axis">
                <span v-for="v in yAxisFee" :key="v">{{ v }}</span>
              </div>
              <div class="bar-item" v-for="c in chartData" :key="c.code">
                <div class="bar money"><span :style="{ height: barH(c.fee, yAxisFeeMax) + '%' }"></span></div>
                <div class="bar-value mono">¥{{ c.fee.toFixed(2) }}</div>
                <div class="bar-label">{{ c.code }}</div>
              </div>
            </div>
            <div class="donut-side">
              <div class="donut-ring">
                <svg viewBox="0 0 36 36" class="donut-svg">
                  <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#f0f2f5" stroke-width="4"/>
                  <circle v-for="seg in donutSegments" :key="seg.code"
                    cx="18" cy="18" r="15.915" fill="transparent"
                    :stroke="seg.color" stroke-width="4"
                    :stroke-dasharray="`${seg.pct} ${100 - Number(seg.pct)}`"
                    :stroke-dashoffset="seg.dashOffset"
                  />
                </svg>
                <div class="donut-center">
                  <strong>总费用</strong>
                  <span class="mono">¥{{ Math.round(totalFeeAll) }}</span>
                </div>
              </div>
              <div class="legend">
                <div class="legend-row" v-for="seg in donutSegments" :key="seg.code">
                  <div class="legend-left">
                    <span class="swatch" :style="{ background: seg.color }"></span>
                    <span>{{ seg.code }}</span>
                  </div>
                  <strong class="mono">{{ seg.pct }}%</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="panel">
        <div class="panel-head">
          <h2>详细报表</h2>
          <span class="panel-meta">{{ reports.length }} 条记录</span>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>时段</th>
                <th>充电桩</th>
                <th>充电次数</th>
                <th>充电时长</th>
                <th class="num">充电电量</th>
                <th class="num">充电费</th>
                <th class="num">服务费</th>
                <th class="num total-col">总费用</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in reports" :key="i">
                <td class="mono time-td">{{ r.time_key }}</td>
                <td><span class="station-tag" :class="r.station_code?.startsWith('FAST') ? 'fast' : 'slow'">{{ r.station_code }}</span></td>
                <td>{{ r.total_charge_count }}</td>
                <td>{{ fmtDuration(r.total_charge_seconds) }}</td>
                <td class="num mono">{{ fmtEnergy(r.total_charge_energy) }}</td>
                <td class="num mono">¥{{ (r.total_charge_fee || 0).toFixed(2) }}</td>
                <td class="num mono">¥{{ (r.total_service_fee || 0).toFixed(2) }}</td>
                <td class="num mono total-val">¥{{ (r.total_fee || 0).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="footer-note">
        <div>说明：报表按所选时间维度统计，不同维度下数据会自动聚合。</div>
      </div>
    </template>

    <div v-else class="empty-state">暂无统计数据，请尝试切换时间维度</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReports, getStations } from '@/api/charging'

const granularity = ref('day')
const reports = ref([])
const stations = ref([])
const loading = ref(false)

function fmtDuration(s) {
  if (!s && s !== 0) return '--'
  const seconds = Math.max(0, Math.floor(Number(s)))
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const rest = seconds % 60
  if (h > 0) return rest > 0 ? `${h}h ${m}m ${rest}s` : `${h}h ${m}m`
  if (m > 0) return rest > 0 ? `${m}m ${rest}s` : `${m}m`
  return `${rest}s`
}

function fmtEnergy(value) {
  const energy = Number(value || 0)
  return `${energy.toFixed(2)} kWh`
}

function sumField(field) {
  return reports.value.reduce((acc, r) => acc + (r[field] || 0), 0)
}

// Aggregate per station for charts
const chartData = computed(() => {
  const map = {}
  stations.value.forEach(s => {
    if (!map[s.station_code]) map[s.station_code] = { code: s.station_code, energy: 0, fee: 0 }
  })
  reports.value.forEach(r => {
    if (!map[r.station_code]) map[r.station_code] = { code: r.station_code, energy: 0, fee: 0 }
    map[r.station_code].energy += r.total_charge_energy || 0
    map[r.station_code].fee += r.total_fee || 0
  })
  return Object.values(map).sort((a, b) => a.code.localeCompare(b.code))
})

const maxEnergy = computed(() => Math.max(...chartData.value.map(c => c.energy), 1))
const maxFee = computed(() => Math.max(...chartData.value.map(c => c.fee), 1))
const chartDataSorted = computed(() => [...chartData.value].sort((a, b) => b.energy - a.energy))

const COLORS = ['#34b27b', '#4f86f7', '#d8a23a', '#ef4444', '#7a5af8', '#98a2b3', '#f97316']
const totalFeeAll = computed(() => chartData.value.reduce((s, c) => s + c.fee, 0))
const donutSegments = computed(() => {
  let offset = 0
  const total = totalFeeAll.value || 1
  return chartData.value.map((c, i) => {
    const pct = (c.fee / total) * 100
    const seg = { code: c.code, pct: pct.toFixed(1), color: COLORS[i % COLORS.length], dashOffset: -offset }
    offset += pct
    return seg
  })
})

function barH(val, max) { return Math.max((val / max) * 100, 2) }

function yAxisSteps(max) {
  const nice = Math.ceil(max / 4)
  return [nice * 4, nice * 3, nice * 2, nice, 0].map(String)
}

const yAxisEnergyMax = computed(() => Math.ceil(maxEnergy.value / 4) * 4)
const yAxisFeeMax = computed(() => Math.ceil(maxFee.value / 4) * 4)
const yAxisEnergy = computed(() => yAxisSteps(maxEnergy.value))
const yAxisFee = computed(() => yAxisSteps(maxFee.value))

async function loadData() {
  loading.value = true
  try {
    const [reportRes, stationRes] = await Promise.all([
      getReports(granularity.value),
      getStations(),
    ])
    const payload = reportRes?.data ?? reportRes
    const stationPayload = stationRes?.data ?? stationRes
    reports.value = payload?.rows || payload?.reports || []
    stations.value = Array.isArray(stationPayload) ? stationPayload : []
  } catch (_) { /* silent */ }
  loading.value = false
}

function switchTab(g) { granularity.value = g; loadData() }

onMounted(loadData)
</script>

<style scoped>
* { box-sizing: border-box; }
.mono { font-family: "SF Mono", Consolas, monospace; }

.page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 28px 30px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  color: #101828;
}
.page-head { margin-bottom: 18px; }
.page-head h1 { margin: 0; font-size: 28px; font-weight: 850; letter-spacing: -.02em; }
.page-head p { margin: 8px 0 0; font-size: 15px; color: #667085; }

/* Toolbar */
.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; margin: 14px 0 16px;
}
.tab-group {
  display: inline-flex; padding: 4px;
  border: 1px solid #e6eaee; border-radius: 14px;
  background: #fff; box-shadow: 0 10px 28px rgba(16,24,40,.06);
}
.tab-btn {
  height: 36px; min-width: 66px; padding: 0 14px; border-radius: 10px;
  display: grid; place-items: center;
  color: #667085; font-weight: 700; font-size: 14px;
  border: none; background: transparent; cursor: pointer;
  font-family: inherit; transition: .15s;
}
.tab-btn.active {
  background: #fff; color: #1f8f60;
  box-shadow: inset 0 0 0 1px #dbe8e0;
}
.btn-refresh {
  height: 40px; border-radius: 12px;
  border: 1px solid #d8eadf;
  background: linear-gradient(180deg, #4bbb87, #37ab77);
  color: #fff; padding: 0 16px; font-weight: 800;
  display: inline-flex; align-items: center; gap: 8px;
  box-shadow: 0 10px 18px rgba(52,178,123,.18);
  cursor: pointer; font-family: inherit; font-size: 14px;
}
.btn-refresh .material-icons { font-size: 16px; }
.btn-refresh:hover { filter: brightness(1.05); }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

.loading-state, .empty-state { color: #98a2b3; font-size: 14px; padding: 60px 0; text-align: center; }

/* KPI Cards */
.kpi-row { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; margin-bottom: 16px; }
.kpi-card {
  min-height: 96px; padding: 16px 18px;
  border: 1px solid #edf0f2; border-radius: 18px; background: #fff;
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  box-shadow: 0 10px 28px rgba(16,24,40,.06);
}
.kpi-left { min-width: 0; }
.kpi-label { color: #98a2b3; font-size: 13px; font-weight: 700; }
.kpi-val { margin-top: 9px; font-size: 28px; font-weight: 900; color: #101828; letter-spacing: -.03em; line-height: 1; }
.kpi-unit { font-size: 14px; font-weight: 400; color: #98a2b3; margin-left: 2px; }
.kpi-icon {
  width: 46px; height: 46px; border-radius: 16px;
  display: grid; place-items: center; flex: 0 0 auto;
}
.kpi-icon .material-icons { font-size: 20px; }
.kpi-icon.green { background: #eaf8f1; color: #1f8f60; }
.kpi-icon.blue { background: #eef4ff; color: #4f86f7; }
.kpi-icon.gold { background: #fff8e8; color: #d8a23a; }
.kpi-icon.red { background: #fff1f1; color: #ef4444; }
.kpi-icon.purple { background: #f4f7ff; color: #7a5af8; }

/* Charts grid */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.chart-box {
  min-height: 320px; background: #fff; border: 1px solid #edf0f2;
  border-radius: 18px; padding: 18px;
  box-shadow: 0 10px 28px rgba(16,24,40,.06);
}
.chart-title { font-size: 16px; font-weight: 850; color: #101828; margin-bottom: 18px; }
.chart-wrap { display: grid; grid-template-columns: 1fr 240px; gap: 18px; align-items: stretch; }

/* Vertical bars */
.bars {
  position: relative; height: 260px;
  display: flex; align-items: flex-end; gap: 16px;
  padding: 18px 10px 14px 48px;
  border-bottom: 1px solid #edf0f2; overflow: hidden;
}
.bars::before {
  content: ""; position: absolute; left: 42px; right: 8px; top: 18px; bottom: 14px;
  background:
    linear-gradient(to top, rgba(232,236,239,.95) 1px, transparent 1px) 0 100% / 100% 25%,
    linear-gradient(to top, rgba(232,236,239,.95) 1px, transparent 1px) 0 75% / 100% 25%,
    linear-gradient(to top, rgba(232,236,239,.95) 1px, transparent 1px) 0 50% / 100% 25%,
    linear-gradient(to top, rgba(232,236,239,.95) 1px, transparent 1px) 0 25% / 100% 25%;
  background-repeat: no-repeat; pointer-events: none;
}
.y-axis {
  position: absolute; left: 0; top: 12px; bottom: 14px; width: 38px;
  display: flex; flex-direction: column; justify-content: space-between;
  color: #98a2b3; font-size: 11px; text-align: right; padding-right: 8px; pointer-events: none;
}
.y-axis span { display: block; transform: translateY(50%); }
.bar-item {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: 10px; min-width: 0; position: relative; z-index: 1; height: 100%;
}
.bar {
  flex: 1; width: 100%; max-width: 92px; border-radius: 14px 14px 6px 6px;
  position: relative; background: #edf0f2; overflow: hidden;
  box-shadow: inset 0 -1px 0 rgba(255,255,255,.5); min-height: 0;
}
.bar span {
  position: absolute; left: 0; bottom: 0; width: 100%; border-radius: inherit;
  min-height: 16px; background: linear-gradient(180deg, #59c892, #34b27b); transition: height .4s;
}
.bar.money span { background: linear-gradient(180deg, #f4c562, #d8a23a); }
.bar-label { font-size: 12px; color: #98a2b3; font-weight: 700; }
.bar-value { font-size: 13px; font-weight: 850; color: #1d2939; white-space: nowrap; }

/* Station tag */
.station-tag {
  display: inline-flex; align-items: center;
  padding: 2px 8px; border-radius: 4px;
  font-size: 12px; font-weight: 800; white-space: nowrap;
}
.station-tag.fast { background: #eef4ff; color: #4f86f7; }
.station-tag.slow { background: #eaf8f1; color: #1f8f60; }

/* Donut */
.donut-side { width: 240px; display: grid; gap: 12px; align-content: start; }
.donut-ring {
  width: 170px; height: 170px; margin: 0 auto; position: relative;
}
.donut-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.donut-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center;
}
.donut-center strong { display: block; font-size: 13px; color: #667085; }
.donut-center span { display: block; font-size: 26px; font-weight: 900; margin-top: 6px; }
.legend { display: grid; gap: 10px; margin-top: 8px; }
.legend-row { display: flex; justify-content: space-between; gap: 16px; color: #344054; font-size: 13px; }
.legend-left { display: flex; align-items: center; gap: 8px; }
.swatch { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* Table Panel */
.panel {
  background: #fff; border: 1px solid #edf0f2; border-radius: 18px;
  overflow: hidden; box-shadow: 0 10px 28px rgba(16,24,40,.06);
  margin-bottom: 16px;
}
.panel-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 18px 18px 14px; border-bottom: 1px solid #f0f2f4;
}
.panel-head h2 { margin: 0; font-size: 16px; font-weight: 850; }
.panel-meta { color: #98a2b3; font-size: 13px; }
.table-scroll { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; font-size: 14px; color: #344054; }
thead { background: #fbfcfc; }
th { padding: 14px 18px; text-align: left; font-size: 13px; font-weight: 700; color: #667085; border-bottom: 1px solid #edf0f2; white-space: nowrap; }
td { padding: 14px 18px; border-bottom: 1px solid #f0f2f4; white-space: nowrap; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fbfcfc; }
th.num, td.num { text-align: right; }
.time-td { color: #1d2939; font-weight: 700; }
.total-col { color: #1d2939; font-weight: 800; }
.total-val { color: #34b27b; font-weight: 800; }

/* Footer */
.footer-note {
  display: flex; justify-content: space-between; align-items: center;
  color: #98a2b3; font-size: 12px; padding: 12px 2px 0;
}

@media (max-width: 1180px) {
  .kpi-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .grid-2 { grid-template-columns: 1fr; }
  .chart-wrap { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .page { padding: 18px 14px 24px; }
  .kpi-row { grid-template-columns: 1fr; }
}
</style>
