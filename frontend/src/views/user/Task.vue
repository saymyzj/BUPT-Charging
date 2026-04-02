<template>
  <div class="user-task-wrapper">
    <!-- Top Nav -->
    <nav class="nav">
      <div class="nav-brand">⚡ 智能充电桩调度计费系统</div>
      <div class="nav-tabs">
        <router-link to="/user/workspace" class="nav-tab">工作台</router-link>
        <router-link to="/user/task" class="nav-tab active">当前任务</router-link>
        <router-link to="/user/account" class="nav-tab">账户中心</router-link>
      </div>
      <div class="nav-right">
        <span>🔔 通知<span class="badge">3</span></span>
        <span>用户: 张三</span>
        <span class="logout">退出</span>
      </div>
    </nav>

    <div class="container">
      <!-- TIMELINE PANEL -->
      <div class="timeline-panel">
        <h3>任务时间线</h3>

        <!-- State 0: 排队等待 -->
        <div class="tl-item" :class="{selected: currentState === 0}" @click="selectState(0)">
          <div class="tl-track">
            <div class="tl-dot done"></div>
            <div class="tl-line done"></div>
          </div>
          <div class="tl-content">
            <div class="tl-title">排队等待</div>
            <div class="tl-time">{{ hasActiveTask ? (reqData.submit_time ? formatTime(reqData.submit_time) + ' 入队' : '等待获取时间...') : '未排队' }}</div>
            <div class="tl-desc">
              排队位置: <strong>{{ queuePositionText }}</strong><br>
              预计等待: <strong>{{ queueWaitDisplay }}</strong><br>
              分配桩号: {{ hasActiveTask ? (reqData.station_id || '预分配中...') : '暂无' }}
            </div>
            <div class="tl-badge waiting">等待中</div>
          </div>
        </div>

        <!-- State 1: 叫号确认 -->
        <div class="tl-item" :class="{selected: currentState === 1}" @click="selectState(1)">
          <div class="tl-track">
            <div class="tl-dot done"></div>
            <div class="tl-line done"></div>
          </div>
          <div class="tl-content">
            <div class="tl-title">叫号确认</div>
            <div class="tl-time" v-if="reqData.last_called_time">{{ formatTime(reqData.last_called_time) }} 叫号</div>
            <div class="tl-time" v-else>待进行</div>
            <div class="tl-desc">
              <span v-if="backendState < 2">确认倒计时: <strong>{{ callTimeFormatted }}</strong><br></span>
              <span v-else>状态: <strong>已确认</strong><br></span>
              桩号: {{ reqData.station_id }}<br>
              位置: 请按导航指示前往
            </div>
            <div class="tl-badge called" v-if="backendState === 1">叫号中</div>
            <div class="tl-badge waiting" style="background:#eaf5ec;color:var(--primary)" v-else-if="backendState >= 2">已确认</div>
            <div class="tl-badge pending" v-else>待进行</div>
          </div>
        </div>

        <!-- State 2: 充电中 (CURRENT) -->
        <div class="tl-item" :class="{selected: currentState === 2}" @click="selectState(2)">
          <div class="tl-track">
            <div class="tl-dot current"></div>
            <div class="tl-line current"></div>
          </div>
          <div class="tl-content">
            <div class="tl-title">充电中</div>
            <div class="tl-time" v-if="reqData.charge_start_time">{{ formatTime(reqData.charge_start_time) }} 开始充电</div>
            <div class="tl-time" v-else>待进行</div>
            <div class="tl-desc">
              进度: <strong>{{ Math.round(chargePct) }}%</strong> (<span>{{ chargeKwh }}</span>/{{ reqData.request_energy || '..' }} kWh)<br>
              已充电: <strong>{{ chargeDurationFormatted }}</strong><br>
              实时费用: <strong>¥<span>{{ chargeFee }}</span></strong>
            </div>
            <div class="tl-badge charging">充电中</div>
          </div>
        </div>

        <!-- State 3: 完成结算 -->
        <div class="tl-item future-item" :class="{selected: currentState === 3}" @click="selectState(3)">
          <div class="tl-track">
            <div class="tl-dot future"></div>
            <div class="tl-line none"></div>
          </div>
          <div class="tl-content">
            <div class="tl-title">完成结算</div>
            <div class="tl-time">待进行</div>
            <div class="tl-desc">充电完成后将生成详单和账单</div>
            <div class="tl-badge pending">待进行</div>
          </div>
        </div>
      </div>

      <!-- DETAIL PANEL -->
      <div class="detail-panel">
        <!-- State 0 Detail -->
        <div class="detail-section" v-show="currentState === 0">
          <div class="detail-header"><h2>排队等待中</h2></div>
          <div class="card">
            <div class="card-title">排队状态</div>
            <div class="queue-center">
              <div class="queue-label">当前排队位置</div>
              <div class="queue-num">{{ queuePositionText }}</div>
            </div>
            <div class="countdown-box">
              <div>
                <div style="font-size:13px;color:var(--text2)">预计等待时间</div>
                <div class="countdown-time">{{ queueWaitDisplay }}</div>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
              <div class="info-row"><span class="info-label">请求编号</span><span class="info-value">{{ hasActiveTask ? (reqData.request_id || '暂无数据') : '未排队' }}</span></div>
              <div class="info-row"><span class="info-label">分配桩号</span><span class="info-value" style="color:var(--accent)">{{ hasActiveTask ? (reqData.station_id || '排队分配中') : '暂无' }}</span></div>
              <div class="info-row"><span class="info-label">预计排队等待</span><span class="info-value">{{ queueWaitDisplay }}</span></div>
            </div>
            <div class="info-tip">{{ hasActiveTask ? '系统正在为您智能调度最优充电桩，请耐心等待' : '当前无进行中的排队任务，请先在工作台提交充电请求' }}</div>
          </div>
          <div class="action-bar">
            <button v-if="hasActiveTask" class="btn btn-secondary" @click="showModal('cancelQueue')">取消排队</button>
          </div>
        </div>

        <!-- State 1 Detail -->
        <div class="detail-section" v-show="currentState === 1">
          <div class="detail-header"><h2>叫号确认</h2></div>
          <div class="call-banner">
            <h2>{{ backendState >= 2 ? '✅ 已确认到场' : '📣 您已被叫号！' }}</h2>
            <p style="color:var(--text2);margin-top:4px">{{ backendState >= 2 ? '车辆已就位，正在充电中' : '请在倒计时结束前确认到场' }}</p>
            <div class="call-ring" v-if="backendState < 2">
              <svg width="180" height="180" viewBox="0 0 180 180">
                <circle cx="90" cy="90" r="82" fill="none" stroke="#ece7de" stroke-width="8"/>
                <circle cx="90" cy="90" r="82" fill="none" stroke="var(--accent)" stroke-width="8" stroke-linecap="round" :stroke-dasharray="515" :stroke-dashoffset="callRingOffset" style="transform:rotate(-90deg);transform-origin:center; transition: stroke-dashoffset 1s linear;"/>
              </svg>
              <div class="call-ring-inner">{{ callTimeFormatted }}</div>
            </div>
            <div v-else style="margin: 30px 0;">
              <div style="font-size: 48px; color: var(--primary)">🔋</div>
            </div>
          </div>
          <div class="card">
            <div class="card-title">叫号信息</div>
            <div class="info-row"><span class="info-label">分配充电桩</span><span class="info-value">{{ reqData.station_id || '暂无' }}</span></div>
            <div class="info-row"><span class="info-label">位置描述</span><span class="info-value">A区 快充区域 1号桩</span></div>
              <div class="info-row"><span class="info-label">充电功率</span><span class="info-value">{{ reqData.charge_mode === 'FAST' ? '30 kW' : '7 kW' }}</span></div>
            <div class="call-warning" v-if="backendState < 2">超时未确认将记为未到场(NO_SHOW)，影响后续优先级</div>
          </div>
          <div class="action-bar" v-if="backendState < 2">
            <button class="btn btn-secondary btn-sm" @click="showModal('cancelQueue')">取消排队</button>
            <button class="btn btn-primary btn-lg" @click="handleConfirmArrivalClick">确认到场</button>
          </div>
          <div class="action-bar" v-else>
            <button class="btn btn-primary btn-lg" @click="syncToBackendState">查看充电进度</button>
          </div>
        </div>

        <!-- State 2 Detail (default current) -->
        <div class="detail-section" v-show="currentState === 2">
          <div class="detail-header"><h2>实时充电监控</h2></div>
          <div class="card">
            <div class="card-title">充电进度</div>
            <div class="charging-hero">
              <div class="progress-ring-wrap">
                <svg viewBox="0 0 220 220">
                  <circle class="ring-bg" cx="110" cy="110" r="96"/>
                  <circle class="ring-fill" cx="110" cy="110" r="96" :stroke-dasharray="603" :stroke-dashoffset="chargeRingOffset"/>
                </svg>
                <div class="ring-pct"><span>{{ Math.round(chargePct) }}</span><small>%</small></div>
              </div>
              <div style="font-size:15px;color:var(--text2)"><span style="font-weight:700;color:var(--primary);font-size:18px">{{ chargeKwh }}</span> / {{ reqData.request_energy || '..' }} kWh</div>
              <div class="bar-track"><div class="bar-fill" :style="{width: chargePct + '%'}"></div></div>
            </div>
            <div class="charging-stats">
              <div class="stat-box"><div class="stat-val">{{ chargeDurationFormatted }}</div><div class="stat-label">已充电时长</div></div>
              <div class="stat-box"><div class="stat-val">~{{ chargeRemainMins }}分钟</div><div class="stat-label">预计剩余</div></div>
              <div class="stat-box"><div class="stat-val">{{ reqData.charge_mode === 'FAST' ? '30 kW' : '7 kW' }}</div><div class="stat-label">输出功率</div></div>
              <div class="stat-box"><div class="stat-val" style="color:var(--accent)">¥<span>{{ chargeFee }}</span></div><div class="stat-label">实时费用</div></div>
            </div>
            <div class="info-tip">充电完成后系统将自动通知您移车</div>
          </div>
          <div class="action-bar">
            <button class="btn btn-secondary" @click="showModal('interrupt')">中断充电</button>
          </div>
        </div>

        <!-- State 3 Detail -->
        <div class="detail-section" v-show="currentState === 3">
          <div class="detail-header"><h2>充电完成 / 结算</h2></div>
          <div class="complete-banner">
            <div class="complete-icon">✓</div>
            <h2 style="color:var(--primary);font-size:22px">充电已完成！</h2>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
            <div class="card">
              <div class="card-title">充电详单</div>
                <table class="bill-table">
                <tr><th>请求编号</th><td>{{ reqData.request_id || '暂无' }}</td></tr>
                <tr><th>充电模式</th><td>{{ reqData.charge_mode === 'FAST' ? '快充' : '慢充' }}</td></tr>
                <tr><th>需求电量</th><td>{{ reqData.request_energy }} kWh</td></tr>
                <tr><th>实际电量</th><td>{{ chargeKwh }} kWh</td></tr>
                <tr><th>排队时间</th><td>{{ reqData.submit_time || '未知' }}</td></tr>
                <tr><th>叫号时间</th><td>{{ reqData.last_called_time || '未知' }}</td></tr>
                <tr><th>开始充电</th><td>{{ reqData.charge_start_time || '未知' }}</td></tr>
                <tr><th>充电桩</th><td>{{ reqData.station_id || '暂无' }}</td></tr>
                <tr><th>最终状态</th><td style="color:var(--primary);font-weight:700">{{ toZhStatus(reqData.status) }}</td></tr>
              </table>
            </div>
            <div class="card">
              <div class="card-title">费用账单</div>
              <table class="bill-table">
                <tr><th>计费模式</th><td>按电量</td></tr>
                <tr><th>计费电量</th><td>{{ billData?.bill?.billing_energy || chargeKwh }} kWh</td></tr>
                <tr><th>电费</th><td>¥{{ billData?.bill?.energy_fee || chargeFee }}</td></tr>
                <tr><th>时长费</th><td>¥{{ billData?.bill?.time_fee || '0.00' }}</td></tr>
                <tr><th>超时占位费</th><td>¥0.00</td></tr>
                <tr class="total"><th>合计</th><td>¥{{ billData?.bill?.total_fee || chargeFee }}</td></tr>
                <tr><th>支付状态</th><td style="color:var(--secondary)">{{ billData?.bill?.payment_status || '待支付' }}</td></tr>
              </table>
            </div>
          </div>
          <div class="action-bar">
            <button v-if="!billData" class="btn btn-outline" @click="handleConfirmLeaveClick">确认离场</button>
            <button v-else class="btn btn-primary btn-lg" @click="handlePayClick">立即支付</button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODALS -->
    <div class="modal-overlay" :class="{show: activeModal === 'cancelQueue'}" @click.self="hideModal">
      <div class="modal">
        <h3>确认取消排队？</h3>
        <p>取消后将退出当前排队队列，需要重新提交充电请求。</p>
        <div class="action-bar">
          <button class="btn btn-outline btn-sm" @click="hideModal">再想想</button>
          <button class="btn btn-secondary" @click="confirmCancelQueue">确认取消</button>
        </div>
      </div>
    </div>
    
    <div class="modal-overlay" :class="{show: activeModal === 'interrupt'}" @click.self="hideModal">
      <div class="modal">
        <h3>确认中断充电？</h3>
        <p>中断后将按实际充电量计费。当前已充电 {{ chargeKwh }} kWh，预计费用 ¥{{ chargeFee }}。</p>
        <div class="action-bar">
          <button class="btn btn-outline btn-sm" @click="hideModal">继续充电</button>
          <button class="btn btn-secondary" @click="confirmInterrupt">确认中断</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  cancelQueue,
  confirmArrival,
  confirmLeave,
  getRequestStatus,
  getResult,
  interruptCharge,
  payRequest
} from '@/api/charging'

