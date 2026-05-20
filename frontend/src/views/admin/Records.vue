<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>设备控制</h1>
        <p>充电桩启动、关闭、故障标记与恢复</p>
      </div>
      <button class="btn-refresh" :disabled="loading" @click="loadStations">
        <span class="material-icons">refresh</span> 刷新
      </button>
    </div>

    <div v-if="loading && !stations.length" class="loading-text">
      <span class="material-icons spin">refresh</span> 加载中...
    </div>

    <template v-else>
      <!-- Stat cards -->
      <div class="stat-grid">
        <div class="stat-card">
          <div class="sc-head">
            <div class="sc-icon si-emerald"><span class="material-icons">computer</span></div>
            <div class="sc-right">
              <div class="sc-label">在线设备</div>
              <div class="sc-num">{{ totalStations }}</div>
            </div>
          </div>
          <div class="sc-bar-meta"><span></span><span>{{ totalStations ? '100' : '0' }}%</span></div>
          <div class="sc-bar"><div class="sc-fill fi-emerald" style="width:100%"></div></div>
        </div>

        <div class="stat-card">
          <div class="sc-head">
            <div class="sc-icon si-green"><span class="material-icons">play_circle_outline</span></div>
            <div class="sc-right">
              <div class="sc-label">运行中</div>
              <div class="sc-num">{{ runningStations }}</div>
            </div>
          </div>
          <div class="sc-bar-meta"><span></span><span>{{ runningRate }}%</span></div>
          <div class="sc-bar"><div class="sc-fill fi-green" :style="{ width: runningRate + '%' }"></div></div>
        </div>

        <div class="stat-card">
          <div class="sc-head">
            <div class="sc-icon si-red"><span class="material-icons">warning_amber</span></div>
            <div class="sc-right">
              <div class="sc-label">故障数</div>
              <div class="sc-num red">{{ faultStations }}</div>
            </div>
          </div>
          <div class="sc-bar-meta"><span></span><span>{{ faultRate }}%</span></div>
          <div class="sc-bar"><div class="sc-fill fi-red" :style="{ width: faultRate + '%' }"></div></div>
        </div>

        <div class="stat-card">
          <div class="sc-head">
            <div class="sc-icon si-gray"><span class="material-icons">pause_circle_outline</span></div>
            <div class="sc-right">
              <div class="sc-label">空闲设备</div>
              <div class="sc-num">{{ idleStations }}</div>
            </div>
          </div>
          <div class="sc-bar-meta"><span></span><span>{{ idleRate }}%</span></div>
          <div class="sc-bar"><div class="sc-fill fi-gray" :style="{ width: idleRate + '%' }"></div></div>
        </div>

        <div class="stat-card">
          <div class="sc-head">
            <div class="sc-icon si-emerald"><span class="material-icons">bolt</span></div>
            <div class="sc-right">
              <div class="sc-label">累计电量</div>
              <div class="sc-num">{{ totalEnergyNum }}<span class="sc-unit">kWh</span></div>
            </div>
          </div>
          <div class="sc-bar-meta"><span></span></div>
          <div class="sc-bar sc-bar-empty"></div>
        </div>

        <div class="stat-card">
          <div class="sc-head">
            <div class="sc-icon si-emerald"><span class="material-icons">event_available</span></div>
            <div class="sc-right">
              <div class="sc-label">累计服务</div>
              <div class="sc-num">{{ totalServices }}<span class="sc-unit">次</span></div>
            </div>
          </div>
          <div class="sc-bar-meta"><span></span></div>
          <div class="sc-bar sc-bar-empty"></div>
        </div>
      </div>

      <!-- Device table -->
      <div class="panel">
        <div class="table-wrap">
          <table class="device-table">
            <thead>
              <tr>
                <th>编号</th>
                <th>模式</th>
                <th>状态</th>
                <th>当前服务</th>
                <th class="center">队列长度</th>
                <th class="center">累计次数</th>
                <th>累计时长</th>
                <th>累计电量</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody v-if="stations.length">
              <tr v-for="s in stations" :key="s.station_code" :class="{ 'row-fault': s.station_status === 'FAULT' }">
                <td class="td-code">{{ s.station_code }}</td>
                <td class="td-mode">{{ CHARGE_MODE_TEXT[s.charge_mode] || s.charge_mode }}</td>
                <td>
                  <span v-if="s.station_status === 'RUNNING'" class="st-running">运行中</span>
                  <span v-else-if="s.station_status === 'FAULT'" class="st-fault">故障</span>
                  <span v-else class="st-idle">空闲</span>
                </td>
                <td :class="s.current_request_id ? 'td-serving' : 'td-free'">{{ currentServiceText(s) }}</td>
                <td class="center mono">{{ s.queue_length ?? 0 }}</td>
                <td class="center mono">{{ s.total_charge_count ?? 0 }}</td>
                <td class="mono">{{ fmtDuration(s.total_charge_seconds) }}</td>
                <td class="mono">{{ fmtEnergy(s.total_charge_energy) }}</td>
                <td>
                  <div class="action-cell">
                    <button v-if="s.station_status === 'SHUTDOWN'" class="act-btn act-start" @click="doAction(s.station_code, 'start')">启动</button>
                    <button v-if="s.station_status === 'RUNNING' && !s.current_request_id && (s.queue_length || 0) === 0" class="act-btn act-gray" @click="doAction(s.station_code, 'shutdown')">关闭</button>
                    <button v-if="s.station_status === 'RUNNING'" class="act-btn act-red" @click="doAction(s.station_code, 'fault')">标记故障</button>
                    <button v-if="s.station_status === 'FAULT'" class="act-btn act-blue" @click="doAction(s.station_code, 'recover')">恢复</button>
                  </div>
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr><td colspan="9" class="empty-row">暂无设备数据</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Rules -->
      <section class="rules-section">
        <h3 class="rules-title">操作规则</h3>
        <div class="rules-grid">
          <div class="rule-card rc-running">
            <h4>运行中</h4>
            <p>设备正在运行，允许以下操作</p>
            <div class="rule-rows">
              <div class="rule-row rr-default">
                <span class="rr-key">关闭</span>
                <span class="rr-desc">停止当前充电服务</span>
              </div>
              <div class="rule-row rr-default">
                <span class="rr-key">标记故障</span>
                <span class="rr-desc">将设备标记为故障，暂停服务</span>
              </div>
            </div>
          </div>
          <div class="rule-card rc-idle">
            <h4>空闲</h4>
            <p>设备空闲中，允许以下操作</p>
            <div class="rule-rows">
              <div class="rule-row rr-plain">
                <span class="rr-key">启动</span>
                <span class="rr-desc">启动充电桩，进入运行状态</span>
              </div>
              <div class="rule-row rr-plain">
                <span class="rr-key">标记故障</span>
                <span class="rr-desc">将设备标记为故障，暂停服务</span>
              </div>
            </div>
          </div>
          <div class="rule-card rc-fault">
            <h4>故障</h4>
            <p>设备处于故障状态，允许以下操作</p>
            <div class="rule-rows">
              <div class="rule-row rr-fault">
                <span class="rr-key">恢复</span>
                <span class="rr-desc">清除故障标记，恢复运行</span>
              </div>
              <div class="rule-row rr-fault">
                <span class="rr-key">标记故障</span>
                <span class="rr-desc">保持或更新故障状态信息</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { addAcceptanceEvent, getAcceptanceState, getStations, startStation, shutdownStation, faultStation, recoverStation } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { STATION_STATUS_TEXT, CHARGE_MODE_TEXT } from '@/constants/enums'

