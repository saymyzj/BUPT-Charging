<template>
  <div class="admin-overview">
    <header class="overview-top">
      <div class="top-title">
        <h1>管理总览</h1>
        <p>实时监控充电站运行状态</p>
      </div>
      <div class="top-actions">
        <span class="refresh-state">自动刷新：开启</span>
        <span class="time-badge">{{ currentTimeText }}</span>
        <span class="date-badge">{{ currentDateText }} {{ currentWeekdayText }}</span>
        <button class="refresh-btn" :disabled="loading" @click="loadStations">
          {{ loading ? '刷新中' : '刷新状态' }}
        </button>
      </div>
    </header>

    <section class="kpi-row">
      <article v-for="item in kpis" :key="item.label" class="kpi">
        <div class="kpi-icon" :class="item.tone">{{ item.icon }}</div>
        <div class="kpi-body">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }} <small>{{ item.unit }}</small></strong>
          <em>{{ item.sub }}</em>
          <div class="bar" :class="item.tone"><i :style="{ width: item.percent + '%' }"></i></div>
        </div>
      </article>
    </section>

    <section class="section queue-section">
      <div class="section-head">
        <div>
          <h2>充电桩队列总览</h2>
          <p>按当前实际桩位展示队列，首位充电车辆与等待车辆分层显示</p>
        </div>
        <div class="legend">
          <span><i class="green"></i>运行中</span>
          <span><i class="blue"></i>充电中</span>
          <span><i class="gray"></i>等待中</span>
        </div>
      </div>

      <div v-if="loading && !stations.length" class="loading-text">加载中...</div>
      <div v-else class="queue-overview">
        <div class="lane-wrap">
          <div class="entry">入口<small>&gt;</small></div>
          <div class="exit">出口<small>&gt;</small></div>
          <div class="main-road"></div>
          <div class="moving-car"><div class="car-body"></div></div>
          <div class="moving-car delay1"><div class="car-body"></div></div>
          <div class="moving-car delay2"><div class="car-body"></div></div>

          <div class="pile-grid">
          <article v-for="station in visibleStations" :key="station.station_code" class="pile-top" :class="stationTone(station)">
            <div class="pile-head">
              <div class="pile-name">{{ station.station_code }}</div>
              <span class="run-pill" :class="stationTone(station)">{{ statusText(station.station_status) }}</span>
            </div>
            <div class="pile-meta">
              <span>当前服务：<b>{{ currentServiceText(station) }}</b></span>
              <span>队列长度：<b>{{ station.queue_length ?? stationQueueRows(station.station_code).length }}</b></span>
            </div>
            <div class="charger" :class="stationTone(station)"></div>
            <i class="branch-line"></i>
          </article>
          </div>
        </div>
        <div class="queue-columns">
          <article
            v-for="station in visibleStations"
            :key="station.station_code"
            class="queue-col"
            :class="{ fault: station.station_status === 'FAULT' }"
          >
            <div class="queue-title">
              <span>{{ station.station_code }} 队列</span>
              <em>{{ stationQueueRows(station.station_code).length }} 辆</em>
            </div>
            <div v-if="stationQueueRows(station.station_code).length" class="queue-lines">
              <template v-for="(row, index) in stationQueueRows(station.station_code)" :key="row.request_id || row.queue_number || index">
                <div
                  class="queue-line"
                  :class="{ active: isQueueRowExpanded(station.station_code, row, index) }"
                  @click="toggleQueueRow(station.station_code, row, index)"
                >
                  <span class="queue-no">{{ index + 1 }}</span>
                  <span class="chip" :class="{ active: isChargingRow(station, row, index) }">
                    {{ userShort(row) }}
                  </span>
                  <span class="q-status" :class="{ active: isChargingRow(station, row, index) }">
                    {{ isChargingRow(station, row, index) ? '充电中' : '等待中' }}
                  </span>
                  <i class="material-icons queue-toggle-icon">
                    {{ isQueueRowExpanded(station.station_code, row, index) ? 'expand_less' : 'expand_more' }}
                  </i>
                </div>
                <div
                  v-if="isQueueRowExpanded(station.station_code, row, index)"
                  class="queue-detail-row"
                  :class="{ active: isChargingRow(station, row, index) }"
                >
                  <strong>{{ userShort(row) }}</strong>
                  <span>ID {{ row.user_id || '--' }}</span>
                  <span>{{ Number(row.request_energy || 0).toFixed(2) }} kWh</span>
                  <em>{{ queueInlineText(station, row, index) }}</em>
                </div>
              </template>
            </div>
            <div v-else class="queue-empty">队列为空</div>
          </article>
        </div>
      </div>
    </section>

    <section class="overview-split">
      <div class="split-main">
        <section class="wait-area">
          <div class="wait-head">
            <div>
              <h2>等候区实时状态 <span class="live-dot">实时更新</span></h2>
            </div>
            <div class="wait-legend">
              <span><i class="blue"></i>快充等待</span>
              <span><i class="orange"></i>慢充等待</span>
              <span><i class="gray"></i>空闲车位</span>
              <b>容量：{{ waitingCapacity }} 个车位</b>
            </div>
          </div>
          <div class="wait-parking">
            <div class="wait-lane"></div>
            <div class="wait-entry-car"></div>
            <div class="parking-grid" :style="{ '--slot-count': parkingSlots.length }">
              <div
                v-for="slot in parkingSlots"
                :key="slot.index"
                class="slot"
                :class="[slot.row ? modeClass(slot.row.charge_mode) : 'empty']"
              >
                <div
                  v-if="slot.row"
                  class="slot-car"
                  :style="{ '--pulse-delay': (slot.index % 5) * 0.18 + 's' }"
                ></div>
                <span class="slot-no">{{ String(slot.index).padStart(2, '0') }}</span>
                <small v-if="slot.row">{{ queueNumberText(slot.row) }}</small>
              </div>
            </div>
            <div class="wait-exit">出口<small>&gt;</small></div>
          </div>
          <div class="wait-footnote">
            <span>说明：等候区只展示普通等待车辆，故障队列不占用等候区容量。</span>
            <span>快充等待 {{ waitingSummary.fast_queue_count || 0 }} 辆</span>
            <span>慢充等待 {{ waitingSummary.slow_queue_count || 0 }} 辆</span>
            <span>空闲车位 {{ freeWaitingSlots }} 个</span>
          </div>
        </section>

        <section class="fault-area" :class="{ empty: !faultQueueRows.length }">
          <div class="fault-area-head">
            <div>
              <h2><span class="fault-dot"></span>故障队列 <span class="fault-count-badge" v-if="faultQueueRows.length">{{ faultQueueRows.length }}</span></h2>
              <p>故障桩中断后的车辆按优先级在此等待重新调度，不占用等候区容量</p>
            </div>
            <div class="fault-legend">
              <span><i class="red"></i>故障车辆 {{ faultQueueRows.length }}</span>
              <span><i class="blue"></i>快充 {{ faultQueueRows.filter(r => r.charge_mode === 'FAST').length }}</span>
              <span><i class="orange"></i>慢充 {{ faultQueueRows.filter(r => r.charge_mode === 'SLOW').length }}</span>
              <span><i class="purple"></i>续充 {{ faultQueueRows.filter(r => r.is_fault_followup).length }}</span>
            </div>
          </div>
          <div class="fault-area-body">
            <div class="fault-lane"></div>
            <div class="fault-grid" v-if="faultQueueRows.length">
              <div
                v-for="row in faultQueueRows"
                :key="row.request_id"
                class="fault-slot"
                :class="modeClass(row.charge_mode)"
              >
                <div class="fault-slot-rank">{{ row.user_id || row.vehicle_code || '--' }}</div>
                <div class="fault-slot-info">
                  <strong>{{ row.username || row.request_id }}</strong>
                  <small>{{ queueNumberText(row) }} · {{ Number(row.request_energy || 0).toFixed(1) }} kWh · {{ row.is_fault_followup ? '续充' : '等待' }}</small>
                </div>
                <span class="fault-slot-mode" :class="modeClass(row.charge_mode)">{{ modeText(row.charge_mode) }}</span>
              </div>
            </div>
            <div v-else class="fault-area-empty">
              <span class="material-icons">verified</span>
              <strong>当前无故障车辆</strong>
              <span>若充电桩发生故障，受影响的车辆将在此处集中展示</span>
            </div>
          </div>
          <div class="fault-footnote">
            <span>故障队列独立于等候区，优先级高于普通排队车辆</span>
          </div>
        </section>

      </div>

      <aside class="side-status">
        <div class="side-card fault-queue-card">
          <div class="side-icon red">障</div>
          <strong>故障队列</strong>
          <span>{{ faultQueueRows.length }} 辆等待优先重调度</span>
        </div>
        <div class="side-card">
          <div class="side-icon pulse">调</div>
          <strong>实时调度</strong>
          <span>队列与车位每 5 秒同步</span>
        </div>
        <div class="side-card">
          <div class="side-icon blue">队</div>
          <strong>当前队列</strong>
          <span>{{ stationQueueTotal }} 个桩内请求</span>
        </div>
        <div class="side-card">
          <div class="side-icon orange">候</div>
          <strong>等候区</strong>
          <span>{{ waitingTotal }} / {{ waitingCapacity }} 个车位</span>
        </div>
      </aside>
    </section>

    <section class="table-section">
      <div class="table-title">充电桩运行状态</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>桩位号</th>
              <th>类型</th>
              <th>状态</th>
              <th>当前服务</th>
              <th>队列长度</th>
              <th>等待人数</th>
              <th>累计电量</th>
              <th>累计服务</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="station in stations" :key="station.station_code" :class="{ 'row-fault': station.station_status === 'FAULT' }">
              <td><strong>{{ station.station_code }}</strong></td>
              <td><span class="mode-pill" :class="modeClass(station.charge_mode)">{{ modeText(station.charge_mode) }}</span></td>
              <td>
                <span class="status-cell" :class="stationTone(station)">
                  <i v-if="station.station_status === 'RUNNING'"></i>
                  {{ statusText(station.station_status) }}
                </span>
              </td>
              <td>{{ currentServiceText(station) }}</td>
              <td>{{ station.queue_length ?? stationQueueRows(station.station_code).length }}</td>
              <td>{{ waitingCount(station) }}</td>
              <td>{{ fmtEnergy(station.total_charge_energy) }}</td>
              <td>{{ station.total_charge_count ?? 0 }} 次</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="charts">
      <article class="chart-box">
        <h3>桩状态分布</h3>
        <div class="chart-content">
          <div class="donut" :style="stationDonutStyle">
            <div><strong>总计</strong><span>{{ stations.length }}</span></div>
          </div>
          <div class="chart-legend">
            <p><i class="green"></i>运行中 <strong>{{ statusCounts.running }}</strong></p>
            <p><i class="red"></i>故障 <strong>{{ statusCounts.fault }}</strong></p>
            <p><i class="gray"></i>关闭 <strong>{{ statusCounts.shutdown }}</strong></p>
          </div>
        </div>
      </article>
      <article class="chart-box">
        <h3>队列构成</h3>
        <div class="chart-content">
          <div class="donut" :style="queueDonutStyle">
            <div><strong>总计</strong><span>{{ totalQueued }}</span></div>
          </div>
          <div class="chart-legend">
            <p><i class="blue"></i>快充等待 <strong>{{ waitingSummary.fast_queue_count || 0 }}</strong></p>
            <p><i class="orange"></i>慢充等待 <strong>{{ waitingSummary.slow_queue_count || 0 }}</strong></p>
            <p><i class="gray"></i>桩内队列 <strong>{{ stationQueueTotal }}</strong></p>
          </div>
        </div>
      </article>
      <article class="chart-box">
        <h3>等候区组成</h3>
        <div class="chart-content">
          <div class="donut" :style="waitingDonutStyle">
            <div><strong>总计</strong><span>{{ waitingCapacity }}</span></div>
          </div>
          <div class="chart-legend">
            <p><i class="blue"></i>快充等待 <strong>{{ waitingSummary.fast_queue_count || 0 }}</strong></p>
            <p><i class="orange"></i>慢充等待 <strong>{{ waitingSummary.slow_queue_count || 0 }}</strong></p>
            <p><i class="gray"></i>空闲车位 <strong>{{ freeWaitingSlots }}</strong></p>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getAcceptanceState, getRequestStatus, getStations, getStationsOverview, getStationQueue, getWaitingArea } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { CHARGE_MODE_TEXT, STATION_STATUS_TEXT } from '@/constants/enums'

