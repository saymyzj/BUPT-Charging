<template>
  <div class="page">
    <div class="page-head">
      <h1>当前请求</h1>
      <p>实时追踪充电进度，管理排队中的请求</p>
    </div>

    <!-- No Active Request -->
    <div class="empty-card" v-if="!req">
      <div class="empty-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
      </div>
      <div class="empty-title">暂无进行中的请求</div>
      <div class="empty-sub">前往工作台提交充电请求</div>
      <router-link to="/user/workspace" class="btn btn-primary" style="width:auto;padding:10px 24px;">前往工作台</router-link>
    </div>

    <template v-if="req">
      <!-- Status Banner -->
      <div class="status-banner" :class="bannerClass">
        <div class="sb-left">
          <div class="sb-icon"><svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div>
            <div class="sb-title">{{ statusText }}</div>
            <div class="sb-sub">{{ bannerSub }}</div>
          </div>
        </div>
        <span class="badge" :class="badgeClass">{{ req.request_status }}</span>
      </div>

      <!-- Key Metrics -->
      <div class="card full">
        <div class="card-head"><h3>关键指标</h3><button class="btn-refresh" @click="refresh">刷新</button></div>
        <div class="card-body">
          <div class="metrics">
            <div class="metric"><div class="m-label">排队号</div><div class="m-val">{{ req.queue_number || '--' }}</div></div>
            <div class="metric"><div class="m-label">前车数量</div><div class="m-val">{{ req.front_waiting_count ?? '--' }}</div></div>
            <div class="metric"><div class="m-label">预计等待</div><div class="m-val">{{ estWait }}</div></div>
            <div class="metric"><div class="m-label">已充电量</div><div class="m-val">{{ chargedEnergyText }}</div></div>
            <div class="metric"><div class="m-label">预计开始</div><div class="m-val">{{ fmtTime(req.estimated_start_time) }}</div></div>
          </div>
        </div>
      </div>

      <!-- Detail + Timeline -->
      <div class="grid-2">
        <div class="card">
          <div class="card-head"><h3>请求详情</h3></div>
          <div class="card-body" style="padding:0;">
            <div class="detail-list">
              <div class="dl-item"><span class="dl-key">请求编号</span><span class="dl-val">{{ req.request_id }}</span></div>
              <div class="dl-item"><span class="dl-key">充电模式</span><span class="dl-val">{{ CHARGE_MODE_TEXT[req.charge_mode] || req.charge_mode }}</span></div>
              <div class="dl-item"><span class="dl-key">请求电量</span><span class="dl-val">{{ req.request_energy }} kWh</span></div>
              <div class="dl-item"><span class="dl-key">已充电量</span><span class="dl-val">{{ chargedEnergyText }}</span></div>
              <div class="dl-item"><span class="dl-key">分配桩位</span><span class="dl-val">{{ req.station_code || '待分配' }}</span></div>
              <div class="dl-item"><span class="dl-key">桩队列位置</span><span class="dl-val">{{ req.station_queue_position ?? '--' }}</span></div>
              <div class="dl-item"><span class="dl-key">预计完成</span><span class="dl-val">{{ fmtTime(req.estimated_finish_time) }}</span></div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head"><h3>进度时间线</h3></div>
          <div class="card-body">
            <div class="timeline">
              <div class="tl-item" :class="tlClass(0)"><div class="tl-dot"></div><div><div class="tl-text">请求已提交</div></div></div>
              <div class="tl-item" :class="tlClass(1)"><div class="tl-dot"></div><div><div class="tl-text">等候区排队</div></div></div>
              <div class="tl-item" :class="tlClass(2)"><div class="tl-dot"></div><div><div class="tl-text">分配到桩队列</div></div></div>
              <div class="tl-item" :class="tlClass(3)"><div class="tl-dot"></div><div><div class="tl-text">充电中</div></div></div>
              <div class="tl-item" :class="tlClass(4)"><div class="tl-dot"></div><div><div class="tl-text">{{ terminalLabel }}</div></div></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="card full">
        <div class="card-head"><h3>可用操作</h3></div>
        <div class="card-body">
          <div class="actions">
            <button class="btn btn-secondary" :disabled="!canEditMode" @click="editMode">修改充电模式</button>
            <button class="btn btn-secondary" :disabled="!canEditEnergy" @click="editEnergy">修改充电量</button>
            <button class="btn btn-danger" :disabled="!canCancel" @click="cancelReq">取消请求</button>
            <button class="btn btn-primary" :disabled="!canStop" @click="stopReq">提前结束充电</button>
            <router-link v-if="canViewDetail" :to="`/user/bills`" class="btn btn-secondary" style="text-decoration:none;text-align:center;">查看详单</router-link>
          </div>
          <p class="actions-note">注: 修改充电模式会回到等候区重新排队。提前结束仅在桩队列或充电中状态可用。</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getActiveRequest, getProfile, getRequestStatus, updateChargeMode, updateRequestEnergy, cancelRequest, stopRequest } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { REQUEST_STATUS, REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT, ACTIVE_STATUSES, HAS_DETAIL_STATUSES } from '@/constants/enums'

