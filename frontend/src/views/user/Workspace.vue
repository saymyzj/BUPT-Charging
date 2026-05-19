<template>
  <main class="page workspace-page">
    <section class="status-row" :class="{ 'status-amber': isWaiting && hasActive }">
      <div class="status-main">
        <div class="status-bolt">{{ isWaiting && hasActive ? '⏳' : '⚡' }}</div>
        <div>
          <div class="status-title" :class="{ 'amber-text': isWaiting && hasActive }">
            <template v-if="isWaiting && hasActive">等待系统分配中</template>
            <template v-else>当前状态：<strong>{{ hasActive ? statusText : '空闲' }}</strong></template>
          </div>
          <div class="status-sub" :class="{ 'amber-text': isWaiting && hasActive }">
            <template v-if="isWaiting && hasActive">系统正在计算最优充电策略，请将车辆驶入公共等候区。</template>
            <template v-else>{{ hasActive ? statusHeadline : '当前没有进行中的充电请求' }}</template>
          </div>
        </div>
      </div>
      <div class="metric"><div class="metric-icon">👤</div><div><div class="metric-label">排队号</div><div class="metric-val">{{ queueNumberText(activeRequest) }}</div></div></div>
      <div class="metric"><div class="metric-icon">🚗</div><div><div class="metric-label">前车数量</div><div class="metric-val">{{ frontVehicleCountText }} 辆</div></div></div>
      <div class="metric"><div class="metric-icon">🕘</div><div><div class="metric-label">{{ durationMetricLabel }}</div><div class="metric-val">{{ durationMetricDisplay }}</div></div></div>
      <div class="metric"><div class="metric-icon">⛽</div><div><div class="metric-label">正常桩</div><div class="metric-val"><span class="green">{{ runningStationCount }}</span> / {{ totalStationCount }}</div></div></div>
      <div class="metric"><div class="metric-icon">🅿</div><div><div class="metric-label">空闲桩</div><div class="metric-val"><span class="green">{{ idleStationCount }}</span> / {{ totalStationCount }}</div></div></div>
    </section>

    <section class="queue-zone">
      <div class="queue-head">
        <div>
          <h2 class="section-title">充电桩调度动态</h2>
          <p class="section-sub">车辆从入口进入主队列，系统选择目标桩位后，车辆沿竖向分支进入对应充电桩。</p>
        </div>
        <div class="legend">
          <span><i style="background:#4f46e5"></i>你的请求</span>
          <span><i style="background:#059669"></i>充电中</span>
          <span><i style="background:#ef4444"></i>故障</span>
          <span><i style="background:#98a2b3"></i>空闲</span>
        </div>
      </div>

      <div class="dispatch-stage">
        <div class="main-lane"></div>
        <div class="route-pulse"></div>
        <span class="entry-label">入口</span>
        <span class="exit-label">出口</span>

        <div v-if="!dispatchPiles.length && stationOverviewLoaded" class="dispatch-empty">暂无充电桩状态数据</div>
        <div class="pile-row">
          <div class="pile" v-for="pile in dispatchPiles" :key="pile.code">
            <div class="pile-name">{{ pile.code }}</div>
            <div class="pile-box" :class="[pile.state, { current: pile.current }]">
              <div class="charger"></div>
              <div v-if="pile.queue" class="queue-badge">{{ pile.queue }}</div>
              <div v-if="pile.current && isQueued" class="pile-waiting-car"></div>
            </div>
            <div class="branch"></div>
            <div class="pile-status" :class="pile.state">{{ pile.label }}</div>
          </div>
        </div>

        <div
          v-for="car in dispatchCars"
          :key="`${car.id}-${car.targetX}-${car.targetCode}`"
          class="car"
          :class="{ assigned: car.assigned, waiting: car.waiting, junction: car.junction }"
          :style="{ '--target-x': car.targetX + 'px', '--delay': car.delay + 's' }"
        >
          <div class="car-body">
            <div class="car-window"></div>
            <div class="wheel left"></div>
            <div class="wheel right"></div>
          </div>
        </div>
      </div>
    </section>

    <section class="main-grid">
      <div class="panel">
        <h2 class="section-title">提交充电请求</h2>
        <p class="section-sub">填写请求电量，系统将自动分配充电桩。</p>
        <div class="form-row">
          <div>
            <label>充电模式</label>
            <select v-model="form.charge_mode" :disabled="hasActive || syncingActive">
              <option value="FAST">⚡ 快充（30kW）</option>
              <option value="SLOW">慢充（10kW）</option>
            </select>
          </div>
          <div>
            <label>请求电量（kWh）
              <span v-if="batteryCapacity" style="font-weight:400;color:#9ca3af;margin-left:6px;">最大 {{ batteryCapacity }} kWh</span>
            </label>
            <input type="number" v-model.number="form.request_energy"
              :placeholder="batteryCapacity ? `1 ~ ${batteryCapacity}` : '1 ~ 电池容量'"
              :disabled="hasActive || syncingActive"
              :max="batteryCapacity || undefined" min="0.1" step="0.1">
            <div v-if="energyOverCapacity" style="color:#ef4444;font-size:12px;margin-top:4px;">
              ⚠ 超出电池容量（{{ batteryCapacity }} kWh），请重新输入
            </div>
          </div>
        </div>
        <button class="submit" @click="submitRequest" :disabled="hasActive || syncingActive || submitting">
          ✈ {{ hasActive ? '当前有进行中的请求' : syncingActive ? '同步中...' : submitting ? '提交中...' : '提交请求' }}
        </button>
        <div class="error-box" v-if="errMsg">{{ errMsg }}</div>
        <div class="notice" v-else>
          <strong>系统自动调度</strong><br>
          提交后，系统会根据当前队列、充电桩状态和最短完成时间策略自动分配桩位。您无需手动选择方案。
        </div>
      </div>

      <div class="panel">
        <h2 class="section-title">当前请求状态</h2>
        <div class="empty" v-if="!activeLoaded && !hasActive && !submitResult">
          <div class="empty-illus" style="display:inline-block; animation: spin 2s linear infinite;">⏳</div>
          <strong>同步状态中...</strong>
          <span>正在获取当前请求状态...</span>
        </div>
        <div class="empty" v-else-if="!hasActive && !submitResult">
          <div class="empty-illus">📋</div>
          <strong>暂无进行中的请求</strong>
          <span>提交请求后，状态将在此处显示。</span>
        </div>
        <div class="request-card" v-else>
          <div class="request-title">{{ statusText }}</div>
          <div class="request-sub">{{ statusSubline }}</div>
          <div class="request-grid">
            <div><span>请求编号</span><strong>{{ activeRequest?.request_id || submitResult?.request_id || '--' }}</strong></div>
            <div><span>排队号</span><strong>{{ queueNumberText(activeRequest || submitResult) }}</strong></div>
            <div><span>模式</span><strong>{{ CHARGE_MODE_TEXT[(activeRequest || submitResult)?.charge_mode] || '--' }}</strong></div>
            <div><span>请求电量</span><strong>{{ (activeRequest || submitResult)?.request_energy || '--' }} kWh</strong></div>
          </div>
          <router-link to="/user/task" class="state-link">查看详情 →</router-link>
        </div>
      </div>

      <div class="panel">
        <h2 class="section-title">充电流程</h2>
        <div class="flow">
          <div class="flow-step"><div class="num">1</div><div><strong>提交充电请求</strong><p>选择充电模式，填写请求电量。</p></div></div>
          <div class="flow-step"><div class="num">2</div><div><strong>等候区排队</strong><p>按提交时间进入等待队列，容量上限 20 辆。</p></div></div>
          <div class="flow-step"><div class="num">3</div><div><strong>系统调度</strong><p>按最短完成时间策略自动分配充电桩。</p></div></div>
          <div class="flow-step"><div class="num">4</div><div><strong>自动开始充电</strong><p>到达队列首位后自动启动。</p></div></div>
          <div class="flow-step"><div class="num">5</div><div><strong>完成结算</strong><p>按分时电价和服务费生成费用。</p></div></div>
        </div>
      </div>
    </section>

    <section class="bottom">
      <div>
        <h2 class="section-title">电价时段 <span>（24小时时间轴）</span></h2>
        <div class="time-axis">
          <div class="axis-bar">
            <div class="now-marker" :data-time="currentTimeText" :style="{ left: currentTimePercent + '%' }"></div>
            <div v-for="segment in priceSegments" :key="segment.start" class="seg" :class="segment.kind">
              {{ segment.label }}<small>{{ segment.priceText }}</small>
            </div>
          </div>
          <div class="time-ticks">
            <span
              v-for="tick in priceTicks"
              :key="tick.label"
              class="tick"
              :class="tick.align"
              :style="{ left: tick.percent + '%' }"
            >
              <b>{{ tick.label }}</b>
            </span>
          </div>
          <div class="formula">ⓘ 费用 = 各时段电量 × 对应电价 + 服务费</div>
        </div>
      </div>
      <div>
        <h2 class="section-title">费用说明</h2>
        <div class="fee-list">
          <div class="fee"><div class="fee-icon">⚡</div><div><strong>电费</strong><p>根据所选时段电价 × 请求电量计算。</p></div></div>
          <div class="fee"><div class="fee-icon">💰</div><div><strong>服务费</strong><p>全时段固定费率，按请求电量收取。</p></div></div>
          <div class="fee"><div class="fee-icon">🧾</div><div><strong>预计总价</strong><p>电费 + 服务费，实际结算为准。</p></div></div>
        </div>
      </div>
    </section>

  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createChargeRequest, getActiveRequest, getProfile, getStationsOverview } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { REQUEST_STATUS, REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT, ACTIVE_STATUSES } from '@/constants/enums'
