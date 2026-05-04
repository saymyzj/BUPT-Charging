<template>
  <div class="page">
    <div class="page-head">
      <h1>详单与账户</h1>
      <p>查看充电详单、费用明细</p>
    </div>

    <!-- No detail -->
    <div class="empty-card" v-if="!detail && !loading">
      <div class="empty-title">暂无详单</div>
      <div class="empty-sub">完成充电后将自动生成详单</div>
    </div>

    <div v-if="loading" class="empty-card"><div class="empty-title">加载中...</div></div>

    <template v-if="detail">
      <!-- Detail Grid -->
      <div class="grid-2">
        <div class="card">
          <div class="card-head"><h3>充电详单</h3><span class="card-tag">GET /api/request/detail/{id}</span></div>
          <div class="card-body" style="padding:0;">
            <div class="detail-grid">
              <div class="dg-item"><span class="dg-key">详单编号</span><span class="dg-val">{{ detail.detail_id || '--' }}</span></div>
              <div class="dg-item"><span class="dg-key">终态</span><span class="dg-val">{{ REQUEST_STATUS_TEXT[detail.request_status] || detail.request_status }}</span></div>
              <div class="dg-item"><span class="dg-key">充电桩</span><span class="dg-val">{{ detail.station_code || '--' }}</span></div>
              <div class="dg-item"><span class="dg-key">充电模式</span><span class="dg-val">{{ CHARGE_MODE_TEXT[detail.charge_mode] || '--' }}</span></div>
              <div class="dg-item"><span class="dg-key">实际电量</span><span class="dg-val">{{ detail.actual_energy ?? '--' }} kWh</span></div>
              <div class="dg-item"><span class="dg-key">充电时长</span><span class="dg-val">{{ fmtDuration(detail.charge_duration_seconds) }}</span></div>
              <div class="dg-item"><span class="dg-key">开始时间</span><span class="dg-val">{{ fmtDateTime(detail.start_time) }}</span></div>
              <div class="dg-item"><span class="dg-key">停止时间</span><span class="dg-val">{{ fmtDateTime(detail.stop_time) }}</span></div>
              <div class="dg-item"><span class="dg-key">充电费</span><span class="dg-val">¥{{ (detail.charge_fee ?? 0).toFixed(2) }}</span></div>
              <div class="dg-item"><span class="dg-key">服务费</span><span class="dg-val">¥{{ (detail.service_fee ?? 0).toFixed(2) }}</span></div>
              <div class="dg-item total"><span class="dg-key">总费用</span><span class="dg-val highlight">¥{{ (detail.total_fee ?? 0).toFixed(2) }}</span></div>
              <div class="dg-item"><span class="dg-key">详单生成时间</span><span class="dg-val">{{ fmtDateTime(detail.detail_generated_at) }}</span></div>
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
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRequestDetail } from '@/api/charging'
import { REQUEST_STATUS_TEXT, CHARGE_MODE_TEXT } from '@/constants/enums'

const detail = ref(null)
const loading = ref(false)

function fmtDuration(s) {
  if (!s && s !== 0) return '--'
  const m = Math.floor(s / 60)
  return `${m} min`
}

function fmtDateTime(t) {
  if (!t) return '--'
  try { return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) } catch { return t }
}

async function loadDetail() {
  const rid = localStorage.getItem('request_id')
  if (!rid) return
  loading.value = true
  try {
    const res = await getRequestDetail(rid)
    const data = res.data || res
    if (data.code !== undefined && data.code !== 0) { loading.value = false; return }
    detail.value = data
  } catch (_) { /* silent */ }
  loading.value = false
}

onMounted(loadDetail)
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 28px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }

.empty-card { text-align: center; padding: 60px 20px; background: white; border: 1px solid #e5e7eb; border-radius: 12px; }
.empty-title { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 6px; }
.empty-sub { font-size: 13px; color: #9ca3af; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; transition: 0.2s; }
.card:hover { border-color: #d1d5db; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.card-head { padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-tag { font-size: 11px; font-family: "SF Mono", monospace; color: #059669; padding: 3px 8px; border-radius: 6px; background: #ecfdf5; border: 1px solid #d1fae5; }
.card-body { padding: 20px; }

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; }
.dg-item { display: flex; justify-content: space-between; align-items: center; padding: 13px 16px; border-bottom: 1px solid #e5e7eb; }
.dg-item:nth-child(odd) { border-right: 1px solid #e5e7eb; }
.dg-item.total { grid-column: 1 / -1; border-right: none; }
.dg-key { font-size: 13px; color: #6b7280; }
.dg-val { font-size: 13px; font-weight: 600; color: #111827; }
.dg-val.highlight { font-size: 16px; color: #059669; }

.rules { display: flex; flex-direction: column; }
.rule-item { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #e5e7eb; }
.rule-item:last-child { border-bottom: none; }
.rule-num { width: 22px; height: 22px; border-radius: 50%; background: #ecfdf5; border: 1px solid #d1fae5; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: #059669; flex-shrink: 0; margin-top: 1px; }
.rule-text { font-size: 13px; color: #1f2937; line-height: 1.6; }
.rule-text code { font-size: 12px; background: #f8faf9; border: 1px solid #e5e7eb; padding: 1px 5px; border-radius: 4px; font-family: "SF Mono", monospace; }
</style>
