<template>
  <div class="page">
    <div class="page-head">
      <h1>我的账单</h1>
      <p>查看充电详单、费用明细和支付状态</p>
    </div>

    <div class="empty-card" v-if="!detail && !loading">
      <div class="empty-title">暂无详单</div>
      <div class="empty-sub">完成充电后将自动生成详单</div>
    </div>

    <div v-if="loading" class="empty-card"><div class="empty-title">加载中...</div></div>

    <template v-if="detail">
      <div class="grid-2">
        <div class="card">
          <div class="card-head"><h3>充电详单</h3><span class="card-tag">GET /api/request/detail/{id}</span></div>
          <div class="card-body" style="padding:0;">
            <div class="detail-grid">
              <div class="dg-item"><span class="dg-key">详单编号</span><span class="dg-val">{{ detail.detail_id || '--' }}</span></div>
              <div class="dg-item"><span class="dg-key">请求结果</span><span class="dg-val">{{ requestResultText(detail) }}</span></div>
              <div class="dg-item"><span class="dg-key">充电桩</span><span class="dg-val">{{ detail.station_code || '--' }}</span></div>
              <div class="dg-item"><span class="dg-key">充电模式</span><span class="dg-val">{{ chargeModeText(detail) }}</span></div>
              <div class="dg-item"><span class="dg-key">实际电量</span><span class="dg-val">{{ detail.actual_energy ?? '--' }} kWh</span></div>
              <div class="dg-item"><span class="dg-key">充电时长</span><span class="dg-val">{{ fmtDuration(detail.charge_duration_seconds) }}</span></div>
              <div class="dg-item"><span class="dg-key">开始时间</span><span class="dg-val">{{ fmtDateTime(detail.start_time) }}</span></div>
              <div class="dg-item"><span class="dg-key">停止时间</span><span class="dg-val">{{ fmtDateTime(detail.stop_time) }}</span></div>
              <div class="dg-item"><span class="dg-key">充电费</span><span class="dg-val">{{ fmtMoney(detail.charge_fee) }}</span></div>
              <div class="dg-item"><span class="dg-key">服务费</span><span class="dg-val">{{ fmtMoney(detail.service_fee) }}</span></div>
              <div class="dg-item total"><span class="dg-key">总费用</span><span class="dg-val highlight">{{ fmtMoney(detail.total_fee) }}</span></div>
              <div class="dg-item"><span class="dg-key">详单生成时间</span><span class="dg-val">{{ fmtDateTime(detail.detail_generated_at) }}</span></div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head"><h3>支付信息</h3></div>
          <div class="card-body">
            <div class="pay-panel">
              <div class="pay-row">
                <span>支付状态</span>
                <strong :class="paymentStatus === 'PAID' ? 'paid' : 'unpaid'">{{ paymentText }}</strong>
              </div>
              <div class="pay-row">
                <span>应付金额</span>
                <strong>{{ fmtMoney(detail.total_fee) }}</strong>
              </div>
              <div class="pay-row">
                <span>支付时间</span>
                <strong>{{ fmtDateTime(paidAt) }}</strong>
              </div>
              <button class="btn-pay" :disabled="paymentStatus === 'PAID'" @click="payBill">
                {{ paymentStatus === 'PAID' ? '已支付' : `立即支付 ${fmtMoney(detail.total_fee)}` }}
              </button>
              <div class="pay-tip" :class="{ success: paymentStatus === 'PAID' }">
                {{ payTip }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>计费规则</h3></div>
        <div class="card-body">
          <div class="rules">
            <div class="rule-item"><div class="rule-num">1</div><div class="rule-text">充电费 = 各时段实际充电量 × 对应电价<br><code>峰 ¥1.0</code> <code>平 ¥0.7</code> <code>谷 ¥0.4</code></div></div>
            <div class="rule-item"><div class="rule-num">2</div><div class="rule-text">服务费 = 总实际充电量 × <code>0.8 元/kWh</code></div></div>
            <div class="rule-item"><div class="rule-num">3</div><div class="rule-text">总费用 = 充电费 + 服务费</div></div>
            <div class="rule-item"><div class="rule-num">4</div><div class="rule-text">充电跨时段时按各段实际电量分别计算</div></div>
            <div class="rule-item"><div class="rule-num">5</div><div class="rule-text">取消或未完成的请求不产生费用</div></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getRequestDetail } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT } from '@/constants/enums'

const detail = ref(null)
const loading = ref(false)
const paidAt = ref(null)
const paymentStatus = computed(() => paidAt.value ? 'PAID' : 'UNPAID')
const paymentText = computed(() => paymentStatus.value === 'PAID' ? '已支付' : '待支付')
const payTip = computed(() => {
  if (paymentStatus.value === 'PAID') return '当前为前端本地模拟支付状态，后端支付接口接入后会以服务端状态为准。'
  return '后端暂未提供支付接口，当前按钮先使用前端本地模拟支付。'
})