const stations = ref([])
const loading = ref(false)
const currentStation = ref(null)
const currentFinishTime = ref(null)
const stationQueues = ref({})
const expandedQueueRows = ref({})
const waitingSummary = ref({ fast_queue_count: 0, slow_queue_count: 0, total_waiting: 0, capacity: 0 })
const waitingAreaRows = ref([])
const faultQueueRows = ref([])
const now = ref(new Date())
let timer = null

const currentTimeText = computed(() => now.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
const currentDateText = computed(() => now.value.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }))
const currentWeekdayText = computed(() => ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][now.value.getDay()] || '')
const waitingCapacity = computed(() => Number(waitingSummary.value.capacity || waitingAreaRows.value.length || 0))
const waitingTotal = computed(() => Number(waitingSummary.value.total_waiting ?? waitingAreaRows.value.length))
const waitingRate = computed(() => percent(waitingTotal.value, waitingCapacity.value))
const runningStations = computed(() => stations.value.filter((s) => s.station_status === 'RUNNING').length)
const visibleStations = computed(() => stations.value.slice(0, 5))
const totalEnergy = computed(() => stations.value.reduce((sum, s) => sum + Number(s.total_charge_energy || 0), 0))
const totalChargeCount = computed(() => stations.value.reduce((sum, s) => sum + Number(s.total_charge_count || 0), 0))
const stationQueueTotal = computed(() => Object.values(stationQueues.value).reduce((sum, rows) => sum + rows.length, 0))
const totalQueued = computed(() => waitingTotal.value + stationQueueTotal.value)
const freeWaitingSlots = computed(() => Math.max(0, waitingCapacity.value - waitingTotal.value))

