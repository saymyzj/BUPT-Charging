<template>
  <div class="bills-layout">
    <!-- ===== LEFT SIDEBAR ===== -->
    <aside class="sidebar">
      <div class="sidebar-head">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        历史账单
      </div>

      <div v-if="loading" class="sidebar-empty">加载中…</div>
      <div v-else-if="!bills.length" class="sidebar-empty">暂无账单记录</div>

      <div v-else class="sidebar-tree">
        <div v-for="yr in groupedBills" :key="yr.year">
          <div class="tree-year" @click="toggleYear(yr.year)">
            <span>{{ expandedYears.has(yr.year) ? '▼' : '▶' }} {{ yr.year }}年</span>
            <span class="tree-year-count">{{ yr.totalCount }}</span>
          </div>
          <div v-if="expandedYears.has(yr.year)">
            <div v-for="mo in yr.months" :key="mo.month">
              <div class="tree-month" @click="toggleMonth(yr.year, mo.month)">
                <span>{{ expandedMonths.has(`${yr.year}-${mo.month}`) ? '▼' : '▶' }} {{ mo.month }}月</span>
                <span class="tree-month-count">{{ mo.bills.length }}</span>
              </div>
              <div v-if="expandedMonths.has(`${yr.year}-${mo.month}`)">
                <div
                  v-for="b in mo.bills" :key="b.request_id"
                  class="bill-card"
                  :class="{ active: selected?.request_id === b.request_id }"
                  @click="select(b)"
                >
                  <div class="bill-card-top">
                    <span class="bill-card-date">{{ fmtShort(b.detail_generated_at || b.stop_time) }}</span>
                    <span class="bill-badge" :class="statusBadgeClass(b)">{{ statusLabel(b) }}</span>
                  </div>
                  <div class="bill-card-id">请求 {{ b.request_id || '--' }}</div>
                  <div class="bill-card-amount">{{ fmtMoney(b.total_fee) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- ===== MAIN ===== -->
    <main class="detail-main">

      <!-- Empty / Loading -->
      <div v-if="loading" class="center-msg">加载中…</div>
      <div v-else-if="!selected" class="center-msg">
        <div class="center-icon"><span class="material-icons">description</span></div>
        <div class="center-title">暂无账单记录</div>
        <div class="center-sub">完成充电后将自动生成详单</div>
      </div>

      <template v-else>
        <!-- Header -->
        <div class="detail-header">
          <div>
            <div class="dh-title-row">
              <h1 class="dh-title">账单详情</h1>
              <span class="bill-badge lg" :class="statusBadgeClass(selected)">{{ statusLabel(selected) }}</span>
            </div>
            <p class="dh-meta">
              {{ fmtDateTime(selected.detail_generated_at || selected.stop_time) }}
              <span class="sep">|</span> 请求编号：<code>{{ selected.request_id || '--' }}</code>
              <span class="sep">|</span> 充电桩：<strong>{{ selected.station_code || '--' }}</strong>
            </p>
          </div>
          <div class="dh-actions">
            <div class="btn-group">
              <button class="btn-sm" :disabled="selectedIndex >= bills.length - 1" @click="nav(1)">← 较早</button>
              <button class="btn-sm" :disabled="selectedIndex <= 0" @click="nav(-1)">较新 →</button>
            </div>
          </div>
        </div>

        <!-- 5 Stat Cards -->
        <div class="stat-row">
          <div class="stat-card">
            <div class="stat-icon blue"><span class="material-icons">bolt</span></div>
            <div>
              <div class="stat-label">实际电量</div>
              <div class="stat-val">{{ selected.actual_energy ?? '--' }} <span class="stat-unit">kWh</span></div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon orange"><span class="material-icons">schedule</span></div>
            <div>
              <div class="stat-label">充电时长</div>
              <div class="stat-val">{{ fmtDuration(selected.charge_duration_seconds) }}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon green"><span class="material-icons">currency_yuan</span></div>
            <div>
              <div class="stat-label">总费用</div>
              <div class="stat-val green-val">{{ fmtMoney(selected.total_fee) }}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon amber"><span class="material-icons">toll</span></div>
            <div>
              <div class="stat-label">充电模式</div>
              <div class="stat-val">{{ chargeModeText(selected) }}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon purple"><span class="material-icons">layers</span></div>
            <div>
              <div class="stat-label">服务费</div>
              <div class="stat-val">{{ fmtMoney(selected.service_fee) }}</div>
            </div>
          </div>
        </div>

        <!-- Body grid -->
        <div class="body-grid">
          <!-- LEFT col -->
          <div class="left-col">
            <!-- Process timeline -->
            <div class="panel process-panel">
              <div class="panel-head">
                <span class="panel-title process-title"><span class="material-icons">route</span> 充电过程</span>
              </div>
              <table class="process-table process-table-large">
                <tbody>
                  <tr>
                    <td class="pt-icon"><span class="material-icons">play_circle_filled</span></td>
                    <td class="pt-time">{{ fmtDateTime(selected.start_time) }}</td>
                    <td class="pt-event">开始充电</td>
                    <td class="pt-desc">充电桩 {{ selected.station_code }} 开始为车辆充电</td>
                  </tr>
                  <tr>
                    <td class="pt-icon charging"><span class="material-icons">offline_bolt</span></td>
                    <td class="pt-time">充电中</td>
                    <td class="pt-event">充电中</td>
                    <td class="pt-desc">电量 <strong>{{ selected.actual_energy ?? '--' }} kWh</strong>&nbsp;·&nbsp;时长 <strong>{{ fmtDuration(selected.charge_duration_seconds) }}</strong></td>
                  </tr>
                  <tr>
                    <td class="pt-icon" :class="stopIconClass(selected)"><span class="material-icons">{{ stopIcon(selected) }}</span></td>
                    <td class="pt-time">{{ fmtDateTime(selected.stop_time) }}</td>
                    <td class="pt-event" :class="stopEventClass(selected)">{{ stopEventLabel(selected) }}</td>
                    <td class="pt-desc" :class="stopDescClass(selected)">{{ stopDesc(selected) }}</td>
                  </tr>
                  <tr v-if="selected.detail_generated_at">
                    <td class="pt-icon done"><span class="material-icons">description</span></td>
                    <td class="pt-time">{{ fmtDateTime(selected.detail_generated_at) }}</td>
                    <td class="pt-event">生成详单</td>
                    <td class="pt-desc pt-amount">{{ fmtMoney(selected.total_fee) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Power / SOC Chart -->
            <div class="panel chart-panel">
              <div class="panel-head chart-head">
                <span class="panel-title"><span class="material-icons">show_chart</span> 账单功率与时段计费</span>
                <div class="chart-legend">
                  <span v-for="seg in chartSegments" :key="seg.label" class="chart-leg-item">
                    <i :style="{ background: seg.bg, border: `1px solid ${seg.border}` }"></i>{{ seg.label }}
                  </span>
                  <span class="chart-leg-item"><i class="line green"></i>功率 (kW)</span>
                  <span class="chart-leg-item"><i class="line blue"></i>进度 (%)</span>
                </div>
              </div>
              <div class="chart-wrap">
                <div class="chart-area" ref="chartArea"
                  @mousemove="onChartMove" @mouseleave="onChartLeave">
                  <svg class="chart-svg" viewBox="0 0 600 180" preserveAspectRatio="none">
                    <!-- segment backgrounds -->
                    <rect v-for="seg in chartSegBgs" :key="seg.x"
                      :x="seg.x" y="0" :width="seg.w" height="180" :fill="seg.fill"/>
                    <line v-for="seg in chartSegBgs.slice(1)" :key="'d'+seg.x"
                      :x1="seg.x" y1="0" :x2="seg.x" y2="180"
                      stroke="#cbd5e1" stroke-dasharray="4,4" stroke-width="1"/>
                    <!-- grid lines -->
                    <line v-for="y in [20,60,100,140,180]" :key="y" x1="0" :y1="y" x2="600" :y2="y"
                      :stroke="y===180?'#e2e8f0':'#f1f5f9'" stroke-width="1"/>
                    <!-- SOC curve -->
                    <polyline v-if="hasValidChartData" :points="socPoints" fill="none" stroke="#2563eb" stroke-width="2.4"/>
                    <!-- Power curve -->
                    <polyline v-if="hasValidChartData" :points="powerPoints" fill="none" stroke="#10b981" stroke-width="2.6" stroke-linejoin="round"/>
                    <!-- crosshair -->
                    <g v-if="hasValidChartData && crosshair.visible">
                      <line :x1="crosshair.svgX" y1="0" :x2="crosshair.svgX" y2="180"
                        stroke="#94a3b8" stroke-dasharray="3,3" stroke-width="1"/>
                      <circle :cx="crosshair.svgX" :cy="crosshair.powerY" r="4"
                        fill="#10b981" stroke="white" stroke-width="2"/>
                      <circle :cx="crosshair.svgX" :cy="crosshair.socY" r="4"
                        fill="#2563eb" stroke="white" stroke-width="2"/>
                    </g>
                  </svg>
                  <div v-if="!hasValidChartData" class="chart-empty">
                    该账单没有有效的实际电量或充电时长，无法绘制功率曲线
                  </div>
                  <!-- y-axis labels -->
                  <div class="chart-y-labels">
                    <span v-for="label in powerAxisLabels" :key="label.power">
                      {{ label.power }}<br><span class="y2">{{ label.progress }}</span>
                    </span>
                  </div>
                  <!-- tooltip -->
                  <div v-if="hasValidChartData && crosshair.visible" class="chart-tooltip"
                    :style="{ left: crosshair.tipX + 'px', top: crosshair.tipY + 'px' }">
                    <div class="tt-head">
                      <span>{{ crosshair.time }}</span>
                      <span :class="crosshair.priceClass">{{ crosshair.price }}</span>
                    </div>
                    <div class="tt-row"><span>平均功率</span><span class="tt-green">{{ crosshair.power }} kW</span></div>
                    <div class="tt-row"><span>充电进度</span><span class="tt-blue">{{ crosshair.soc }} %</span></div>
                  </div>
                </div>
                <!-- x-axis time labels -->
                <div class="chart-x-labels">
                  <span v-for="t in chartTimeTicks" :key="t.label"
                    :class="{ 'tick-peak': t.isPeak }">{{ t.label }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- RIGHT col -->
          <div class="right-col">
            <!-- Payment -->
            <div class="panel">
              <div class="panel-head"><span class="panel-title"><span class="material-icons">credit_card</span> 支付信息</span></div>

              <!-- PAID -->
              <template v-if="paymentStatus === 'PAID'">
                <div class="pay-rows">
                  <div class="pay-row">
                    <span>支付状态</span>
                    <span class="bill-badge badge-green">已完成</span>
                  </div>
                  <div class="pay-row">
                    <span>实付金额</span>
                    <strong>{{ fmtMoney(selected.total_fee) }}</strong>
                  </div>
                  <div class="pay-row">
                    <span>支付方式</span>
                    <span>账号余额</span>
                  </div>
                  <div class="pay-row">
                    <span>支付时间</span>
                    <span class="mono">{{ fmtDateTime(selected.paid_at) }}</span>
                  </div>
                </div>
                <div class="pay-tip success">
                  <span class="material-icons">verified</span><span>本次交易已完成，感谢使用！</span>
                </div>
              </template>

              <!-- UNPAID -->
              <template v-else>
                <div class="unpaid-notice">
                  <div class="unpaid-amount">{{ fmtMoney(selected.total_fee) }}</div>
                  <div class="unpaid-label">待支付金额</div>
                  <div class="unpaid-sub">充电费 {{ fmtMoney(selected.charge_fee) }} + 服务费 {{ fmtMoney(selected.service_fee) }}</div>
                </div>
                <div class="unpaid-actions">
                  <button class="btn-pay" @click="handlePay" :disabled="paying">
                    {{ paying ? '处理中…' : '立即支付' }}
                  </button>
                </div>
                <div class="pay-tip" v-if="payMsg">
                  <span class="material-icons" style="font-size:16px">info</span><span>{{ payMsg }}</span>
                </div>
              </template>
            </div>

            <!-- Cost detail -->
            <div class="panel">
              <div class="panel-head" style="display:flex;justify-content:space-between;align-items:center;">
                <span class="panel-title"><span class="material-icons">receipt_long</span> 费用明细</span>
              </div>
              <div class="cost-rows">
                <div class="cost-row">
                  <div>
                    <div class="cost-name">电费</div>
                    <div class="cost-formula">({{ selected.actual_energy ?? '--' }} kWh × 电价 峰/平/谷)</div>
                  </div>
                  <span class="cost-val">{{ fmtMoney(selected.charge_fee) }}</span>
                </div>
                <div class="cost-row">
                  <div>
                    <div class="cost-name">服务费</div>
                    <div class="cost-formula">(按总电量 × ¥0.80 /kWh)</div>
                  </div>
                  <span class="cost-val">{{ fmtMoney(selected.service_fee) }}</span>
                </div>
              </div>
              <div class="cost-total">
                <span>合计</span>
                <span class="cost-total-val">{{ fmtMoney(selected.total_fee) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Billing Rules -->
        <div class="rules-panel">
          <div class="panel-head"><span class="panel-title"><span class="material-icons">gavel</span> 计费规则</span></div>
          <div class="rules-grid">
            <div class="rule-card">
              <div class="rule-icon orange"><span class="material-icons">settings</span></div>
              <div class="rule-name">峰时电价</div>
              <div class="rule-val">¥1.0 /kWh</div>
              <div class="rule-hint">10:00–15:00, 18:00–21:00</div>
            </div>
            <div class="rule-card">
              <div class="rule-icon blue"><span class="material-icons">bar_chart</span></div>
              <div class="rule-name">平时电价</div>
              <div class="rule-val">¥0.7 /kWh</div>
              <div class="rule-hint">07:00–10:00, 15:00–18:00, 21:00–23:00</div>
            </div>
            <div class="rule-card">
              <div class="rule-icon green"><span class="material-icons">bedtime</span></div>
              <div class="rule-name">谷时电价</div>
              <div class="rule-val">¥0.4 /kWh</div>
              <div class="rule-hint">23:00–07:00</div>
            </div>
            <div class="rule-card">
              <div class="rule-icon purple"><span class="material-icons">layers</span></div>
              <div class="rule-name">服务费</div>
              <div class="rule-val">¥0.8 /kWh</div>
              <div class="rule-hint">按总实际充电量计算</div>
            </div>
            <div class="rule-card">
              <div class="rule-icon teal"><span class="material-icons">track_changes</span></div>
              <div class="rule-name">计费精度</div>
              <div class="rule-val">0.01 kWh</div>
              <div class="rule-hint">跨时段按各段分别计算</div>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getRequestDetails } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { CHARGE_MODE_TEXT } from '@/constants/enums'

const route = useRoute()
const bills = ref([])
const loading = ref(false)
const selected = ref(null)

const selectedIndex = computed(() => bills.value.findIndex(b => b.request_id === selected.value?.request_id))

const paymentStatus = computed(() => selected.value?.payment_status || 'UNAVAILABLE')
const payBadgeClass = computed(() => paymentStatus.value === 'PAID' ? 'badge-green' : 'badge-amber')

const paying = ref(false)
const payMsg = ref('')

async function handlePay() {
  paying.value = true
  payMsg.value = ''
  await new Promise(r => setTimeout(r, 800))
  paying.value = false
  payMsg.value = '暂未接入支付接口，请联系管理员完成支付。'
}

const chargeFeeRatio = computed(() => {
  const total = Number(selected.value?.total_fee)
  const charge = Number(selected.value?.charge_fee)
  if (!total || !charge) return 50
  return Math.round((charge / total) * 100)
})
const serviceFeeRatio = computed(() => 100 - chargeFeeRatio.value)

// ---- Chart ----
const chartArea = ref(null)
const crosshair = ref({ visible: false, svgX: 0, powerY: 0, socY: 0, tipX: 0, tipY: 0, time: '', price: '', priceClass: '', power: '0', soc: '0' })

const chartSegments = [
  { label: '谷电段 (¥0.40)', bg: 'rgba(16,185,129,0.06)', border: '#a7f3d0' },
  { label: '尖峰段 (¥1.00)', bg: 'rgba(245,158,11,0.06)', border: '#fde68a' },
]

const chartBillingInfo = computed(() => {
  const b = selected.value
  if (!b) return { startMs: 0, durationMin: 60, endMs: 60 * 60000, energy: 0, avgPower: 0, maxPower: 30 }
  const parsedStart = new Date(b.start_time || 0).getTime()
  const startMs = Number.isFinite(parsedStart) ? parsedStart : 0
  const durationSeconds = Number(b.charge_duration_seconds)
  const durationMin = Math.max(1, Number.isFinite(durationSeconds) ? durationSeconds / 60 : 60)
  const endMs = startMs + durationMin * 60000
  const energy = Math.max(0, Number(b.actual_energy) || 0)
  const avgPower = durationMin > 0 ? energy / (durationMin / 60) : 0
  const ratedPower = b.charge_mode === 'SLOW' ? 10 : 30
  const maxPower = Math.max(ratedPower, Math.ceil(avgPower / 10) * 10, 10)
  return { startMs, durationMin, endMs, energy, avgPower, maxPower }
})

const hasValidChartData = computed(() => {
  const { energy, durationMin } = chartBillingInfo.value
  return energy > 0 && durationMin > 0
})

const chartSegBgs = computed(() => {
  const { startMs, endMs } = chartBillingInfo.value
  if (!startMs || endMs <= startMs) return [{ x: 0, w: 600, fill: 'rgba(16,185,129,0.05)' }]
  const segments = []
  let cursor = startMs
  while (cursor < endMs) {
    const nextBoundary = nextPriceBoundary(cursor)
    const next = Math.min(endMs, nextBoundary)
    const x = Math.round(((cursor - startMs) / (endMs - startMs)) * 600)
    const w = Math.max(1, Math.round(((next - cursor) / (endMs - startMs)) * 600))
    segments.push({ x, w, fill: priceInfoAt(cursor).fill })
    cursor = next
  }
  return segments
})

const socPoints = computed(() => {
  return Array.from({ length: 16 }, (_, i) => {
    const ratio = i / 15
    const x = ratio * 600
    const y = progressToY(ratio * 100)
    return `${x},${y.toFixed(1)}`
  }).join(' ')
})

const powerPoints = computed(() => {
  const { avgPower, maxPower } = chartBillingInfo.value
  const y = powerToY(avgPower, maxPower)
  return `0,${y.toFixed(1)} 600,${y.toFixed(1)}`
})

const powerAxisLabels = computed(() => {
  const max = chartBillingInfo.value.maxPower
  return [1, 0.75, 0.5, 0.25, 0].map(ratio => ({
    power: Math.round(max * ratio),
    progress: Math.round(100 * ratio),
  }))
})

const chartTimeTicks = computed(() => {
  const { startMs, durationMin } = chartBillingInfo.value
  const ticks = []
  for (let i = 0; i <= 5; i++) {
    const ms = startMs + (durationMin * 60000 * i) / 5
    const d = new Date(ms)
    const label = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
    const h = d.getHours()
    const isPeak = h >= 18 && h < 21
    ticks.push({ label, isPeak })
  }
  return ticks
})

function powerToY(power, maxPower) {
  if (!maxPower) return 180
  return 180 - Math.max(0, Math.min(1, power / maxPower)) * 160
}

function progressToY(progress) {
  return 180 - Math.max(0, Math.min(1, progress / 100)) * 160
}

function priceInfoAt(ms) {
  const h = new Date(ms).getHours()
  if (h >= 18 && h < 21) return { price: '¥1.00 (峰)', priceClass: 'tt-amber', fill: 'rgba(245,158,11,0.06)' }
  if (h >= 23 || h < 7) return { price: '¥0.40 (谷)', priceClass: 'tt-green', fill: 'rgba(16,185,129,0.05)' }
  return { price: '¥0.70 (平)', priceClass: 'tt-blue', fill: 'rgba(37,99,235,0.045)' }
}

function nextPriceBoundary(ms) {
  const d = new Date(ms)
  const candidates = [7, 18, 21, 23].map(hour => {
    const next = new Date(d)
    next.setHours(hour, 0, 0, 0)
    if (next.getTime() <= ms) next.setDate(next.getDate() + 1)
    return next.getTime()
  })
  return Math.min(...candidates)
}

function onChartMove(e) {
  if (!hasValidChartData.value) return
  const el = chartArea.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  const svgX = ratio * 600
  const { startMs, durationMin, avgPower, maxPower } = chartBillingInfo.value
  const powerY = powerToY(avgPower, maxPower)
  const progress = ratio * 100
  const socY = progressToY(progress)
  const elapsed = Math.round(ratio * durationMin)
  const d = new Date(startMs + elapsed * 60000)
  const time = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
  const priceMeta = priceInfoAt(d.getTime())
  const price = priceMeta.price
  const priceClass = priceMeta.priceClass
  const powerVal = avgPower.toFixed(1)
  const socVal = progress.toFixed(1)
  let tipX = e.clientX - rect.left + 12
  if (tipX + 176 > rect.width) tipX = e.clientX - rect.left - 188
  crosshair.value = {
    visible: true, svgX, powerY, socY,
    tipX, tipY: Math.max(8, e.clientY - rect.top - 20),
    time, price, priceClass, power: powerVal, soc: socVal
  }
}
function onChartLeave() { crosshair.value = { ...crosshair.value, visible: false } }

const expandedYears = ref(new Set())
const expandedMonths = ref(new Set())

function toggleYear(yr) {
  const s = new Set(expandedYears.value)
  s.has(yr) ? s.delete(yr) : s.add(yr)
  expandedYears.value = s
}
function toggleMonth(yr, mo) {
  const key = `${yr}-${mo}`
  const s = new Set(expandedMonths.value)
  s.has(key) ? s.delete(key) : s.add(key)
  expandedMonths.value = s
}

const groupedBills = computed(() => {
  const map = {}
  bills.value.forEach(b => {
    const d = new Date(b.detail_generated_at || b.stop_time || 0)
    const yr = d.getFullYear()
    const mo = d.getMonth() + 1
    if (!map[yr]) map[yr] = { year: yr, months: {} }
    if (!map[yr].months[mo]) map[yr].months[mo] = { month: mo, bills: [] }
    map[yr].months[mo].bills.push(b)
  })
  return Object.values(map)
    .sort((a, b) => b.year - a.year)
    .map(yr => ({
      ...yr,
      months: Object.values(yr.months).sort((a, b) => b.month - a.month),
      totalCount: Object.values(yr.months).reduce((s, m) => s + m.bills.length, 0)
    }))
})

function select(b) {
  selected.value = b
  const d = new Date(b.detail_generated_at || b.stop_time || 0)
  const yr = d.getFullYear()
  const mo = d.getMonth() + 1
  if (!expandedYears.value.has(yr)) toggleYear(yr)
  if (!expandedMonths.value.has(`${yr}-${mo}`)) toggleMonth(yr, mo)
}
function nav(dir) {
  const idx = selectedIndex.value + dir
  if (idx >= 0 && idx < bills.value.length) select(bills.value[idx])
}

function statusLabel(row) {
  return row?.payment_status === 'PAID' ? '已完成' : '待支付'
}
function statusBadgeClass(row) {
  return row?.payment_status === 'PAID' ? 'badge-green' : 'badge-amber'
}

function terminationStatus(row) {
  return row?.termination_status || row?.request_status || ''
}
function stopIcon(row) {
  const s = terminationStatus(row)
  if (s === 'FAULT_INTERRUPTED') return 'error'
  if (s === 'CANCELLED') return 'cancel'
  return 'stop_circle'
}
function stopIconClass(row) {
  const s = terminationStatus(row)
  if (s === 'FAULT_INTERRUPTED') return 'fault'
  if (s === 'CANCELLED') return 'cancelled'
  return ''
}
function stopEventLabel(row) {
  const s = terminationStatus(row)
  if (s === 'FAULT_INTERRUPTED') return '故障中断'
  if (s === 'CANCELLED') return '用户取消'
  if (s === 'COMPLETED_EARLY') return '提前结束'
  return '充电完成'
}
function stopEventClass(row) {
  const s = terminationStatus(row)
  if (s === 'FAULT_INTERRUPTED') return 'pt-event-fault'
  return ''
}
function stopDesc(row) {
  const s = terminationStatus(row)
  if (s === 'FAULT_INTERRUPTED') return `充电桩 ${row.station_code || ''} 发生故障，充电中断`
  if (s === 'CANCELLED') return '用户主动取消充电请求'
  if (s === 'COMPLETED_EARLY') return '用户提前结束充电'
  return `充电完成，共充 ${row.actual_energy ?? '--'} kWh`
}
function stopDescClass(row) {
  const s = terminationStatus(row)
  if (s === 'FAULT_INTERRUPTED') return 'pt-desc-fault'
  return ''
}
function chargeModeText(row) {
  if (row?.charge_mode) return CHARGE_MODE_TEXT[row.charge_mode] || row.charge_mode
  if (row?.station_code?.startsWith('FAST')) return '快充'
  if (row?.station_code?.startsWith('SLOW')) return '慢充'
  return '--'
}
function fmtMoney(value) {
  const n = Number(value)
  return Number.isFinite(n) ? `¥${n.toFixed(2)}` : '--'
}
function fmtDuration(s) {
  if (!s && s !== 0) return '--'
  if (s > 0 && s < 60) return `${Math.ceil(s)} sec`
  return `${Math.floor(s / 60)} min`
}
function fmtDateTime(t) {
  if (!t) return '--'
  try {
    return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return t }
}
function fmtShort(t) {
  if (!t) return '--'
  try {
    const d = new Date(t)
    return `${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
  } catch { return t }
}

async function loadBills() {
  loading.value = true
  try {
    const res = await getRequestDetails()
    const data = unwrapResponseData(res)
    bills.value = (Array.isArray(data) ? data : []).sort((a, b) => {
      return new Date(b.detail_generated_at || b.stop_time || 0) - new Date(a.detail_generated_at || a.stop_time || 0)
    })
    const targetId = route.query.id
    const target = targetId ? bills.value.find(b => b.request_id === targetId || b.request_id === Number(targetId)) : null
    selected.value = target || bills.value[0] || null
    if (selected.value) {
      const d = new Date(selected.value.detail_generated_at || selected.value.stop_time || 0)
      const yr = d.getFullYear()
      const mo = d.getMonth() + 1
      expandedYears.value = new Set([yr])
      expandedMonths.value = new Set([`${yr}-${mo}`])
    }
  } catch (_) { bills.value = [] }
  loading.value = false
}

onMounted(loadBills)
</script>

<style scoped>
* { box-sizing: border-box; }
.bills-layout { display: flex; height: calc(100vh - 56px); background: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", Arial, sans-serif; overflow: hidden; font-size: 15px; line-height: 1.62; color: #1f2937; }

/* SIDEBAR */
.sidebar { width: 240px; flex-shrink: 0; border-right: 1px solid #e5e7eb; background: #fff; display: flex; flex-direction: column; overflow-y: auto; padding: 16px 12px; }
.sidebar-head { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 16px; }
.sidebar-empty { font-size: 14px; color: #9ca3af; text-align: center; padding: 32px 0; }
.sidebar-tree { flex: 1; }
.tree-year { font-size: 13px; font-weight: 700; color: #374151; padding: 6px 8px; cursor: pointer; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; user-select: none; }
.tree-year:hover { background: #f3f4f6; }
.tree-year-count { font-size: 11px; color: #9ca3af; font-weight: 500; background: #f3f4f6; padding: 1px 6px; border-radius: 999px; }
.tree-month { font-size: 12px; color: #6b7280; padding: 4px 16px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-radius: 5px; user-select: none; }
.tree-month:hover { background: #f9fafb; }
.tree-month-count { font-size: 11px; color: #d1d5db; }
.bill-card { margin: 4px 4px 4px 16px; padding: 10px 12px; border: 1px solid #f1f5f9; border-radius: 10px; cursor: pointer; transition: 0.15s; }
.bill-card:hover { border-color: #e2e8f0; background: #f8fafc; }
.bill-card.active { background: #f0fdf4; border-color: #bbf7d0; }
.bill-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.bill-card-date { font-size: 11px; color: #9ca3af; font-weight: 500; }
.bill-card-id { font-size: 11px; color: #6b7280; font-family: "SF Mono", monospace; margin-bottom: 2px; }
.bill-card-amount { font-size: 14px; font-weight: 700; color: #111827; }

/* MAIN */
.detail-main { flex: 1; overflow-y: auto; padding: 24px 28px 40px; }
.detail-main > * + * { margin-top: 20px; }
.center-msg { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: #9ca3af; }
.center-icon { font-size: 40px; color: #d1d5db; }
.center-icon .material-icons { font-size: 48px; }
.center-title { font-size: 17px; font-weight: 600; color: #374151; }
.center-sub { font-size: 14px; }

/* HEADER */
.detail-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.dh-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.dh-title { font-size: 22px; font-weight: 800; color: #111827; margin: 0; }
.dh-meta { font-size: 13px; color: #9ca3af; margin: 0; }
.dh-meta code { font-family: "SF Mono", monospace; color: #4b5563; }
.dh-meta strong { color: #4b5563; font-weight: 600; }
.sep { margin: 0 6px; color: #d1d5db; }
.dh-actions { display: flex; gap: 8px; flex-shrink: 0; }
.btn-group { display: flex; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.btn-group button { padding: 7px 14px; border: none; background: none; font-size: 13px; font-weight: 600; color: #4b5563; cursor: pointer; transition: 0.15s; }
.btn-group button:not(:last-child) { border-right: 1px solid #e5e7eb; }
.btn-group button:hover:not(:disabled) { background: #f9fafb; }
.btn-group button:disabled { opacity: 0.4; cursor: not-allowed; }

/* BADGES */
.bill-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.bill-badge.lg { font-size: 12px; padding: 3px 10px; }
.badge-green { background: #d1fae5; color: #065f46; }
.badge-amber { background: #fef3c7; color: #92400e; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-gray { background: #f1f5f9; color: #475569; }

/* STAT ROW */
.stat-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.stat-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.stat-icon { width: 46px; height: 46px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.stat-icon .material-icons { font-size: 22px; }
.stat-icon.blue { background: #eff6ff; }
.stat-icon.orange { background: #fff7ed; }
.stat-icon.green { background: #f0fdf4; color: #059669; font-size: 16px; font-weight: 800; }
.stat-icon.amber { background: #fffbeb; }
.stat-icon.purple { background: #faf5ff; }
.stat-label { font-size: 12px; color: #9ca3af; font-weight: 500; margin-bottom: 4px; }
.stat-val { font-size: 16px; font-weight: 800; color: #111827; }
.stat-val.green-val { color: #059669; }
.stat-unit { font-size: 13px; font-weight: 600; color: #6b7280; }

/* BODY GRID */
.body-grid { display: grid; grid-template-columns: 1fr 320px; gap: 16px; }
.left-col { display: flex; flex-direction: column; gap: 16px; }
.right-col { display: flex; flex-direction: column; gap: 16px; }

/* PANEL */
.panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.panel-head { padding: 14px 18px; border-bottom: 1px solid #f1f5f9; }
.panel-title { font-size: 13px; font-weight: 700; color: #111827; display: inline-flex; align-items: center; gap: 6px; }
.panel-title .material-icons { font-size: 16px; color: #9ca3af; }
.process-title { font-size: 15px; font-weight: 800; }

/* PROCESS TABLE */
.process-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.process-table-large { font-size: 14px; }
.process-table tr { border-bottom: 1px solid #f8fafc; }
.process-table tr:last-child { border-bottom: none; }
.process-table-large td { padding: 13px 16px; color: #374151; vertical-align: middle; }
.process-table-large .pt-icon { width: 34px; color: #94a3b8; text-align: center; vertical-align: middle; }
.pt-icon .material-icons { font-size: 20px; vertical-align: middle; }
.pt-icon.charging { color: #059669; }
.pt-icon.done { color: #059669; font-weight: 700; }
.pt-icon.fault { color: #ef4444; }
.pt-icon.cancelled { color: #6b7280; }
.pt-event-fault { color: #ef4444 !important; }
.pt-desc-fault { color: #ef4444; }
.process-table-large .pt-time { color: #6b7280; font-size: 13px; white-space: nowrap; }
.process-table-large .pt-event { font-weight: 800; color: #111827; white-space: nowrap; }
.process-table-large .pt-desc { color: #4b5563; font-size: 13px; line-height: 1.5; }
.pt-amount { color: #059669; font-weight: 700; }

/* CHART */
.chart-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.chart-legend { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.chart-leg-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #6b7280; font-weight: 600; white-space: nowrap; }
.chart-leg-item i { width: 10px; height: 10px; display: inline-block; flex-shrink: 0; }
.chart-leg-item i.line { height: 2px; width: 14px; border-radius: 1px; }
.chart-leg-item i.line.green { background: #10b981; }
.chart-leg-item i.line.blue { background: #2563eb; }
.chart-wrap { padding: 4px 18px 12px; }
.chart-area { position: relative; height: 200px; cursor: crosshair; overflow: hidden; }
.chart-svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.chart-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 0 24px;
  color: #667085;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  pointer-events: none;
}
.chart-y-labels { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: space-between; padding: 0 4px 20px; pointer-events: none; }
.chart-y-labels span { font-size: 9px; color: #9ca3af; display: flex; justify-content: space-between; }
.y2 { color: #bfdbfe; }
.chart-x-labels { display: flex; justify-content: space-between; font-size: 11px; color: #9ca3af; margin-top: 4px; }
.tick-peak { color: #d97706; font-weight: 700; }
.chart-tooltip { position: absolute; background: rgba(15,23,42,.94); backdrop-filter: blur(4px); color: #fff; padding: 10px 12px; border-radius: 10px; font-size: 10px; width: 176px; z-index: 20; pointer-events: none; border: 1px solid rgba(255,255,255,.1); }
.tt-head { display: flex; justify-content: space-between; font-weight: 700; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,.1); padding-bottom: 6px; margin-bottom: 6px; }
.tt-row { display: flex; justify-content: space-between; margin-bottom: 4px; color: #94a3b8; }
.tt-green { color: #34d399; font-weight: 700; }
.tt-blue { color: #60a5fa; font-weight: 700; }
.tt-amber { color: #fbbf24; }

/* PAYMENT */
.pay-rows { padding: 4px 0; }
.pay-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 18px; border-bottom: 1px solid #f8fafc; font-size: 13px; color: #6b7280; }
.pay-row strong { font-size: 14px; color: #111827; }
.pay-row .mono { font-size: 12px; color: #374151; }
.pay-row .mono.small { font-size: 11px; color: #9ca3af; }
.pay-tip { display: flex; gap: 8px; align-items: flex-start; margin: 12px; padding: 10px 12px; border-radius: 10px; background: #fffbeb; border: 1px solid #fde68a; color: #92400e; font-size: 13px; line-height: 1.5; }
.pay-tip.success { background: #f0fdf4; border-color: #bbf7d0; color: #065f46; }
.unpaid-notice { padding: 24px 18px 16px; text-align: center; }
.unpaid-amount { font-size: 30px; font-weight: 900; color: #d97706; letter-spacing: -0.5px; }
.unpaid-label { font-size: 12px; color: #9ca3af; margin-top: 4px; font-weight: 500; }
.unpaid-sub { font-size: 12px; color: #6b7280; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #e5e7eb; }
.unpaid-actions { padding: 0 18px 16px; }
.btn-pay { width: 100%; padding: 12px; border: none; border-radius: 10px; background: #10b981; color: #fff; font-size: 15px; font-weight: 700; cursor: pointer; transition: 0.15s; }
.btn-pay:hover:not(:disabled) { background: #059669; }
.btn-pay:disabled { background: #d1d5db; cursor: not-allowed; color: #9ca3af; }

/* COST */
.cost-rows { padding: 4px 0; }
.cost-row { display: flex; justify-content: space-between; align-items: flex-start; padding: 12px 18px; border-bottom: 1px solid #f8fafc; gap: 12px; }
.cost-name { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 2px; }
.cost-formula { font-size: 11px; color: #9ca3af; }
.cost-val { font-size: 14px; font-weight: 700; color: #111827; white-space: nowrap; }
.cost-total { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: #f8fafc; }
.cost-total span { font-size: 15px; font-weight: 800; color: #111827; }
.cost-total-val { color: #059669; font-size: 17px; }

/* BILLING RULES */
.rules-panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.04); margin-bottom: 24px; }
.rules-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0; }
.rule-card { padding: 16px; border-right: 1px solid #f1f5f9; }
.rule-card:last-child { border-right: none; }
.rule-icon { width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; margin-bottom: 8px; }
.rule-icon .material-icons { font-size: 18px; }
.rule-icon.orange { background: #fff7ed; }
.rule-icon.blue { background: #eff6ff; }
.rule-icon.green { background: #f0fdf4; }
.rule-icon.purple { background: #faf5ff; }
.rule-icon.teal { background: #f0fdfa; }
.rule-name { font-size: 12px; color: #6b7280; font-weight: 500; margin-bottom: 4px; }
.rule-val { font-size: 15px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.rule-hint { font-size: 11px; color: #9ca3af; line-height: 1.4; }

@media (max-width: 1100px) {
  .stat-row { grid-template-columns: repeat(3, 1fr); }
  .body-grid { grid-template-columns: 1fr; }
  .rules-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .bills-layout { flex-direction: column; height: auto; }
  .sidebar { width: 100%; height: 200px; border-right: none; border-bottom: 1px solid #e5e7eb; }
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .rules-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
