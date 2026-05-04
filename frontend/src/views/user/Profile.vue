<template>
  <div class="page">
    <div class="page-head">
      <h1>账户中心</h1>
      <p>查看当前登录用户信息和账单记录</p>
    </div>

    <div class="card">
      <div class="card-head"><h3>基本信息</h3></div>
      <div class="card-body">
        <div v-if="loading" class="empty">加载中...</div>
        <div v-else class="profile-grid">
          <div class="profile-item">
            <span class="label">用户编号</span>
            <span class="value">{{ profile.user_id || '--' }}</span>
          </div>
          <div class="profile-item">
            <span class="label">用户名</span>
            <span class="value">{{ profile.username || username }}</span>
          </div>
          <div class="profile-item">
            <span class="label">角色</span>
            <span class="value">{{ profile.role || role }}</span>
          </div>
          <div class="profile-item">
            <span class="label">电池容量</span>
            <span class="value">{{ capacityText }}</span>
          </div>
          <div class="profile-item">
            <span class="label">注册时间</span>
            <span class="value">{{ fmtDateTime(profile.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card bills-card">
      <div class="card-head">
        <h3>我的账单</h3>
        <span class="hint">当前浏览器已记录的请求</span>
      </div>
      <div class="card-body">
        <div v-if="billsLoading" class="empty">账单加载中...</div>
        <div v-else-if="!bills.length" class="empty">暂无账单记录</div>
        <div v-else class="table-wrap">
          <table class="bills-table">
            <thead>
              <tr>
                <th>详单编号</th>
                <th>请求编号</th>
                <th>充电桩</th>
                <th>实际电量</th>
                <th>总费用</th>
                <th>请求结果</th>
                <th>支付状态</th>
                <th>生成时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="bill in bills" :key="bill.request_id">
                <td>{{ bill.detail_id || '--' }}</td>
                <td>{{ bill.request_id }}</td>
                <td>{{ bill.station_code || '--' }}</td>
                <td>{{ fmtKwh(bill.actual_energy) }}</td>
                <td class="amount">{{ fmtMoney(bill.total_fee) }}</td>
                <td>{{ requestResultText(bill) }}</td>
                <td>
                  <span class="pay-badge" :class="{ paid: isPaid(bill) }">
                    {{ isPaid(bill) ? '已支付' : '待支付' }}
                  </span>
                </td>
                <td>{{ fmtDateTime(bill.detail_generated_at || bill.stop_time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getProfile, getRequestDetail } from '@/api/charging'
import { REQUEST_STATUS_TEXT } from '@/constants/enums'

const profile = ref({})
const loading = ref(false)
const bills = ref([])
const billsLoading = ref(false)
const username = localStorage.getItem('username') || 'user'
const role = localStorage.getItem('user_role') || 'USER'

const capacityText = computed(() => {
  if ((profile.value.role || role) === 'ADMIN') return '不适用'
  return profile.value.battery_capacity == null ? '--' : `${profile.value.battery_capacity} kWh`
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

function paidStorageKey(bill) {
  const id = bill.detail_id || bill.request_id
  return id ? `bill_paid_${id}` : ''
}

function isPaid(bill) {
  if (bill.payment_status === 'PAID') return true
  const key = paidStorageKey(bill)
  return Boolean(key && localStorage.getItem(key))
}

function rememberedRequestIds() {
  const ids = []
  try {
    const stored = JSON.parse(localStorage.getItem('request_ids') || '[]')
    if (Array.isArray(stored)) ids.push(...stored)
  } catch (_) { /* ignore broken local data */ }
  const current = localStorage.getItem('request_id')
  if (current) ids.push(current)
  return [...new Set(ids.filter(Boolean))]
}

async function loadProfile() {
  loading.value = true
  try {
    const res = await getProfile()
    const data = res.data || res
    if (data.code === undefined || data.code === 0) {
      profile.value = data
      if (data.username) localStorage.setItem('username', data.username)
    }
  } catch (_) { /* silent */ }
  loading.value = false
}

async function loadBills() {
  billsLoading.value = true
  const loaded = []
  for (const requestId of rememberedRequestIds()) {
    try {
      const res = await getRequestDetail(requestId)
      const data = res.data || res
      if (data.code === undefined || data.code === 0) {
        loaded.push({ ...data, request_id: data.request_id || requestId })
      }
    } catch (_) { /* detail may not exist until the request ends */ }
  }
  bills.value = loaded.sort((a, b) => {
    const at = new Date(a.detail_generated_at || a.stop_time || 0).getTime()
    const bt = new Date(b.detail_generated_at || b.stop_time || 0).getTime()
    return bt - at
  })
  billsLoading.value = false
}

onMounted(async () => {
  await loadProfile()
  await loadBills()
})
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 28px; }
.page-head h1 { font-size: 22px; font-weight: 700; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }
.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; }
.bills-card { margin-top: 16px; }
.card-head { padding: 14px 20px; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.hint { font-size: 12px; color: #9ca3af; }
.card-body { padding: 20px; }
.empty { padding: 32px; text-align: center; color: #9ca3af; }
.profile-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.profile-item { display: flex; justify-content: space-between; align-items: center; padding: 16px; border: 1px solid #e5e7eb; border-radius: 10px; background: #f8faf9; }
.label { font-size: 13px; color: #6b7280; }
.value { font-size: 14px; font-weight: 700; color: #111827; }
.table-wrap { overflow-x: auto; }
.bills-table { width: 100%; border-collapse: collapse; min-width: 880px; }
.bills-table th, .bills-table td { padding: 14px 12px; border-bottom: 1px solid #eef2f7; text-align: left; white-space: nowrap; }
.bills-table th { font-size: 12px; font-weight: 600; color: #94a3b8; }
.bills-table td { font-size: 14px; color: #1f2937; }
.bills-table .amount { font-weight: 700; color: #059669; }
.pay-badge { display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 9px; background: #fffbeb; color: #b45309; font-size: 12px; font-weight: 700; }
.pay-badge.paid { background: #ecfdf5; color: #047857; }
@media (max-width: 720px) {
  .page { padding: 22px 18px; }
  .profile-grid { grid-template-columns: 1fr; }
  .card-head { align-items: flex-start; flex-direction: column; }
}
</style>
