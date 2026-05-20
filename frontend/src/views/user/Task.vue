<template>
  <div class="page">

    <!-- Hero -->
    <div class="page-hero">
      <div>
        <h1>当前请求</h1>
      </div>
      <div class="live-pill" v-if="req"><span class="live-dot"></span>实时更新中</div>
    </div>

    <!-- No Active Request -->
    <div class="empty-card" v-if="!req && !initialLoading">
      <div class="empty-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
      </div>
      <div class="empty-title">暂无进行中的请求</div>
      <div class="empty-sub">前往工作台提交充电请求</div>
      <router-link to="/user/workspace" class="btn btn-primary" style="width:auto;padding:10px 24px;">前往工作台</router-link>
    </div>

    <template v-if="req">

      <!-- Status Row -->
      <div class="status-row" :class="{ 'status-amber': isWaiting }">
        <div class="status-main">
          <div class="status-bolt">{{ isWaiting ? '⏳' : '⚡' }}</div>
          <div>
            <div class="status-title" :class="{ 'amber-text': isWaiting }">
              <template v-if="isWaiting">等待系统分配中</template>
              <template v-else>当前位置：<strong>{{ locationText }}</strong></template>
            </div>
            <div class="status-sub" :class="{ 'amber-text': isWaiting }">
              <template v-if="isWaiting">系统正在计算最优充电策略，请将车辆驶入公共等候区。</template>
              <template v-else>{{ reasonText }}</template>
            </div>
          </div>
        </div>
        <div class="s-metric">
          <div class="s-metric-icon">前车</div>
          <div>
            <div class="s-metric-val">{{ frontVehicleCountText }}</div>
          </div>
        </div>
        <div class="s-metric">
          <div class="s-metric-icon">已充</div>
          <div>
            <div class="s-metric-val green">{{ chargePercentText }}</div>
          </div>
        </div>
        <div class="s-metric">
          <div class="s-metric-icon">剩余</div>
          <div>
            <div class="s-metric-val">{{ remainingTimeText }}</div>
          </div>
        </div>
        <div class="s-metric">
          <div class="s-metric-icon">队列号</div>
          <div>
            <div class="s-metric-val">{{ queueNumberText(req) }}</div>
          </div>
        </div>
      </div>

      <!-- Queue Zone -->
      <section class="queue-zone">
        <div class="queue-head">
          <div>
            <h2 class="q-section-title">请求总览</h2>
            <p class="q-section-sub">先看整体状态，再快速找到你自己的请求。高亮卡片为你的当前单子。</p>
          </div>
          <div class="q-legend">
            <span><i class="q-dot" style="background:#4f46e5"></i>你的请求</span>
            <span><i class="q-dot" style="background:#059669"></i>充电中</span>
            <span><i class="q-dot" style="background:#ef4444"></i>故障</span>
            <span><i class="q-dot" style="background:#98a2b3"></i>空闲</span>
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
            :key="`${car.id}-${car.targetX}`"
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

      <!-- Main Grid -->
      <div class="main-grid">
        <div class="left-stack">

          <!-- Detail Panel -->
          <div class="panel">
            <div class="panel-head">
              <div>
                <h2 class="panel-title">请求详情</h2>
                <div class="panel-sub">确认本次请求的核心字段与当前分配结果。</div>
              </div>
              <button class="btn-refresh" @click="refresh">刷新</button>
            </div>
            <div class="detail-wrap">
              <div class="detail-summary">
                <div class="detail-chip">
                  <span>请求编号</span>
                  <strong>{{ req.request_id }}</strong>
                </div>
                <div class="detail-chip">
                  <span>当前状态</span>
                  <strong>{{ statusText }}</strong>
                </div>
                <div class="detail-chip">
                  <span>分配桩位</span>
                  <strong>{{ req.station_code || '待分配' }}</strong>
                </div>
              </div>
              <table class="detail-table">
                <tbody>
                  <tr>
                    <td>请求编号</td><td>{{ req.request_id }}</td>
                    <td>充电模式</td><td>{{ CHARGE_MODE_TEXT[req.charge_mode] || req.charge_mode }}</td>
                  </tr>
                  <tr>
                    <td>请求电量</td><td>{{ req.request_energy }} kWh</td>
                    <td>已充电量</td><td>{{ chargedEnergyText }}</td>
                  </tr>
                  <tr>
                    <td>已充百分比</td><td>{{ chargePercentText }}</td>
                    <td>分配桩位</td><td>{{ req.station_code || '待分配' }}</td>
                  </tr>
                  <tr>
                    <td>桩队列位置</td><td>{{ req.station_queue_position ?? '--' }}</td>
                    <td>预计完成</td><td>{{ fmtTime(req.estimated_finish_time) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Actions Panel -->
          <div class="panel">
            <div class="panel-head">
              <div>
                <h2 class="panel-title">可用操作</h2>
                <div class="panel-sub">根据当前状态，部分操作暂时不可用。</div>
              </div>
            </div>
            <div class="actions-wrap">
              <div class="action-row">
                <button class="btn btn-secondary" :disabled="!canEditMode" @click="editMode">修改充电模式</button>
                <button class="btn btn-secondary" :disabled="!canEditEnergy" @click="editEnergy">修改充电量</button>
                <button class="btn btn-danger" :disabled="!canCancel" @click="cancelReq">取消请求</button>
                <button class="btn btn-primary" :disabled="!canStop" @click="stopReq">提前结束充电</button>
                <router-link v-if="canViewDetail" to="/user/bills" class="btn btn-secondary" style="text-decoration:none;text-align:center;">查看详单</router-link>
              </div>
              <p class="notice">注：修改充电模式会回到等候区重新排队。提前结束仅在队列或充电中状态可用。</p>
            </div>
          </div>

        </div>

        <!-- Timeline Panel -->
        <div class="panel">
          <div class="panel-head">
            <div>
              <h2 class="panel-title">进度时间线</h2>
              <div class="panel-sub">用时间线呈现请求从提交到充电的每个状态。</div>
            </div>
          </div>
          <div class="timeline-wrap">
            <div class="timeline-scroll">
              <div class="timeline-list">
                <div
                  v-for="item in timelineItems"
                  :key="item.key"
                  class="timeline-item"
                  :class="item.state"
                >
                  <div class="tl-main">
                    <div class="tl-title">{{ item.text }}</div>
                    <div v-if="item.sub" class="tl-sub">{{ item.sub }}</div>
                  </div>
                  <div class="tl-side">
                    <span v-if="item.state.includes('active')" class="tl-pill">进行中</span>
                    <span v-else-if="item.state.includes('danger')" class="tl-pill tl-pill-danger">异常</span>
                    <span v-else-if="item.state.includes('warning')" class="tl-pill tl-pill-warn">调整中</span>
                    <span v-else-if="item.state.includes('done')" class="tl-pill tl-pill-done">已完成</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Footer Band -->
      <div class="footer-band">
        <div class="info-box">
          <h3>当前请求摘要</h3>
          <div class="info-list">
            <div class="info-row"><span>当前状态</span><strong>{{ statusText }}</strong></div>
            <div class="info-row"><span>请求编号</span><strong>{{ req.request_id }}</strong></div>
            <div class="info-row"><span>服务桩位</span><strong>{{ req.station_code || '待分配' }}</strong></div>
          </div>
        </div>
        <div class="info-box">
          <h3>系统说明</h3>
          <div class="info-list">
            <div class="info-row"><span>调度方式</span><strong>按最短完成时间分配</strong></div>
            <div class="info-row"><span>当前队列号</span><strong>{{ queueNumberText(req) }}</strong></div>
            <div class="info-row"><span>{{ scheduleTimeLabel }}</span><strong>{{ scheduleTimeText }}</strong></div>
          </div>
        </div>
        <div class="info-box">
          <h3>后续动作</h3>
          <div class="info-list">
            <div class="info-row"><span>状态同步</span><strong>自动刷新中</strong></div>
            <div class="info-row"><span>账单生成</span><strong>完成后自动生成</strong></div>
            <div class="info-row"><span>充电进度</span><strong>{{ chargedEnergyText }} / {{ req.request_energy }} kWh</strong></div>
          </div>
        </div>
      </div>

    </template>
  </div>
  <ActionDialog v-bind="dialog" @confirm="confirmDialog" @cancel="cancelDialog" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getActiveRequest, getProfile, updateChargeMode, updateRequestEnergy, cancelRequest, stopRequest, getStationsOverview } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { REQUEST_STATUS, REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT, ACTIVE_STATUSES, HAS_DETAIL_STATUSES } from '@/constants/enums'
import { clearLegacyLocalState } from '@/utils/authSession'
import { formatRequestRemainingText } from '@/utils/requestEta'
import ActionDialog from '@/components/ActionDialog.vue'
import { useActionDialog } from '@/composables/useActionDialog'

const { dialog, openConfirm, openInput, openMessage, confirmDialog, cancelDialog } = useActionDialog()

const ACTIVE_SNAPSHOT_KEY = 'active_request_snapshot'
const FAULT_HANDOFF_KEY = 'active_request_fault_handoff'
const req = ref(null)
const initialLoading = ref(true)
const batteryCapacity = ref(null)
const faultHandoff = ref(loadFaultHandoff())
const stationOverview = ref(null)
const stationOverviewLoaded = ref(false)
const pileTargets = [212, 424, 636, 848, 1060]
let pollTimer = null

const statusText = computed(() => REQUEST_STATUS_TEXT[req.value?.request_status] || req.value?.request_status || '--')

const bannerClass = computed(() => {
  const s = req.value?.request_status
  if (s === REQUEST_STATUS.WAITING_AREA) return 'banner-amber'
  if (s === REQUEST_STATUS.QUEUED) return 'banner-blue'
  if (s === REQUEST_STATUS.CHARGING) return 'banner-green'
  return 'banner-gray'
})

const badgeClass = computed(() => {
  const s = req.value?.request_status
  if (s === REQUEST_STATUS.WAITING_AREA) return 'badge-amber'
  if (s === REQUEST_STATUS.QUEUED) return 'badge-blue'
  if (s === REQUEST_STATUS.CHARGING) return 'badge-green'
  return 'badge-gray'
})

const bannerSub = computed(() => {
  if (!req.value) return ''
  const s = req.value.request_status
  if (hasFaultHandoff.value && (s === REQUEST_STATUS.QUEUED || s === REQUEST_STATUS.CHARGING)) {
    return `从 ${faultHandoff.value.fromStation || '原充电桩'} 中断后，已重新分配至 ${req.value.station_code || '新充电桩'}`
  }
  if (s === REQUEST_STATUS.WAITING_AREA) return `排队号 ${queueNumberText(req.value)} · 前方 ${frontVehicleCountText.value} 辆车`
  if (s === REQUEST_STATUS.QUEUED) return `分配至 ${req.value.station_code} · 队列第 ${req.value.station_queue_position ?? '?'} 位 · 前方 ${frontVehicleCountText.value} 辆车`
  if (s === REQUEST_STATUS.CHARGING) return `${req.value.station_code} 充电中 · 已充 ${chargePercentText.value}`
  if (s === REQUEST_STATUS.COMPLETED) return '充电已正常完成'
  if (s === REQUEST_STATUS.COMPLETED_EARLY) return '充电已提前结束'
  if (s === REQUEST_STATUS.CANCELLED) return '请求已取消'
  if (s === REQUEST_STATUS.FAULT_INTERRUPTED) return '因故障中断'
  return ''
})

const estWait = computed(() => {
  if (req.value?.request_status === REQUEST_STATUS.CHARGING) return '已开始'
  return formatRequestRemainingText(req.value)
})

const chargedEnergyText = computed(() => {
  return chargedEnergyNumber.value === null ? '--' : `${chargedEnergyNumber.value.toFixed(2)} kWh`
})

const chargedEnergyNumber = computed(() => {
  const value = req.value?.charged_energy ?? req.value?.actual_energy
  const n = Number(value)
  return Number.isFinite(n) ? Math.max(0, n) : null
})

const requestEnergyNumber = computed(() => {
  const n = Number(req.value?.request_energy)
  return Number.isFinite(n) && n > 0 ? n : null
})

const chargePercent = computed(() => {
  if (chargedEnergyNumber.value === null || requestEnergyNumber.value === null) return null
  return Math.min(100, Math.max(0, (chargedEnergyNumber.value / requestEnergyNumber.value) * 100))
})

const chargePercentText = computed(() => {
  return chargePercent.value === null ? '--' : `${chargePercent.value.toFixed(1)}%`
})

const chargeProgressWidth = computed(() => {
  return chargePercent.value === null ? '0%' : `${chargePercent.value}%`
})

const frontVehicleCount = computed(() => {
  const s = req.value?.request_status
  if (s === REQUEST_STATUS.QUEUED || s === REQUEST_STATUS.CHARGING) {
    const position = Number(req.value?.station_queue_position)
    if (Number.isFinite(position)) return Math.max(0, position - 1)
  }
  const count = Number(req.value?.front_waiting_count)
  return Number.isFinite(count) ? Math.max(0, count) : null
})

const frontVehicleCountText = computed(() => {
  return frontVehicleCount.value === null ? '--' : String(frontVehicleCount.value)
})

const hasFaultHandoff = computed(() => {
  return Boolean(faultHandoff.value && faultHandoff.value.toRequestId === req.value?.request_id)
})

const locationText = computed(() => {
  if (!req.value) return '--'
  const s = req.value.request_status
  if (s === REQUEST_STATUS.WAITING_AREA) return '等候区等待调度'
  if (s === REQUEST_STATUS.QUEUED) return `${req.value.station_code || '充电桩'} 桩队列第 ${req.value.station_queue_position ?? '?'} 位`
  if (s === REQUEST_STATUS.CHARGING) return `${req.value.station_code || '充电桩'} 正在充电`
  if (s === REQUEST_STATUS.FAULT_INTERRUPTED) return '故障中断'
  return statusText.value
})

const reasonText = computed(() => {
  if (!req.value) return ''
  if (hasFaultHandoff.value) return `原 ${faultHandoff.value.fromStation || '充电桩'} 故障中断后，系统已为剩余电量重新调度。`
  const s = req.value.request_status
  if (s === REQUEST_STATUS.WAITING_AREA) return `还未进入固定桩队列，前方 ${frontVehicleCountText.value} 辆车等待调度。`
  if (s === REQUEST_STATUS.QUEUED) return `已分配充电桩，前方 ${frontVehicleCountText.value} 辆车完成后开始充电。`
  if (s === REQUEST_STATUS.CHARGING) return `已充 ${chargedEnergyText.value}，目标 ${requestEnergyNumber.value ? `${requestEnergyNumber.value.toFixed(2)} kWh` : '--'}。`
  return bannerSub.value
})

const remainingTimeText = computed(() => {
  return formatRequestRemainingText(req.value)
})

const scheduleTimeLabel = computed(() => {
  return req.value?.request_status === REQUEST_STATUS.CHARGING ? '预计结束' : '预计开始'
})

const scheduleTimeText = computed(() => {
  if (!req.value) return '--'
  return req.value.request_status === REQUEST_STATUS.CHARGING
    ? fmtTime(req.value.estimated_finish_time)
    : fmtTime(req.value.estimated_start_time)
})

// Timeline step
const activeStep = computed(() => {
  const s = req.value?.request_status
  if (s === REQUEST_STATUS.WAITING_AREA) return 1
  if (s === REQUEST_STATUS.QUEUED) return 2
  if (s === REQUEST_STATUS.CHARGING) return 3
  return 4
})

const terminalLabel = computed(() => {
  const s = req.value?.request_status
  if (s === REQUEST_STATUS.COMPLETED) return '正常完成'
  if (s === REQUEST_STATUS.COMPLETED_EARLY) return '提前结束'
  if (s === REQUEST_STATUS.CANCELLED) return '已取消'
  if (s === REQUEST_STATUS.FAULT_INTERRUPTED) return '故障中断'
  return '充电完成'
})

function tlClass(step) {
  if (step < activeStep.value) return 'done'
  if (step === activeStep.value) return 'active'
  return ''
}

const timelineItems = computed(() => {
  const items = [
    { key: 'submitted', text: '请求已提交', state: tlClass(0) },
    { key: 'waiting', text: '等候区排队', state: tlClass(1) },
  ]

  if (hasFaultHandoff.value) {
    items.push(
      {
        key: 'fault-interrupted',
        text: '故障中断',
        sub: `${faultHandoff.value.fromRequestId || '上一段任务'} 在 ${faultHandoff.value.fromStation || '原充电桩'} 被中断`,
        state: 'done danger',
      },
      {
        key: 'fault-requeue',
        text: '重新排队',
        sub: '系统已为剩余电量重新进入调度流程',
        state: 'done warning',
      },
    )
  }

  items.push(
    {
      key: 'assigned',
      text: hasFaultHandoff.value ? '已分配新充电桩' : '分配到桩队列',
      sub: hasFaultHandoff.value ? `${req.value?.station_code || '新充电桩'} · 队列第 ${req.value?.station_queue_position ?? '?'} 位` : '',
      state: tlClass(2),
    },
    {
      key: 'charging',
      text: hasFaultHandoff.value ? '继续充电' : '充电中',
      state: tlClass(3),
    },
    { key: 'terminal', text: terminalLabel.value, state: tlClass(4) },
  )

  return items
})

// Button rules per §4.3
const canEditMode = computed(() => req.value?.request_status === REQUEST_STATUS.WAITING_AREA)
const canEditEnergy = computed(() => req.value?.request_status === REQUEST_STATUS.WAITING_AREA)
const canCancel = computed(() => req.value?.request_status === REQUEST_STATUS.WAITING_AREA)
const canStop = computed(() => [REQUEST_STATUS.QUEUED, REQUEST_STATUS.CHARGING].includes(req.value?.request_status))
const canViewDetail = computed(() => HAS_DETAIL_STATUSES.includes(req.value?.request_status))

function fmtTime(t) {
  if (!t) return '--'
  try {
    return new Date(t).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch { return t }
}

function formatLocalDateTime(date = new Date()) {
  const pad = (value) => String(value).padStart(2, '0')
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate())
  ].join('-') + `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

async function refresh() {
  await Promise.all([syncActiveRequest(), loadStationOverview()])
}

async function loadStationOverview() {
  try {
    const res = await getStationsOverview()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return
    stationOverview.value = data
  } catch (_) { /* silent */ } finally {
    stationOverviewLoaded.value = true
  }
}

const overviewStations = computed(() => {
  const d = stationOverview.value
  if (!d) return []
  const fast = Array.isArray(d.fast_stations) ? d.fast_stations : []
  const slow = Array.isArray(d.slow_stations) ? d.slow_stations : []
  return [...fast, ...slow].sort((a, b) => String(a.station_code).localeCompare(String(b.station_code)))
})

const dispatchPiles = computed(() => {
  const currentCode = req.value?.station_code || ''
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

const isWaiting = computed(() => req.value?.request_status === REQUEST_STATUS.WAITING_AREA)
const isQueued = computed(() => req.value?.request_status === REQUEST_STATUS.QUEUED)
const isCharging = computed(() => req.value?.request_status === REQUEST_STATUS.CHARGING)

const dispatchCars = computed(() => {
  const status = req.value?.request_status
  const activeIndex = dispatchPiles.value.findIndex((p) => p.current)
  const otherQueuedIndexes = dispatchPiles.value
    .map((p, i) => ({ p, i }))
    .filter(({ p }) => !p.current && (p.queue > 0 || p.state === 'busy'))
    .map(({ i }) => i)

  const cars = []
  if (status === REQUEST_STATUS.WAITING_AREA) {
    return []
  } else if (status === REQUEST_STATUS.QUEUED && activeIndex >= 0) {
    cars.push({ id: 0, targetX: pileTargets[activeIndex], delay: 0, assigned: true, junction: true })
  } else if (status === REQUEST_STATUS.CHARGING && activeIndex >= 0) {
    cars.push({ id: 0, targetX: pileTargets[activeIndex], delay: 0, assigned: true })
  }
  otherQueuedIndexes.forEach((index, i) => {
    cars.push({ id: i + 1, targetX: pileTargets[index], delay: (i + 1) * 2.6, assigned: true })
  })
  return cars
})

function stationVisualState(station, current = false) {
  if (current) return 'mine'
  if (station.station_status === 'FAULT') return 'fault'
  if (station.station_status === 'SHUTDOWN') return 'shutdown'
  if (station.current_request_id) return 'busy'
  const q = Number(station.queue_length ?? station.current_queue_length ?? 0)
  if (Number.isFinite(q) && q > 0) return 'queue'
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
  return String(a || '').replace(/[-_\s]/g, '').toUpperCase() === String(b || '').replace(/[-_\s]/g, '').toUpperCase()
}

async function syncActiveRequest(clearWhenNone = true) {
  try {
    const res = await getActiveRequest()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return false
    if (data.request_id && ACTIVE_STATUSES.includes(data.request_status)) {
      clearLegacyLocalState()
      updateFaultTrace(data)
      req.value = data
      return true
    }
    clearLegacyLocalState()
    clearFaultTrace()
    if (clearWhenNone) req.value = null
    return false
  } catch (_) {
    return false
  }
}

function activeSnapshot(data) {
  return {
    requestId: data.request_id,
    status: data.request_status,
    stationCode: data.station_code || null,
    queueNumber: data.queue_number || null,
    savedAt: new Date().toISOString(),
  }
}

function queueNumberText(row) {
  if (!row) return '--'
  if (row.is_fault_followup && row.source_queue_number && row.source_queue_number !== row.queue_number) {
    return `${row.queue_number}（源${row.source_queue_number}）`
  }
  return row.queue_number || '--'
}

function loadJson(key) {
  try {
    const raw = sessionStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveJson(key, value) {
  sessionStorage.setItem(key, JSON.stringify(value))
}

function loadFaultHandoff() {
  return loadJson(FAULT_HANDOFF_KEY)
}

function clearFaultTrace() {
  sessionStorage.removeItem(ACTIVE_SNAPSHOT_KEY)
  sessionStorage.removeItem(FAULT_HANDOFF_KEY)
  faultHandoff.value = null
}

function updateFaultTrace(data) {
  const previous = loadJson(ACTIVE_SNAPSHOT_KEY)
  const next = activeSnapshot(data)
  const previousHadStation = Boolean(previous?.stationCode)
  const nextHadStation = Boolean(next.stationCode)
  const requestChanged = previous?.requestId && previous.requestId !== next.requestId
  const stationChanged = previous?.requestId === next.requestId && previousHadStation && nextHadStation && previous.stationCode !== next.stationCode

  if ((requestChanged && previousHadStation) || stationChanged) {
    const handoff = {
      fromRequestId: previous.requestId,
      toRequestId: next.requestId,
      fromStation: previous.stationCode,
      toStation: next.stationCode,
      detectedAt: next.savedAt,
    }
    saveJson(FAULT_HANDOFF_KEY, handoff)
    faultHandoff.value = handoff
  } else {
    const currentHandoff = loadFaultHandoff()
    faultHandoff.value = currentHandoff?.toRequestId === next.requestId ? currentHandoff : null
  }

  saveJson(ACTIVE_SNAPSHOT_KEY, next)
}

async function loadProfile() {
  try {
    const res = await getProfile()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return
    batteryCapacity.value = Number(data.battery_capacity)
  } catch (_) { /* silent */ }
}

async function editMode() {
  const newMode = req.value.charge_mode === 'FAST' ? 'SLOW' : 'FAST'
  const confirmed = await openConfirm({
    title: '修改充电模式',
    message: `切换为 ${CHARGE_MODE_TEXT[newMode]}？将回到等候区重新排队。`,
    severity: 'warning',
    confirmText: '确认切换',
  })
  if (!confirmed) return
  try {
    const res = await updateChargeMode({ request_id: req.value.request_id, charge_mode: newMode })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      await openMessage({ title: '修改失败', message: data.message || '修改失败', severity: 'danger' })
      return
    }
    await refresh()
  } catch (e) {
    await openMessage({ title: '修改失败', message: e?.response?.data?.message || '修改失败', severity: 'danger' })
  }
}

async function editEnergy() {
  const cap = batteryCapacity.value
  const val = await openInput({
    title: '修改充电量',
    message: cap ? `当前请求电量 ${req.value.request_energy} kWh（电池容量 ${cap} kWh）` : `当前请求电量 ${req.value.request_energy} kWh`,
    inputLabel: '新充电量 (kWh)',
    inputPlaceholder: '输入新电量',
    inputType: 'number',
    inputMin: 0.1,
    inputStep: 0.1,
    inputValue: req.value.request_energy,
    confirmText: '确认修改',
  })
  if (val == null) return
  const num = parseFloat(val)
  if (!num || num <= 0) {
    await openMessage({ title: '输入无效', message: '电量必须大于 0', severity: 'danger' })
    return
  }
  if (cap && num > cap) {
    await openMessage({ title: '超出限制', message: `请求电量不能超过电池容量 ${cap} kWh`, severity: 'warning' })
    return
  }
  try {
    const res = await updateRequestEnergy({ request_id: req.value.request_id, request_energy: num })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      await openMessage({ title: '修改失败', message: data.message || '修改失败', severity: 'danger' })
      return
    }
    await refresh()
  } catch (e) {
    await openMessage({ title: '修改失败', message: e?.response?.data?.message || '修改失败', severity: 'danger' })
  }
}

async function cancelReq() {
  const confirmed = await openConfirm({
    title: '取消请求',
    message: '确认取消当前充电请求？取消后不可恢复。',
    severity: 'danger',
    confirmText: '确认取消',
  })
  if (!confirmed) return
  try {
    const res = await cancelRequest({ request_id: req.value.request_id })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      await openMessage({ title: '取消失败', message: data.message || '取消失败', severity: 'danger' })
      return
    }
    await refresh()
  } catch (e) {
    await openMessage({ title: '取消失败', message: e?.response?.data?.message || '取消失败', severity: 'danger' })
  }
}

async function stopReq() {
  const confirmed = await openConfirm({
    title: '提前结束充电',
    message: '确认提前结束充电？将按已充电量结算。',
    severity: 'warning',
    confirmText: '确认结束',
  })
  if (!confirmed) return
  try {
    const res = await stopRequest({
      request_id: req.value.request_id,
      stop_time: formatLocalDateTime()
    })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      await openMessage({ title: '操作失败', message: data.message || '操作失败', severity: 'danger' })
      return
    }
    await refresh()
  } catch (e) {
    await openMessage({ title: '操作失败', message: e?.response?.data?.message || '操作失败', severity: 'danger' })
  }
}

function startPoll() { stopPoll(); pollTimer = setInterval(refresh, 5000) }
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }

onMounted(async () => { loadProfile(); await refresh(); initialLoading.value = false; loadStationOverview(); startPoll() })
onUnmounted(() => { stopPoll() })
</script>

<style scoped>
/* BASE */
.page {
  max-width: 1540px;
  margin: 0 auto;
  padding: 24px 30px 34px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", Arial, sans-serif;
  color: #101828;
}

/* HERO */
.page-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 16px; }
.page-hero h1 { margin: 0; font-size: 28px; font-weight: 850; line-height: 1.15; letter-spacing: -.4px; color: #101828; }
.page-hero p { margin: 8px 0 0; color: #667085; font-size: 14px; line-height: 1.7; }

.live-pill { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; color: #059669; font-size: 13px; font-weight: 750; background: rgba(5,150,105,.08); white-space: nowrap; }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 0 0 rgba(16,185,129,.25); animation: livePulse 2.8s infinite; flex-shrink: 0; display: inline-block; }
@keyframes livePulse {
  0% { box-shadow: 0 0 0 0 rgba(16,185,129,.28); }
  70% { box-shadow: 0 0 0 8px rgba(16,185,129,0); }
  100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
}

/* EMPTY */
.empty-card { text-align: center; padding: 60px 20px; background: rgba(255,255,255,.98); border: 1px solid #e5e7eb; border-radius: 20px; box-shadow: 0 12px 30px rgba(16,24,40,.05); }
.empty-icon { margin-bottom: 16px; }
.empty-title { font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 6px; }
.empty-sub { font-size: 13px; color: #9ca3af; margin-bottom: 24px; }

/* BANNER */
.banner { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 16px 20px; margin-bottom: 16px; border: 1px solid #d8f0df; border-radius: 16px; background: linear-gradient(180deg, rgba(236,253,245,.96), rgba(244,251,247,.96)); box-shadow: 0 14px 34px rgba(16,24,40,.06); }
.banner-amber { border-color: #fde68a; background: linear-gradient(180deg, rgba(255,251,235,.96), rgba(255,253,243,.96)); }
.banner-blue { border-color: #bfdbfe; background: linear-gradient(180deg, rgba(239,246,255,.96), rgba(245,249,255,.96)); }
.banner-gray { border-color: #e5e7eb; background: linear-gradient(180deg, #f9fafb, #fff); }

.banner-left { display: flex; align-items: center; gap: 16px; min-width: 0; }
.banner-icon { width: 54px; height: 54px; border-radius: 16px; display: grid; place-items: center; color: #fff; background: linear-gradient(135deg, #34d399, #059669); box-shadow: 0 14px 26px rgba(5,150,105,.18); font-size: 26px; flex-shrink: 0; }
.banner-amber .banner-icon { background: linear-gradient(135deg, #fbbf24, #d97706); box-shadow: 0 14px 26px rgba(217,119,6,.18); }
.banner-blue .banner-icon { background: linear-gradient(135deg, #60a5fa, #2563eb); box-shadow: 0 14px 26px rgba(37,99,235,.18); }
.banner-gray .banner-icon { background: linear-gradient(135deg, #9ca3af, #6b7280); box-shadow: none; }
.banner-copy strong { display: block; font-size: 17px; font-weight: 800; line-height: 1.2; color: #101828; }
.banner-copy span { display: block; margin-top: 5px; color: #667085; font-size: 13px; line-height: 1.5; }

.status-chip { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; border: 1px solid rgba(5,150,105,.16); background: rgba(255,255,255,.72); color: #059669; font-size: 13px; font-weight: 750; white-space: nowrap; flex-shrink: 0; }
.badge-amber.status-chip { color: #d97706; border-color: rgba(217,119,6,.16); }
.badge-blue.status-chip { color: #2563eb; border-color: rgba(37,99,235,.16); }
.badge-gray.status-chip { color: #9ca3af; border-color: #e5e7eb; }

/* STATUS ROW */
.status-amber { border-color: #fde68a !important; background: linear-gradient(180deg, rgba(255,251,235,.98), rgba(255,253,243,.98)) !important; }
.amber-text { color: #92400e !important; }
.status-row { display: grid; grid-template-columns: 1.6fr repeat(4, 1fr); gap: 0; border: 1px solid #e5e7eb; border-radius: 20px; background: rgba(255,255,255,.98); box-shadow: 0 12px 30px rgba(16,24,40,.05); margin-bottom: 16px; overflow: hidden; }
.status-main { display: flex; align-items: center; gap: 16px; padding: 18px 20px; }
.status-bolt { font-size: 28px; flex-shrink: 0; }
.status-title { font-size: 15px; color: #111827; font-weight: 600; }
.status-title strong { color: #059669; font-size: 20px; margin-left: 6px; font-weight: 850; }
.status-sub { margin-top: 6px; color: #667085; font-size: 13px; line-height: 1.55; }
.s-metric { display: flex; align-items: center; justify-content: center; gap: 12px; min-height: 58px; border-left: 1px solid #e5e7eb; }
.s-metric-icon { height: 36px; padding: 0 12px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; color: #059669; background: #ecfdf5; font-size: 13px; font-weight: 800; flex-shrink: 0; white-space: nowrap; }
.s-metric-label { color: #667085; font-size: 13px; }
.s-metric-val { margin-top: 4px; font-size: 20px; font-weight: 800; color: #101828; }
.s-metric-val.green { color: #059669; }

/* QUEUE ZONE */
.queue-zone { padding: 22px 0 24px; }
.queue-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; margin-bottom: 16px; }
.q-section-title { margin: 0 0 8px; font-size: 21px; font-weight: 850; line-height: 1.2; color: #101828; }
.q-section-sub { margin: 0; color: #667085; font-size: 13px; line-height: 1.65; }
.q-legend { display: flex; align-items: center; gap: 18px; color: #667085; font-size: 13px; flex-wrap: wrap; }
.q-dot { width: 8px; height: 8px; display: inline-block; border-radius: 50%; margin-right: 6px; vertical-align: middle; }

/* DISPATCH STAGE */
.dispatch-stage { position: relative; height: 250px; overflow: hidden; border-radius: 20px; background: radial-gradient(circle at 7% 45%, rgba(16,185,129,.12), transparent 26%), radial-gradient(circle at 85% 18%, rgba(37,99,235,.08), transparent 24%), linear-gradient(180deg, rgba(236,253,245,.48), rgba(255,255,255,.96)); border: 1px solid #e4efe9; box-shadow: 0 14px 36px rgba(16,24,40,.06); }
.main-lane { position: absolute; left: 64px; right: 64px; top: 164px; height: 3px; border-radius: 999px; background: linear-gradient(90deg, transparent, #cbd5e1 8%, #cbd5e1 92%, transparent); }
.main-lane::after { content: ""; position: absolute; right: -12px; top: -5px; width: 12px; height: 12px; border-top: 3px solid #cbd5e1; border-right: 3px solid #cbd5e1; transform: rotate(45deg); }
.route-pulse { position: absolute; left: 64px; right: 64px; top: 163px; height: 5px; background: linear-gradient(90deg, transparent, rgba(16,185,129,.18) 30%, transparent); animation: pulseMove 4s linear infinite; pointer-events: none; }
.entry-label, .exit-label { position: absolute; top: 174px; color: #667085; font-size: 13px; font-weight: 600; }
.entry-label { left: 64px; }
.exit-label { right: 62px; }
.dispatch-empty { position: absolute; inset: 0; display: grid; place-items: center; color: #98a2b3; font-size: 14px; }
.pile-row { position: absolute; left: 170px; right: 150px; top: 24px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 28px; z-index: 3; }
.pile { position: relative; text-align: center; min-width: 110px; }
.pile-name { font-weight: 800; margin-bottom: 8px; font-size: 15px; color: #101828; }
.pile-box { height: 92px; width: 110px; margin: 0 auto; border: 2px dashed #cfd8d3; border-radius: 16px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.72); position: relative; transition: .25s; }
.pile-box.busy { border-style: solid; border-color: rgba(5,150,105,.48); background: rgba(236,253,245,.82); }
.pile-box.queue { border-style: solid; border-color: rgba(37,99,235,.35); background: rgba(239,246,255,.82); }
.pile-box.fault { border-style: solid; border-color: rgba(239,68,68,.42); background: rgba(254,242,242,.86); }
.pile-box.shutdown { border-style: dashed; border-color: #cbd5e1; background: rgba(248,250,252,.78); }
.pile-box.mine { border-style: solid; border-color: rgba(79,70,229,.55); background: rgba(238,242,255,.9); }
.pile-box.mine.current { box-shadow: 0 0 0 5px rgba(79,70,229,.1), 0 18px 30px rgba(79,70,229,.14); }
.branch { position: absolute; left: 50%; top: 118px; width: 3px; height: 46px; transform: translateX(-50%); background: linear-gradient(180deg, #a7f3d0, #cbd5e1); border-radius: 999px; }
.branch::after { content: ""; position: absolute; left: -4px; bottom: -5px; width: 11px; height: 11px; border-radius: 50%; background: #fff; border: 2px solid #cbd5e1; }
.pile-box.busy + .branch { background: linear-gradient(180deg, #10b981, #a7f3d0); }
.charger { width: 36px; height: 58px; border-radius: 10px 10px 6px 6px; background: linear-gradient(180deg, #fff, #e5e7eb); border: 1px solid #cbd5e1; box-shadow: 0 12px 22px rgba(15,23,42,.1); position: relative; }
.charger::before { content: ""; position: absolute; left: 11px; top: 8px; width: 14px; height: 18px; border-radius: 3px; background: #0f766e; }
.charger::after { content: "⚡"; position: absolute; left: 11px; top: 32px; color: #059669; font-size: 14px; }
.queue-badge { position: absolute; top: -11px; right: -10px; width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; color: #fff; font-size: 13px; font-weight: 800; background: #2563eb; box-shadow: 0 8px 16px rgba(37,99,235,.24); }
.pile-status { margin-top: 60px; font-size: 13px; color: #667085; }
.pile-status::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #98a2b3; margin-right: 6px; }
.pile-status.busy::before { background: #059669; }
.pile-status.queue::before { background: #2563eb; }
.pile-status.mine::before { background: #4f46e5; }
.pile-status.fault::before { background: #ef4444; }
.pile-status.shutdown::before { background: #98a2b3; }
.car { position: absolute; width: 56px; height: 31px; left: 0; top: 0; transform: translate(-100px, 151px); opacity: 0; z-index: 8; animation: dispatchCar 13s cubic-bezier(.4,0,.2,1) infinite; animation-delay: var(--delay); }
.car-body { position: absolute; inset: 5px 2px; background: linear-gradient(180deg, #fff, #dbeafe); border: 1px solid #94a3b8; border-radius: 16px 16px 10px 10px; box-shadow: 0 8px 16px rgba(15,23,42,.16); }
.car.assigned .car-body { border-color: rgba(5,150,105,.72); box-shadow: 0 10px 22px rgba(5,150,105,.18); }
.car-window { position: absolute; left: 17px; top: 2px; width: 19px; height: 9px; background: #bfdbfe; border-radius: 6px 6px 3px 3px; }
.wheel { position: absolute; bottom: -3px; width: 8px; height: 8px; background: #475467; border-radius: 50%; }
.wheel.left { left: 10px; }
.wheel.right { right: 10px; }
/* WAIT NOTICE */
.wait-notice { display: flex; align-items: center; gap: 14px; padding: 14px 18px; border-radius: 14px; border: 1px solid #fde68a; background: linear-gradient(180deg, rgba(255,251,235,.98), rgba(255,253,243,.96)); margin-bottom: 14px; }
.wait-notice-icon { font-size: 22px; flex-shrink: 0; }
.wait-notice-title { font-size: 15px; font-weight: 800; color: #92400e; }
.wait-notice-sub { margin: 4px 0 0; font-size: 13px; color: #b45309; line-height: 1.5; }

/* CAR INSIDE PILE (QUEUED) */
.pile-waiting-car { position: absolute; bottom: 5px; left: 50%; transform: translateX(-50%); width: 30px; height: 14px; background: linear-gradient(180deg, #fff, #ede9fe); border: 1px solid rgba(79,70,229,.55); border-radius: 6px 6px 4px 4px; }
.pile-waiting-car::before { content: ""; position: absolute; left: 8px; top: 2px; width: 14px; height: 5px; background: rgba(79,70,229,.18); border-radius: 3px; }

/* JUNCTION CAR (QUEUED — static at intersection) */
.car.junction { animation: none !important; transform: translate(var(--target-x), 151px) !important; opacity: 1 !important; }
.car.junction .car-body { border-color: rgba(79,70,229,.72); box-shadow: 0 10px 22px rgba(79,70,229,.18); animation: junctionPulse 2.2s ease-in-out infinite; }
@keyframes junctionPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.65; } }

/* WAITING CAR (WAITING_AREA — horizontal only, no branch) */
.car.waiting { animation: waitCar 9s ease-in-out infinite !important; }
@keyframes waitCar {
  0%   { transform: translate(-86px, 151px); opacity: 0; }
  6%   { transform: translate(66px, 151px); opacity: 1; }
  80%  { transform: translate(1300px, 151px); opacity: 1; }
  90%  { opacity: 0; }
  100% { transform: translate(-86px, 151px); opacity: 0; }
}

@keyframes pulseMove { 0% { transform: translateX(0); opacity: 0; } 12% { opacity: .22; } 88% { opacity: .22; } 100% { transform: translateX(1240px); opacity: 0; } }
@keyframes dispatchCar {
  0%  { transform: translate(-86px, 151px); opacity: 0; }
  5%  { transform: translate(66px, 151px); opacity: 1; }
  42% { transform: translate(var(--target-x), 151px); opacity: 1; }
  58% { transform: translate(var(--target-x), 104px); opacity: 1; }
  72% { transform: translate(var(--target-x), 60px); opacity: 1; }
  86% { transform: translate(var(--target-x), 60px); opacity: 1; }
  100% { transform: translate(var(--target-x), 60px); opacity: 0; }
}

/* MAIN GRID */
.main-grid { display: grid; grid-template-columns: 1.06fr .94fr; gap: 16px; margin-bottom: 18px; }
.left-stack { display: grid; gap: 16px; align-content: start; }

/* PANELS */
.panel { border: 1px solid #e5e7eb; border-radius: 20px; background: rgba(255,255,255,.98); box-shadow: 0 12px 30px rgba(16,24,40,.05); overflow: hidden; }
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 15px 18px; border-bottom: 1px solid #eef2ef; }
.panel-title { margin: 0; font-size: 16px; font-weight: 850; line-height: 1.2; color: #101828; }
.panel-sub { margin-top: 5px; color: #667085; font-size: 12px; line-height: 1.55; }

/* DETAIL PANEL */
.detail-wrap { padding: 15px 18px 18px; }
.detail-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.detail-chip { padding: 12px 14px; border: 1px solid #edf2ef; border-radius: 14px; background: linear-gradient(180deg, #fff, #fbfcfb); }
.detail-chip span { display: block; color: #98a2b3; font-size: 12px; line-height: 1.4; }
.detail-chip strong { display: block; margin-top: 6px; font-size: 17px; font-weight: 800; line-height: 1.1; color: #101828; overflow-wrap: anywhere; }

.detail-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.detail-table tr + tr td { border-top: 1px solid #edf2ef; }
.detail-table td { padding: 12px 10px; vertical-align: top; }
.detail-table td:nth-child(odd) { color: #667085; width: 23%; }
.detail-table td:nth-child(even) { text-align: right; width: 27%; font-weight: 700; color: #101828; }

/* ACTIONS PANEL */
.actions-wrap { padding: 15px 18px 18px; }
.action-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }
.notice { color: #667085; font-size: 12px; line-height: 1.7; margin: 0; }

/* BUTTONS */
.btn { height: 42px; padding: 0 18px; border-radius: 12px; border: 1px solid transparent; display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; font-weight: 750; cursor: pointer; transition: .15s; text-decoration: none; }
.btn-primary { color: #fff; background: linear-gradient(135deg, #34d399, #059669); box-shadow: 0 10px 18px rgba(5,150,105,.14); }
.btn-primary:not(:disabled):hover { background: linear-gradient(135deg, #10b981, #047857); }
.btn-secondary { color: #344054; border-color: #e5e7eb; background: #fff; }
.btn-secondary:not(:disabled):hover { border-color: #10b981; color: #059669; }
.btn-danger { color: #f97316; border-color: #fde4d3; background: #fffaf6; }
.btn-danger:not(:disabled):hover { background: #fef2f2; border-color: #fca5a5; color: #ef4444; }
.btn:disabled { opacity: 0.35; cursor: not-allowed; }

.btn-refresh { padding: 6px 14px; border-radius: 8px; border: 1px solid #e5e7eb; background: #fff; font-size: 12px; font-weight: 600; color: #667085; cursor: pointer; transition: .15s; }
.btn-refresh:hover { border-color: #10b981; color: #059669; }

/* TIMELINE */
.timeline-wrap { padding: 14px 18px 18px; }
.timeline-scroll { max-height: 440px; overflow-y: auto; padding-right: 6px; scrollbar-width: thin; scrollbar-color: #cbd5e1 transparent; }
.timeline-scroll::-webkit-scrollbar { width: 6px; }
.timeline-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
.timeline-list { display: grid; position: relative; padding-left: 26px; }
.timeline-list::before { content: ""; position: absolute; left: 10px; top: 10px; bottom: 10px; width: 0; border-left: 2px dashed #d7dde6; pointer-events: none; }

.timeline-item { position: relative; display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: flex-start; padding: 14px 12px 14px 4px; border-top: 1px solid #edf2ef; border-radius: 14px; }
.timeline-item:first-child { border-top: 0; }
.timeline-item::before { content: ""; position: absolute; left: -18px; top: 18px; width: 10px; height: 10px; border-radius: 50%; background: #f0fdf4; border: 2px solid #d1d5db; }
.timeline-item.done::before { background: #d1fae5; border-color: #059669; box-shadow: 0 0 0 4px rgba(5,150,105,.08); }
.timeline-item.active::before { width: 14px; height: 14px; left: -20px; top: 16px; background: #10b981; border-color: #d1fae5; }
.timeline-item.danger::before { background: #fee2e2; border-color: #ef4444; box-shadow: 0 0 0 4px rgba(239,68,68,.08); }
.timeline-item.warning::before { background: #fef3c7; border-color: #f59e0b; box-shadow: 0 0 0 4px rgba(245,158,11,.08); }
.timeline-item.active { background: linear-gradient(180deg, rgba(236,253,245,.86), rgba(255,255,255,.98)); border: 1px solid #d9f0df; padding-left: 12px; }

.tl-main { min-width: 0; }
.tl-title { font-size: 14px; font-weight: 750; line-height: 1.35; color: #101828; }
.tl-sub { margin-top: 4px; color: #667085; font-size: 12px; line-height: 1.45; }
.tl-side { display: flex; align-items: center; padding-top: 2px; }

.tl-pill { display: inline-flex; align-items: center; padding: 4px 9px; border-radius: 999px; background: #ecfdf5; color: #059669; font-size: 11px; font-weight: 750; }
.tl-pill-done { background: #f0fdf4; color: #16a34a; }
.tl-pill-danger { background: #fef2f2; color: #ef4444; }
.tl-pill-warn { background: #fffbeb; color: #d97706; }

/* FOOTER BAND */
.footer-band { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.info-box { border: 1px solid #e5e7eb; border-radius: 18px; background: rgba(255,255,255,.98); box-shadow: 0 12px 30px rgba(16,24,40,.05); padding: 15px 18px; }
.info-box h3 { margin: 0 0 10px; font-size: 15px; font-weight: 850; line-height: 1.2; color: #101828; }
.info-list { display: grid; }
.info-row { display: flex; justify-content: space-between; gap: 12px; padding: 11px 0; border-top: 1px solid #edf2ef; color: #344054; font-size: 13px; line-height: 1.45; }
.info-row:first-child { border-top: 0; padding-top: 0; }
.info-row span { color: #667085; }
.info-row strong { color: #101828; font-weight: 700; }

/* RESPONSIVE */
@media (max-width: 1200px) {
  .main-grid { grid-template-columns: 1fr; }
  .footer-band { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 980px) {
  .status-row { grid-template-columns: 1.4fr repeat(3, 1fr); }
  .status-row .s-metric:last-child { display: none; }
}
@media (max-width: 640px) {
  .page { padding: 20px 16px; }
  .page-hero { flex-direction: column; align-items: flex-start; }
  .status-row { grid-template-columns: 1fr; gap: 0; }
  .s-metric { border-left: none; border-top: 1px solid #e5e7eb; justify-content: flex-start; padding: 12px 4px; }
  .detail-summary { grid-template-columns: 1fr; }
  .footer-band { grid-template-columns: 1fr; }
  .action-row { flex-direction: column; }
  .btn { justify-content: center; width: 100%; }
}
</style>