import { clearLegacyLocalState } from '@/utils/authSession'
import { formatRequestRemainingText } from '@/utils/requestEta'

const form = ref({ charge_mode: 'FAST', request_energy: null })
const submitting = ref(false)
const errMsg = ref('')
const submitResult = ref(null)
const currentReq = ref(null)
const batteryCapacity = ref(null)
const syncingActive = ref(false)
const activeLoaded = ref(false)
const STATION_OVERVIEW_CACHE_KEY = 'workspace_station_overview_cache'
const stationOverview = ref(loadCachedStationOverview())
const stationOverviewLoaded = ref(Boolean(stationOverview.value))
let pollTimer = null
let clockTimer = null
const now = ref(new Date())

const pileTargets = [212, 424, 636, 848, 1060]

const hasActive = computed(() => {
  if (!currentReq.value) return false
  return ACTIVE_STATUSES.includes(currentReq.value.request_status)
})

const energyOverCapacity = computed(() =>
  batteryCapacity.value && form.value.request_energy > batteryCapacity.value
)

const activeRequest = computed(() => hasActive.value ? currentReq.value : null)

const statusText = computed(() => {
  if (!activeRequest.value) return '空闲'
  return REQUEST_STATUS_TEXT[activeRequest.value.request_status] || activeRequest.value.request_status
})

const durationMetricLabel = computed(() => {
  if (activeRequest.value?.request_status === REQUEST_STATUS.CHARGING) return '剩余充电'
  return '剩余排队'
})

const durationMetricDisplay = computed(() => {
  const request = activeRequest.value
  if (!request) return '--'
  return formatRequestRemainingText(request, now.value)
})

const frontVehicleCount = computed(() => {
  const request = activeRequest.value
  if (!request) return null
  if ([REQUEST_STATUS.QUEUED, REQUEST_STATUS.CHARGING].includes(request.request_status)) {
    const position = Number(request.station_queue_position)
    if (Number.isFinite(position)) return Math.max(0, position - 1)
  }
  const count = Number(request.front_waiting_count)
  return Number.isFinite(count) ? Math.max(0, count) : null
})

const frontVehicleCountText = computed(() => {
  return frontVehicleCount.value === null ? '--' : String(frontVehicleCount.value)
})

const chargedEnergy = computed(() => {
  const n = Number(activeRequest.value?.charged_energy ?? activeRequest.value?.actual_energy)
  return Number.isFinite(n) ? Math.max(0, n) : null
})

const chargePercentText = computed(() => {
  const total = Number(activeRequest.value?.request_energy)
  if (chargedEnergy.value === null || !Number.isFinite(total) || total <= 0) return '--'
  return `${Math.min(100, Math.max(0, chargedEnergy.value / total * 100)).toFixed(1)}%`
})

