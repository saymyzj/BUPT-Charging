<template>
  <div class="wrap">
    <!-- Hero -->
    <section class="hero">
      <div>
        <h1>账户中心</h1>
        <p>管理个人信息、资产与偏好设置</p>
      </div>
    </section>

    <!-- Account Overview Panel -->
    <section class="panel account-overview">
      <!-- Profile Block -->
      <div class="profile-block">
        <div class="profile-avatar">
          <div class="profile-face" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 12a4.2 4.2 0 1 0 0-8.4 4.2 4.2 0 0 0 0 8.4Zm0 2c-4.1 0-7.5 2.5-8 5.8-.1.7.5 1.2 1.1 1.2h13.8c.7 0 1.2-.6 1.1-1.2-.5-3.3-3.9-5.8-8-5.8Z"/></svg>
          </div>
        </div>
        <div class="profile-info">
          <div class="profile-name">
            <strong>{{ profile.username || '--' }}</strong>
            <span class="tag">{{ profile.role === 'ADMIN' ? '管理员' : '普通用户' }}</span>
          </div>
          <div class="profile-meta">
            <div><span>用户编号</span><span class="mono">{{ profile.user_id || '--' }}</span></div>
            <div><span>注册时间</span><span class="mono">{{ fmtDateTime(profile.created_at) }}</span></div>
            <div v-if="profile.role !== 'ADMIN'">
              <span>电池容量</span>
              <span class="cap-display">
                <span class="mono">{{ capacityText }}</span>
                <button v-if="!isEditingCapacity" class="edit-icon-btn" @click="startCapacityEdit" title="修改容量">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"/></svg>
                </button>
              </span>
            </div>
          </div>
          <template v-if="profile.role !== 'ADMIN' && isEditingCapacity">
            <div class="capacity-inline">
              <input type="number" v-model.number="capacityForm" min="1" placeholder="新容量 (kWh)" @keyup.enter="saveCapacity" @keyup.escape="cancelCapacityEdit">
              <button :disabled="capacitySaving" @click="saveCapacity" class="cap-save-btn">{{ capacitySaving ? '保存中' : '确认' }}</button>
              <button @click="cancelCapacityEdit" class="cap-cancel-btn">取消</button>
            </div>
            <div v-if="capacityMsg" class="capacity-msg">{{ capacityMsg }}</div>
          </template>
        </div>
      </div>

      <!-- 累计消费 -->
      <div class="summary-card">
        <div class="summary-head">
          <div class="summary-icon" style="background:#fffbeb;color:#f97316">
            <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2.3"><circle cx="12" cy="12" r="8"/><path d="M12 7v10M9 9.2c.7-.8 2.2-1.1 3.4-.7 1.3.4 2 1.3 1.8 2.3-.2 1.2-1.2 1.7-2.6 1.9-1.6.2-2.5.7-2.6 1.8-.1 1.1 1 2 2.8 2 1.2 0 2.3-.4 3-1.1"/></svg>
          </div>
          <div>
            <div class="summary-label">累计消费</div>
            <div class="summary-value mono">{{ fmtMoney(totalSpent) }}</div>
          </div>
        </div>
        <div v-if="sparklineData.length" class="spark-chart">
          <div class="spark-y-axis">
            <span>{{ spendAxisLabels.max }}</span>
            <span>0</span>
          </div>
          <div class="spark-body">
            <svg class="sparkline" viewBox="0 0 180 42" preserveAspectRatio="none">
              <line x1="0" y1="14" x2="180" y2="14" stroke="#f0f2f4" stroke-width="1" vector-effect="non-scaling-stroke"/>
              <line x1="0" y1="28" x2="180" y2="28" stroke="#f0f2f4" stroke-width="1" vector-effect="non-scaling-stroke"/>
              <path :d="spendSparkline.area" fill="#f97316" opacity=".11"/>
              <path :d="spendSparkline.line" fill="none" stroke="#f97316" stroke-width="2.4" vector-effect="non-scaling-stroke"/>
            </svg>
            <div class="spark-x-axis">
              <span>{{ spendAxisLabels.startDate }}</span>
              <span>{{ spendAxisLabels.endDate }}</span>
            </div>
          </div>
        </div>
        <div class="summary-note">含服务费 {{ fmtMoney(totalServiceFee) }}</div>
      </div>

      <!-- 累计充电量 -->
      <div class="summary-card">
        <div class="summary-head">
          <div class="summary-icon" style="background:#eff6ff;color:#2563eb">
            <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2.3"><path d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z"/></svg>
          </div>
          <div>
            <div class="summary-label">累计充电量</div>
            <div class="summary-value mono">{{ totalEnergy.toFixed(2) }} <span class="unit">kWh</span></div>
          </div>
        </div>
        <div v-if="sparklineData.length" class="spark-chart">
          <div class="spark-y-axis">
            <span>{{ energyAxisLabels.max }}</span>
            <span>0</span>
          </div>
          <div class="spark-body">
            <svg class="sparkline" viewBox="0 0 180 42" preserveAspectRatio="none">
              <line x1="0" y1="14" x2="180" y2="14" stroke="#f0f2f4" stroke-width="1" vector-effect="non-scaling-stroke"/>
              <line x1="0" y1="28" x2="180" y2="28" stroke="#f0f2f4" stroke-width="1" vector-effect="non-scaling-stroke"/>
              <path :d="energySparkline.area" fill="#2563eb" opacity=".11"/>
              <path :d="energySparkline.line" fill="none" stroke="#2563eb" stroke-width="2.4" vector-effect="non-scaling-stroke"/>
            </svg>
            <div class="spark-x-axis">
              <span>{{ energyAxisLabels.startDate }}</span>
              <span>{{ energyAxisLabels.endDate }}</span>
            </div>
          </div>
        </div>
        <div class="summary-note">共 {{ paidBills.length }} 次完成</div>
      </div>

      <!-- 账单总览 -->
      <div class="summary-card">
        <div class="summary-head">
          <div class="summary-icon" style="background:#ecfdf5;color:#059669">
            <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2.3"><path d="M4 6h16v12H4z"/><path d="M4 10h16"/><path d="M8 14h2"/><path d="M12 14h4"/></svg>
          </div>
          <div>
            <div class="summary-label">账单总览</div>
            <div class="summary-value mono">{{ bills.length }} <span class="unit">笔</span></div>
          </div>
        </div>
        <div class="bill-stats">
          <div class="bill-stat-col">
            <span class="bsc-num">{{ paidBills.length }}</span>
            <span class="bsc-label">已完成</span>
          </div>
          <div class="bill-stat-divider"></div>
          <div class="bill-stat-col">
            <span class="bsc-num" :class="{ 'bsc-warn': unpaidBills.length > 0 }">{{ unpaidBills.length }}</span>
            <span class="bsc-label">待支付</span>
          </div>
        </div>
        <div class="summary-note" :class="{ 'note-warn': unpaidBills.length > 0 }">
          {{ unpaidBills.length > 0 ? `待支付金额 ${fmtMoney(totalUnpaid)}` : '无待支付账单' }}
        </div>
      </div>
    </section>

    <!-- Ledger -->
    <section class="panel ledger">
      <div class="ledger-head">
        <div>
          <h2>账户流水</h2>
          <p>记录您的历史充电消费账单</p>
        </div>
        <router-link class="link-green" to="/user/bills">查看账单详情 →</router-link>
      </div>

      <div class="filters">
        <button class="filter" :class="{ active: activeFilter === 'all' }" @click="activeFilter = 'all'">全部</button>
        <button class="filter" :class="{ active: activeFilter === 'unpaid' }" @click="activeFilter = 'unpaid'">待支付</button>
        <button class="filter" :class="{ active: activeFilter === 'paid' }" @click="activeFilter = 'paid'">已支付</button>
      </div>

      <div class="table-wrap">
        <div v-if="billsLoading" class="table-empty">加载中…</div>
        <div v-else-if="!filteredBills.length" class="table-empty">暂无记录</div>
        <div v-else class="table-scroll">
          <table>
            <tbody>
              <tr v-for="bill in filteredBills" :key="bill.request_id">
                <td class="td-icon">
                  <span class="type-icon" :class="isPaid(bill) ? 'paid' : 'unpaid'">
                    <span class="material-icons">{{ isPaid(bill) ? 'check_circle' : 'payments' }}</span>
                  </span>
                </td>
                <td class="mono td-time">{{ fmtDateTime(bill.detail_generated_at || bill.stop_time) }}</td>
                <td>
                  <div class="entry-title">充电消费</div>
                  <div class="entry-sub">{{ bill.station_code || '--' }} · {{ requestResultText(bill) }}</div>
                </td>
                <td class="amount" :class="isPaid(bill) ? '' : 'amount-unpaid'">{{ fmtMoney(bill.total_fee) }}</td>
                <td class="mono order-td">请求 {{ bill.request_id || '—' }}</td>
                <td class="td-detail">
                  <button class="detail-link" @click="router.push({ path: '/user/bills', query: { id: bill.request_id } })">详情 ›</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="!billsLoading && bills.length > 0" class="ledger-foot">共 {{ bills.length }} 条记录</div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile, getRequestDetails, updateProfileBatteryCapacity } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { REQUEST_STATUS_TEXT } from '@/constants/enums'