const statusCounts = computed(() => ({
  running: stations.value.filter((s) => s.station_status === 'RUNNING').length,
  fault: stations.value.filter((s) => s.station_status === 'FAULT').length,
  shutdown: stations.value.filter((s) => s.station_status === 'SHUTDOWN').length,
}))

const kpis = computed(() => [
  {
    label: '等候区占用',
    value: waitingTotal.value,
    unit: `/ ${waitingCapacity.value || 0}`,
    sub: `占用率 ${waitingRate.value}%`,
    percent: waitingRate.value,
    icon: 'P',
    tone: 'green',
  },
  {
    label: '快充等待',
    value: waitingSummary.value.fast_queue_count || 0,
    unit: '辆',
    sub: `占用率 ${percent(waitingSummary.value.fast_queue_count || 0, waitingCapacity.value)}%`,
    percent: percent(waitingSummary.value.fast_queue_count || 0, waitingCapacity.value),
    icon: 'F',
    tone: 'blue',
  },
  {
    label: '慢充等待',
    value: waitingSummary.value.slow_queue_count || 0,
    unit: '辆',
    sub: `占用率 ${percent(waitingSummary.value.slow_queue_count || 0, waitingCapacity.value)}%`,
    percent: percent(waitingSummary.value.slow_queue_count || 0, waitingCapacity.value),
    icon: 'S',
    tone: 'orange',
  },
  {
    label: '故障队列',
    value: faultQueueRows.value.length,
    unit: '条',
    sub: '不占用等候区容量',
    percent: percent(faultQueueRows.value.length, Math.max(waitingCapacity.value, 1)),
    icon: 'R',
    tone: 'purple',
  },
  {
    label: '正常桩',
    value: runningStations.value,
    unit: `/ ${stations.value.length}`,
    sub: `正常率 ${percent(runningStations.value, stations.value.length)}%`,
    percent: percent(runningStations.value, stations.value.length),
    icon: 'N',
    tone: 'green',
  },
  {
    label: '累计充电量',
    value: totalEnergy.value.toFixed(1),
    unit: 'kWh',
    sub: '来自充电桩统计',
    percent: 100,
    icon: 'E',
    tone: 'blue',
  },
  {
    label: '累计服务车辆',
    value: totalChargeCount.value,
    unit: '辆',
    sub: '来自充电桩统计',
    percent: 100,
    icon: 'C',
    tone: 'green',
  },
])

const parkingSlots = computed(() => {
  const count = Math.max(waitingCapacity.value, waitingAreaRows.value.length, 1)
  return Array.from({ length: count }, (_, index) => ({
    index: index + 1,
    row: waitingAreaRows.value[index] || null,
  }))
})

const stationDonutStyle = computed(() => {
  const total = Math.max(stations.value.length, 1)
  const running = statusCounts.value.running / total * 100
  const fault = running + statusCounts.value.fault / total * 100
  return { background: `conic-gradient(#10b981 0 ${running}%, #ef4444 ${running}% ${fault}%, #98a2b3 ${fault}% 100%)` }
})

const queueDonutStyle = computed(() => {
  const total = Math.max(totalQueued.value, 1)
  const fast = Number(waitingSummary.value.fast_queue_count || 0) / total * 100
  const slow = fast + Number(waitingSummary.value.slow_queue_count || 0) / total * 100
  return { background: `conic-gradient(#2563eb 0 ${fast}%, #f97316 ${fast}% ${slow}%, #98a2b3 ${slow}% 100%)` }
})

const waitingDonutStyle = computed(() => {
  const total = Math.max(waitingCapacity.value, 1)
  const fast = Number(waitingSummary.value.fast_queue_count || 0) / total * 100
  const slow = fast + Number(waitingSummary.value.slow_queue_count || 0) / total * 100
  return { background: `conic-gradient(#2563eb 0 ${fast}%, #f97316 ${fast}% ${slow}%, #98a2b3 ${slow}% 100%)` }
})

async function loadStations() {
  loading.value = true
  try {
    const res = await getStations()
    const data = unwrapResponseData(res)
    stations.value = Array.isArray(data) ? data : (data.stations || [])
    stationQueues.value = await loadAllStationQueues()
    await loadWaitingArea()
  } catch (_) {
    /* keep last visible data */
  } finally {
    loading.value = false
  }
}

async function loadAcceptanceClock() {
  try {
    const data = unwrapResponseData(await getAcceptanceState())
    if (data.enabled && data.simulation_time) {
      now.value = new Date(data.simulation_time)
    } else {
      now.value = new Date()
    }
  } catch (_) {
    now.value = new Date()
  }
}

async function loadWaitingArea() {
  const [overviewRes, waitingRes] = await Promise.all([
    getStationsOverview().catch(() => null),
    getWaitingArea().catch(() => null),
  ])
  const overview = overviewRes ? unwrapResponseData(overviewRes) : {}
  const waitingPayload = waitingRes ? unwrapResponseData(waitingRes) : {}
  waitingSummary.value = {
    ...(overview.waiting_queue || {}),
    ...pickWaitingSummary(waitingPayload),
  }
  waitingAreaRows.value = Array.isArray(waitingPayload.rows) ? waitingPayload.rows : []
  faultQueueRows.value = Array.isArray(waitingPayload.fault_queue) ? waitingPayload.fault_queue : []
}

async function loadAllStationQueues() {
  const entries = await Promise.all(
    stations.value.map((station) =>
      getStationQueue(station.station_code)
        .then((res) => {
          const data = unwrapResponseData(res)
          return [station.station_code, Array.isArray(data) ? data : (data.queue || [])]
        })
        .catch(() => [station.station_code, []]),
    ),
  )
  return Object.fromEntries(entries)
}

function pickWaitingSummary(payload) {
  if (!payload || !Array.isArray(payload.rows)) return {}
  return {
    fast_queue_count: payload.fast_queue_count ?? 0,
    slow_queue_count: payload.slow_queue_count ?? 0,
    total_waiting: payload.total_waiting ?? payload.rows.length,
    fault_queue_count: payload.fault_queue_count ?? 0,
    capacity: payload.capacity ?? 0,
  }
}

function stationQueueRows(code) {
  return stationQueues.value[code] || []
}

function queueRowKey(code, row, index) {
  return row?.request_id || row?.queue_number || `${code}-${index}`
}

function isQueueRowExpanded(code, row, index) {
  return expandedQueueRows.value[queueRowKey(code, row, index)] === true
}

function toggleQueueRow(code, row, index) {
  const key = queueRowKey(code, row, index)
  expandedQueueRows.value = { ...expandedQueueRows.value, [key]: !isQueueRowExpanded(code, row, index) }
}

