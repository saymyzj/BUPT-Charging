<template>
  <div class="page">
    <div class="page-head">
      <h1>管理总览</h1>
      <p>充电桩运行状态一览</p>
    </div>

    <div class="toolbar">
      <button class="btn btn-primary" @click="loadStations">刷新状态</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

    <!-- Station Grid -->
    <div class="station-grid" v-if="!loading">
      <div class="station-card" v-for="s in stations" :key="s.station_code" :class="'st-' + (s.station_status || '').toLowerCase()">
        <div class="st-header">
          <span class="st-code">{{ s.station_code }}</span>
          <span class="st-badge" :class="'badge-' + (s.station_status || '').toLowerCase()">{{ STATION_STATUS_TEXT[s.station_status] || s.station_status }}</span>
        </div>
        <div class="st-info">
          <div class="st-row"><span>模式</span><span>{{ CHARGE_MODE_TEXT[s.charge_mode] || s.charge_mode }}</span></div>
          <div class="st-row"><span>当前服务</span><span>{{ s.current_request_id || '空闲' }}</span></div>
          <div class="st-row"><span>队列长度</span><span>{{ s.queue_length ?? 0 }}</span></div>
          <div class="st-row"><span>累计次数</span><span>{{ s.total_charge_count ?? 0 }}</span></div>
          <div class="st-row"><span>累计电量</span><span>{{ (s.total_charge_energy ?? 0).toFixed(1) }} kWh</span></div>
        </div>
        <button class="btn-queue" @click="viewQueue(s.station_code)">查看队列</button>
      </div>
    </div>

    <!-- Queue Modal -->
    <div class="modal-overlay" v-if="showModal" @click.self="showModal=false">
      <div class="modal-card">
        <div class="modal-head"><h3>{{ modalCode }} 桩队列</h3><button class="modal-close" @click="showModal=false">&times;</button></div>
        <div class="modal-body">
          <div v-if="queueLoading">加载中...</div>
          <table class="t" v-if="!queueLoading && queueData.length">
            <thead><tr><th>用户ID</th><th>电池容量</th><th>请求电量</th><th>排队号</th><th>排队时长</th></tr></thead>
            <tbody>
              <tr v-for="q in queueData" :key="q.queue_number">
                <td>{{ q.user_id }}</td>
                <td>{{ q.battery_capacity }} kWh</td>
                <td>{{ q.request_energy }} kWh</td>
                <td><strong>{{ q.queue_number }}</strong></td>
                <td>{{ Math.ceil((q.queue_wait_seconds || 0) / 60) }} min</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!queueLoading && !queueData.length" style="color:#9ca3af;font-size:13px;text-align:center;padding:20px;">队列为空</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStations, getStationQueue } from '@/api/charging'
import { STATION_STATUS_TEXT, CHARGE_MODE_TEXT } from '@/constants/enums'

const stations = ref([])
const loading = ref(false)
const showModal = ref(false)
const modalCode = ref('')
const queueData = ref([])
const queueLoading = ref(false)

async function loadStations() {
  loading.value = true
  try {
    const res = await getStations()
    const data = res.data || res
    stations.value = Array.isArray(data) ? data : (data.stations || [])
  } catch (_) { /* silent */ }
  loading.value = false
}

async function viewQueue(code) {
  modalCode.value = code
  showModal.value = true
  queueLoading.value = true
  queueData.value = []
  try {
    const res = await getStationQueue(code)
    const data = res.data || res
    queueData.value = Array.isArray(data) ? data : (data.queue || [])
  } catch (_) { /* silent */ }
  queueLoading.value = false
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

.station-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.station-card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; transition: 0.2s; }
.station-card:hover { border-color: #d1d5db; box-shadow: 0 2px 10px rgba(0,0,0,0.04); }
.station-card.st-running { border-left: 3px solid #10b981; }
.station-card.st-shutdown { border-left: 3px solid #9ca3af; }
.station-card.st-fault { border-left: 3px solid #ef4444; }
.st-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.st-code { font-size: 15px; font-weight: 700; color: #111827; }
.st-badge { font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 999px; }
.badge-running { background: #ecfdf5; color: #059669; border: 1px solid #d1fae5; }
.badge-shutdown { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }
.badge-fault { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.st-info { margin-bottom: 14px; }
.st-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; color: #6b7280; border-bottom: 1px solid #f3f4f6; }
.st-row span:last-child { font-weight: 600; color: #1f2937; }
.btn-queue { width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #e5e7eb; background: white; font-size: 12px; font-weight: 600; color: #6b7280; cursor: pointer; transition: 0.12s; }
.btn-queue:hover { border-color: #10b981; color: #059669; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-card { background: white; border-radius: 16px; width: 600px; max-height: 80vh; overflow-y: auto; }
.modal-head { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid #e5e7eb; }
.modal-head h3 { font-size: 16px; font-weight: 700; }
.modal-close { background: none; border: none; font-size: 24px; cursor: pointer; color: #9ca3af; }
.modal-body { padding: 20px 24px; }
table.t { width: 100%; border-collapse: collapse; }
table.t th { text-align: left; padding: 10px 12px; font-size: 11px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e5e7eb; }
table.t td { padding: 10px 12px; font-size: 13px; border-bottom: 1px solid #f3f4f6; color: #374151; }
table.t td strong { color: #111827; }
</style>