const profile = ref({})
const loading = ref(false)
const bills = ref([])
const billsLoading = ref(false)
const capacityForm = ref(null)
const capacitySaving = ref(false)
const capacityMsg = ref('')
const isEditingCapacity = ref(false)
const router = useRouter()
const activeFilter = ref('all')

const capacityText = computed(() => {
  if (profile.value.role === 'ADMIN') return '不适用'
  return profile.value.battery_capacity == null ? '--' : `${profile.value.battery_capacity} kWh`
})

const paidBills = computed(() => bills.value.filter(b => isPaid(b)))
const unpaidBills = computed(() => bills.value.filter(b => !isPaid(b)))
const totalSpent = computed(() => bills.value.reduce((s, b) => s + Number(b.total_fee || 0), 0))
const totalServiceFee = computed(() => bills.value.reduce((s, b) => s + Number(b.service_fee || 0), 0))
const totalEnergy = computed(() => bills.value.reduce((s, b) => s + Number(b.actual_energy || 0), 0))
const totalUnpaid = computed(() => unpaidBills.value.reduce((s, b) => s + Number(b.total_fee || 0), 0))

const sparklineData = computed(() => {
  return [...bills.value]
    .sort((a, b) => {
      const at = new Date(a.detail_generated_at || a.stop_time || 0).getTime()
      const bt = new Date(b.detail_generated_at || b.stop_time || 0).getTime()
      return at - bt
    })
    .map(b => ({ fee: Number(b.total_fee || 0), energy: Number(b.actual_energy || 0), date: b.detail_generated_at || b.stop_time }))
})