const statusHeadline = computed(() => {
  if (!hasActive.value) return '没有进行中的充电请求'
  const request = activeRequest.value
  if (request.request_status === REQUEST_STATUS.WAITING_AREA) return `等候区排队，前方 ${frontVehicleCountText.value} 辆`
  if (request.request_status === REQUEST_STATUS.QUEUED) return `${request.station_code || '充电桩'} 队列第 ${request.station_queue_position ?? '?'} 位`
  if (request.request_status === REQUEST_STATUS.CHARGING) return `${request.station_code || '充电桩'} 正在充电，已充 ${chargePercentText.value}`
  return statusText.value
})

const statusSubline = computed(() => {
  if (!hasActive.value) return '选择充电模式和目标电量后提交，页面会自动同步排队状态。'
  const request = activeRequest.value
  if (request.request_status === REQUEST_STATUS.CHARGING) return `已充电量 ${chargedEnergy.value === null ? '--' : `${chargedEnergy.value.toFixed(2)} kWh`}，预计完成 ${fmtDateTime(request.estimated_finish_time)}`
  return `预计开始 ${fmtDateTime(request.estimated_start_time)}，剩余排队 ${durationMetricDisplay.value}`
})

const currentTimeText = computed(() => {
  const pad = (value) => String(value).padStart(2, '0')
  return `${pad(now.value.getHours())}:${pad(now.value.getMinutes())}`
})

const currentTimePercent = computed(() => {
  const minutes = now.value.getHours() * 60 + now.value.getMinutes() + now.value.getSeconds() / 60
  return priceAxisPercent(minutes)
})

const priceSegments = [
  { start: 0, end: 7 * 60, label: '谷时', kind: 'valley', priceText: '¥0.4/kWh' },
  { start: 7 * 60, end: 10 * 60, label: '平时', kind: 'normal', priceText: '¥0.7/kWh' },
  { start: 10 * 60, end: 15 * 60, label: '峰时', kind: 'peak', priceText: '¥1.0/kWh' },
  { start: 15 * 60, end: 18 * 60, label: '平时', kind: 'normal', priceText: '¥0.7/kWh' },
  { start: 18 * 60, end: 21 * 60, label: '峰时', kind: 'peak', priceText: '¥1.0/kWh' },
  { start: 21 * 60, end: 23 * 60, label: '平时', kind: 'normal', priceText: '¥0.7/kWh' },
  { start: 23 * 60, end: 24 * 60, label: '谷时', kind: 'valley', priceText: '¥0.4/kWh' },
]

const priceTicks = [
  { label: '00:00', minute: 0, align: 'start' },
  { label: '07:00', minute: 7 * 60 },
  { label: '10:00', minute: 10 * 60 },
  { label: '15:00', minute: 15 * 60 },
  { label: '18:00', minute: 18 * 60 },
  { label: '21:00', minute: 21 * 60 },
  { label: '23:00', minute: 23 * 60, align: 'near-end' },
  { label: '24:00', minute: 24 * 60, align: 'end' },
].map((tick) => ({
  ...tick,
  percent: priceAxisPercent(tick.minute),
}))

function priceAxisPercent(minutes) {
  const clamped = Math.max(0, Math.min(24 * 60, minutes))
  return clamped / (24 * 60) * 100
}

const overviewStations = computed(() => {
  const data = stationOverview.value
  if (!data) return []
  const fast = Array.isArray(data.fast_stations) ? data.fast_stations : []
  const slow = Array.isArray(data.slow_stations) ? data.slow_stations : []
  return [...fast, ...slow].sort((a, b) => String(a.station_code).localeCompare(String(b.station_code)))
})

const waitingSummary = computed(() => {
  return stationOverview.value?.waiting_queue || {
    fast_queue_count: 0,
    slow_queue_count: 0,
    total_waiting: 0,
    capacity: 0,
  }
})

const totalStationCount = computed(() => overviewStations.value.length || '--')

const runningStationCount = computed(() => {
  if (!overviewStations.value.length) return '--'
  return overviewStations.value.filter((station) => station.station_status === 'RUNNING').length
})

const idleStationCount = computed(() => {
  if (!overviewStations.value.length) return '--'
  return overviewStations.value.filter((station) => {
    if (station.station_status !== 'RUNNING') return false
    const length = Number(station.queue_length ?? station.current_queue_length ?? 0)
    const capacity = Number(station.queue_capacity)
    return !station.current_request_id && (!Number.isFinite(capacity) || length < capacity)
  }).length
})

const dispatchPiles = computed(() => {
  const currentCode = activeRequest.value?.station_code || ''
  return overviewStations.value.slice(0, 5).map((station) => {
    const queueLength = Math.max(0, Number(station.queue_length ?? station.current_queue_length ?? 0) || 0)
    const current = currentCode && stationCodeEquals(station.station_code, currentCode)
    const state = stationVisualState(station, current)
    return {
      code: station.station_code,
      state,
      queue: queueLength,
      current,
      label: current ? '当前请求' : stationVisualLabel(station, queueLength),
    }
  })
})

const isWaiting = computed(() => activeRequest.value?.request_status === REQUEST_STATUS.WAITING_AREA)
const isQueued = computed(() => activeRequest.value?.request_status === REQUEST_STATUS.QUEUED)
const isCharging = computed(() => activeRequest.value?.request_status === REQUEST_STATUS.CHARGING)

const dispatchCars = computed(() => {
  const status = activeRequest.value?.request_status
  const activeIndex = dispatchPiles.value.findIndex((pile) => pile.current)
  const otherQueuedIndexes = dispatchPiles.value
    .map((pile, index) => ({ pile, index }))
    .filter(({ pile }) => !pile.current && (pile.queue > 0 || pile.state === 'busy'))
    .map(({ index }) => index)

  const cars = []
  if (status === REQUEST_STATUS.WAITING_AREA) {
    return []
  } else if (status === REQUEST_STATUS.QUEUED && activeIndex >= 0) {
    cars.push({ id: 0, targetX: pileTargets[activeIndex], delay: 0, assigned: true, junction: true, targetCode: dispatchPiles.value[activeIndex]?.code || '' })
  } else if (status === REQUEST_STATUS.CHARGING && activeIndex >= 0) {
    cars.push({ id: 0, targetX: pileTargets[activeIndex], delay: 0, assigned: true, targetCode: dispatchPiles.value[activeIndex]?.code || '' })
  }
  otherQueuedIndexes.forEach((index, i) => {
    cars.push({ id: i + 1, targetX: pileTargets[index], delay: (i + 1) * 2.6, assigned: true, targetCode: dispatchPiles.value[index]?.code || '' })
  })
  return cars
})