const router = useRouter()

const currentState = ref(0)
const backendState = ref(0)
const manualSelectedState = ref(null)
const activeModal = ref(null)
const hasActiveTask = ref(false)
const currentReqId = ref('')
const reqData = ref({})
const billData = ref(null)

const CONFIRM_TIMEOUT_SECONDS = 180
const POLL_INTERVAL_MS = 3000

const waitSec = ref(0)
const callSec = ref(CONFIRM_TIMEOUT_SECONDS)
const chargePct = ref(0)
const chargeDurationSec = ref(0)

let pollingTimer = null
let uiTimer = null

const statusTextMap = {
  PENDING: '待调度',
  WAITING: '排队中',
  CALLED: '已叫号',
  CONFIRMED: '已确认',
  CHARGING: '充电中',
  COMPLETED: '已完成',
  COMPLETED_EARLY: '提前完成',
  INTERRUPTED: '已中断',
  CANCELLED: '已取消',
  NO_SHOW: '已过号',
  FAILED: '失败'
}

const backendMessageMap = {
  'Invalid parameters': '参数不合法',
  'Request not found': '未找到该充电请求',
  'Current status does not allow cancel': '当前状态不允许取消排队',
  'Request is not in CALLED status': '当前不在叫号状态，无法确认到场',
  'Request is not in CHARGING status': '当前不在充电中状态，无法中断充电',
  'Request is not in completed status': '当前还不能确认离场',
  'Charging station is not in WAITING_TO_LEAVE status': '充电桩当前还不能离场'
}