const stations = ref([])
const loading = ref(false)

const totalStations = computed(() => stations.value.length)
const runningStations = computed(() => stations.value.filter((s) => s.station_status === 'RUNNING').length)
const faultStations = computed(() => stations.value.filter((s) => s.station_status === 'FAULT').length)
const idleStations = computed(() =>
  stations.value.filter((s) => s.station_status === 'RUNNING' && !s.current_request_id && (s.queue_length || 0) === 0).length
)
const runningRate = computed(() => totalStations.value ? Math.round(runningStations.value / totalStations.value * 100) : 0)
const faultRate = computed(() => totalStations.value ? Math.round(faultStations.value / totalStations.value * 100) : 0)
const idleRate = computed(() => totalStations.value ? Math.round(idleStations.value / totalStations.value * 100) : 0)
const totalEnergyNum = computed(() => Number(stations.value.reduce((sum, s) => sum + Number(s.total_charge_energy || 0), 0)).toFixed(2))
const totalEnergy = computed(() => fmtEnergy(stations.value.reduce((sum, s) => sum + Number(s.total_charge_energy || 0), 0)))
const totalServices = computed(() =>
  stations.value.reduce((sum, s) => sum + Number(s.total_charge_count || 0), 0).toLocaleString('zh-CN')
)

async function loadStations() {
  loading.value = true
  try {
    const res = await getStations()
    const data = unwrapResponseData(res)
    stations.value = Array.isArray(data) ? data : (data.stations || [])
  } catch (_) {
    stations.value = []
  }
  loading.value = false
}

