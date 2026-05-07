<template>
  <div class="page">
    <div class="page-head">
      <h1>工作台</h1>
      <p>提交充电请求，查看实时状态</p>
    </div>

    <!-- Stats -->
    <div class="stats">
      <div class="stat"><div class="stat-label green">当前状态</div><div class="stat-val">{{ hasActive ? statusText : '空闲' }}</div></div>
      <div class="stat"><div class="stat-label blue">排队号</div><div class="stat-val">{{ activeRequest?.queue_number || '--' }}</div></div>
      <div class="stat"><div class="stat-label amber">前车数量</div><div class="stat-val">{{ frontVehicleCountText }}</div></div>
      <div class="stat"><div class="stat-label gray">预计等待</div><div class="stat-val">{{ estWaitDisplay }}</div></div>
    </div>

    <div class="status-strip" :class="hasActive ? 'active' : 'idle'">
      <div>
        <div class="strip-kicker">{{ hasActive ? '当前进度' : '当前可提交' }}</div>
        <div class="strip-title">{{ statusHeadline }}</div>
        <div class="strip-sub">{{ statusSubline }}</div>
      </div>
      <router-link v-if="hasActive" to="/user/task" class="strip-action">查看详情</router-link>
    </div>

    <!-- Form + Current Status -->
    <div class="grid-2">
      <div class="card">
        <div class="card-head"><h3>提交充电请求</h3><span class="card-tag">POST /api/request/create</span></div>
        <div class="card-body">
          <div class="form-grid">
            <div class="field">
              <label>充电模式</label>
              <select v-model="form.charge_mode" :disabled="hasActive || syncingActive">
                <option value="FAST">快充 (30kW)</option>
                <option value="SLOW">慢充 (10kW)</option>
              </select>
            </div>
            <div class="field">
              <label>请求电量 (kWh)</label>
              <input type="number" v-model.number="form.request_energy" placeholder="1 ~ 电池容量" :disabled="hasActive || syncingActive" min="1">
            </div>
          </div>
          <button class="btn btn-primary" @click="submitRequest" :disabled="hasActive || syncingActive || submitting">
            {{ hasActive ? '当前有进行中的请求' : syncingActive ? '同步中...' : submitting ? '提交中...' : '提交请求' }}
          </button>

          <!-- Error -->
          <div class="error-box" v-if="errMsg">{{ errMsg }}</div>

          <!-- Result -->
          <div class="result" v-if="submitResult">
            <div class="result-title">请求已提交</div>
            <div class="result-grid">
              <div class="r-item"><div class="rl">请求编号</div><div class="rv">{{ submitResult.request_id }}</div></div>
              <div class="r-item"><div class="rl">排队号</div><div class="rv">{{ submitResult.queue_number }}</div></div>
              <div class="r-item"><div class="rl">状态</div><div class="rv">{{ REQUEST_STATUS_TEXT[submitResult.request_status] || submitResult.request_status }}</div></div>
              <div class="r-item"><div class="rl">模式</div><div class="rv">{{ CHARGE_MODE_TEXT[submitResult.charge_mode] }}</div></div>
              <div class="r-item"><div class="rl">请求电量</div><div class="rv">{{ submitResult.request_energy }} kWh</div></div>
              <div class="r-item"><div class="rl">前车数量</div><div class="rv">{{ submitResult.front_waiting_count }} 辆</div></div>
            </div>
          </div>

          <div class="link-task" v-if="hasActive">
            <router-link to="/user/task">查看当前请求详情 →</router-link>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>充电流程</h3></div>
        <div class="card-body">
          <div class="flow-item"><div class="flow-num">1</div><div><div class="flow-text">提交充电请求</div><div class="flow-sub">选择快充/慢充，填写请求电量</div></div></div>
          <div class="flow-item"><div class="flow-num">2</div><div><div class="flow-text">等候区排队</div><div class="flow-sub">按提交时间排序，容量上限 20 辆</div></div></div>
          <div class="flow-item"><div class="flow-num">3</div><div><div class="flow-text">调度分配桩位</div><div class="flow-sub">最短完成时间策略自动分配</div></div></div>
          <div class="flow-item"><div class="flow-num">4</div><div><div class="flow-text">充电中</div><div class="flow-sub">到达桩队列首位后自动启动</div></div></div>
          <div class="flow-item"><div class="flow-num">5</div><div><div class="flow-text">完成 · 结算</div><div class="flow-sub">各时段电量×电价 + 服务费 = 总费用</div></div></div>
        </div>
      </div>
    </div>

    <!-- Price -->
    <div class="card" style="margin-bottom:16px;">
      <div class="card-head"><h3>电价时段</h3></div>
      <div class="card-body">
        <div class="price-grid">
          <div class="price-row"><div class="price-dot" style="background:#ef4444;"></div><div class="price-info"><div class="price-name">峰时</div><div class="price-time">10:00–15:00, 18:00–21:00</div></div><div class="price-val">¥1.0/kWh</div></div>
          <div class="price-row"><div class="price-dot" style="background:#f59e0b;"></div><div class="price-info"><div class="price-name">平时</div><div class="price-time">07:00–10:00, 15:00–18:00, 21:00–23:00</div></div><div class="price-val">¥0.7/kWh</div></div>
          <div class="price-row"><div class="price-dot" style="background:#3b82f6;"></div><div class="price-info"><div class="price-name">谷时</div><div class="price-time">23:00–07:00</div></div><div class="price-val">¥0.4/kWh</div></div>
          <div class="price-row"><div class="price-dot" style="background:#10b981;"></div><div class="price-info"><div class="price-name">服务费</div><div class="price-time">全时段固定费率</div></div><div class="price-val">¥0.8/kWh</div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createChargeRequest, getActiveRequest, getProfile } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { REQUEST_STATUS, REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT, ACTIVE_STATUSES } from '@/constants/enums'
