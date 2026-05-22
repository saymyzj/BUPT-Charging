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

      <!-- Station cards -->
      <div class="pile-section">
        <div class="pile-section-head">
          <h2>充电桩设备总览</h2>
          <div class="pile-legend">
            <span class="lg"><i class="lg-dot lg-green"></i>运行中</span>
            <span class="lg"><i class="lg-dot lg-red"></i>故障</span>
            <span class="lg"><i class="lg-dot lg-gray"></i>已关闭</span>
          </div>
        </div>
        <div class="pile-grid-wrap" v-if="stations.length">
          <div class="pile-grid">
            <article
              v-for="s in stations"
              :key="s.station_code"
              class="pile-card"
              :class="toneClass(s)"
            >
              <!-- Charger visual -->
              <div class="pc-charger-wrap">
                <div class="pc-charger" :class="toneClass(s)">
                  <span class="material-icons pc-charger-icon">ev_station</span>
                </div>
                <span class="pc-status-dot" :class="toneClass(s)"></span>
              </div>

              <!-- Name + Mode + Status -->
              <div class="pc-identity">
                <strong class="pc-name">{{ s.station_code }}</strong>
                <span class="pc-mode">{{ CHARGE_MODE_TEXT[s.charge_mode] || s.charge_mode }}</span>
                <span class="pc-pill" :class="toneClass(s)">{{ statusLabel(s.station_status) }}</span>
              </div>

              <!-- Current service -->
              <div class="pc-service" :class="{ active: s.current_request_id }">
                <span class="material-icons pc-service-icon">{{ s.current_request_id ? 'person' : 'no_accounts' }}</span>
                <span>{{ currentServiceText(s) }}</span>
              </div>

              <!-- Metrics -->
              <div class="pc-metrics">
                <div class="pc-m"><span>队列</span><strong>{{ s.queue_length ?? 0 }}</strong></div>
                <div class="pc-m"><span>服务</span><strong>{{ s.total_charge_count ?? 0 }}<small>次</small></strong></div>
                <div class="pc-m"><span>时长</span><strong>{{ fmtDuration(s.total_charge_seconds) }}</strong></div>
                <div class="pc-m"><span>电量</span><strong>{{ fmtEnergy(s.total_charge_energy) }}</strong></div>
              </div>

              <!-- Actions -->
              <div class="pc-actions">
                <button v-if="s.station_status === 'SHUTDOWN'" class="act-btn act-start" @click="doAction(s.station_code, 'start')">
                  <span class="material-icons">play_arrow</span>启动
                </button>
                <button v-if="s.station_status === 'RUNNING' && !s.current_request_id && (s.queue_length || 0) === 0" class="act-btn act-off" @click="doAction(s.station_code, 'shutdown')">
                  <span class="material-icons">power_settings_new</span>关闭
                </button>
                <button v-if="s.station_status === 'RUNNING'" class="act-btn act-red" @click="doAction(s.station_code, 'fault')">
                  <span class="material-icons">report_problem</span>标记故障
                </button>
                <button v-if="s.station_status === 'FAULT'" class="act-btn act-blue" @click="doAction(s.station_code, 'recover')">
                  <span class="material-icons">healing</span>恢复
                </button>
              </div>

              <!-- Expandable queue -->
              <div class="pc-queue-toggle" @click="toggleQueue(s.station_code)">
                <span>队列详情 ({{ stationQueueRows(s.station_code).length }})</span>
                <span class="material-icons pc-toggle-icon">{{ expandedStations[s.station_code] ? 'expand_less' : 'expand_more' }}</span>
              </div>
              <div v-if="expandedStations[s.station_code]" class="pc-queue-list">
                <template v-if="stationQueueRows(s.station_code).length">
                  <div
                    v-for="(row, idx) in stationQueueRows(s.station_code)"
                    :key="row.request_id || idx"
                    class="pq-row"
                    :class="{ charging: isChargingRow(s, row, idx) }"
                  >
                    <span class="pq-no">{{ idx + 1 }}</span>
                    <span class="pq-user">{{ userShort(row) }}</span>
                    <span class="pq-energy">{{ Number(row.request_energy || 0).toFixed(1) }} kWh</span>
                    <em class="pq-status">{{ isChargingRow(s, row, idx) ? '充电中' : '等待中' }}</em>
                  </div>
                </template>
                <div v-else class="pq-empty">队列为空</div>
              </div>
            </article>
          </div>
        </div>
        <div v-else class="empty-row">暂无设备数据</div>
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
  <ActionDialog v-bind="dialog" @confirm="confirmDialog" @cancel="cancelDialog" />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { addAcceptanceEvent, getAcceptanceState, getStations, getStationQueue, startStation, shutdownStation, faultStation, recoverStation } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { STATION_STATUS_TEXT, CHARGE_MODE_TEXT } from '@/constants/enums'