async function doAction(code, action) {
  const map = { start: startStation, shutdown: shutdownStation, fault: faultStation, recover: recoverStation }
  const fn = map[action]
  if (!fn) return
  try {
    const acceptance = await pausedAcceptanceState()
    if (acceptance && ['fault', 'recover'].includes(action)) {
      await addAcceptanceEvent({
        at: acceptance.simulation_time,
        event_type: action === 'fault' ? 'FAULT' : 'RECOVER',
        station_code: code,
        value: action === 'fault' ? 0 : null,
        raw_text: `手动${action === 'fault' ? '标记故障' : '恢复'} ${code}`,
      })
      alert('验收模式暂停中：操作已加入当前模拟时刻待执行队列。')
      return
    }
    const res = await fn(code)
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      alert(data.message || '操作失败')
      return
    }
    await loadStations()
  } catch (e) {
    const code = e?.response?.data?.code
    if (code === 1007) alert('充电桩未处于可关闭状态')
    else alert(e?.response?.data?.message || '操作失败')
  }
}

async function pausedAcceptanceState() {
  try {
    const data = unwrapResponseData(await getAcceptanceState())
    return data.enabled && data.status === 'PAUSED' ? data : null
  } catch (_) {
    return null
  }
}

function currentServiceText(station) {
  if (!station?.current_request_id) return '空闲'
  if (station.current_user?.username) return `用户 ${maskIdentifier(station.current_user.username)}`
  if (station.current_user?.user_id) return `用户 ${maskIdentifier(station.current_user.user_id)}`
  return '服务中'
}

function maskIdentifier(value) {
  const text = String(value || '')
  if (text.length <= 4) return text
  if (text.length <= 7) return `${text.slice(0, 2)}****${text.slice(-1)}`
  return `${text.slice(0, 3)}****${text.slice(-3)}`
}

function fmtDuration(value) {
  const seconds = Math.max(0, Math.floor(Number(value || 0)))
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const rest = seconds % 60
  if (h > 0) return rest > 0 ? `${h}h ${m}m ${rest}s` : `${h}h ${m}m`
  if (m > 0) return rest > 0 ? `${m}m ${rest}s` : `${m}m`
  return `${rest}s`
}

function fmtEnergy(value) {
  return `${Number(value || 0).toFixed(2)} kWh`
}

onMounted(loadStations)
</script>

<style scoped>
* { box-sizing: border-box; }
.page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 36px 40px 52px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif;
  font-size: 14px;
  color: #1f2937;
}