function stationVisualState(station, current = false) {
  if (current) return 'mine'
  if (station.station_status === 'FAULT') return 'fault'
  if (station.station_status === 'SHUTDOWN') return 'shutdown'
  if (station.current_request_id) return 'busy'
  const queueLength = Number(station.queue_length ?? station.current_queue_length ?? 0)
  if (Number.isFinite(queueLength) && queueLength > 0) return 'queue'
  return 'ready'
}

function stationVisualLabel(station, queueLength) {
  if (station.station_status === 'FAULT') return '故障'
  if (station.station_status === 'SHUTDOWN') return '已关闭'
  if (station.current_request_id) return '充电中'
  if (queueLength > 0) return '排队中'
  return '空闲'
}

function stationCodeEquals(a, b) {
  return normalizeStationCode(a) === normalizeStationCode(b)
}

function normalizeStationCode(code) {
  return String(code || '').replace(/[-_\s]/g, '').toUpperCase()
}

function fmtDateTime(time) {
  if (!time) return '--'
  try {
    return new Date(time).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return '--'
  }
}

function queueNumberText(row) {
  if (!row) return '--'
  if (row.is_fault_followup && row.source_queue_number && row.source_queue_number !== row.queue_number) {
    return `${row.queue_number}（源${row.source_queue_number}）`
  }
  return row.queue_number || '--'
}

async function loadProfile() {
  try {
    const res = await getProfile()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return
    batteryCapacity.value = Number(data.battery_capacity)
  } catch (_) { /* silent */ }
}

async function loadStationOverview() {
  try {
    const res = await getStationsOverview()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return
    stationOverview.value = data
    stationOverviewLoaded.value = true
    saveCachedStationOverview(data)
  } catch (_) {
    stationOverviewLoaded.value = true
  }
}