import ActionDialog from '@/components/ActionDialog.vue'
import { useActionDialog } from '@/composables/useActionDialog'

const { dialog, openConfirm, openMessage, confirmDialog, cancelDialog } = useActionDialog()

const stations = ref([])
const loading = ref(false)
const stationQueues = ref({})
const expandedStations = ref({})

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
    await loadQueues()
  } catch (_) {
    stations.value = []
  }
  loading.value = false
}

async function loadQueues() {
  const entries = await Promise.all(
    stations.value.map((s) =>
      getStationQueue(s.station_code)
        .then((res) => {
          const data = unwrapResponseData(res)
          return [s.station_code, Array.isArray(data) ? data : (data.queue || [])]
        })
        .catch(() => [s.station_code, []])
    )
  )
  stationQueues.value = Object.fromEntries(entries)
}

function stationQueueRows(code) {
  return stationQueues.value[code] || []
}

function toggleQueue(code) {
  expandedStations.value = { ...expandedStations.value, [code]: !expandedStations.value[code] }
}

function isChargingRow(station, row, index) {
  return row?.request_status === 'CHARGING' || (index === 0 && Boolean(station?.current_request_id))
}

function userShort(row) {
  return row?.username || row?.user_id || row?.request_id || '--'
}

const ACTION_LABELS = {
  start: { title: '启动充电桩', message: (c) => `确认启动 ${c}？`, severity: 'primary', confirmText: '启动' },
  shutdown: { title: '关闭充电桩', message: (c) => `确认关闭 ${c}？关闭后将停止接受新请求。`, severity: 'warning', confirmText: '关闭' },
  fault: { title: '标记故障', message: (c) => `确认将 ${c} 标记为故障？队列中的请求将被重新调度。`, severity: 'danger', confirmText: '确认故障' },
  recover: { title: '恢复充电桩', message: (c) => `确认恢复 ${c}？`, severity: 'primary', confirmText: '恢复' },
}

