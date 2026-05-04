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
      <div class="stat"><div class="stat-label amber">前车数量</div><div class="stat-val">{{ activeRequest?.front_waiting_count ?? '--' }}</div></div>
      <div class="stat"><div class="stat-label gray">预计等待</div><div class="stat-val">{{ estWaitDisplay }}</div></div>
    </div>

    <!-- Form + Current Status -->
    <div class="grid-2">
      <div class="card">
        <div class="card-head"><h3>提交充电请求</h3><span class="card-tag">POST /api/request/create</span></div>
        <div class="card-body">
          <div class="form-grid">
            <div class="field">
              <label>充电模式</label>
              <select v-model="form.charge_mode" :disabled="hasActive || activeConflict">
                <option value="FAST">快充 (30kW)</option>
                <option value="SLOW">慢充 (10kW)</option>
              </select>
            </div>
            <div class="field">
              <label>请求电量 (kWh)</label>
              <input type="number" v-model.number="form.request_energy" placeholder="1 ~ 电池容量" :disabled="hasActive || activeConflict" min="1">
            </div>
          </div>
          <button class="btn btn-primary" @click="submitRequest" :disabled="hasActive || activeConflict || submitting">
            {{ hasActive || activeConflict ? '当前有进行中的请求' : submitting ? '提交中...' : '提交请求' }}
          </button>

          <!-- Error -->
          <div class="error-box" v-if="errMsg">{{ errMsg }}</div>
          <div class="link-task" v-if="activeConflict">
            <router-link to="/user/task">前往当前请求页查看状态</router-link>
          </div>

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
import { createChargeRequest, getProfile, getRequestStatus } from '@/api/charging'
import { REQUEST_STATUS, REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT, ACTIVE_STATUSES } from '@/constants/enums'

const form = ref({ charge_mode: 'FAST', request_energy: null })
const submitting = ref(false)
const errMsg = ref('')
const submitResult = ref(null)
const currentReq = ref(null)
const batteryCapacity = ref(null)
const activeConflict = ref(localStorage.getItem('active_request_conflict') === '1')
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

async function loadProfile() {
  try {
    const res = await getProfile()
    const data = res.data || res
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

function rememberActiveConflict() {
  activeConflict.value = true
  localStorage.setItem('active_request_conflict', '1')
}

function clearActiveConflict() {
  activeConflict.value = false
  localStorage.removeItem('active_request_conflict')
}

function rememberRequestId(requestId) {
  if (!requestId) return
  let ids = []
  try {
    const stored = JSON.parse(localStorage.getItem('request_ids') || '[]')
    if (Array.isArray(stored)) ids = stored
  } catch (_) { /* ignore broken local data */ }
  localStorage.setItem('request_ids', JSON.stringify([...new Set([requestId, ...ids])]))
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
    const data = res.data || res
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
    localStorage.setItem('request_id', data.request_id)
    rememberRequestId(data.request_id)
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
      rememberActiveConflict()
      errMsg.value = '当前用户已有活跃请求，但本地缺少请求编号，无法直接展示详情。请进入当前请求页查看提示，或由管理员结束该请求后重试。'
    }
    else errMsg.value = msg || e?.message || '提交失败'
  } finally {
    submitting.value = false
  }
}

async function pollStatus() {
  const rid = localStorage.getItem('request_id')
  if (!rid) return
  try {
    const res = await getRequestStatus(rid)
    const data = res.data || res
    if (data.code !== undefined && data.code !== 0) {
      if (data.code === 1002) {
        localStorage.removeItem('request_id')
        currentReq.value = null
      }
      return
    }
    clearActiveConflict()
    currentReq.value = data
    if (!ACTIVE_STATUSES.includes(data.request_status)) {
      currentReq.value = null
      stopPoll()
    }
  } catch (_) { /* silent */ }
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
  const rid = localStorage.getItem('request_id')
  if (rid) {
    pollStatus()
    startPoll()
  }
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
</style>