function buildSparklinePath(values, width = 180, height = 42) {
  if (!values.length) return { line: '', area: '' }
  if (values.length === 1) {
    const y = Math.round(height * 0.45)
    return {
      line: `M0 ${y} L${width} ${y}`,
      area: `M0 ${height} L0 ${y} L${width} ${y} L${width} ${height}Z`
    }
  }
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1
  const pad = 4
  const pts = values.map((v, i) => ({
    x: Math.round((i / (values.length - 1)) * width),
    y: Math.round(height - pad - ((v - min) / range) * (height - pad * 2))
  }))
  let d = `M${pts[0].x} ${pts[0].y}`
  for (let i = 1; i < pts.length; i++) {
    const p = pts[i - 1]
    const c = pts[i]
    const mx = Math.round((p.x + c.x) / 2)
    d += ` C${mx} ${p.y} ${mx} ${c.y} ${c.x} ${c.y}`
  }
  const area = `M0 ${height} L${pts[0].x} ${pts[0].y}${d.substring(d.indexOf(' C'))} L${pts[pts.length - 1].x} ${height}Z`
  return { line: d, area }
}

const spendSparkline = computed(() => buildSparklinePath(sparklineData.value.map(d => d.fee)))
const energySparkline = computed(() => buildSparklinePath(sparklineData.value.map(d => d.energy)))