function loadCachedStationOverview() {
  try {
    const raw = sessionStorage.getItem(STATION_OVERVIEW_CACHE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveCachedStationOverview(data) {
  try {
    sessionStorage.setItem(STATION_OVERVIEW_CACHE_KEY, JSON.stringify(data))
  } catch (_) {
    /* ignore quota/cache errors */
  }
}

function formatLocalDateTime(date = new Date()) {
  const pad = (value) => String(value).padStart(2, '0')
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate())
  ].join('-') + `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function clearActiveConflict() {
  clearLegacyLocalState()
}

function rememberActiveRequest(data) {
  if (!data?.request_id) return
  clearActiveConflict()
  currentReq.value = data
}

async function loadActiveRequest() {
  syncingActive.value = true
  try {
    const res = await getActiveRequest()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return false
    if (data.request_id && ACTIVE_STATUSES.includes(data.request_status)) {
      rememberActiveRequest(data)
      return true
    }
    clearLegacyLocalState()
    currentReq.value = null
    clearActiveConflict()
    return false
  } catch (_) {
    return false
  } finally {
    syncingActive.value = false
    activeLoaded.value = true
  }
}

async function submitRequest() {
  errMsg.value = ''
  if (!form.value.request_energy || form.value.request_energy <= 0) {
    errMsg.value = '请输入有效的请求电量'
    return
  }
  if (batteryCapacity.value && form.value.request_energy > batteryCapacity.value) {
    errMsg.value = `请求电量不能超过电池容量 ${batteryCapacity.value} kWh`
    return
  }

  submitting.value = true
  try {
    const res = await createChargeRequest({
      charge_mode: form.value.charge_mode,
      request_energy: form.value.request_energy,
      request_time: formatLocalDateTime()
    })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      errMsg.value = data.message || '提交失败'
      return
    }
    const createdRequest = {
      ...data,
      charge_mode: form.value.charge_mode,
      request_energy: form.value.request_energy
    }
    submitResult.value = createdRequest
    clearActiveConflict()
    currentReq.value = createdRequest
    startPoll()
  } catch (e) {
    const code = e?.response?.data?.code
    const msg = e?.response?.data?.message
    if (code === 1004) errMsg.value = '等候区已满，请稍后再试'
    else if (code === 1005) errMsg.value = '当前模式无可用充电桩'
    else if (code === 1008) errMsg.value = '请求电量不合法'
    else if (code === 1003) {
      const synced = await loadActiveRequest()
      if (synced) {
        errMsg.value = '当前用户已有进行中的请求，已自动同步到页面。'
        startPoll()
      } else {
        errMsg.value = '服务端提示已有进行中的请求，但当前账号未同步到请求详情，请刷新页面后重试。'
      }
    }
    else errMsg.value = msg || e?.message || '提交失败'
  } finally {
    submitting.value = false
  }
}

async function pollStatus() {
  await Promise.all([
    loadActiveRequest(),
    loadStationOverview(),
  ])
}

function startPoll() {
  stopPoll()
  pollTimer = setInterval(pollStatus, 5000)
}

function stopPoll() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onMounted(() => {
  loadProfile()
  loadStationOverview()
  pollStatus()
  startPoll()
  clockTimer = setInterval(() => {
    now.value = new Date()
  }, 30000)
})

onUnmounted(() => {
  stopPoll()
  if (clockTimer) {
    clearInterval(clockTimer)
    clockTimer = null
  }
})
</script>

<style scoped>
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* STATUS AMBER */
.status-amber { border-color: #fde68a !important; background: linear-gradient(180deg, rgba(255,251,235,.98), rgba(255,253,243,.98)) !important; }
.amber-text { color: #92400e !important; }

/* WAIT NOTICE — absolute overlay inside dispatch-stage */
.wait-notice { position: absolute; z-index: 12; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; gap: 14px; padding: 14px 22px; border-radius: 16px; border: 1px solid #fde68a; background: rgba(255,251,235,.97); white-space: nowrap; box-shadow: 0 8px 28px rgba(0,0,0,.08); }
.wait-notice-icon { font-size: 22px; flex-shrink: 0; }
.wait-notice-title { font-size: 15px; font-weight: 800; color: #92400e; }
.wait-notice-sub { margin: 4px 0 0; font-size: 13px; color: #b45309; line-height: 1.5; white-space: normal; max-width: 360px; }

/* CAR INSIDE PILE (QUEUED) */
.pile-waiting-car { position: absolute; bottom: 5px; left: 50%; transform: translateX(-50%); width: 30px; height: 14px; background: linear-gradient(180deg, #fff, #ede9fe); border: 1px solid rgba(79,70,229,.55); border-radius: 6px 6px 4px 4px; }
.pile-waiting-car::before { content: ""; position: absolute; left: 8px; top: 2px; width: 14px; height: 5px; background: rgba(79,70,229,.18); border-radius: 3px; }

/* JUNCTION CAR (QUEUED — static at intersection) */
.car.junction { animation: none !important; transform: translate(var(--target-x), 151px) !important; opacity: 1 !important; }
.car.junction .car-body { border-color: rgba(79,70,229,.72); box-shadow: 0 10px 22px rgba(79,70,229,.18); animation: junctionPulse 2.2s ease-in-out infinite; }
@keyframes junctionPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.65; } }

/* WAITING CAR (WAITING_AREA — horizontal only) */
.car.waiting { animation: waitCar 9s ease-in-out infinite !important; }
@keyframes waitCar {
  0%   { transform: translate(-86px, 151px); opacity: 0; }
  6%   { transform: translate(66px, 151px); opacity: 1; }
  80%  { transform: translate(1300px, 151px); opacity: 1; }
  90%  { opacity: 0; }
  100% { transform: translate(-86px, 151px); opacity: 0; }
}

.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 28px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.stat { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px 20px; transition: 0.2s; }
.stat:hover { border-color: #34d399; box-shadow: 0 2px 12px rgba(16,185,129,0.06); }
.stat-label { font-size: 12px; font-weight: 500; color: #6b7280; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.stat-label::before { content: ""; width: 6px; height: 6px; border-radius: 2px; }
.stat-label.green::before { background: #10b981; }
.stat-label.blue::before { background: #3b82f6; }
.stat-label.amber::before { background: #f59e0b; }
.stat-label.gray::before { background: #9ca3af; }
.stat-val { font-size: 26px; font-weight: 700; color: #111827; letter-spacing: -1px; }

.status-strip { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 18px 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: white; margin-bottom: 16px; }
.status-strip.active { border-color: #bfdbfe; background: #eff6ff; }
.status-strip.idle { border-color: #d1fae5; background: #ecfdf5; }
.strip-kicker { font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.4px; }
.strip-title { margin-top: 5px; font-size: 18px; font-weight: 700; color: #111827; }
.strip-sub { margin-top: 4px; font-size: 13px; color: #6b7280; line-height: 1.5; }
.strip-action { flex: 0 0 auto; padding: 9px 14px; border-radius: 8px; background: white; border: 1px solid #bfdbfe; color: #1d4ed8; font-size: 13px; font-weight: 700; text-decoration: none; }
.strip-action:hover { background: #dbeafe; }

.queue-zone { padding: 24px 0 26px; border-bottom: 1px solid #e5e7eb; margin-bottom: 18px; }
.queue-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
.section-title { font-size: 22px; font-weight: 800; margin: 0 0 8px; color: #101828; }
.section-sub { color: #667085; font-size: 14px; margin: 0; line-height: 1.7; }
.legend { display: flex; gap: 18px; color: #667085; font-size: 13px; white-space: nowrap; }
.legend i { width: 8px; height: 8px; display: inline-block; border-radius: 3px; margin-right: 6px; }
.dispatch-stage {
  position: relative;
  height: 250px;
  overflow: hidden;
  border-radius: 20px;
  background:
    radial-gradient(circle at 7% 45%, rgba(16,185,129,.12), transparent 26%),
    radial-gradient(circle at 85% 18%, rgba(37,99,235,.08), transparent 24%),
    linear-gradient(180deg, rgba(236,253,245,.48), rgba(255,255,255,.96));
  border: 1px solid #e4efe9;
  box-shadow: 0 14px 36px rgba(16, 24, 40, 0.06);
}
.energy-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(5, 150, 105, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(5, 150, 105, 0.08) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(180deg, rgba(0,0,0,.45), transparent 70%);
}
.pulse-halo {
  position: absolute;
  left: 72px;
  top: 144px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid rgba(16,185,129,.32);
  animation: halo 2.2s ease-out infinite;
}
.main-lane {
  position: absolute;
  left: 64px;
  right: 64px;
  top: 164px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, #cbd5e1 8%, #cbd5e1 92%, transparent);
}
.main-lane::after {
  content: "";
  position: absolute;
  right: -12px;
  top: -5px;
  width: 12px;
  height: 12px;
  border-top: 3px solid #cbd5e1;
  border-right: 3px solid #cbd5e1;
  transform: rotate(45deg);
}
.entry-label, .exit-label {
  position: absolute;
  top: 174px;
  color: #667085;
  font-size: 13px;
  font-weight: 600;
}
.entry-label { left: 64px; }
.exit-label { right: 62px; }
.pile-row {
  position: absolute;
  left: 170px;
  right: 150px;
  top: 24px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 28px;
  z-index: 3;
}
.pile { position: relative; text-align: center; min-width: 110px; }
.pile-name { font-weight: 800; margin-bottom: 8px; font-size: 15px; color: #101828; }
.pile-box {
  height: 92px;
  width: 110px;
  margin: 0 auto;
  border: 2px dashed #cfd8d3;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,.72);
  position: relative;
  transition: .25s;
}
.pile-box.busy { border-style: solid; border-color: rgba(5,150,105,.48); background: rgba(236,253,245,.82); }
.pile-box.queue { border-style: solid; border-color: rgba(37,99,235,.35); background: rgba(239,246,255,.82); }
.pile-box.mine { border-style: solid; border-color: rgba(79,70,229,.55); background: rgba(238,242,255,.9); }
.pile-box.mine.current { box-shadow: 0 0 0 5px rgba(79,70,229,.1), 0 18px 30px rgba(79,70,229,.14); }
.branch {
  position: absolute;
  left: 50%;
  top: 118px;
  width: 3px;
  height: 46px;
  transform: translateX(-50%);
  background: linear-gradient(180deg, #a7f3d0, #cbd5e1);
  border-radius: 999px;
}
.branch::after {
  content: "";
  position: absolute;
  left: -4px;
  bottom: -5px;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #cbd5e1;
}
.pile-box.busy + .branch { background: linear-gradient(180deg, #10b981, #a7f3d0); }
.charger {
  width: 36px;
  height: 58px;
  border-radius: 10px 10px 6px 6px;
  background: linear-gradient(180deg, #fff, #e5e7eb);
  border: 1px solid #cbd5e1;
  box-shadow: 0 12px 22px rgba(15,23,42,.1);
  position: relative;
}
.charger::before {
  content:"";
  position:absolute;
  left:11px;
  top:8px;
  width:14px;
  height:18px;
  border-radius:3px;
  background:#0f766e;
}
.charger::after {
  content:"⚡";
  position:absolute;
  left:11px;
  top:32px;
  color:#059669;
  font-size:14px;
}
.queue-badge {
  position: absolute;
  top: -11px;
  right: -10px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  background: #2563eb;
  box-shadow: 0 8px 16px rgba(37,99,235,.24);
}
.pile-status { margin-top: 60px; font-size: 13px; color: #667085; }
.pile-status::before {
  content:"";
  display:inline-block;
  width:8px;
  height:8px;
  border-radius:50%;
  background:#10b981;
  margin-right:6px;
}
.vehicle {
  position: absolute;
  z-index: 4;
  width: 54px;
  height: 30px;
  border-radius: 10px 14px 8px 8px;
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 14px 24px rgba(5,150,105,.2);
  top: 149px;
  left: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}
.vehicle::before, .vehicle::after {
  content:"";
  position:absolute;
  bottom:-5px;
  width:10px;
  height:10px;
  border-radius:50%;
  background:#0f172a;
}
.vehicle::before { left:9px; }
.vehicle::after { right:9px; }
.vehicle-live { animation: driveMain 7.2s ease-in-out infinite; }
.vehicle-live.active { background: linear-gradient(135deg, #2563eb, #10b981); }
.vehicle-shadow {
  opacity: .44;
  animation: driveMain 7.2s ease-in-out infinite;
  animation-delay: -3.4s;
  transform: scale(.82);
}
.lane-dot {
  position: absolute;
  top: 160px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 8px rgba(16,185,129,.08);
  animation: dotFlow 3.6s linear infinite;
}
.dot-a { left: 26%; }
.dot-b { left: 50%; animation-delay: -1.2s; }
.dot-c { left: 72%; animation-delay: -2.4s; }

@keyframes driveMain {
  0% { left: 62px; transform: translateY(0); opacity: 0; }
  8% { opacity: 1; }
  42% { transform: translateY(0); }
  55% { left: 46%; transform: translateY(-74px); }
  70% { left: 58%; transform: translateY(-74px); }
  84% { transform: translateY(0); opacity: 1; }
  100% { left: calc(100% - 122px); transform: translateY(0); opacity: 0; }
}
@keyframes dotFlow {
  0% { transform: translateX(-18px) scale(.8); opacity: .1; }
  40% { opacity: .8; }
  100% { transform: translateX(48px) scale(1); opacity: 0; }
}
@keyframes halo {
  0% { transform: scale(.5); opacity: .55; }
  100% { transform: scale(2.8); opacity: 0; }
}

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; transition: 0.2s; }
.card:hover { border-color: #d1d5db; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.card-head { padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-tag { font-size: 11px; font-family: "SF Mono", monospace; color: #059669; padding: 3px 8px; border-radius: 6px; background: #ecfdf5; border: 1px solid #d1fae5; }
.card-body { padding: 20px; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; }
.field label { display: block; font-size: 12px; font-weight: 500; color: #6b7280; margin-bottom: 6px; }
.field select, .field input { width: 100%; padding: 10px 12px; background: #f8faf9; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 14px; font-family: inherit; color: #1f2937; outline: none; transition: 0.15s; }
.field select:focus, .field input:focus { border-color: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,0.1); }
.field select:disabled, .field input:disabled { opacity: 0.5; cursor: not-allowed; }

.btn { padding: 10px 20px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.15s; width: 100%; }
.btn-primary { background: #10b981; color: white; }
.btn-primary:hover:not(:disabled) { background: #059669; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.error-box { margin-top: 12px; padding: 12px 14px; border-radius: 8px; background: #fef2f2; border: 1px solid #fecaca; color: #ef4444; font-size: 13px; font-weight: 500; }

.link-task { margin-top: 12px; text-align: center; }
.link-task a { font-size: 13px; color: #059669; font-weight: 600; text-decoration: none; }
.link-task a:hover { text-decoration: underline; }

/* FLOW */
.flow-item { display: flex; gap: 14px; padding: 12px 0; border-bottom: 1px solid #e5e7eb; }
.flow-item:last-child { border-bottom: none; }
.flow-num { width: 24px; height: 24px; border-radius: 50%; background: #ecfdf5; border: 1px solid #d1fae5; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #059669; flex-shrink: 0; margin-top: 2px; }
.flow-text { font-size: 13px; font-weight: 600; color: #111827; }
.flow-sub { font-size: 12px; color: #9ca3af; margin-top: 2px; }

/* PRICE */
.price-grid { display: flex; flex-direction: column; }
.price-row { display: flex; align-items: center; padding: 14px 0; border-bottom: 1px solid #e5e7eb; }
.price-row:last-child { border-bottom: none; }
.price-dot { width: 8px; height: 8px; border-radius: 3px; margin-right: 14px; flex-shrink: 0; }
.price-info { flex: 1; }
.price-name { font-size: 13px; font-weight: 600; color: #1f2937; }
.price-time { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.price-val { font-size: 16px; font-weight: 700; color: #059669; letter-spacing: -0.3px; }

.workspace-page {
  max-width: 1520px;
  padding: 30px 38px 36px;
}

.status-row {
  display: grid;
  grid-template-columns: 1.35fr repeat(5, 1fr);
  align-items: center;
  gap: 0;
  padding: 22px 0 26px;
  border-bottom: 1px solid #e5e7eb;
}

.status-main {
  display: flex;
  align-items: center;
  gap: 18px;
}

.status-bolt {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #34d399, #047857);
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 28px;
  box-shadow: 0 18px 36px rgba(5, 150, 105, .22);
}

.status-title {
  font-size: 15px;
  color: #111827;
}

.status-title strong {
  color: #059669;
  font-size: 20px;
  margin-left: 6px;
}

.status-sub {
  margin-top: 6px;
  color: #667085;
  font-size: 14px;
}

.metric {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-height: 64px;
  border-left: 1px solid #e5e7eb;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #ecfdf5;
  display: grid;
  place-items: center;
  color: #059669;
  font-size: 21px;
}

.metric-label {
  color: #667085;
  font-size: 14px;
}

.metric-val {
  margin-top: 6px;
  font-size: 21px;
  font-weight: 800;
  color: #101828;
}

.metric-val .green {
  color: #059669;
}

.route-pulse {
  position: absolute;
  top: 160px;
  left: 72px;
  height: 10px;
  width: 10px;
  border-radius: 50%;
  background: #059669;
  opacity: .18;
  animation: pulseMove 4s linear infinite;
  z-index: 2;
}

.dispatch-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
  z-index: 5;
}

.car {
  position: absolute;
  width: 56px;
  height: 31px;
  left: 0;
  top: 0;
  transform: translate(-100px, 151px);
  opacity: 0;
  z-index: 8;
  animation: dispatchCar 13s cubic-bezier(.4,0,.2,1) infinite;
  animation-delay: var(--delay);
}

.car-body {
  position: absolute;
  inset: 5px 2px;
  background: linear-gradient(180deg, #ffffff, #dbeafe);
  border: 1px solid #94a3b8;
  border-radius: 16px 16px 10px 10px;
  box-shadow: 0 8px 16px rgba(15,23,42,.16);
}

.car.assigned .car-body {
  border-color: rgba(5,150,105,.72);
  box-shadow: 0 10px 22px rgba(5,150,105,.18);
}

.car-window {
  position: absolute;
  left: 17px;
  top: 2px;
  width: 19px;
  height: 9px;
  background: #bfdbfe;
  border-radius: 6px 6px 3px 3px;
}

.wheel {
  position: absolute;
  bottom: -3px;
  width: 8px;
  height: 8px;
  background: #475467;
  border-radius: 50%;
}

.wheel.left { left: 10px; }
.wheel.right { right: 10px; }

.pile-status::before {
  background: #98a2b3;
}

.pile-status.busy::before {
  background: #059669;
}

.pile-status.queue::before {
  background: #2563eb;
}

.pile-status.mine::before {
  background: #4f46e5;
}

.pile-status.fault::before {
  background: #ef4444;
}

.pile-status.shutdown::before {
  background: #98a2b3;
}

.pile-box.fault {
  border-style: solid;
  border-color: rgba(239,68,68,.42);
  background: rgba(254,242,242,.86);
}

.pile-box.shutdown {
  border-style: dashed;
  border-color: #cbd5e1;
  background: rgba(248,250,252,.78);
}

.main-grid {
  display: grid;
  grid-template-columns: 1.06fr .94fr .92fr;
  gap: 34px;
  padding: 26px 0;
  border-bottom: 1px solid #e5e7eb;
}

.panel {
  border-right: 1px solid #e5e7eb;
  padding-right: 34px;
  min-height: 315px;
}

.panel:last-child {
  border-right: 0;
  padding-right: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  margin-top: 24px;
}

.workspace-page label {
  display: block;
  margin-bottom: 10px;
  color: #344054;
  font-weight: 700;
  font-size: 14px;
}

.workspace-page select,
.workspace-page input {
  width: 100%;
  height: 52px;
  padding: 0 18px;
  border: 1px solid #d0d5dd;
  border-radius: 10px;
  background: #fff;
  font: inherit;
  color: #344054;
  outline: none;
  transition: .18s;
}

.workspace-page select:focus,
.workspace-page input:focus {
  border-color: #059669;
  box-shadow: 0 0 0 4px rgba(16,185,129,.1);
}

.workspace-page select:disabled,
.workspace-page input:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.submit {
  margin-top: 24px;
  height: 58px;
  width: 100%;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #059669, #047857);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 14px 28px rgba(5,150,105,.18);
  transition: transform .18s, opacity .18s;
}

.submit:hover:not(:disabled) {
  transform: translateY(-1px);
}

.submit:disabled {
  opacity: .48;
  cursor: not-allowed;
}

.notice {
  margin-top: 26px;
  padding: 16px 18px;
  border: 1px solid #cfeee0;
  border-radius: 12px;
  background: #f1fbf6;
  color: #344054;
  line-height: 1.8;
  font-size: 14px;
}

.notice strong {
  color: #059669;
}

.empty {
  height: 245px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #667085;
}

.empty-illus {
  font-size: 82px;
  opacity: .25;
  margin-bottom: 12px;
}

.empty strong {
  font-size: 21px;
  color: #111827;
  margin-bottom: 8px;
}

.request-card {
  margin-top: 22px;
  padding: 18px;
  border: 1px solid #d1fae5;
  border-radius: 14px;
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
}

.request-title {
  font-size: 20px;
  font-weight: 800;
  color: #059669;
}

.request-sub {
  margin-top: 8px;
  color: #667085;
  font-size: 13px;
  line-height: 1.7;
}

.request-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 16px;
}

.request-grid div {
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #d1fae5;
}

.request-grid span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.request-grid strong {
  display: block;
  margin-top: 4px;
  color: #101828;
  font-size: 14px;
  overflow-wrap: anywhere;
}

.state-link {
  display: inline-flex;
  margin-top: 16px;
  color: #059669;
  font-weight: 800;
  font-size: 13px;
  text-decoration: none;
}

.flow {
  margin-top: 22px;
  display: grid;
  gap: 13px;
}

.flow-step {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 14px;
  align-items: start;
}

.num {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #ecfdf5;
  border: 1px solid #ccebdd;
  display: grid;
  place-items: center;
  color: #059669;
  font-weight: 800;
  font-size: 13px;
}

.flow-step strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.flow-step p {
  margin: 0;
  color: #667085;
  font-size: 13px;
  line-height: 1.55;
}

.bottom {
  display: grid;
  grid-template-columns: 1.35fr .9fr;
  gap: 48px;
  padding: 26px 0 0;
}

.bottom .section-title span {
  font-size: 14px;
  color: #667085;
  font-weight: 500;
}

.time-axis {
  margin-top: 32px;
}

.axis-legend {
  display:flex;
  gap:24px;
  align-items:center;
  font-size:14px;
  color:#344054;
  margin-bottom:16px;
}

.axis-legend i {
  width:9px;
  height:9px;
  border-radius:3px;
  display:inline-block;
  margin-right:8px;
}

.axis-bar {
  height:58px;
  display:grid;
  grid-template-columns: 7fr 3fr 5fr 3fr 3fr 2fr 1fr;
  border-radius:12px;
  box-shadow: inset 0 0 0 1px #d9e2dd;
  overflow:visible;
  position:relative;
}

.axis-bar::before,
.axis-bar::after {
  content: "";
  position: absolute;
  bottom: -12px;
  width: 1px;
  height: 12px;
  background: #cbd5e1;
  pointer-events: none;
}

.axis-bar::before { left: 0; }
.axis-bar::after { right: 0; }

.seg {
  position: relative;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  border-right:1px solid rgba(255,255,255,.58);
  font-weight:800;
  font-size:14px;
}

.seg small {
  margin-top:4px;
  font-weight:700;
}

.seg:first-of-type {
  border-radius: 12px 0 0 12px;
}

.seg:last-of-type {
  border-right: 0;
  border-radius: 0 12px 12px 0;
}

.seg:not(:last-of-type)::after {
  content: "";
  position: absolute;
  right: 0;
  bottom: -12px;
  width: 1px;
  height: 12px;
  background: #cbd5e1;
  pointer-events: none;
}

.seg.valley { background:#dbeafe; color:#1d4ed8; }
.seg.normal { background:#fef3c7; color:#d97706; }
.seg.peak { background:#fee2e2; color:#dc2626; }

.time-ticks {
  position: relative;
  height: 38px;
  margin-top: 0;
  color:#667085;
  font-size:12px;
}

.tick {
  position: absolute;
  top: 0;
  white-space: nowrap;
  font-weight: 700;
  transform: translateX(-50%);
}

.tick b {
  display: block;
  margin-top: 10px;
  font: inherit;
}

.tick.start b {
  transform: none;
}

.tick.end {
  transform: translateX(-100%);
}

.tick.near-end {
  transform: translateX(-100%);
}

.tick.start {
  transform: translateX(0);
}

.formula {
  margin-top:16px;
  color:#667085;
  font-size:14px;
  text-align: right;
}

.now-marker {
  position: absolute;
  top: -10px;
  bottom: 0;
  width: 0;
  border-left: 2px dashed #059669;
  z-index: 6;
  transform: translateX(-1px);
  pointer-events: none;
  transition: left 600ms ease;
}

.now-marker::before {
  content: "当前 " attr(data-time);
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  border-radius: 999px;
  background: #059669;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
  box-shadow: 0 8px 18px rgba(5,150,105,.18);
}

.now-marker::after {
  content: "";
  position: absolute;
  bottom: 38px;
  left: -6px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #059669;
  box-shadow: 0 0 0 4px rgba(16,185,129,.12);
}

.fee-list {
  margin-top: 26px;
  display:grid;
  grid-template-columns: repeat(3,1fr);
  gap: 28px;
}

.fee {
  display:grid;
  grid-template-columns: 42px 1fr;
  gap:14px;
  align-items:start;
  border-right:1px solid #e5e7eb;
  padding-right:24px;
}

.fee:last-child {
  border-right:0;
}

.fee-icon {
  font-size:32px;
  color: #f59e0b;
}

.fee:nth-child(3) .fee-icon {
  color: #059669;
}

.fee strong {
  display:block;
  margin-bottom:8px;
}

.fee p {
  margin:0;
  color:#667085;
  font-size:14px;
  line-height:1.7;
}

@keyframes pulseMove {
  0% { transform: translateX(0); opacity: 0; }
  12% { opacity: .22; }
  88% { opacity: .22; }
  100% { transform: translateX(1240px); opacity: 0; }
}

@keyframes dispatchCar {
  0% { transform: translate(-86px, 151px); opacity: 0; }
  5% { transform: translate(66px, 151px); opacity: 1; }
  42% { transform: translate(var(--target-x), 151px); opacity: 1; }
  58% { transform: translate(var(--target-x), 104px); opacity: 1; }
  72% { transform: translate(var(--target-x), 60px); opacity: 1; }
  86% { transform: translate(var(--target-x), 60px); opacity: 1; }
  100% { transform: translate(var(--target-x), 60px); opacity: 0; }
}

@media (max-width: 980px) {
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .grid-2 { grid-template-columns: 1fr; }
  .queue-head { align-items: flex-start; flex-direction: column; }
  .dispatch-stage { height: 360px; }
  .pile-row { left: 28px; right: 28px; grid-template-columns: repeat(2, 1fr); }
  .main-lane, .entry-label, .exit-label, .vehicle, .lane-dot, .pulse-halo, .route-pulse, .car { display: none; }
  .status-row, .main-grid, .bottom { grid-template-columns: 1fr; }
  .metric { border-left: 0; border-top: 1px solid #e5e7eb; justify-content: flex-start; padding-top: 14px; }
  .panel { border-right: 0; border-bottom: 1px solid #e5e7eb; padding-right: 0; padding-bottom: 24px; }
  .fee-list { grid-template-columns: 1fr; }
  .fee { border-right: 0; border-bottom: 1px solid #e5e7eb; padding-bottom: 18px; }
}

@media (max-width: 640px) {
  .page { padding: 20px 16px; }
  .stats { grid-template-columns: 1fr; gap: 10px; }
  .stat { padding: 14px 16px; }
  .stat-val { font-size: 22px; }
  .status-strip { align-items: stretch; flex-direction: column; }
  .strip-action { text-align: center; }
  .form-grid { grid-template-columns: 1fr; }
  .price-row { align-items: flex-start; gap: 8px; }
  .price-val { white-space: nowrap; }
}
</style>