const toZhStatus = (status) => statusTextMap[status] || status || '未知状态'
const toZhBackendMessage = (message) => backendMessageMap[message] || message || ''

const toZhBackendErrorDetail = (errorText) => {
  if (!errorText) return ''
  return errorText
    .replace('Missing required field:', '缺少必填字段：')
    .replace('must be ISO 8601 format', '时间格式必须为 ISO 8601')
}

const getApiErrorMessage = (err, fallbackMessage) => {
  const backendMessage = toZhBackendMessage(err?.response?.data?.message)
  const backendErrors = err?.response?.data?.data?.errors
  if (Array.isArray(backendErrors) && backendErrors.length > 0) {
    return `${backendMessage || fallbackMessage}: ${backendErrors.map(toZhBackendErrorDetail).join('; ')}`
  }
  return backendMessage || fallbackMessage
}

const parseDate = (value) => {
  if (!value) return null
  const normalized = String(value).replace('Z', '+00:00')
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

const formatTime = (iso) => {
  const date = parseDate(iso)
  if (!date) return ''
  return [
    String(date.getHours()).padStart(2, '0'),
    String(date.getMinutes()).padStart(2, '0'),
    String(date.getSeconds()).padStart(2, '0')
  ].join(':')
}

const fmtMS = (seconds) => {
  if (!Number.isFinite(seconds) || seconds <= 0) return '00:00'
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`
}

const stageFromStatus = (status) => {
  if (['WAITING', 'PENDING', 'FAULT_REQUEUE'].includes(status)) return 0
  if (['CALLED', 'CONFIRMED'].includes(status)) return 1
  if (status === 'CHARGING') return 2
  if (['COMPLETED', 'COMPLETED_EARLY', 'INTERRUPTED'].includes(status)) return 3
  return 0
}

const isFinalStatus = (status) => ['COMPLETED', 'COMPLETED_EARLY', 'INTERRUPTED', 'CANCELLED', 'NO_SHOW'].includes(status)

const selectState = (idx) => {
  if (!hasActiveTask.value && idx > 0) {
    ElMessage.warning('当前暂无进行中的排队任务')
    return
  }
  if (idx > backendState.value) {
    ElMessage.warning('请先完成前一阶段，再进入下一阶段')
    return
  }
  manualSelectedState.value = idx
  currentState.value = idx
}

const syncToBackendState = () => {
  manualSelectedState.value = null
  currentState.value = backendState.value
}

const showModal = (id) => { activeModal.value = id }
const hideModal = () => { activeModal.value = null }

const persistTaskFlow = () => {
  if (!currentReqId.value || !hasActiveTask.value) return
  sessionStorage.setItem(`taskFlow_${currentReqId.value}`, JSON.stringify(reqData.value))
}

const clearSessionTask = () => {
  if (currentReqId.value) {
    sessionStorage.removeItem(`taskFlow_${currentReqId.value}`)
  }
  sessionStorage.removeItem('currentRequestID')
  localStorage.removeItem('currentRequestID')
}

const initNoTaskState = () => {
  hasActiveTask.value = false
  currentReqId.value = ''
  currentState.value = 0
  backendState.value = 0
  manualSelectedState.value = null
  billData.value = null
  waitSec.value = 0
  callSec.value = CONFIRM_TIMEOUT_SECONDS
  chargeDurationSec.value = 0
  chargePct.value = 0
  reqData.value = {
    status: 'NO_TASK',
    estimated_wait_seconds: 0,
    queue_position: null,
    submit_time: null,
    station_id: null,
    request_energy: 0,
    actual_energy: 0
  }
}

const applyBackendData = (data) => {
  if (!data) return
  hasActiveTask.value = true
  currentReqId.value = data.request_id || currentReqId.value

  const next = {
    ...reqData.value,
    ...data,
    queue_position: data.queue_position ?? reqData.value.queue_position ?? null,
    estimated_wait_seconds: Number(data.estimated_wait_seconds ?? reqData.value.estimated_wait_seconds ?? 0),
    request_energy: Number(data.request_energy ?? reqData.value.request_energy ?? 0),
    actual_energy: Number(data.actual_energy ?? reqData.value.actual_energy ?? 0)
  }

  reqData.value = next
  backendState.value = stageFromStatus(next.status)
  currentState.value = manualSelectedState.value ?? backendState.value
  persistTaskFlow()
}

const refreshDerivedState = () => {
  const now = Date.now()
  const submitAt = parseDate(reqData.value.submit_time)
  const calledAt = parseDate(reqData.value.last_called_time)
  const chargeStartAt = parseDate(reqData.value.charge_start_time || reqData.value.estimated_start_time)
  const finishAt = parseDate(reqData.value.estimated_finish_time || reqData.value.charge_end_time)

  if (backendState.value === 0) {
    if (finishAt && submitAt) {
      const estimateStart = parseDate(reqData.value.estimated_start_time)
      waitSec.value = estimateStart ? Math.max(0, Math.floor((estimateStart.getTime() - now) / 1000)) : Number(reqData.value.estimated_wait_seconds || 0)
    } else {
      waitSec.value = Number(reqData.value.estimated_wait_seconds || 0)
    }
  } else {
    waitSec.value = 0
  }

  if (backendState.value === 1 && calledAt) {
    callSec.value = Math.max(0, Math.floor((calledAt.getTime() + CONFIRM_TIMEOUT_SECONDS * 1000 - now) / 1000))
  } else {
    callSec.value = CONFIRM_TIMEOUT_SECONDS
  }

  if (backendState.value === 2 && chargeStartAt && finishAt && finishAt > chargeStartAt) {
    const totalSeconds = Math.max(1, Math.floor((finishAt.getTime() - chargeStartAt.getTime()) / 1000))
    const elapsedSeconds = Math.max(0, Math.floor((now - chargeStartAt.getTime()) / 1000))
    chargeDurationSec.value = Math.min(totalSeconds, elapsedSeconds)
    chargePct.value = Math.min(100, elapsedSeconds / totalSeconds * 100)
  } else if (backendState.value >= 3) {
    chargePct.value = 100
  } else {
    chargeDurationSec.value = 0
    chargePct.value = 0
  }
}

const fetchResultData = async () => {
  if (!currentReqId.value) return
  try {
    const res = await getResult(currentReqId.value)
    if (res && res.code === 0) {
      billData.value = res.data
    }
  } catch (err) {
    console.warn('获取详单/账单失败', err)
  }
}

const pollStatus = async () => {
  if (!currentReqId.value) return
  try {
    const res = await getRequestStatus(currentReqId.value)
    if (res && res.code === 0 && res.data) {
      applyBackendData(res.data)
      refreshDerivedState()
      if (isFinalStatus(res.data.status)) {
        await fetchResultData()
      }
    }
  } catch (err) {
    console.error('Failed to poll status', err)
  }
}

const initTaskFlowFromSession = async () => {
  const reqId = sessionStorage.getItem('currentRequestID') || localStorage.getItem('currentRequestID') || ''
  if (!reqId) {
    initNoTaskState()
    return
  }

  currentReqId.value = reqId
  const rawFlow = sessionStorage.getItem(`taskFlow_${reqId}`)
  const flow = rawFlow ? JSON.parse(rawFlow) : null

  if (flow) {
    hasActiveTask.value = true
    reqData.value = { ...reqData.value, ...flow }
    backendState.value = stageFromStatus(flow.status)
    currentState.value = backendState.value
    refreshDerivedState()
  }

  await pollStatus()
}

const confirmCancelQueue = async () => {
  hideModal()
  if (!['PENDING', 'WAITING', 'CALLED'].includes(reqData.value?.status)) {
    ElMessage.warning(`当前状态为 ${toZhStatus(reqData.value?.status)}，不能取消排队`)
    return
  }

  try {
    const now = new Date().toISOString().substring(0, 19)
    const res = await cancelQueue({ request_id: currentReqId.value, cancel_time: now })
    if (res && res.code === 0) {
      ElMessage.success('取消排队成功')
      clearSessionTask()
      initNoTaskState()
    } else {
      ElMessage.error(`取消失败: ${toZhBackendMessage(res?.message) || '请求未成功'}`)
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '取消失败'))
  }
}

const handleConfirmArrivalClick = async () => {
  if (backendState.value !== 1) {
    ElMessage.warning('当前未到叫号确认阶段')
    return
  }

  try {
    const now = new Date().toISOString().substring(0, 19)
    const res = await confirmArrival({ request_id: currentReqId.value, confirm_time: now })
    if (res && res.code === 0) {
      ElMessage.success('到场确认成功')
      await pollStatus()
    } else {
      ElMessage.error(`确认失败: ${toZhBackendMessage(res?.message) || '请求未成功'}`)
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '确认到场失败'))
  }
}

const confirmInterrupt = async () => {
  hideModal()
  if (backendState.value !== 2) {
    ElMessage.warning('当前未处于充电阶段，不能中断充电')
    return
  }

  try {
    const now = new Date().toISOString().substring(0, 19)
    const res = await interruptCharge({ request_id: currentReqId.value, interrupt_time: now })
    if (res && res.code === 0) {
      ElMessage.success('中断充电成功')
      await pollStatus()
      await fetchResultData()
    } else {
      ElMessage.error(`中断失败: ${toZhBackendMessage(res?.message) || '请求未成功'}`)
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '中断充电失败'))
  }
}

const handleConfirmLeaveClick = async () => {
  try {
    const now = new Date().toISOString().substring(0, 19)
    const res = await confirmLeave({ request_id: currentReqId.value, leave_time: now })
    if (res && res.code === 0) {
      ElMessage.success('确认离场成功')
      await fetchResultData()
      await pollStatus()
    } else {
      ElMessage.error(`确认离场失败: ${toZhBackendMessage(res?.message) || '请求未成功'}`)
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '确认离场失败'))
  }
}

const handlePayClick = async () => {
  const totalFee = Number(billData.value?.bill?.total_fee || 0)
  if (!currentReqId.value || !billData.value?.bill) {
    ElMessage.warning('账单尚未生成，暂不可支付')
    return
  }

  try {
    const now = new Date().toISOString().substring(0, 19)
    const res = await payRequest({ request_id: currentReqId.value, pay_time: now, pay_amount: totalFee })
    if (res && res.code === 0) {
      ElMessage.success('支付成功！欢迎下次使用。')
      clearSessionTask()
      initNoTaskState()
      router.push('/user/workspace')
    } else {
      ElMessage.error(`支付失败: ${toZhBackendMessage(res?.message) || '请求未成功'}`)
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '支付失败'))
  }
}

const waitTimeFormatted = computed(() => fmtMS(waitSec.value))
const callTimeFormatted = computed(() => fmtMS(callSec.value))
const callRingOffset = computed(() => 515 * (1 - callSec.value / CONFIRM_TIMEOUT_SECONDS))
const chargeDurationFormatted = computed(() => fmtMS(chargeDurationSec.value))

const queuePositionText = computed(() => {
  if (!hasActiveTask.value) return '未排队'
  if (backendState.value !== 0) return '已叫号'

  const queuePosition = reqData.value.queue_position
  if (typeof queuePosition === 'number') return `第${queuePosition}位`
  if (queuePosition && typeof queuePosition.position === 'number') return `第${queuePosition.position}位`
  return '等待更新'
})

const queueWaitDisplay = computed(() => (backendState.value === 0 ? waitTimeFormatted.value : '--:--'))

const chargeRemainMins = computed(() => {
  const finishAt = parseDate(reqData.value.estimated_finish_time || reqData.value.charge_end_time)
  if (!finishAt || backendState.value !== 2) return 0
  return Math.max(0, Math.ceil((finishAt.getTime() - Date.now()) / 60000))
})

const chargeKwh = computed(() => {
  if (billData.value?.detail?.charge_energy) return Number(billData.value.detail.charge_energy).toFixed(1)
  if (reqData.value.actual_energy) return Number(reqData.value.actual_energy).toFixed(1)
  const requestEnergy = Number(reqData.value.request_energy || 0)
  return (requestEnergy * (chargePct.value / 100)).toFixed(1)
})

const chargeFee = computed(() => {
  if (billData.value?.bill?.total_fee != null) return Number(billData.value.bill.total_fee).toFixed(2)
  return (Number(chargeKwh.value) * 1.5).toFixed(2)
})

const chargeRingOffset = computed(() => 603 * (1 - chargePct.value / 100))

onMounted(async () => {
  await initTaskFlowFromSession()
  pollingTimer = setInterval(pollStatus, POLL_INTERVAL_MS)
  uiTimer = setInterval(refreshDerivedState, 1000)
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
  if (uiTimer) clearInterval(uiTimer)
})
</script><style scoped>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.user-task-wrapper {
  --bg:#faf8f5;--card:#ffffff;--shadow:0 4px 12px rgba(120,80,40,0.08);
  --primary:#2d6a4f;--secondary:#c45d3e;--accent:#d4a853;
  --text:#2c2c2c;--text2:#7a7a7a;--nav-bg:#f5f0e8;
  --radius:10px;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);
  color:var(--text);
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}
h1,h2,h3,h4,h5{font-family:Georgia,serif}

/* NAV */
.nav{background:var(--nav-bg);border-bottom:3px solid var(--accent);display:flex;align-items:center;padding:0 32px;height:60px;position:sticky;top:0;z-index:100;width:100%}
.nav-brand{font-family:Georgia,serif;font-size:18px;font-weight:700;color:var(--primary);white-space:nowrap}
.nav-tabs{display:flex;gap:0;margin:0 auto}
.nav-tab{padding:18px 28px;font-size:15px;color:var(--text2);cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-3px;transition:all .2s;text-decoration:none}
.nav-tab:hover{color:var(--text)}
.nav-tab.active{color:var(--primary);border-bottom-color:var(--primary);font-weight:600}
.nav-right{display:flex;align-items:center;gap:20px;font-size:14px;color:var(--text2);white-space:nowrap}
.nav-right .badge{background:var(--secondary);color:#fff;border-radius:10px;padding:1px 7px;font-size:11px;margin-left:2px}
.nav-right .logout{color:var(--secondary);cursor:pointer;transition:opacity .2s}
.nav-right .logout:hover{opacity:.7}

/* LAYOUT */
.container{display:flex;flex:1;min-height:0;width:100%}

/* TIMELINE PANEL */
.timeline-panel{width:35%;min-width:360px;background:var(--card);border-right:1px solid #ece7de;padding:28px 24px;overflow-y:auto}
.timeline-panel h3{font-size:16px;color:var(--primary);margin-bottom:24px;padding-bottom:12px;border-bottom:1px solid #ece7de}

.tl-item{display:flex;gap:16px;cursor:pointer;padding:8px 12px;border-radius:var(--radius);transition:background .2s;margin-bottom:4px}
.tl-item:hover{background:#faf6ef}
.tl-item.selected{background:#f0f7f3}

.tl-track{display:flex;flex-direction:column;align-items:center;width:24px;flex-shrink:0;position:relative}
.tl-dot{width:16px;height:16px;border-radius:50%;border:3px solid #d0ccc4;background:#fff;z-index:2;flex-shrink:0;transition:all .3s}
.tl-dot.done{background:var(--primary);border-color:var(--primary)}
.tl-dot.current{background:var(--accent);border-color:var(--accent);box-shadow:0 0 0 4px rgba(212,168,83,.2);animation:tl-pulse 2s infinite}
.tl-dot.future{background:#fff;border-color:#d0ccc4}
@keyframes tl-pulse{0%,100%{box-shadow:0 0 0 4px rgba(212,168,83,.2)}50%{box-shadow:0 0 0 8px rgba(212,168,83,.1)}}
.tl-line{width:3px;flex:1;min-height:20px}
.tl-line.done{background:var(--primary)}
.tl-line.current{background:var(--accent)}
.tl-line.future{background:#d0ccc4;border-left:1.5px dashed #d0ccc4;width:0;margin-left:1.5px}
.tl-line.none{background:transparent}

.tl-content{flex:1;padding-bottom:20px}
.tl-title{font-family:Georgia,serif;font-size:15px;font-weight:700;color:var(--text);margin-bottom:4px}
.tl-item.future-item .tl-title{color:var(--text2)}
.tl-time{font-size:12px;color:var(--text2);margin-bottom:6px}
.tl-desc{font-size:13px;color:var(--text2);line-height:1.5}
.tl-desc strong{color:var(--text)}

.tl-badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;margin-top:6px}
.tl-badge.waiting{background:#fef3e2;color:var(--accent)}
.tl-badge.called{background:#fff3e0;color:#e67e22}
.tl-badge.charging{background:#e8f5e9;color:var(--primary)}
.tl-badge.completed{background:#e0f2f1;color:#00897b}
.tl-badge.pending{background:#f0ebe3;color:var(--text2)}

/* DETAIL PANEL */
.detail-panel{flex:1;padding:28px 36px;overflow-y:auto}
.detail-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.detail-header h2{font-size:22px;color:var(--primary)}

.card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:28px;margin-bottom:20px;animation:fadeIn .4s ease}
.card-title{font-family:Georgia,serif;font-size:17px;color:var(--primary);margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #ece7de}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

.info-row{display:flex;justify-content:space-between;padding:8px 0;font-size:14px;border-bottom:1px solid #f5f0e8}
.info-row:last-child{border-bottom:none}
.info-label{color:var(--text2)}
.info-value{font-weight:600;color:var(--text)}

.btn{padding:12px 28px;border:none;border-radius:var(--radius);font-size:15px;font-weight:600;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:8px}
.btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.1)}
.btn:active{transform:translateY(0)}
.btn-primary{background:var(--primary);color:#fff}
.btn-secondary{background:var(--secondary);color:#fff}
.btn-outline{background:transparent;border:2px solid var(--text2);color:var(--text2)}
.btn-lg{padding:16px 40px;font-size:17px}
.btn-sm{padding:8px 18px;font-size:13px}
.action-bar{display:flex;gap:12px;justify-content:flex-end;margin-top:24px}

/* QUEUE */
.queue-center{text-align:center;padding:24px}
.queue-num{font-family:Georgia,serif;font-size:80px;font-weight:700;color:var(--accent)}
.queue-label{color:var(--text2);font-size:14px;margin-top:4px}
.countdown-box{display:flex;align-items:center;justify-content:center;gap:12px;margin:16px 0;padding:16px;background:#fdf8ef;border-radius:var(--radius)}
.countdown-time{font-family:Georgia,serif;font-size:36px;font-weight:700;color:var(--accent)}
.info-tip{background:#f0f7f3;border-left:4px solid var(--primary);padding:12px 16px;border-radius:0 var(--radius) var(--radius) 0;font-size:13px;color:var(--primary);margin-top:16px}

/* CALL */
.call-banner{text-align:center;padding:28px;background:#fdf8ef;border:2px solid var(--accent);border-radius:var(--radius);margin-bottom:20px}
.call-banner h2{color:var(--accent);font-size:24px;margin-bottom:4px}
.call-ring{width:180px;height:180px;border-radius:50%;position:relative;margin:20px auto;display:flex;align-items:center;justify-content:center}
.call-ring svg{position:absolute;top:0;left:0;transform:rotate(-90deg)}
.call-ring-inner{font-family:Georgia,serif;font-size:40px;font-weight:700;color:var(--accent);z-index:2}
.call-warning{background:#fef0ec;border-left:4px solid var(--secondary);padding:12px 16px;border-radius:0 var(--radius) var(--radius) 0;font-size:13px;color:var(--secondary);margin-top:16px}

/* CHARGING */
.charging-hero{text-align:center;padding:16px}
.progress-ring-wrap{position:relative;width:220px;height:220px;margin:0 auto 20px}
.progress-ring-wrap svg{width:220px;height:220px}
.ring-bg{fill:none;stroke:#ece7de;stroke-width:14}
.ring-fill{fill:none;stroke:var(--primary);stroke-width:14;stroke-linecap:round;transition:stroke-dashoffset 1s ease;transform:rotate(-90deg);transform-origin:center}
.ring-pct{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-family:Georgia,serif;font-size:48px;font-weight:700;color:var(--primary)}
.ring-pct small{font-size:20px;font-weight:400}
.charging-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}
.stat-box{background:#f8f5ef;border-radius:var(--radius);padding:16px 12px;text-align:center}
.stat-val{font-family:Georgia,serif;font-size:22px;font-weight:700;color:var(--primary)}
.stat-label{font-size:11px;color:var(--text2);margin-top:4px}
.bar-track{width:100%;height:14px;background:#ece7de;border-radius:7px;overflow:hidden;margin:10px 0}
.bar-fill{height:100%;background:var(--primary);border-radius:7px;transition:width 1s ease;position:relative}
.bar-fill::after{content:'';position:absolute;right:0;top:0;bottom:0;width:30px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.5));animation:shine 2s infinite}
@keyframes shine{0%,100%{opacity:0}50%{opacity:1}}

/* COMPLETED */
.complete-banner{text-align:center;padding:20px;margin-bottom:16px}
.complete-icon{width:72px;height:72px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:36px;color:#fff}
.bill-table{width:100%;border-collapse:collapse;margin-top:8px}
.bill-table th,.bill-table td{padding:10px 16px;text-align:left;font-size:14px;border-bottom:1px solid #f0ebe3}
.bill-table th{color:var(--text2);font-weight:500;width:40%}
.bill-table td{font-weight:600}
.bill-table tr.total td,.bill-table tr.total th{font-size:17px;color:var(--primary);border-top:2px solid var(--primary);font-weight:700}

/* MODAL */
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.4);z-index:200;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:var(--card);border-radius:var(--radius);padding:32px;max-width:420px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,.15)}
.modal h3{font-family:Georgia,serif;color:var(--text);margin-bottom:12px}
.modal p{color:var(--text2);font-size:14px;margin-bottom:24px;line-height:1.6}
.modal .action-bar{margin-top:0}
</style>