function fmtShortDate(t) {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const spendAxisLabels = computed(() => {
  const data = sparklineData.value
  if (!data.length) return { max: '', startDate: '', endDate: '' }
  const max = Math.max(...data.map(d => d.fee))
  return {
    max: `¥${max.toFixed(0)}`,
    startDate: fmtShortDate(data[0].date),
    endDate: fmtShortDate(data[data.length - 1].date)
  }
})

const energyAxisLabels = computed(() => {
  const data = sparklineData.value
  if (!data.length) return { max: '', startDate: '', endDate: '' }
  const max = Math.max(...data.map(d => d.energy))
  return {
    max: `${max.toFixed(1)}kWh`,
    startDate: fmtShortDate(data[0].date),
    endDate: fmtShortDate(data[data.length - 1].date)
  }
})

const filteredBills = computed(() => {
  if (activeFilter.value === 'paid') return paidBills.value
  if (activeFilter.value === 'unpaid') return unpaidBills.value
  return bills.value
})

function fmtDateTime(t) {
  if (!t) return '--'
  try {
    return new Date(t).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch { return t }
}

function fmtKwh(value) {
  const n = Number(value)
  return Number.isFinite(n) ? `${n.toFixed(2)} kWh` : '--'
}

function fmtMoney(value) {
  const n = Number(value)
  return Number.isFinite(n) ? `¥${n.toFixed(2)}` : '--'
}

function requestResultText(bill) {
  const status = bill.termination_status || bill.request_status
  return REQUEST_STATUS_TEXT[status] || status || '--'
}

function isPaid(bill) {
  if (bill.payment_status === 'PAID') return true
  return false
}

async function loadProfile() {
  loading.value = true
  try {
    const res = await getProfile()
    const data = unwrapResponseData(res)
    if (data.code === undefined || data.code === 0) {
      profile.value = data
      capacityForm.value = data.battery_capacity
    }
  } catch (_) { /* silent */ }
  loading.value = false
}

async function loadBills() {
  billsLoading.value = true
  try {
    const res = await getRequestDetails()
    const data = unwrapResponseData(res)
    bills.value = Array.isArray(data) ? data : []
  } catch (_) {
    bills.value = []
  }
  bills.value = bills.value.sort((a, b) => {
    const at = new Date(a.detail_generated_at || a.stop_time || 0).getTime()
    const bt = new Date(b.detail_generated_at || b.stop_time || 0).getTime()
    return bt - at
  })
  billsLoading.value = false
}

function startCapacityEdit() {
  capacityMsg.value = ''
  capacityForm.value = profile.value.battery_capacity
  isEditingCapacity.value = true
}

function cancelCapacityEdit() {
  capacityMsg.value = ''
  capacityForm.value = profile.value.battery_capacity
  isEditingCapacity.value = false
}

async function saveCapacity() {
  capacityMsg.value = ''
  const value = Number(capacityForm.value)
  if (!Number.isFinite(value) || value <= 0) {
    capacityMsg.value = '电池容量必须大于 0'
    return
  }
  capacitySaving.value = true
  try {
    const res = await updateProfileBatteryCapacity({ battery_capacity: value })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      capacityMsg.value = data.message || '修改失败'
      return
    }
    profile.value.battery_capacity = data.battery_capacity
    capacityMsg.value = '已保存'
    isEditingCapacity.value = false
  } catch (e) {
    capacityMsg.value = e?.response?.data?.message || '修改失败'
  } finally {
    capacitySaving.value = false
  }
}

onMounted(async () => {
  await loadProfile()
  await loadBills()
})
</script>

<style scoped>
* { box-sizing: border-box; }
.mono { font-family: "SF Mono", "Cascadia Mono", Consolas, monospace; }

.wrap {
  max-width: 1540px;
  margin: 0 auto;
  padding: 24px 30px 40px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  color: #101828;
}

.hero { margin-bottom: 16px; }
.hero h1 { margin: 0; font-size: 28px; font-weight: 850; line-height: 1.15; }
.hero p { margin: 8px 0 0; color: #667085; font-size: 14px; }

.panel {
  background: rgba(255,255,255,.96);
  border: 1px solid #edf2ef;
  border-radius: 20px;
  box-shadow: 0 14px 34px rgba(16,24,40,.06);
}

/* Account Overview */
.account-overview {
  display: grid;
  grid-template-columns: 1.45fr repeat(3, 1fr);
  min-height: 250px;
  overflow: hidden;
}

/* Profile Block */
.profile-block {
  display: flex;
  align-items: flex-start;
  gap: 22px;
  padding: 24px;
  border-right: 1px solid #edf2ef;
}
.profile-avatar {
  position: relative;
  width: 104px; height: 104px;
  border-radius: 50%;
  display: grid; place-items: center;
  background: rgba(16,185,129,.1);
  flex: 0 0 auto;
}
.profile-avatar::after {
  content: "";
  position: absolute; right: 12px; bottom: 12px;
  width: 12px; height: 12px; border-radius: 999px;
  background: #10b981; border: 3px solid #fff;
}
.profile-face {
  width: 84px; height: 84px; border-radius: 50%;
  color: #fff;
  background: radial-gradient(circle at 34% 28%, #34d399, #047857);
  display: grid; place-items: center;
  box-shadow: 0 16px 32px rgba(5,150,105,.18);
}
.profile-face svg { width: 58px; height: 58px; fill: currentColor; }
.profile-info { flex: 1; min-width: 0; }
.profile-name { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
.profile-name strong { font-size: 19px; font-weight: 850; }
.tag {
  display: inline-flex; align-items: center;
  height: 24px; padding: 0 8px; border-radius: 7px;
  color: #059669; background: #ecfdf5; border: 1px solid #d4f7e8;
  font-size: 12px; font-weight: 800; white-space: nowrap;
}
.profile-meta { display: grid; gap: 12px; color: #344054; font-size: 13px; margin-bottom: 14px; }
.profile-meta div { display: grid; grid-template-columns: 70px 1fr; gap: 10px; align-items: center; }
.profile-meta span:first-child { color: #667085; }
.cap-display { display: inline-flex; align-items: center; gap: 6px; }
.edit-icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 5px; border: 1px solid #e5e7eb;
  background: #f9fafb; color: #6b7280; cursor: pointer; padding: 0; flex-shrink: 0;
  transition: .12s;
}
.edit-icon-btn svg { width: 12px; height: 12px; }
.edit-icon-btn:hover { background: #f3f4f6; border-color: #d1d5db; color: #374151; }

.capacity-inline {
  display: grid; grid-template-columns: 1fr auto auto; gap: 6px; margin-top: 12px;
}
.capacity-inline input {
  padding: 7px 10px; border: 1px solid #e5e7eb; border-radius: 8px;
  font-size: 13px; outline: none; min-width: 0; font-family: inherit;
}
.capacity-inline input:focus { border-color: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,.1); }
.cap-save-btn {
  padding: 7px 12px; border: none; border-radius: 8px;
  background: #10b981; color: #fff; font-size: 13px; font-weight: 700;
  cursor: pointer; white-space: nowrap; font-family: inherit;
}
.cap-save-btn:disabled { opacity: .5; cursor: not-allowed; }
.cap-cancel-btn {
  padding: 7px 10px; border: 1px solid #e5e7eb; border-radius: 8px;
  background: #fff; color: #6b7280; font-size: 13px; font-weight: 600;
  cursor: pointer; font-family: inherit;
}
.capacity-msg { margin-top: 6px; font-size: 12px; color: #059669; }

/* Summary Cards */
.summary-card {
  padding: 24px 22px;
  border-right: 1px solid #edf2ef;
  display: flex; flex-direction: column; justify-content: space-between;
  min-width: 0;
}
.summary-card:last-child { border-right: 0; }
.summary-head { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }
.summary-icon {
  width: 48px; height: 48px; border-radius: 50%;
  display: grid; place-items: center; flex: 0 0 auto;
}
.summary-icon svg { width: 22px; height: 22px; }
.summary-label { color: #667085; font-size: 13px; font-weight: 750; margin-bottom: 4px; }
.summary-value { font-size: 22px; font-weight: 850; white-space: nowrap; }
.summary-value .unit { font-size: 13px; font-weight: 600; color: #667085; }
.summary-note { color: #667085; font-size: 12px; }
.spark-chart { display: flex; gap: 6px; margin-top: 10px; }
.spark-y-axis {
  display: flex; flex-direction: column; justify-content: space-between;
  font-size: 10px; color: #98a2b3; white-space: nowrap; padding-bottom: 16px;
  font-family: "SF Mono", Consolas, monospace;
}
.spark-body { flex: 1; min-width: 0; }
.sparkline { width: 100%; height: 42px; display: block; }
.spark-x-axis {
  display: flex; justify-content: space-between;
  font-size: 10px; color: #98a2b3; margin-top: 4px;
  font-family: "SF Mono", Consolas, monospace;
}
.note-warn { color: #b45309; font-weight: 700; }
.bill-stats {
  display: flex; align-items: center; gap: 0;
  margin-bottom: 16px;
  background: #f9fafb; border-radius: 10px; overflow: hidden;
}
.bill-stat-col {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  padding: 12px 8px; gap: 4px;
}
.bill-stat-divider { width: 1px; height: 40px; background: #e5e7eb; flex-shrink: 0; }
.bsc-num { font-size: 20px; font-weight: 850; color: #101828; }
.bsc-warn { color: #d97706; }
.bsc-label { font-size: 11px; color: #9ca3af; font-weight: 600; }
.red { color: #ef4444; }
.green { color: #059669; }

/* Ledger */
.ledger { margin-top: 18px; padding: 24px; }
.ledger-head {
  display: flex; justify-content: space-between;
  align-items: flex-start; gap: 20px; margin-bottom: 22px;
}
.ledger h2 { margin: 0; font-size: 22px; font-weight: 850; line-height: 1.2; }
.ledger p { margin: 8px 0 0; color: #667085; font-size: 14px; }
.link-green { display: inline-flex; align-items: center; gap: 7px; color: #059669; font-size: 13px; font-weight: 850; text-decoration: none; white-space: nowrap; }
.link-green:hover { text-decoration: underline; }

.filters { display: flex; gap: 12px; margin-bottom: 18px; }
.filter {
  height: 38px; padding: 0 18px;
  border: 1px solid #e5e7eb; border-radius: 10px;
  color: #475467; background: #f9fafb;
  font-size: 13px; font-weight: 750; cursor: pointer;
  font-family: inherit;
}
.filter.active { color: #059669; background: #ecfdf5; border-color: #a7f3d0; }

.table-wrap { border: 1px solid #e5e7eb; border-radius: 16px; overflow: hidden; background: #fff; }
.table-empty { padding: 40px; text-align: center; color: #9ca3af; font-size: 14px; }
.table-scroll { max-height: 580px; overflow-y: auto; }
.table-scroll::-webkit-scrollbar { width: 10px; }
.table-scroll::-webkit-scrollbar-thumb { background: #98a2b3; border-radius: 999px; border: 3px solid #fff; }

table { width: 100%; min-width: 860px; border-collapse: collapse; font-size: 14px; }
tr { border-bottom: 1px solid #edf2ef; }
tr:last-child { border-bottom: 0; }
td { padding: 18px 14px; vertical-align: middle; color: #344054; }
tr:hover { background: #fbfdfc; }

.td-icon { width: 46px; }
.type-icon {
  width: 28px; height: 28px; border-radius: 50%;
  display: grid; place-items: center;
  margin-left: 4px;
}
.type-icon .material-icons { font-size: 18px; }
.type-icon.paid { background: #ecfdf5; color: #059669; border: 2px solid #a7f3d0; }
.type-icon.unpaid { background: #fffbeb; color: #d97706; border: 2px solid #fde68a; }
.td-time { color: #475467; font-size: 13px; white-space: nowrap; width: 200px; }
.entry-title { font-weight: 850; color: #243047; }
.entry-sub { margin-top: 4px; color: #667085; font-size: 13px; }
.amount { font-weight: 850; white-space: nowrap; text-align: right; font-variant-numeric: tabular-nums; color: #101828; }
.amount-unpaid { color: #d97706; }
.order-td { color: #475467; white-space: nowrap; }
.td-detail { text-align: right; padding-right: 20px; }
.detail-link { background: none; border: none; cursor: pointer; color: #344054; font-size: 14px; font-weight: 800; padding: 0; font-family: inherit; }
.detail-link:hover { color: #059669; }

.pay-badge { display: inline-flex; align-items: center; border-radius: 999px; padding: 3px 10px; background: #fffbeb; color: #b45309; font-size: 12px; font-weight: 700; }
.pay-badge.paid { background: #ecfdf5; color: #047857; }
.ledger-foot { text-align: center; color: #98a2b3; font-size: 13px; font-weight: 700; padding-top: 16px; }

@media (max-width: 1100px) {
  .account-overview { grid-template-columns: 1fr 1fr; }
  .profile-block { grid-column: 1 / -1; border-right: none; border-bottom: 1px solid #edf2ef; }
  .summary-card { border-right: none; border-bottom: 1px solid #edf2ef; }
}
</style>