import { clearLegacyLocalState } from '@/utils/authSession'

const form = ref({ charge_mode: 'FAST', request_energy: null })
const submitting = ref(false)
const errMsg = ref('')
const submitResult = ref(null)
const currentReq = ref(null)
const batteryCapacity = ref(null)
const syncingActive = ref(false)
let pollTimer = null

const hasActive = computed(() => {
  if (!currentReq.value) return false
  return ACTIVE_STATUSES.includes(currentReq.value.request_status)
})

const activeRequest = computed(() => hasActive.value ? currentReq.value : null)

const statusText = computed(() => {
  if (!activeRequest.value) return '空闲'
  return REQUEST_STATUS_TEXT[activeRequest.value.request_status] || activeRequest.value.request_status
})

const estWaitDisplay = computed(() => {
  if (!activeRequest.value?.estimated_wait_seconds) return '--'
  const m = Math.ceil(activeRequest.value.estimated_wait_seconds / 60)
  return `~${m} min`
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
  return `预计开始 ${fmtDateTime(request.estimated_start_time)}，预计等待 ${estWaitDisplay.value}`
})

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

async function loadProfile() {
  try {
    const res = await getProfile()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return
    batteryCapacity.value = Number(data.battery_capacity)
  } catch (_) { /* silent */ }
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
  }
}

async function submitRequest() {
  errMsg.value = ''
  submitResult.value = null

  if (!form.value.request_energy || form.value.request_energy <= 0) {
    errMsg.value = '请求电量必须大于 0'
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
  const synced = await loadActiveRequest()
  if (!synced) stopPoll()
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
  pollStatus()
  startPoll()
})

onUnmounted(() => { stopPoll() })
</script>

<style scoped>
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

.result { margin-top: 16px; padding: 16px; border-radius: 10px; background: #ecfdf5; border: 1px solid #d1fae5; }
.result-title { font-size: 12px; font-weight: 600; color: #059669; margin-bottom: 12px; }
.result-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.r-item { padding: 10px 12px; border-radius: 8px; background: white; border: 1px solid #d1fae5; }
.r-item .rl { font-size: 10px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; }
.r-item .rv { font-size: 15px; font-weight: 700; color: #111827; margin-top: 2px; }

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

@media (max-width: 980px) {
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .grid-2 { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .page { padding: 20px 16px; }
  .stats { grid-template-columns: 1fr; gap: 10px; }
  .stat { padding: 14px 16px; }
  .stat-val { font-size: 22px; }
  .status-strip { align-items: stretch; flex-direction: column; }
  .strip-action { text-align: center; }
  .form-grid { grid-template-columns: 1fr; }
  .result-grid { grid-template-columns: 1fr; }
  .price-row { align-items: flex-start; gap: 8px; }
  .price-val { white-space: nowrap; }
}
</style>
