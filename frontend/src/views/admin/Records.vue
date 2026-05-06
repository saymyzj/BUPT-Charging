<template>
  <div class="page">
    <div class="page-head">
      <h1>设备控制</h1>
      <p>充电桩启动、关闭、故障标记与恢复</p>
    </div>

    <div class="toolbar">
      <button class="btn btn-primary" @click="loadStations">刷新</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

    <table class="t" v-if="!loading && stations.length">
      <thead>
        <tr>
          <th>编号</th>
          <th>模式</th>
          <th>状态</th>
          <th>当前请求</th>
          <th>队列长度</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in stations" :key="s.station_code">
          <td><strong>{{ s.station_code }}</strong></td>
          <td>{{ CHARGE_MODE_TEXT[s.charge_mode] || s.charge_mode }}</td>
          <td><span class="st-badge" :class="'badge-' + (s.station_status||'').toLowerCase()">{{ STATION_STATUS_TEXT[s.station_status] || s.station_status }}</span></td>
          <td>{{ s.current_request_id || '--' }}</td>
          <td>{{ s.queue_length ?? 0 }}</td>
          <td class="action-cell">
            <button class="btn-sm btn-green" v-if="s.station_status === 'SHUTDOWN'" @click="doAction(s.station_code, 'start')">启动</button>
            <button class="btn-sm btn-gray" v-if="s.station_status === 'RUNNING' && !s.current_request_id && (s.queue_length||0) === 0" @click="doAction(s.station_code, 'shutdown')">关闭</button>
            <button class="btn-sm btn-red" v-if="s.station_status === 'RUNNING'" @click="doAction(s.station_code, 'fault')">标记故障</button>
            <button class="btn-sm btn-blue" v-if="s.station_status === 'FAULT'" @click="doAction(s.station_code, 'recover')">恢复</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Rules Card -->
    <div class="card" style="margin-top:24px;">
      <div class="card-head"><h3>操作规则</h3></div>
      <div class="card-body">
        <table class="rules-table">
          <thead><tr><th>桩状态</th><th>条件</th><th>可用操作</th></tr></thead>
          <tbody>
            <tr><td>SHUTDOWN</td><td>任意</td><td>启动</td></tr>
            <tr><td>RUNNING</td><td>空闲且队列为空</td><td>关闭、标记故障</td></tr>
            <tr><td>RUNNING</td><td>有服务或队列不空</td><td>标记故障</td></tr>
            <tr><td>FAULT</td><td>任意</td><td>恢复</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStations, startStation, shutdownStation, faultStation, recoverStation } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { STATION_STATUS_TEXT, CHARGE_MODE_TEXT } from '@/constants/enums'

const stations = ref([])
const loading = ref(false)

async function loadStations() {
  loading.value = true
  try {
    const res = await getStations()
    const data = unwrapResponseData(res)
    stations.value = Array.isArray(data) ? data : (data.stations || [])
  } catch (_) { /* silent */ }
  loading.value = false
}

async function doAction(code, action) {
  const map = { start: startStation, shutdown: shutdownStation, fault: faultStation, recover: recoverStation }
  const fn = map[action]
  if (!fn) return
  try {
    const res = await fn(code)
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '操作失败'); return }
    await loadStations()
  } catch (e) {
    const code = e?.response?.data?.code
    if (code === 1007) alert('充电桩未处于可关闭状态')
    else alert(e?.response?.data?.message || '操作失败')
  }
}

onMounted(loadStations)
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 20px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }
.toolbar { margin-bottom: 16px; }
.btn { padding: 8px 18px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.12s; }
.btn-primary { background: #10b981; color: white; }
.btn-primary:hover { background: #059669; }
.loading-text { color: #9ca3af; font-size: 14px; padding: 40px 0; text-align: center; }

table.t { width: 100%; border-collapse: collapse; background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; }
table.t th { text-align: left; padding: 12px 16px; font-size: 11px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e5e7eb; background: #f8faf9; }
table.t td { padding: 14px 16px; font-size: 13px; border-bottom: 1px solid #f3f4f6; color: #374151; }
table.t td strong { color: #111827; font-weight: 700; }
table.t tr:last-child td { border-bottom: none; }

.st-badge { font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 999px; }
.badge-running { background: #ecfdf5; color: #059669; }
.badge-shutdown { background: #f9fafb; color: #6b7280; }
.badge-fault { background: #fef2f2; color: #ef4444; }

.action-cell { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-sm { padding: 5px 10px; border-radius: 6px; border: 1px solid; font-size: 11px; font-weight: 600; cursor: pointer; transition: 0.12s; background: white; }
.btn-green { border-color: #d1fae5; color: #059669; }
.btn-green:hover { background: #ecfdf5; }
.btn-gray { border-color: #e5e7eb; color: #6b7280; }
.btn-gray:hover { background: #f3f4f6; }
.btn-red { border-color: #fecaca; color: #ef4444; }
.btn-red:hover { background: #fef2f2; }
.btn-blue { border-color: #bfdbfe; color: #3b82f6; }
.btn-blue:hover { background: #eff6ff; }

.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; }
.card-head { padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-body { padding: 20px; }
.rules-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.rules-table th { text-align: left; padding: 8px 12px; color: #6b7280; border-bottom: 1px solid #e5e7eb; font-weight: 500; font-size: 11px; text-transform: uppercase; }
.rules-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; color: #374151; }
</style>