const req = ref(null)
const batteryCapacity = ref(null)
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
  if (s === REQUEST_STATUS.WAITING_AREA) return `排队号 ${req.value.queue_number} · 前方 ${req.value.front_waiting_count ?? 0} 辆车`
  if (s === REQUEST_STATUS.QUEUED) return `分配至 ${req.value.station_code} · 队列第 ${req.value.station_queue_position ?? '?'} 位`
  if (s === REQUEST_STATUS.CHARGING) return `${req.value.station_code} 充电中`
  if (s === REQUEST_STATUS.COMPLETED) return '充电已正常完成'
  if (s === REQUEST_STATUS.COMPLETED_EARLY) return '充电已提前结束'
  if (s === REQUEST_STATUS.CANCELLED) return '请求已取消'
  if (s === REQUEST_STATUS.FAULT_INTERRUPTED) return '因故障中断'
  return ''
})

const estWait = computed(() => {
  if (!req.value?.estimated_wait_seconds) return '--'
  return `~${Math.ceil(req.value.estimated_wait_seconds / 60)} min`
})

const chargedEnergyText = computed(() => {
  const value = req.value?.charged_energy ?? req.value?.actual_energy
  const n = Number(value)
  return Number.isFinite(n) ? `${n.toFixed(2)} kWh` : '--'
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
  await syncActiveRequest()
}

async function syncActiveRequest(clearWhenNone = true) {
  try {
    const res = await getActiveRequest()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) return false
    if (data.request_id && ACTIVE_STATUSES.includes(data.request_status)) {
      localStorage.removeItem('request_id')
      localStorage.removeItem('active_request_conflict')
      req.value = data
      return true
    }
    localStorage.removeItem('request_id')
    localStorage.removeItem('active_request_conflict')
    if (clearWhenNone) req.value = null
    return false
  } catch (_) {
    return false
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

async function editMode() {
  const newMode = req.value.charge_mode === 'FAST' ? 'SLOW' : 'FAST'
  if (!confirm(`切换为 ${CHARGE_MODE_TEXT[newMode]}？将回到等候区重新排队。`)) return
  try {
    const res = await updateChargeMode({ request_id: req.value.request_id, charge_mode: newMode })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '修改失败'); return }
    await refresh()
  } catch (e) { alert(e?.response?.data?.message || '修改失败') }
}

async function editEnergy() {
  const val = prompt('输入新电量 (kWh):', req.value.request_energy)
  if (!val) return
  const num = parseFloat(val)
  if (!num || num <= 0) { alert('电量必须大于 0'); return }
  if (batteryCapacity.value && num > batteryCapacity.value) {
    alert(`请求电量不能超过电池容量 ${batteryCapacity.value} kWh`)
    return
  }
  try {
    const res = await updateRequestEnergy({ request_id: req.value.request_id, request_energy: num })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '修改失败'); return }
    await refresh()
  } catch (e) { alert(e?.response?.data?.message || '修改失败') }
}

async function cancelReq() {
  if (!confirm('确认取消当前请求？')) return
  try {
    const res = await cancelRequest({ request_id: req.value.request_id })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '取消失败'); return }
    await refresh()
  } catch (e) { alert(e?.response?.data?.message || '取消失败') }
}

async function stopReq() {
  if (!confirm('确认提前结束充电？将按已充电量结算。')) return
  try {
    const res = await stopRequest({
      request_id: req.value.request_id,
      stop_time: formatLocalDateTime()
    })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '操作失败'); return }
    await refresh()
  } catch (e) { alert(e?.response?.data?.message || '操作失败') }
}

function startPoll() { stopPoll(); pollTimer = setInterval(refresh, 5000) }
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }

onMounted(() => { loadProfile(); refresh(); startPoll() })
onUnmounted(() => { stopPoll() })
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 28px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }

/* EMPTY */
.empty-card { text-align: center; padding: 60px 20px; background: white; border: 1px solid #e5e7eb; border-radius: 12px; }
.empty-icon { margin-bottom: 16px; }
.empty-title { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 6px; }
.empty-sub { font-size: 13px; color: #9ca3af; margin-bottom: 20px; }

/* STATUS BANNER */
.status-banner { padding: 20px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.banner-amber { background: #fffbeb; border: 1px solid #fde68a; }
.banner-blue { background: #eff6ff; border: 1px solid #bfdbfe; }
.banner-green { background: #ecfdf5; border: 1px solid #d1fae5; }
.banner-gray { background: #f9fafb; border: 1px solid #e5e7eb; }
.sb-left { display: flex; align-items: center; gap: 16px; }
.sb-icon { width: 48px; height: 48px; border-radius: 12px; background: #10b981; display: flex; align-items: center; justify-content: center; }
.banner-amber .sb-icon { background: #f59e0b; }
.banner-blue .sb-icon { background: #3b82f6; }
.banner-gray .sb-icon { background: #9ca3af; }
.sb-title { font-size: 16px; font-weight: 700; color: #111827; }
.sb-sub { font-size: 13px; color: #6b7280; margin-top: 2px; }

.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.badge::before { content:""; width: 6px; height: 6px; border-radius: 50%; }
.badge-amber { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.badge-amber::before { background: #f59e0b; }
.badge-green { background: #ecfdf5; color: #059669; border: 1px solid #d1fae5; }
.badge-green::before { background: #10b981; }
.badge-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-blue::before { background: #3b82f6; }
.badge-gray { background: #f9fafb; color: #9ca3af; border: 1px solid #e5e7eb; }
.badge-gray::before { background: #9ca3af; }

.full { margin-bottom: 16px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; transition: 0.2s; }
.card:hover { border-color: #d1d5db; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.card-head { padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-body { padding: 20px; }

.btn-refresh { padding: 5px 12px; border-radius: 6px; border: 1px solid #e5e7eb; background: white; font-size: 11px; font-weight: 600; color: #6b7280; cursor: pointer; transition: 0.12s; }
.btn-refresh:hover { border-color: #10b981; color: #059669; }

.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.metric { padding: 16px; border-radius: 10px; background: #f8faf9; border: 1px solid #e5e7eb; }
.m-label { font-size: 11px; color: #9ca3af; font-weight: 500; text-transform: uppercase; letter-spacing: 0.3px; }
.m-val { font-size: 20px; font-weight: 700; color: #111827; margin-top: 6px; letter-spacing: -0.3px; }

/* DETAIL LIST */
.detail-list { display: grid; grid-template-columns: 1fr 1fr; }
.dl-item { display: flex; justify-content: space-between; padding: 13px 20px; border-bottom: 1px solid #e5e7eb; }
.dl-item:nth-child(odd) { border-right: 1px solid #e5e7eb; }
.dl-key { font-size: 13px; color: #6b7280; }
.dl-val { font-size: 13px; font-weight: 600; color: #111827; }

/* TIMELINE */
.timeline { display: flex; flex-direction: column; }
.tl-item { display: flex; gap: 14px; padding: 14px 0; border-bottom: 1px solid #e5e7eb; }
.tl-item:last-child { border-bottom: none; }
.tl-dot { width: 10px; height: 10px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; border: 2px solid #10b981; background: white; }
.tl-item.done .tl-dot { background: #10b981; }
.tl-item.active .tl-dot { background: #10b981; box-shadow: 0 0 0 4px #d1fae5; }
.tl-text { font-size: 13px; font-weight: 500; color: #1f2937; }

/* ACTIONS */
.actions { display: flex; gap: 10px; flex-wrap: wrap; }
.btn { padding: 10px 20px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.15s; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #10b981; color: white; }
.btn-primary:hover:not(:disabled) { background: #059669; }
.btn-secondary { background: transparent; border: 1px solid #e5e7eb; color: #6b7280; }
.btn-secondary:hover:not(:disabled) { border-color: #10b981; color: #059669; }
.btn-danger { background: transparent; border: 1px solid #fecaca; color: #ef4444; }
.btn-danger:hover:not(:disabled) { background: #fef2f2; }
.btn:disabled { opacity: 0.35; cursor: not-allowed; }
.actions-note { font-size: 12px; color: #9ca3af; margin-top: 12px; }
</style>