function isChargingRow(station, row, index) {
  return row?.request_status === 'CHARGING' || (index === 0 && Boolean(station?.current_request_id))
}

function modeText(mode) {
  return CHARGE_MODE_TEXT[mode] || (mode === 'FAST' ? '快充' : mode === 'SLOW' ? '慢充' : '--')
}

function modeClass(mode) {
  return mode === 'FAST' ? 'fast' : mode === 'SLOW' ? 'slow' : 'pending'
}

function statusText(status) {
  return STATION_STATUS_TEXT[status] || status || '--'
}

function stationTone(station) {
  const status = station?.station_status
  if (status === 'FAULT') return 'red'
  if (status === 'SHUTDOWN') return 'gray'
  return 'green'
}

function currentServiceText(station) {
  if (!station?.current_request_id) return '空闲'
  if (station.current_user?.username) return station.current_user.username
  if (station.current_user?.user_id) return station.current_user.user_id
  return station.current_request_id
}

function waitingCount(station) {
  const rows = stationQueueRows(station.station_code)
  if (!rows.length) return 0
  return rows.filter((row, index) => !isChargingRow(station, row, index)).length
}

function userShort(row) {
  return row?.username || row?.user_id || row?.request_id || '--'
}

function queueNumberText(row) {
  if (!row) return '--'
  if (row.is_fault_followup && row.source_queue_number && row.source_queue_number !== row.queue_number) {
    return `${row.queue_number}（源${row.source_queue_number}）`
  }
  return row.queue_number || '--'
}

function queueInlineText(station, row, index) {
  if (isChargingRow(station, row, index)) return '正在服务'
  const frontCount = Math.max(0, index)
  const mode = modeText(row?.charge_mode || station?.charge_mode)
  return `前方 ${frontCount} 辆 · ${mode}`
}

async function viewQueue(code) {
  modalCode.value = code
  currentStation.value = stations.value.find((station) => station.station_code === code) || null
  currentFinishTime.value = null
  showModal.value = true
  queueLoading.value = true
  queueData.value = []
  try {
    const res = await getStationQueue(code)
    const data = unwrapResponseData(res)
    queueData.value = Array.isArray(data) ? data : (data.queue || [])
    stationQueues.value = { ...stationQueues.value, [code]: queueData.value }
    if (currentStation.value?.current_request_id) {
      const statusRes = await getRequestStatus(currentStation.value.current_request_id)
      const status = unwrapResponseData(statusRes)
      currentFinishTime.value = status.estimated_finish_time || null
    }
  } catch (_) {
    /* keep modal open */
  } finally {
    queueLoading.value = false
  }
}

function queueTimeText(row, index) {
  const hasChargingHead = Boolean(currentStation.value?.current_request_id)
  if (hasChargingHead && index === 0) {
    const remain = remainingMinutes(currentFinishTime.value)
    return remain === null ? '正在服务' : `正在服务，还需 ${remain} min`
  }
  const frontCount = hasChargingHead ? index : Math.max(0, index)
  const finish = estimateFinishTime(index)
  return `前方 ${frontCount} 人，预计 ${finish ? fmtTime(finish) : '--'} 充完`
}

function estimateFinishTime(index) {
  const station = currentStation.value
  if (!station) return null
  const power = station.charge_mode === 'FAST' ? 30 : 10
  const start = currentFinishTime.value ? new Date(currentFinishTime.value) : now.value
  if (Number.isNaN(start.getTime())) return null
  const startIndex = station.current_request_id ? 1 : 0
  let cursor = new Date(start)
  for (let i = startIndex; i <= index; i += 1) {
    const item = queueData.value[i]
    if (!item) break
    cursor = new Date(cursor.getTime() + Number(item.request_energy || 0) / power * 3600000)
  }
  return cursor
}

function remainingMinutes(time) {
  if (!time) return null
  const finish = new Date(time)
  if (Number.isNaN(finish.getTime())) return null
  return Math.max(0, Math.ceil((finish.getTime() - now.value.getTime()) / 60000))
}

function fmtTime(time) {
  try {
    return new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return '--'
  }
}

function fmtEnergy(value) {
  return `${Number(value || 0).toFixed(2)} kWh`
}

function percent(value, total) {
  const denominator = Number(total || 0)
  if (!denominator) return 0
  return Math.min(100, Math.round(Number(value || 0) / denominator * 100))
}