function billKey() {
  const id = detail.value?.detail_id || detail.value?.request_id || localStorage.getItem('request_id')
  return id ? `bill_paid_${id}` : ''
}

function loadLocalPayment() {
  const key = billKey()
  paidAt.value = key ? localStorage.getItem(key) : null
}

function payBill() {
  const key = billKey()
  if (!key || paymentStatus.value === 'PAID') return
  const now = formatLocalDateTime()
  localStorage.setItem(key, now)
  paidAt.value = now
}

function requestResultText(row) {
  const status = row?.termination_status || row?.request_status
  return REQUEST_STATUS_TEXT[status] || status || '--'
}

function chargeModeText(row) {
  if (row?.charge_mode) return CHARGE_MODE_TEXT[row.charge_mode] || row.charge_mode
  if (row?.station_code?.startsWith('FAST')) return '快充'
  if (row?.station_code?.startsWith('SLOW')) return '慢充'
  return '--'
}

function formatLocalDateTime(date = new Date()) {
  const pad = (value) => String(value).padStart(2, '0')
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate())
  ].join('-') + `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function fmtDuration(s) {
  if (!s && s !== 0) return '--'
  if (s > 0 && s < 60) return `${Math.ceil(s)} sec`
  const m = Math.floor(s / 60)
  return `${m} min`
}

function fmtDateTime(t) {
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

function fmtMoney(value) {
  const n = Number(value)
  return Number.isFinite(n) ? `¥${n.toFixed(2)}` : '--'
}

async function loadDetail() {
  const rid = localStorage.getItem('request_id')
  if (!rid) return
  loading.value = true
  try {
    const res = await getRequestDetail(rid)
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { loading.value = false; return }
    detail.value = data
    loadLocalPayment()
  } catch (_) { /* silent */ }
  loading.value = false
}

onMounted(loadDetail)
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 28px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: 0; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }
.empty-card { text-align: center; padding: 60px 20px; background: white; border: 1px solid #e5e7eb; border-radius: 12px; }
.empty-title { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 6px; }
.empty-sub { font-size: 13px; color: #9ca3af; }
.grid-2 { display: grid; grid-template-columns: 1fr 420px; gap: 16px; margin-bottom: 16px; }
.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; transition: 0.2s; }
.card:hover { border-color: #d1d5db; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.card-head { padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-tag { font-size: 11px; font-family: "SF Mono", monospace; color: #059669; padding: 3px 8px; border-radius: 6px; background: #ecfdf5; border: 1px solid #d1fae5; }
.card-body { padding: 20px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; }
.dg-item { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 13px 16px; border-bottom: 1px solid #e5e7eb; }
.dg-item:nth-child(odd) { border-right: 1px solid #e5e7eb; }
.dg-item.total { grid-column: 1 / -1; border-right: none; }
.dg-key { font-size: 13px; color: #6b7280; }
.dg-val { font-size: 13px; font-weight: 600; color: #111827; text-align: right; }
.dg-val.highlight { font-size: 16px; color: #059669; }
.pay-panel { display: grid; gap: 14px; }
.pay-row { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 1px solid #eef2f7; font-size: 13px; color: #6b7280; }
.pay-row strong { color: #111827; font-size: 15px; }
.pay-row strong.paid { color: #059669; }
.pay-row strong.unpaid { color: #b45309; }
.btn-pay { width: 100%; border: none; border-radius: 8px; padding: 12px 14px; background: #10b981; color: white; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn-pay:hover:not(:disabled) { background: #059669; }
.btn-pay:disabled { background: #d1d5db; cursor: not-allowed; }
.pay-tip { padding: 10px 12px; border-radius: 8px; background: #fffbeb; border: 1px solid #fde68a; color: #92400e; font-size: 12px; line-height: 1.5; }
.pay-tip.success { background: #ecfdf5; border-color: #bbf7d0; color: #047857; }
.rules { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 28px; }
.rule-item { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #e5e7eb; }
.rule-num { width: 22px; height: 22px; border-radius: 50%; background: #ecfdf5; border: 1px solid #d1fae5; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: #059669; flex-shrink: 0; margin-top: 1px; }
.rule-text { font-size: 13px; color: #1f2937; line-height: 1.6; }
.rule-text code { font-size: 12px; background: #f8faf9; border: 1px solid #e5e7eb; padding: 1px 5px; border-radius: 4px; font-family: "SF Mono", monospace; }
@media (max-width: 980px) {
  .grid-2 { grid-template-columns: 1fr; }
  .rules { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .page { padding: 22px 18px; }
  .detail-grid { grid-template-columns: 1fr; }
  .dg-item:nth-child(odd) { border-right: none; }
}
</style>