/* Page header */
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 32px;
}
.page-head h1 { font-size: 26px; font-weight: 900; letter-spacing: -0.5px; color: #111827; margin: 0; }
.page-head p { font-size: 13px; color: #6b7280; margin: 5px 0 0; }

.btn-refresh {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 16px; border-radius: 9px;
  border: 1px solid #e5e7eb; background: #f9fafb;
  font-size: 13px; font-weight: 700; color: #374151;
  cursor: pointer; transition: .15s; flex-shrink: 0;
}
.btn-refresh .material-icons { font-size: 16px; }
.btn-refresh:hover { background: #f3f4f6; border-color: #d1d5db; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

.loading-text {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  color: #9ca3af; font-size: 15px; padding: 80px 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; display: inline-block; }

/* Stat grid */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}
.stat-card {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 18px;
  padding: 22px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.sc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}
.sc-icon {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sc-icon .material-icons { font-size: 20px; }
.si-emerald { background: #ecfdf5; color: #059669; }
.si-green   { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.si-red     { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.si-gray    { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }
.sc-right { text-align: right; }
.sc-label { font-size: 11px; color: #9ca3af; font-weight: 700; margin-bottom: 4px; }
.sc-num { font-size: 24px; font-weight: 900; color: #111827; font-variant-numeric: tabular-nums; line-height: 1; }
.sc-num.red { color: #dc2626; }
.sc-unit { font-size: 11px; font-weight: 700; color: #9ca3af; margin-left: 3px; }
.sc-bar-meta {
  display: flex; justify-content: space-between;
  font-size: 11px; color: #9ca3af;
  margin: 16px 0 6px;
}
.sc-bar { height: 5px; background: #f1f5f9; border-radius: 999px; overflow: hidden; }
.sc-bar-empty { background: #f0fdf4; }
.sc-fill { height: 100%; border-radius: 999px; transition: width .4s; }
.fi-emerald { background: #10b981; }
.fi-green   { background: #22c55e; }
.fi-red     { background: #ef4444; }
.fi-gray    { background: #94a3b8; }

/* Panel / Table */
.panel {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
  margin-bottom: 28px;
}
.table-wrap { overflow-x: auto; }
.device-table {
  width: 100%; border-collapse: collapse;
  text-align: left; font-size: 13px; min-width: 1000px;
}
.device-table thead th {
  padding: 16px 24px;
  font-size: 12px; font-weight: 500; color: #9ca3af;
  border-bottom: 1px solid #f1f5f9; white-space: nowrap;
}
.device-table tbody tr {
  border-bottom: 1px solid #f9fafb; transition: background .12s;
}
.device-table tbody tr:last-child { border-bottom: none; }
.device-table tbody tr:hover { background: rgba(249,250,251,.6); }
.device-table tbody tr.row-fault { background: rgba(254,242,242,.18); }
.device-table td { padding: 18px 24px; color: #374151; vertical-align: middle; }
.td-code { font-weight: 800; color: #111827; font-size: 14px; }
.td-mode { font-weight: 500; }
.td-serving { font-weight: 600; color: #111827; }
.td-free    { color: #6b7280; font-weight: 500; }
.center { text-align: center; }
.mono   { font-family: "SF Mono", Consolas, monospace; color: #6b7280; white-space: nowrap; }

/* Status labels */
.st-running { font-weight: 700; color: #10b981; font-size: 13px; }
.st-idle    { font-weight: 700; color: #9ca3af; font-size: 13px; }
.st-fault {
  display: inline-flex; align-items: center;
  padding: 3px 9px; border-radius: 5px;
  background: #fef2f2; color: #ef4444;
  font-weight: 700; font-size: 12px;
  border: 1px solid #fecaca;
}

/* Action buttons */
.action-cell { display: flex; gap: 18px; align-items: center; }
.act-btn {
  background: none; border: none; cursor: pointer;
  font-size: 13px; font-weight: 700; padding: 0; transition: color .12s;
  font-family: inherit;
}
.act-start { color: #10b981; }
.act-start:hover { color: #059669; }
.act-gray  { color: #9ca3af; }
.act-gray:hover  { color: #374151; }
.act-red   { color: #f87171; }
.act-red:hover   { color: #dc2626; }
.act-blue  { color: #60a5fa; }
.act-blue:hover  { color: #2563eb; }

.empty-row { padding: 60px 24px; text-align: center; color: #9ca3af; font-size: 14px; }

/* Rules */
.rules-section { }
.rules-title { font-size: 16px; font-weight: 800; color: #111827; margin: 0 0 16px; }
.rules-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}
.rule-card {
  background: #fff;
  border: 1px solid #f1f5f9;
  border-top-width: 2px;
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.rc-running { border-top-color: #34d399; }
.rc-idle    { border-top-color: #94a3b8; background: rgba(249,250,251,.5); border-color: #e5e7eb; }
.rc-fault   { border-top-color: #f87171; background: rgba(254,242,242,.08); border-color: #fecaca; }
.rule-card h4 { font-size: 15px; font-weight: 800; margin: 0 0 6px; }
.rc-running h4 { color: #059669; }
.rc-idle h4    { color: #6b7280; }
.rc-fault h4   { color: #ef4444; }
.rule-card p { font-size: 13px; color: #6b7280; margin: 0 0 18px; line-height: 1.6; }
.rule-rows { display: flex; flex-direction: column; gap: 10px; }
.rule-row {
  display: flex; gap: 16px; align-items: flex-start;
  padding: 13px 14px; border-radius: 9px;
  border: 1px solid;
}
.rr-default { background: rgba(249,250,251,.5); border-color: #f9fafb; }
.rr-plain   { background: #fff; border-color: #f1f5f9; }
.rr-fault   { background: rgba(255,255,255,.6); border-color: #fef2f2; }
.rr-key  { font-size: 13px; font-weight: 800; color: #374151; min-width: 60px; flex-shrink: 0; }
.rr-desc { font-size: 12px; color: #6b7280; margin-top: 1px; line-height: 1.5; }

@media (max-width: 1280px) {
  .stat-grid  { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .rules-grid { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .page { padding: 24px 20px 32px; }
  .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