onMounted(() => {
  loadAcceptanceClock()
  loadStations()
  timer = window.setInterval(() => {
    loadAcceptanceClock()
    loadStations()
  }, 5000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.admin-overview {
  max-width: 1680px;
  margin: 0;
  padding: 22px 28px 30px;
  color: #101828;
  background: #eef2f0;
  display: flex;
  flex-direction: column;
}

.overview-top {
  position: sticky;
  top: 0;
  z-index: 30;
  min-height: 66px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin: -22px -28px 18px;
  padding: 0 28px;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid #edf0ee;
}

.top-title {
  min-width: 0;
}

.overview-top h1 {
  margin: 0;
  font-size: 21px;
  font-weight: 900;
  letter-spacing: .2px;
}

.section-head h2,
.wait-head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: .1px;
}

.overview-top p,
.section-head p,
.wait-head p {
  margin: 5px 0 0;
  color: #667085;
  font-size: 13px;
  line-height: 1.55;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #475467;
  font-size: 13px;
}

.refresh-state,
.time-badge,
.date-badge {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #344054;
  font-size: 13px;
  font-weight: 700;
}

.refresh-state {
  color: #059669;
  border-color: #d1fae5;
  background: #ecfdf5;
}

.time-badge {
  font-size: 20px;
  font-weight: 900;
  letter-spacing: .2px;
}

.date-badge {
  color: #667085;
}

.refresh-btn,
.queue-title button {
  border: 1px solid #cceedd;
  background: #ecfdf5;
  color: #059669;
  border-radius: 10px;
  font-weight: 800;
  cursor: pointer;
  transition: background .15s, border-color .15s;
}
.queue-title button:hover {
  background: #d1fae5;
  border-color: #6ee7b7;
}

.refresh-btn {
  height: 38px;
  padding: 0 16px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.kpi {
  min-height: 96px;
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
  align-items: center;
  padding: 14px;
  border: 1px solid #edf0ee;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 14px 38px rgba(16, 24, 40, .055);
  transition: border-color .2s, box-shadow .2s, transform .2s;
  animation: kpiEnter .5s ease both;
}
.kpi:hover {
  border-color: #a7f3d0;
  box-shadow: 0 20px 48px rgba(16, 24, 40, .09), 0 0 0 3px rgba(16,185,129,.06);
  transform: translateY(-2px);
}
.kpi:nth-child(1) { animation-delay: 0s; }
.kpi:nth-child(2) { animation-delay: .07s; }
.kpi:nth-child(3) { animation-delay: .14s; }
.kpi:nth-child(4) { animation-delay: .21s; }
.kpi:nth-child(5) { animation-delay: .28s; }
.kpi:nth-child(6) { animation-delay: .35s; }
.kpi:nth-child(7) { animation-delay: .42s; }

.kpi:nth-child(1),
.kpi:nth-child(5) {
  min-height: 116px;
}
.kpi:nth-child(1) .kpi-body strong,
.kpi:nth-child(5) .kpi-body strong {
  font-size: 22px;
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 15px;
  display: grid;
  place-items: center;
  font-weight: 900;
}

.kpi-icon.green { background: #ecfdf5; color: #059669; }
.kpi-icon.blue { background: #eff6ff; color: #2563eb; }
.kpi-icon.orange { background: #fff7ed; color: #f97316; }
.kpi-icon.purple { background: #f5f3ff; color: #8b5cf6; }

.kpi-body span {
  color: #475467;
  font-size: 13px;
}

.kpi-body strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
  line-height: 1;
  font-weight: 850;
}

.kpi-body small {
  font-size: 14px;
  color: #344054;
}

.kpi-body em {
  display: block;
  margin-top: 6px;
  color: #667085;
  font-size: 12px;
  font-style: normal;
}

.bar {
  height: 5px;
  margin-top: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf0ee;
}

.bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #10b981;
  transition: width 1s cubic-bezier(.4,0,.2,1);
}

.bar.blue i { background: #2563eb; }
.bar.orange i { background: #f97316; }
.bar.purple i { background: #8b5cf6; }

.section,
.wait-area,
.table-section,
.chart-box {
  border: 1px solid #edf0ee;
  border-radius: 16px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 14px 38px rgba(16, 24, 40, .055);
  transition: border-color .2s, box-shadow .2s, transform .2s;
  animation: sectionEnter .55s ease both;
}
.section:hover,
.chart-box:hover {
  border-color: #d1fae5;
  box-shadow: 0 22px 52px rgba(16, 24, 40, .08);
}

.section,
.wait-area,
.table-section {
  order: 5;
}

.charts {
  order: 6;
}

.table-section {
  margin-bottom: 16px;
}

.section-head,
.wait-head,
.table-title {
  min-height: 54px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 18px;
  border-bottom: 1px solid #edf0ee;
}

.legend {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #667085;
  font-size: 12px;
}

.legend i,
.chart-legend i {
  width: 8px;
  height: 8px;
  display: inline-block;
  border-radius: 3px;
}

i.green { background: #10b981; }
i.blue { background: #2563eb; }
i.orange { background: #f97316; }
i.purple { background: #8b5cf6; }
i.red { background: #ef4444; }
i.gray { background: #98a2b3; }

.queue-section {
  order: 2;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.queue-overview {
  position: relative;
  min-height: 300px;
  min-width: 1200px;
  padding: 12px 20px 14px;
  background:
    radial-gradient(circle at 6% 35%, rgba(16,185,129,.08), transparent 24%),
    radial-gradient(circle at 75% 20%, rgba(37,99,235,.05), transparent 20%),
    linear-gradient(180deg, #fff, #fcfefd);
  overflow: visible;
}

.lane-wrap {
  position: relative;
  height: 132px;
  margin: 0 2px 6px;
  overflow: hidden;
}

.main-road {
  position: absolute;
  left: 64px;
  right: 64px;
  top: 88px;
  height: 8px;
  border-radius: 999px;
  background:
    repeating-linear-gradient(90deg, #d4dbe4 0 18px, transparent 18px 32px),
    linear-gradient(90deg, transparent, #eef2f6 12%, #eef2f6 88%, transparent);
}

.entry,
.exit {
  position: absolute;
  top: 62px;
  width: 50px;
  height: 42px;
  border-radius: 8px;
  border: 1px solid #d0d5dd;
  background: #fff;
  display: grid;
  place-items: center;
  color: #344054;
  font-weight: 750;
  z-index: 4;
}

.entry { left: 0; }
.exit { right: 0; }

.entry small,
.exit small {
  display: block;
  color: #059669;
  font-size: 18px;
  line-height: 10px;
}

.moving-car {
  position: absolute;
  top: 68px;
  left: 32px;
  width: 56px;
  height: 30px;
  animation: overviewDrive 8s linear infinite;
  opacity: .9;
  z-index: 5;
}

.moving-car.delay1 {
  animation-delay: -2.2s;
}

.moving-car.delay2 {
  animation-delay: -4.6s;
}

.car-body {
  position: absolute;
  inset: 7px 3px 5px;
  width: auto;
  height: auto;
  border-radius: 18px 18px 10px 10px;
  background: linear-gradient(180deg, #fff, #dbeafe);
  border: 1px solid #aab4c0;
  box-shadow: 0 9px 18px rgba(15,23,42,.14);
}

.car-body::before {
  content: "";
  position: absolute;
  left: 19px;
  top: 2px;
  width: 22px;
  height: 9px;
  border-radius: 8px 8px 3px 3px;
  background: #bfdbfe;
}

.car-body::after {
  content: "";
  position: absolute;
  left: 11px;
  bottom: -4px;
  width: 40px;
  height: 8px;
  background:
    radial-gradient(circle at 7px 4px, #475467 0 4px, transparent 4px),
    radial-gradient(circle at 33px 4px, #475467 0 4px, transparent 4px);
}

@keyframes overviewDrive {
  0% { transform: translateX(-110px); opacity: 0; }
  6% { opacity: .5; }
  15% { opacity: .95; }
  92% { opacity: .9; }
  100% { transform: translateX(1310px); opacity: 0; }
}

.pile-grid,
.queue-columns {
  display: grid;
  grid-template-columns: repeat(5, minmax(190px, 1fr));
  gap: 14px;
}

.pile-grid {
  position: absolute;
  left: 84px;
  right: 84px;
  top: 0;
  z-index: 6;
}

.pile-top {
  position: relative;
  height: 132px;
}

.pile-top.gray {
  opacity: .55;
  filter: grayscale(.45);
}

.pile-head {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 4px;
}

.pile-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 17px;
  font-weight: 900;
  letter-spacing: -.3px;
  color: #101828;
}

.table-title em {
  font-style: normal;
  color: #047857;
  background: #ecfdf3;
  border: 1px solid #cdeee0;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 850;
}

.run-pill {
  height: 20px;
  flex-shrink: 0;
  padding: 0 9px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #10b981;
  color: #fff;
  font-weight: 700;
  font-size: 11px;
  max-width: 80px;
  overflow: hidden;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(16,185,129,.35);
}

.run-pill.red {
  background: #ef4444;
  color: #fff;
  box-shadow: 0 1px 4px rgba(239,68,68,.35);
  animation: faultBlink 1.5s ease-in-out infinite;
}

@keyframes faultBlink {
  0%, 100% { opacity: 1; box-shadow: 0 1px 6px rgba(239,68,68,.4); }
  50% { opacity: .72; box-shadow: 0 2px 14px rgba(239,68,68,.65); }
}

.run-pill.gray {
  background: #d1d5db;
  color: #6b7280;
  box-shadow: none;
}

.pile-meta {
  display: grid;
  gap: 1px;
  color: #9ca3af;
  font-size: 11px;
  line-height: 1.4;
  padding-right: 4px;
}

.pile-meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pile-meta b {
  color: #6b7280;
  font-weight: 700;
}

.charger {
  position: absolute;
  left: 50%;
  top: 62px;
  transform: translateX(-50%);
  width: 26px;
  height: 46px;
  border-radius: 8px 8px 5px 5px;
  border: 1px solid #cbd5e1;
  background: linear-gradient(180deg, #fff, #e6eaf0);
  box-shadow: 0 10px 19px rgba(15,23,42,.13);
  z-index: 2;
}

.charger::before {
  content: "";
  position: absolute;
  left: 9px;
  top: 8px;
  width: 9px;
  height: 14px;
  border-radius: 3px;
  background: #10b981;
}

.charger.red::before { background: #ef4444; }
.charger.gray::before { background: #98a2b3; }

.charger::after {
  content: "";
  position: absolute;
  left: 8px;
  top: 27px;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: rgba(16,185,129,.2);
}

.branch-line {
  position: absolute;
  left: 50%;
  top: 102px;
  width: 2px;
  height: 28px;
  border-left: 2px dashed #10b981;
  transform: translateX(-50%);
  z-index: 1;
}

.branch-line::after {
  content: "";
  position: absolute;
  left: -5px;
  bottom: -2px;
  width: 10px;
  height: 10px;
  border-right: 2px solid #10b981;
  border-bottom: 2px solid #10b981;
  transform: rotate(45deg);
}

.queue-columns {
  padding: 0 84px;
  margin-top: 0;
  min-width: 1200px;
}

.queue-col {
  padding: 10px;
  border: 1px solid #e5ece8;
  background: #fff;
  border-radius: 12px;
  transition: border-color .18s, box-shadow .18s, transform .18s;
}

.queue-col:hover {
  border-color: #bdebd6;
  box-shadow: 0 8px 18px rgba(16,24,40,.045);
  transform: translateY(-1px);
}

.queue-col.fault {
  border-color: #fecdd3;
  background: #fff7f7;
}

.queue-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 850;
  min-height: 26px;
  gap: 8px;
}

.queue-title span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-title em {
  margin-left: auto;
  font-style: normal;
  color: #047857;
  background: #ecfdf3;
  border: 1px solid #cdeee0;
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 10px;
  white-space: nowrap;
}

.queue-title .material-icons {
  font-size: 17px;
  color: #667085;
}

.queue-lines {
  display: grid;
  gap: 4px;
  max-height: none;
  overflow-y: auto;
  padding-right: 4px;
}

.queue-line {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr) 48px 16px;
  align-items: center;
  gap: 6px;
  min-height: 22px;
  font-size: 11px;
  cursor: pointer;
  padding: 3px 4px;
  border-radius: 8px;
  transition: background .15s, box-shadow .15s;
}

.queue-line:hover,
.queue-line.active {
  background: #f8fafc;
}

.queue-no {
  color: #667085;
  text-align: right;
  font-weight: 800;
}

.chip {
  min-width: 0;
  height: 22px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #f3f4f6;
  color: #9ca3af;
  font-weight: 600;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip.active {
  background: #dbeafe;
  border-color: #93c5fd;
  border-left: 3px solid #1d4ed8;
  color: #1d4ed8;
  font-weight: 700;
}

.q-status {
  color: #d1d5db;
  font-weight: 600;
  font-size: 11px;
}

.q-status.active {
  color: #2563eb;
  font-weight: 800;
}

.queue-toggle-icon {
  color: #98a2b3;
  font-size: 16px;
}

.queue-empty,
.empty-modal,
.loading-text {
  padding: 20px;
  color: #98a2b3;
  text-align: center;
  font-size: 13px;
}

.queue-detail-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 3px;
  padding: 8px;
  border: 1px solid #edf2ef;
  border-radius: 10px;
  background: #fbfefc;
}

.queue-detail-row.active {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.queue-detail-row strong {
  color: #101828;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-detail-row span,
.queue-detail-row em {
  font-size: 11px;
  color: #667085;
  font-style: normal;
}

.queue-detail-row em {
  color: #047857;
  font-weight: 800;
}

.row-fault td {
  background: rgba(254,242,242,.7);
}
.row-fault td:first-child {
  border-left: 3px solid #ef4444;
}

.overview-split {
  order: 3;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 14px;
  align-items: start;
  margin-bottom: 16px;
}
.split-main {
  display: grid;
  gap: 10px;
}

.wait-area {
  order: 1;
}

.wait-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  color: #667085;
  font-size: 12px;
}

.wait-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.wait-legend i {
  width: 8px;
  height: 8px;
  border-radius: 3px;
}

.wait-legend b {
  color: #344054;
}

.wait-parking {
  position: relative;
  min-height: 174px;
  padding: 18px 22px 28px;
  background:
    radial-gradient(circle at 4% 48%, rgba(16,185,129,.09), transparent 22%),
    linear-gradient(180deg, #fff, #fcfefd);
  overflow: hidden;
}

.live-dot {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 12px;
  color: #059669;
  font-size: 12px;
  font-weight: 750;
}
.live-dot::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 0 rgba(16,185,129,.4);
  animation: livePing 1.6s ease-out infinite;
  flex-shrink: 0;
}

.wait-lane {
  position: absolute;
  left: 20px;
  right: 20px;
  top: 72px;
  height: 54px;
  margin: 0;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(226,232,240,.65), rgba(248,250,252,.9));
  overflow: hidden;
}

.wait-lane::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 25px;
  height: 2px;
  background: repeating-linear-gradient(90deg, #cbd5e1 0 18px, transparent 18px 34px);
}

.wait-entry-car {
  position: absolute;
  left: 10px;
  top: 81px;
  width: 78px;
  height: 38px;
  border-radius: 36px 42px 14px 14px;
  background: linear-gradient(180deg, #8da3a2, #4b6470);
  opacity: .55;
  box-shadow: 0 10px 20px rgba(16,185,129,.2);
  animation: waitCar 4.8s ease-in-out infinite;
  z-index: 3;
}

@keyframes waitCar {
  0% { transform: translateX(-94px); opacity: 0; }
  25% { transform: translateX(0); opacity: .55; }
  60% { transform: translateX(42px); opacity: .4; }
  100% { transform: translateX(118px); opacity: 0; }
}

.parking-grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(58px, 1fr));
  gap: 8px;
  margin-left: 92px;
  margin-right: 78px;
  z-index: 4;
}

.slot {
  min-height: 96px;
  position: relative;
  display: grid;
  place-items: center;
  border: 1px dashed #d0d5dd;
  border-radius: 12px;
  background: rgba(255,255,255,.78);
  color: #98a2b3;
  font-weight: 850;
}

.slot.fast {
  border-style: solid;
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #2563eb;
}

.slot.slow {
  border-style: solid;
  border-color: #fed7aa;
  background: #fff7ed;
  color: #f97316;
}

.slot.pending {
  border-color: #ddd6fe;
  background: #f5f3ff;
  color: #8b5cf6;
}

.slot-car {
  width: 34px;
  height: 58px;
  border-radius: 16px 16px 9px 9px;
  background: linear-gradient(180deg, #fff, currentColor);
  border: 1px solid rgba(15, 23, 42, .18);
  opacity: .85;
  position: relative;
  animation: parkedPulse 2.4s ease-in-out infinite;
  animation-delay: var(--pulse-delay, 0s);
  transform-origin: center bottom;
}

.slot-car::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -7px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
  transform: translateX(-50%);
  opacity: .28;
  animation: chargeDot 1.8s ease-in-out infinite;
  animation-delay: var(--pulse-delay, 0s);
}

@keyframes parkedPulse {
  0%, 100% {
    transform: translateY(0) scale(1);
    filter: drop-shadow(0 8px 12px rgba(15,23,42,.12));
  }
  50% {
    transform: translateY(-3px) scale(1.02);
    filter: drop-shadow(0 12px 18px rgba(15,23,42,.18));
  }
}

@keyframes chargeDot {
  0%, 100% {
    box-shadow: 0 0 0 0 currentColor;
    opacity: .2;
  }
  50% {
    box-shadow: 0 0 0 7px transparent;
    opacity: .48;
  }
}

.slot span {
  position: absolute;
  left: 8px;
  top: 7px;
  font-size: 11px;
}

.slot small {
  position: absolute;
  right: 8px;
  bottom: 7px;
  font-size: 11px;
}

.wait-exit {
  position: absolute;
  right: 24px;
  top: 76px;
  width: 58px;
  height: 48px;
  display: grid;
  place-items: center;
  margin-top: 0;
  border: 1px solid #d0d5dd;
  border-radius: 8px;
  background: rgba(255,255,255,.92);
  color: #667085;
  font-size: 12px;
  font-weight: 850;
  text-align: center;
  z-index: 5;
}

.wait-footnote {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  padding: 11px 18px 14px;
  border-top: 1px solid #edf0ee;
  color: #667085;
  font-size: 12px;
}

.fault-area {
  order: 2;
  margin-bottom: 0;
  border: 1px solid #fecdd3;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(16, 24, 40, .045);
  overflow: hidden;
}
.fault-area-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  min-height: 54px;
  padding: 14px 18px;
  border-bottom: 1px solid #fecdd3;
  background: linear-gradient(180deg, #fff 0%, #fffbfb 100%);
}
.fault-area-head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #101828;
  display: flex;
  align-items: center;
  gap: 8px;
}
.fault-area-head p {
  margin: 5px 0 0;
  color: #9f1239;
  font-size: 12px;
  font-weight: 600;
}
.fault-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239,68,68,.2);
  animation: faultPulse 1.6s ease-in-out infinite;
}
@keyframes faultPulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(239,68,68,.2); }
  50% { box-shadow: 0 0 0 7px rgba(239,68,68,.08); }
}
.fault-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 999px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 12px;
  font-weight: 900;
}
.fault-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  color: #667085;
  font-size: 12px;
}
.fault-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.fault-legend i {
  width: 8px;
  height: 8px;
  border-radius: 3px;
}
.fault-area-body {
  position: relative;
  min-height: 80px;
  padding: 18px 22px 20px;
  background:
    radial-gradient(circle at 4% 48%, rgba(239,68,68,.06), transparent 22%),
    linear-gradient(180deg, #fff, #fffcfc);
  overflow: hidden;
}
.fault-lane {
  position: absolute;
  left: 20px;
  right: 20px;
  top: 50%;
  height: 2px;
  border-radius: 1px;
  background: #fecdd3;
  transform: translateY(-50%);
  z-index: 0;
  overflow: hidden;
}
.fault-lane::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(90deg, #fecdd3 0 18px, transparent 18px 34px);
}
.fault-grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  z-index: 4;
}
.fault-slot {
  display: grid;
  grid-template-columns: 64px 1fr auto;
  gap: 0 12px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid #fecdd3;
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, #fff8f8 100%);
  box-shadow: 0 6px 16px rgba(239,68,68,.06);
  transition: box-shadow .15s, transform .15s;
}
.fault-slot:hover {
  box-shadow: 0 10px 24px rgba(239,68,68,.12);
  transform: translateY(-1px);
}
.fault-slot-rank {
  width: 60px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #fef2f2;
  color: #dc2626;
  font-weight: 900;
  font-size: 15px;
}
.fault-slot-info {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.fault-slot-info strong {
  font-size: 14px;
  color: #101828;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fault-slot-info small {
  font-size: 11px;
  color: #667085;
}
.fault-slot-mode {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 850;
  white-space: nowrap;
}
.fault-slot-mode.fast { background: #eff6ff; color: #2563eb; }
.fault-slot-mode.slow { background: #fff7ed; color: #f97316; }
.fault-slot-mode.pending { background: #f5f3ff; color: #8b5cf6; }
.fault-slot.fast { border-color: #bfdbfe; background: linear-gradient(180deg, #fff 0%, #f8fbff 100%); }
.fault-slot.slow { border-color: #fed7aa; background: linear-gradient(180deg, #fff 0%, #fffcf8 100%); }
.fault-slot.pending { border-color: #ddd6fe; background: linear-gradient(180deg, #fff 0%, #fcfbff 100%); }
.fault-slot.fast .fault-slot-rank { background: #eff6ff; color: #2563eb; }
.fault-slot.slow .fault-slot-rank { background: #fff7ed; color: #ea580c; }
.fault-area-empty {
  padding: 32px 18px;
  text-align: center;
  color: #667085;
  display: grid;
  gap: 6px;
  justify-items: center;
}
.fault-area-empty .material-icons {
  font-size: 36px;
  color: #d1d5db;
}
.fault-area-empty strong {
  font-size: 14px;
  color: #344054;
}
.fault-area-empty span {
  font-size: 12px;
  color: #667085;
  line-height: 1.6;
}
.fault-footnote {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  padding: 11px 18px 14px;
  border-top: 1px solid #fecdd3;
  color: #9f1239;
  font-size: 12px;
}

.side-status {
  display: grid;
  gap: 10px;
  align-content: start;
}

.side-card {
  min-height: 0;
  display: grid;
  grid-template-columns: 36px 1fr;
  grid-template-rows: auto auto;
  column-gap: 10px;
  align-content: center;
  padding: 12px 14px;
  border: 1px solid #edf0ee;
  border-radius: 12px;
  background: rgba(255,255,255,.95);
  box-shadow: 0 6px 18px rgba(16, 24, 40, .04);
  transition: border-color .2s, box-shadow .2s, transform .2s;
}
.side-card:hover {
  border-color: #a7f3d0;
  box-shadow: 0 18px 40px rgba(16, 24, 40, .09);
  transform: translateY(-2px);
}

.side-icon {
  grid-row: 1 / span 2;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #ecfdf5;
  color: #059669;
  font-size: 16px;
  font-weight: 900;
}

.side-icon.blue {
  background: #eff6ff;
  color: #2563eb;
}

.side-icon.orange {
  background: #fff7ed;
  color: #f97316;
}

.side-icon.red {
  background: #fff1f2;
  color: #e11d48;
}

.fault-queue-card {
  border-color: #ffe4e6;
  background: linear-gradient(180deg, #fff 0%, #fff7f8 100%);
}

@media (max-width: 1200px) {
  .fault-legend {
    flex-wrap: wrap;
  }
}

@media (max-width: 720px) {
  .fault-area-head {
    padding: 14px 14px 10px;
  }

}

.side-icon.pulse {
  animation: sidePulse 1.8s ease-in-out infinite;
}

@keyframes sidePulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,.18); }
  50% { box-shadow: 0 0 0 9px rgba(16,185,129,.08); }
}

.side-card strong {
  color: #101828;
  font-size: 13px;
  line-height: 1.3;
}

.side-card span {
  margin-top: 2px;
  color: #667085;
  font-size: 11px;
  line-height: 1.4;
}

.table-title {
  font-weight: 850;
  font-size: 16px;
  color: #101828;
  letter-spacing: .2px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  background: #f8faf9;
  color: #475467;
  text-align: left;
  padding: 12px 14px;
  font-size: 12px;
  font-weight: 850;
  letter-spacing: .2px;
  border-bottom: 1px solid #edf0ee;
  white-space: nowrap;
}

td {
  padding: 12px 14px;
  border-bottom: 1px solid #edf0ee;
  color: #344054;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}

td strong {
  color: #101828;
  font-size: 14px;
  font-weight: 900;
}

.mode-pill,
.status-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 48px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 900;
  line-height: 1;
}

.mode-pill.fast {
  color: #059669;
  background: #ecfdf5;
}

.mode-pill.slow {
  color: #f97316;
  background: #fff7ed;
}

.status-cell.green {
  color: #0f2f5f;
  background: transparent;
  font-weight: 650;
}

.status-cell.green i {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #38a169;
  box-shadow: 0 0 0 4px rgba(56, 161, 105, .12);
}

.status-cell.gray {
  color: #2563eb;
  background: #eff6ff;
}

.status-cell.red {
  color: #dc2626;
  background: #fef2f2;
}

.charts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.chart-box {
  min-height: 230px;
  padding: 16px 18px 14px;
}

.chart-box h3 {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 900;
  letter-spacing: .2px;
  color: #101828;
}

.chart-content {
  display: grid;
  grid-template-columns: 150px 1fr;
  align-items: center;
  gap: 18px;
}

.donut {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  animation: donutIn .8s cubic-bezier(.34,1.56,.64,1) both;
  animation-delay: .2s;
}

.donut > div {
  width: 82px;
  height: 82px;
  display: grid;
  place-items: center;
  align-content: center;
  border-radius: 50%;
  background: #fff;
  box-shadow: inset 0 0 0 1px #edf0ee;
}

.donut strong {
  font-size: 12px;
  color: #667085;
  font-weight: 850;
}

.donut span {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 950;
  color: #101828;
}

.chart-legend {
  display: grid;
  gap: 10px;
}

.chart-legend p {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0;
  color: #344054;
  font-size: 13px;
  font-weight: 650;
}

.chart-legend i {
  margin-right: 8px;
}

.chart-legend strong {
  color: #101828;
  font-size: 14px;
  font-weight: 900;
}

.overview-footer {
  display: grid;
  grid-template-columns: 1.1fr 1.45fr;
  gap: 0;
  margin-top: 16px;
  padding: 0;
  min-height: 78px;
  border: 1px solid #edf0ee;
  border-radius: 16px;
  background: rgba(255,255,255,.95);
  box-shadow: 0 14px 38px rgba(16, 24, 40, .055);
  overflow: hidden;
  color: #475467;
  font-size: 13px;
}

.overview-footer > div {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 14px 18px;
  border-right: 1px solid #edf0ee;
}

.overview-footer > div:last-child {
  border-right: 0;
}

.footer-status,
.footer-desc {
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(248,250,249,.82));
}

.footer-status > div,
.footer-desc {
  min-width: 0;
}

.footer-status > div,
.footer-desc {
  display: grid;
  gap: 4px;
}

.footer-status {
  align-items: center;
}

.footer-status span,
.footer-desc span {
  color: #475467;
  font-size: 13px;
  line-height: 1.45;
  font-weight: 650;
}

.overview-footer strong {
  color: #101828;
  font-size: 14px;
  font-weight: 900;
  white-space: nowrap;
}

.overview-footer span {
  font-weight: 650;
  line-height: 1.45;
}

.ok-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #10b981;
  flex: 0 0 auto;
  animation: livePing 2s ease-out infinite;
}


.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 24, 40, .38);
  animation: overlayIn .2s ease both;
}

.modal-card {
  width: min(820px, calc(100vw - 48px));
  max-height: 82vh;
  overflow: auto;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 64px rgba(16,24,40,.22);
  animation: modalUp .3s cubic-bezier(.34,1.56,.64,1) both;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #edf0ee;
}

.modal-head h3 {
  margin: 0;
  font-size: 16px;
}

.modal-head button {
  border: 0;
  background: transparent;
  color: #98a2b3;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 18px 22px;
}

/* ─────────────── ANIMATION KEYFRAMES ─────────────── */
@keyframes kpiEnter {
  from { opacity: 0; transform: translateY(16px) scale(.98); }
  to   { opacity: 1; transform: none; }
}
@keyframes sectionEnter {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: none; }
}
@keyframes donutIn {
  from { opacity: 0; transform: scale(.7) rotate(-60deg); }
  to   { opacity: 1; transform: none; }
}
@keyframes livePing {
  0%   { box-shadow: 0 0 0 0 rgba(16,185,129,.45); }
  70%  { box-shadow: 0 0 0 8px rgba(16,185,129,0); }
  100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
}
@keyframes overlayIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes modalUp {
  from { opacity: 0; transform: translateY(24px) scale(.96); }
  to   { opacity: 1; transform: none; }
}

/* ─── TABLE ROW HOVER ─── */
tbody tr {
  transition: background .15s;
}
tbody tr:hover td {
  background: #f8fdf9;
}

/* ─── REFRESH BTN SPIN ─── */
.refresh-btn:not(:disabled):hover {
  transform: scale(1.03);
}
.refresh-btn:disabled {
  opacity: .65;
  cursor: wait;
}

@media (max-width: 1280px) {
  .kpi-row {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .overview-split {
    grid-template-columns: 1fr;
  }

  .side-status {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .admin-overview {
    padding: 18px;
  }

  .overview-top,
  .section-head,
  .wait-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .kpi-row,
  .charts,
  .side-status {
    grid-template-columns: 1fr;
  }
}
</style>