async function doAction(code, action) {
  const map = { start: startStation, shutdown: shutdownStation, fault: faultStation, recover: recoverStation }
  const fn = map[action]
  if (!fn) return
  const label = ACTION_LABELS[action]
  const confirmed = await openConfirm({
    title: label.title,
    message: label.message(code),
    severity: label.severity,
    confirmText: label.confirmText,
  })
  if (!confirmed) return
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
      await openMessage({ title: '操作失败', message: data.message || '操作失败', severity: 'danger' })
      return
    }
    await loadStations()
  } catch (e) {
    const errCode = e?.response?.data?.code
    const msg = errCode === 1007 ? '充电桩未处于可关闭状态' : (e?.response?.data?.message || '操作失败')
    await openMessage({ title: '操作失败', message: msg, severity: 'danger' })
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

function toneClass(s) {
  if (s.station_status === 'FAULT') return 'tone-red'
  if (s.station_status === 'SHUTDOWN') return 'tone-gray'
  return 'tone-green'
}

function statusLabel(status) {
  if (status === 'RUNNING') return '运行中'
  if (status === 'FAULT') return '故障'
  return '已关闭'
}

onMounted(loadStations)
</script>

<style scoped>
* { box-sizing: border-box; }
.page {
  max-width: 1440px;
  margin: 0 auto;
  padding: 36px 40px 52px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif;
  font-size: 14px;
  color: #1f2937;
}

/* Page header */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  padding: 18px 20px;
  border: 1px solid #e5ece8;
  border-radius: 16px;
  background: linear-gradient(135deg, #fff 0%, #f4fbf7 100%);
  box-shadow: 0 12px 30px rgba(16,24,40,.055);
}
.page-head h1 { font-size: 24px; font-weight: 900; color: #101828; margin: 0; }
.page-head p { font-size: 13px; color: #667085; margin: 6px 0 0; }

.btn-refresh {
  display: inline-flex; align-items: center; gap: 6px;
  height: 40px;
  padding: 0 16px; border-radius: 10px;
  border: 1px solid #dce8e1; background: #fff;
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
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: #fff;
  border: 1px solid #edf2ef;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 8px 22px rgba(16,24,40,.045);
}
.sc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}
.sc-icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sc-icon .material-icons { font-size: 20px; }
.si-emerald { background: #ecfdf5; color: #059669; }
.si-green   { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.si-red     { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.si-gray    { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }
.sc-right { text-align: right; }
.sc-label { font-size: 12px; color: #667085; font-weight: 700; margin-bottom: 6px; }
.sc-num { font-size: 20px; font-weight: 900; color: #111827; font-variant-numeric: tabular-nums; line-height: 1; }
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

/* Pile section */
.pile-section {
  background: #fff;
  border: 1px solid #edf2ef;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(16,24,40,.055);
  margin-bottom: 22px;
  overflow: hidden;
}
.pile-section-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 22px; border-bottom: 1px solid #edf0ee;
}
.pile-section-head h2 { margin: 0; font-size: 16px; font-weight: 900; color: #101828; }
.pile-legend { display: flex; gap: 16px; }
.lg { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: #667085; font-weight: 600; }
.lg-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.lg-green { background: #10b981; }
.lg-red { background: #ef4444; }
.lg-gray { background: #b0b8c4; }

/* Grid layout filling container */
.pile-grid-wrap { padding: 20px 22px; }
.pile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

/* Individual station card */
.pile-card {
  background: #fff;
  border: 1.5px solid #e0ece5;
  border-radius: 16px;
  padding: 20px 16px 16px;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  transition: border-color .2s, box-shadow .2s, transform .2s;
  position: relative;
}
.pile-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(16,24,40,.08);
}
.pile-card.tone-green { border-color: #c6f0da; }
.pile-card.tone-green:hover { border-color: #6ee7a8; }
.pile-card.tone-red {
  border-color: #fecdd3;
  background: linear-gradient(180deg, #fff 60%, #fff5f5 100%);
}
.pile-card.tone-red:hover { border-color: #f87171; }
.pile-card.tone-gray {
  border-color: #e5e7eb;
  background: #fafbfc;
  opacity: .7;
}
.pile-card.tone-gray:hover { opacity: .9; border-color: #d1d5db; }

/* Charger icon visual */
.pc-charger-wrap { position: relative; }
.pc-charger {
  width: 56px; height: 56px; border-radius: 16px;
  display: grid; place-items: center;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  box-shadow: 0 6px 16px rgba(16,185,129,.12);
}
.pc-charger.tone-red {
  background: linear-gradient(135deg, #fef2f2, #fecdd3);
  box-shadow: 0 6px 16px rgba(239,68,68,.12);
}
.pc-charger.tone-gray {
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
  box-shadow: 0 6px 16px rgba(107,114,128,.08);
}
.pc-charger-icon { font-size: 26px; color: #059669; }
.tone-red .pc-charger-icon { color: #ef4444; }
.tone-gray .pc-charger-icon { color: #9ca3af; }

.pc-status-dot {
  position: absolute; bottom: -2px; right: -2px;
  width: 14px; height: 14px; border-radius: 50%;
  border: 2.5px solid #fff;
}
.pc-status-dot.tone-green { background: #10b981; animation: pulse-green 2s ease-in-out infinite; }
.pc-status-dot.tone-red { background: #ef4444; animation: pulse-red 1.5s ease-in-out infinite; }
.pc-status-dot.tone-gray { background: #b0b8c4; }

@keyframes pulse-green {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,.4); }
  50% { box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}
@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,.4); }
  50% { box-shadow: 0 0 0 5px rgba(239,68,68,0); }
}

/* Identity */
.pc-identity { text-align: center; }
.pc-name { display: block; font-size: 15px; font-weight: 900; color: #101828; margin-bottom: 2px; }
.pc-mode { display: block; font-size: 11px; font-weight: 800; color: #047857; margin-bottom: 6px; }
.pc-pill {
  display: inline-flex; align-items: center; height: 22px; padding: 0 10px;
  border-radius: 999px; font-size: 11px; font-weight: 850;
}
.pc-pill.tone-green { color: #047857; background: #ecfdf5; border: 1px solid #a7f3d0; }
.pc-pill.tone-red { color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; }
.pc-pill.tone-gray { color: #6b7280; background: #f3f4f6; border: 1px solid #e5e7eb; }

/* Service */
.pc-service {
  display: flex; align-items: center; gap: 6px; width: 100%;
  padding: 8px 10px; border-radius: 10px;
  background: #f8faf9; border: 1px solid #edf2ef;
  font-size: 12px; color: #9ca3af; font-weight: 600;
}
.pc-service.active { color: #101828; background: #f0fdf4; border-color: #bbf7d0; font-weight: 700; }
.pc-service-icon { font-size: 16px; }

/* Metrics 2×2 grid */
.pc-metrics {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1px;
  width: 100%; background: #edf2ef; border: 1px solid #edf2ef;
  border-radius: 10px; overflow: hidden;
}
.pc-m { background: #fff; padding: 8px 10px; text-align: center; }
.pc-m span { display: block; font-size: 10px; color: #98a2b3; font-weight: 700; margin-bottom: 2px; }
.pc-m strong { font-size: 13px; font-weight: 900; color: #101828; font-variant-numeric: tabular-nums; }
.pc-m strong small { font-size: 10px; font-weight: 600; color: #98a2b3; margin-left: 1px; }

/* Action buttons */
.pc-actions { display: flex; gap: 6px; width: 100%; flex-wrap: wrap; }
.act-btn {
  border: 1px solid transparent; cursor: pointer;
  border-radius: 8px; height: 32px; padding: 0 10px;
  font-size: 11px; font-weight: 800; transition: .15s;
  font-family: inherit;
  display: inline-flex; align-items: center; justify-content: center; gap: 3px;
  flex: 1;
}
.act-btn .material-icons { font-size: 15px; }
.act-start { color: #047857; background: #ecfdf3; border-color: #bbf7d0; }
.act-start:hover { background: #d1fae5; }
.act-off   { color: #475467; background: #f8fafc; border-color: #e5e7eb; }
.act-off:hover   { background: #eef2f6; }
.act-red   { color: #dc2626; background: #fff1f2; border-color: #fecdd3; }
.act-red:hover   { background: #ffe4e6; }
.act-blue  { color: #2563eb; background: #eff6ff; border-color: #bfdbfe; }
.act-blue:hover  { background: #dbeafe; }

.empty-row { padding: 60px 24px; text-align: center; color: #9ca3af; font-size: 14px; }

/* Queue toggle & list */
.pc-queue-toggle {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: 6px 10px; border-radius: 8px;
  background: #f8faf9; border: 1px solid #edf2ef;
  cursor: pointer; transition: background .15s;
  font-size: 12px; font-weight: 700; color: #667085;
  user-select: none;
}
.pc-queue-toggle:hover { background: #f0fdf4; border-color: #bbf7d0; color: #047857; }
.pc-toggle-icon { font-size: 18px; transition: transform .2s; }

.pc-queue-list {
  width: 100%; display: grid; gap: 4px;
  animation: fadeIn .18s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }

.pq-row {
  display: grid; grid-template-columns: 20px minmax(0,1fr) auto auto;
  align-items: center; gap: 6px;
  padding: 6px 8px; border-radius: 8px;
  border: 1px solid #edf2ef; background: #fff;
  font-size: 12px; transition: background .12s;
}
.pq-row:hover { background: #f8faf9; }
.pq-row.charging { background: #eff6ff; border-color: #bfdbfe; }
.pq-no { font-size: 10px; font-weight: 900; color: #9ca3af; text-align: center; }
.pq-user { font-weight: 700; color: #101828; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pq-energy { font-size: 11px; color: #6b7280; font-variant-numeric: tabular-nums; white-space: nowrap; }
.pq-status { font-style: normal; font-size: 11px; font-weight: 800; color: #9ca3af; white-space: nowrap; }
.pq-row.charging .pq-status { color: #2563eb; }
.pq-empty { padding: 12px; text-align: center; color: #d1d5db; font-size: 12px; }

/* Rules */
.rules-section { padding: 18px 20px; border: 1px solid #edf2ef; border-radius: 16px; background: #fff; box-shadow: 0 10px 26px rgba(16,24,40,.045); }
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
