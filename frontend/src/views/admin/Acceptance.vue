<template>
  <div class="acceptance-page">
    <header class="page-head">
      <div>
        <h1>验收控制台</h1>
        <p>独立验收中枢：初始化数据、全局模拟时钟、样例执行队列与状态快照</p>
      </div>
      <div class="head-actions">
        <button class="ghost-btn" @click="loadAll"><span class="material-icons">refresh</span>刷新</button>
        <button class="ghost-btn" @click="initializeDatabase"><span class="material-icons">storage</span>初始化数据库</button>
        <button v-if="state?.enabled" class="tool-btn danger" @click="disableMode"><span class="material-icons">power_settings_new</span>关闭验收模式</button>
        <button class="primary-btn" @click="enableMode"><span class="material-icons">play_circle</span>启用验收模式</button>
      </div>
    </header>

    <section class="status-strip">
      <div class="strip-item">
        <span class="strip-icon ok-bg"><span class="material-icons">verified_user</span></span>
        <div><span class="label">验收模式</span><strong :class="state?.enabled ? 'ok' : 'muted'">{{ state?.enabled ? '已启用' : '未启用' }}</strong></div>
      </div>
      <div class="strip-item">
        <span class="strip-icon gray-bg"><span class="material-icons">schedule</span></span>
        <div><span class="label">模拟时间</span><strong>{{ clock }}</strong></div>
      </div>
      <div class="strip-item">
        <span class="strip-icon ok-bg"><span class="material-icons">play_arrow</span></span>
        <div><span class="label">执行状态</span><strong>{{ statusText }}</strong></div>
      </div>
      <div class="strip-item">
        <span class="strip-icon gray-bg"><span class="material-icons">flag</span></span>
        <div><span class="label">事件</span><strong>{{ state?.event_counts?.EXECUTED || 0 }}/{{ state?.event_counts?.TOTAL || 0 }}</strong></div>
      </div>
      <div class="strip-item">
        <span class="strip-icon ok-bg"><span class="material-icons">hub</span></span>
        <div><span class="label">正确性</span><strong :class="snapshot?.integrity?.ok === false ? 'bad' : 'ok'">{{ snapshot?.integrity?.ok === false ? '有异常' : '通过' }}</strong></div>
      </div>
      <div class="quick-links">
        <router-link to="/admin/overview" target="_blank"><span class="material-icons">dashboard</span>管理总览</router-link>
        <router-link to="/admin/records" target="_blank"><span class="material-icons">settings_input_component</span>设备控制</router-link>
        <router-link to="/admin/statistics" target="_blank"><span class="material-icons">monitoring</span>报表统计</router-link>
        <router-link to="/login" target="_blank"><span class="material-icons">login</span>登录页</router-link>
      </div>
    </section>

    <section class="account-strip">
      <div>
        <h2>验收账号入口</h2>
        <p>初始化或确认样例后生成账号。用户账号密码统一为 123456，可一键打开独立工作台。</p>
      </div>
      <button class="tool-btn strong" @click="openAllUserWorkspaces"><span class="material-icons">groups</span>打开所有用户工作台</button>
      <label class="demo-toggle" :class="{ disabled: !canEnableDemo }">
        <input v-model="demoNextEvent" type="checkbox" :disabled="!canEnableDemo" />
        <span>下个事件演示</span>
      </label>
      <div class="account-links">
        <a v-if="adminEntry" :href="adminEntry.url" target="_blank">admin</a>
        <a v-for="user in visibleUserEntries" :key="user.user_id" :href="user.url" target="_blank">{{ user.username }}</a>
        <button v-if="hiddenUserCount > 0" class="more-users" @click="openAllUserWorkspaces">...</button>
      </div>
    </section>

    <section class="control-panel">
      <div class="timeline-head">
        <div>
          <h2>模拟时间轴</h2>
          <p>拖动时间只定位模拟时刻；执行动作会按该时刻写入真实业务状态。</p>
        </div>
        <div class="timeline-tools">
          <label>起点 <input v-model="timelineStart" type="time" @change="normalizeTimelineBounds" /></label>
          <label>终点 <input v-model="timelineEnd" type="time" @change="normalizeTimelineBounds" /></label>
          <label>跳转 <input v-model="jumpTimeText" type="text" placeholder="08:20:30" /></label>
          <button class="tool-btn compact" @click="jumpToSpecifiedTime"><span class="material-icons">my_location</span>跳转</button>
          <div class="speed-group">
            <button v-for="speed in speeds" :key="speed" :class="{ active: playbackSpeed === speed }" @click="playbackSpeed = speed">{{ speed }}x</button>
          </div>
        </div>
      </div>
      <div class="timeline-row">
        <span>{{ timelineStart }}</span>
        <div class="timeline-frame">
          <div class="timeline-fill" :style="{ width: `${timelineProgress}%` }"></div>
          <button
            v-for="mark in timelineMarks"
            :key="mark.key"
            class="timeline-mark"
            :class="{ done: mark.done, failed: mark.failed }"
            :style="{ left: `${mark.left}%` }"
            :title="mark.title"
            @click="jumpToEvent(mark.event)"
          ></button>
          <input
            v-model.number="sliderSeconds"
            type="range"
            min="0"
            :max="timelineDuration"
            step="1"
            @input="handleSliderInput"
            @change="commitSliderTime"
          />
        </div>
        <span>{{ timelineEnd }}</span>
      </div>
      <div class="timeline-meta">
        <span>当前：{{ timelineClock }}</span>
        <span v-if="nextPendingEvent">下一事件：{{ nextPendingEvent.clock }} · {{ eventTitle(nextPendingEvent) }}</span>
        <span v-else>没有待执行事件</span>
      </div>
      <div class="control-actions">
        <button class="tool-btn" disabled title="验收执行不支持回溯；如需回看请使用快照历史"><span class="material-icons">keyboard_double_arrow_left</span>上一事件</button>
        <button class="tool-btn" @click="jumpRelative(1)"><span class="material-icons">keyboard_double_arrow_right</span>下一事件</button>
        <button class="tool-btn play" :disabled="isRunning" @click="startExecution"><span class="material-icons">play_arrow</span>开始执行</button>
        <button class="tool-btn play" @click="executeUntilNext"><span class="material-icons">double_arrow</span>执行到下一事件</button>
        <button class="tool-btn" @click="pauseExecution"><span class="material-icons">pause_circle</span>暂停执行</button>
        <button class="tool-btn danger" @click="executeAll"><span class="material-icons">fast_forward</span>立即执行至最终态</button>
      </div>
      <div v-if="snapshot?.integrity?.warnings?.length" class="integrity-box">
        <strong>正确性告警</strong>
        <span v-for="warning in snapshot.integrity.warnings" :key="warning">{{ warning }}</span>
      </div>
      <div v-if="actionLog.length" class="action-log">
        <span v-for="item in actionLog.slice(0, 4)" :key="item.id" :class="item.level">{{ item.text }}</span>
      </div>
    </section>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        <span class="material-icons">{{ tab.icon }}</span>{{ tab.label }}
      </button>
    </div>

    <section v-if="activeTab === 'overview'" class="workspace-grid">
      <div class="event-card">
        <div class="card-head">
          <h3>执行事件队列</h3>
          <span>{{ events.length }} 条</span>
        </div>
        <div class="event-list">
          <button
            v-for="event in events"
            :key="event.event_id"
            class="event-row"
            :class="{ current: event.at === simulationTime, executing: runningEventId === event.event_id, failed: event.status === 'FAILED' }"
            :title="eventTitle(event)"
            @click="selectEvent(event)"
          >
            <span class="event-time">{{ event.clock }}</span>
            <span class="event-main">{{ eventTitle(event) }}</span>
            <span class="event-status" :class="event.status">{{ event.status }}</span>
          </button>
        </div>
      </div>

      <div class="stations-card">
        <div class="card-head">
          <h3>当前状态总览</h3>
          <span>{{ snapshot?.clock || '--' }}</span>
        </div>
        <div class="station-grid">
          <article v-for="station in snapshot?.stations || []" :key="station.station_code" class="station-tile" :class="station.station_status.toLowerCase()">
            <div class="station-top">
              <strong>{{ station.display_name }}</strong>
              <span>{{ station.station_status }}</span>
            </div>
            <div class="lane">
              <div
                v-for="slot in station.queue_capacity"
                :key="slot"
                class="slot"
                :class="{ occupied: station.queue[slot - 1] }"
              >
                <template v-if="station.queue[slot - 1]">
                  <b>{{ station.queue[slot - 1].vehicle_code }}</b>
                  <small>{{ station.queue[slot - 1].charged_energy }}度 / ¥{{ station.queue[slot - 1].current_fee }}</small>
                </template>
                <template v-else>空位</template>
              </div>
            </div>
          </article>
        </div>
      </div>

      <aside class="waiting-card">
        <div class="card-head">
          <h3>等候区</h3>
          <span>{{ snapshot?.waiting_area_count || 0 }}/10</span>
        </div>
        <div class="waiting-list">
          <div v-for="item in snapshot?.waiting_area || []" :key="item.request_id" class="waiting-item">
            <b>{{ item.vehicle_code }}</b>
            <span>{{ item.queue_number }}</span>
            <em :class="item.charge_mode">{{ item.charge_mode }}</em>
            <small>{{ item.request_energy }} 度</small>
          </div>
          <div v-if="!snapshot?.waiting_area?.length" class="empty">暂无等候车辆</div>
        </div>
        <div v-if="snapshot?.fault_queue?.length" class="waiting-list fault-list">
          <div v-for="item in snapshot.fault_queue" :key="item.request_id" class="fault-queue-card">
            <b>{{ item.vehicle_code }}</b>
            <span>{{ item.charged_energy ?? 0 }}度 / ¥{{ item.current_fee ?? 0 }}</span>
            <em>故障队列</em>
          </div>
        </div>
      </aside>
    </section>

    <section v-if="activeTab === 'sample'" class="sample-grid">
      <div class="upload-card">
        <h3>载入 xlsx 验收样例</h3>
        <p>载入后先确认识别结果，可手动修正再开始执行。</p>
        <label class="upload-zone" for="acceptance-xlsx">
          <span class="material-icons">cloud_upload</span>
          <strong>拖拽文件到此处，或点击选择文件</strong>
          <small>支持 .xlsx 格式</small>
        </label>
        <input id="acceptance-xlsx" class="file-input" type="file" accept=".xlsx" @change="handleFileChange" />
        <div class="file-line">
          <label class="file-pick" for="acceptance-xlsx">选择文件</label>
          <span>{{ selectedFile?.name || '未选择文件' }}</span>
        </div>
        <button class="primary-btn full" :disabled="!selectedFile" @click="parseFile"><span class="material-icons">assignment</span>解析样例</button>
        <div v-if="parsed?.warnings?.length" class="warning-box">
          <div v-for="warning in parsed.warnings" :key="warning">{{ warning }}</div>
        </div>
      </div>
      <div class="events-editor">
        <div class="card-head">
          <h3>识别确认与修正</h3>
          <button class="primary-btn" :disabled="!editableEvents.length" @click="confirmEvents">确认事件列表</button>
        </div>
        <div class="editor-table">
          <div class="editor-head">
            <span>启用</span><span>时刻</span><span>原始事件</span><span>类型</span><span>车辆</span><span>桩</span><span>模式</span><span>数值</span>
          </div>
          <div v-for="event in editableEvents" :key="event.event_id" class="editor-row">
            <input v-model="event.enabled" type="checkbox" />
            <input v-model="event.at" />
            <input v-model="event.raw_text" />
            <select v-model="event.event_type">
              <option>APPLY</option>
              <option>CHANGE</option>
              <option>CANCEL_OR_STOP</option>
              <option>FAULT</option>
              <option>RECOVER</option>
            </select>
            <input v-model="event.vehicle_code" />
            <input v-model="event.station_code" />
            <select v-model="event.charge_mode">
              <option :value="null">--</option>
              <option>FAST</option>
              <option>SLOW</option>
            </select>
            <input v-model="event.value" type="number" step="0.1" />
          </div>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'snapshots'" class="snapshot-grid">
      <div class="history-list">
        <div class="card-head"><h3>快照历史</h3><button class="ghost-btn" @click="loadSnapshots">刷新</button></div>
        <button
          v-for="item in snapshotRows"
          :key="item.id"
          class="snapshot-row"
          :class="{ active: selectedSnapshotItem?.id === item.id, failed: item.snapshot?.integrity?.ok === false }"
          @click="selectSnapshot(item)"
        >
          <span class="snapshot-clock">{{ item.clock }}</span>
          <b>{{ phaseText(item.phase) }}</b>
          <small>{{ item.eventLabel }}</small>
          <em>等候区 {{ item.summary.waiting_area_count }}</em>
        </button>
      </div>
      <div class="snapshot-detail">
        <div class="card-head"><h3>事件前后状态</h3><span>{{ selectedSnapshot?.clock || snapshot?.clock || '--' }}</span></div>
        <div class="compare-grid">
          <section v-for="board in snapshotCompareBoards" :key="board.title" class="snapshot-board">
            <div class="snapshot-board-head">
              <strong>{{ board.title }}</strong>
              <span>{{ board.snapshot?.clock || '--' }}</span>
            </div>
            <div class="mini-stations">
              <article v-for="station in board.snapshot?.stations || []" :key="station.station_code" class="mini-station" :class="String(station.station_status || '').toLowerCase()">
                <div class="mini-station-top">
                  <b>{{ station.display_name || station.station_code }}</b>
                  <span>{{ station.station_status }}</span>
                </div>
                <div class="mini-lane">
                  <div v-for="slot in station.queue_capacity || 3" :key="slot" class="mini-slot" :class="{ occupied: station.queue?.[slot - 1] }">
                    <template v-if="station.queue?.[slot - 1]">
                      <b>{{ station.queue[slot - 1].vehicle_code }}</b>
                      <small>{{ station.queue[slot - 1].charged_energy }}度 / ¥{{ station.queue[slot - 1].current_fee }}</small>
                    </template>
                    <template v-else>空位</template>
                  </div>
                </div>
              </article>
            </div>
            <div class="mini-waiting">
              <b>等候区 {{ board.snapshot?.waiting_area_count || 0 }}/10</b>
              <div>
                <span v-for="item in board.snapshot?.waiting_area || []" :key="item.request_id">
                  {{ item.vehicle_code }} {{ item.queue_number }} {{ item.charge_mode }} {{ item.request_energy }}度
                </span>
              </div>
              <b v-if="board.snapshot?.fault_queue?.length">故障队列 {{ board.snapshot.fault_queue_count || board.snapshot.fault_queue.length }}</b>
              <div v-if="board.snapshot?.fault_queue?.length">
                <span v-for="item in board.snapshot.fault_queue" :key="item.request_id">
                  {{ item.vehicle_code }} {{ item.effective_queue_number || item.queue_number }} {{ item.charge_mode }} {{ item.request_energy }}度
                </span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'table'" class="table-card acceptance-table-card">
      <div class="card-head">
        <h3>表格视图</h3>
        <div class="card-actions">
          <span>由真实系统快照整理生成 · {{ tableSnapshotRows.length }} 行</span>
          <button class="tool-btn compact" @click="exportTableXlsx"><span class="material-icons">download</span>导出 xlsx</button>
        </div>
      </div>
      <table class="acceptance-table">
        <thead>
          <tr><th>时刻</th><th>事件</th><th>快充1</th><th>快充2</th><th>快充3</th><th>慢充1</th><th>慢充2</th><th>等候区</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in tableSnapshotRows" :key="row.id">
            <td class="time-cell">{{ row.time }}</td>
            <td class="event-cell">{{ row.event || '状态快照' }}</td>
            <td v-for="key in tableStationKeys" :key="key" class="station-cell">
              <div class="table-slot" :class="{ empty: !stationFor(row.snapshot, key)?.queue?.length, fault: stationFor(row.snapshot, key)?.station_status === 'FAULT' }">
                <template v-if="stationFor(row.snapshot, key)?.station_status === 'FAULT'">
                  <span class="empty-text danger-text">故障</span>
                </template>
                <template v-else-if="stationFor(row.snapshot, key)?.queue?.length">
                  <div v-for="item in stationFor(row.snapshot, key).queue" :key="item.request_id" class="charge-chip">
                    <b>{{ item.vehicle_code }}</b>
                    <span>{{ item.charged_energy }}度 / ¥{{ item.current_fee }}</span>
                    <em :class="item.status">{{ item.status === 'CHARGING' ? '充电中' : '排队' }}</em>
                  </div>
                </template>
                <span v-else class="empty-text">空闲</span>
              </div>
            </td>
            <td class="waiting-cell">
              <div v-if="row.snapshot?.waiting_area?.length || row.snapshot?.fault_queue?.length" class="waiting-cell-stack">
                <div v-if="row.snapshot?.waiting_area?.length" class="waiting-pills">
                  <span v-for="item in row.snapshot.waiting_area" :key="item.request_id">
                    <b>{{ item.vehicle_code }}</b>
                    <em :class="item.charge_mode">{{ item.charge_mode }}</em>
                    {{ item.request_energy }}度
                  </span>
                </div>
                <div v-if="row.snapshot?.fault_queue?.length" class="fault-table-list">
                  <div v-for="item in row.snapshot.fault_queue" :key="item.request_id" class="charge-chip fault-queue-chip">
                    <b>{{ item.vehicle_code }}</b>
                    <span>{{ item.charged_energy ?? 0 }}度 / ¥{{ item.current_fee ?? 0 }}</span>
                    <em>故障队列</em>
                  </div>
                </div>
              </div>
              <span v-else class="empty-text">空</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  disableAcceptance,
  enableAcceptance,
  executeAcceptanceAll,
  executeAcceptanceCurrent,
  executeAcceptanceUntil,
  exportAcceptanceXlsxUrl,
  getAcceptanceEvents,
  getAcceptanceSnapshot,
  getAcceptanceSnapshots,
  getAcceptanceState,
  initializeAcceptanceDatabase,
  parseAcceptanceXlsx,
  resetAcceptance,
  saveAcceptanceEvents,
  setAcceptanceStatus,
  setAcceptanceTime,
} from '@/api/charging'
import { unwrapResponseData } from '@/api/request'

const state = ref(null)
const events = ref([])
const snapshot = ref(null)
const snapshots = ref([])
const selectedSnapshotItem = ref(null)
const activeTab = ref('overview')
const selectedFile = ref(null)
const parsed = ref(null)
const editableEvents = ref([])
const playbackSpeed = ref(10)
const timelineStart = ref('06:00')
const timelineEnd = ref('11:00')
const jumpTimeText = ref('08:00:00')
const sliderSeconds = ref(0)
const isRunning = ref(false)
const isScrubbing = ref(false)
const runningEventId = ref('')
const actionLog = ref([])
const demoNextEvent = ref(false)
let refreshTimer = null

const tabs = [
  { key: 'overview', label: '执行总览', icon: 'dashboard' },
  { key: 'sample', label: '样例确认', icon: 'upload_file' },
  { key: 'snapshots', label: '快照历史', icon: 'history' },
  { key: 'table', label: '表格视图', icon: 'table_view' },
]
const speeds = [1, 5, 10, 60]
const tableStationKeys = ['FAST_01', 'FAST_02', 'FAST_03', 'SLOW_01', 'SLOW_02']

const simulationTime = computed(() => state.value?.simulation_time || '2026-05-20T06:00:00')
const clock = computed(() => simulationTime.value.slice(11, 19))
const timelineClock = computed(() => isScrubbing.value || isRunning.value ? timeFromSeconds(sliderSeconds.value).slice(11, 19) : clock.value)
const statusText = computed(() => ({ IDLE: '未启用', PAUSED: '暂停中', RUNNING: '执行中', COMPLETED: '已完成' }[state.value?.status] || state.value?.status || '--'))
const timelineStartMinutes = computed(() => clockToMinuteOfDay(timelineStart.value, 6 * 60))
const timelineEndMinutes = computed(() => clockToMinuteOfDay(timelineEnd.value, 11 * 60))
const timelineStartSeconds = computed(() => timelineStartMinutes.value * 60)
const timelineEndSeconds = computed(() => timelineEndMinutes.value * 60)
const timelineDuration = computed(() => Math.max(1, timelineEndSeconds.value - timelineStartSeconds.value))
const adminEntry = computed(() => {
  const admin = state.value?.accounts?.admin
  return admin ? { ...admin, url: `/admin/overview?token=${encodeURIComponent(admin.token)}` } : null
})
const userEntries = computed(() => (state.value?.accounts?.users || []).map(user => ({
  ...user,
  url: `/user/workspace?token=${encodeURIComponent(user.token)}`,
})))
const visibleUserEntries = computed(() => userEntries.value.slice(0, 7))
const hiddenUserCount = computed(() => Math.max(0, userEntries.value.length - visibleUserEntries.value.length))
const canEnableDemo = computed(() => events.value.some(event => event.source === 'XLSX'))
const tableRows = computed(() => {
  const rows = snapshots.value.map(item => item.snapshot?.table_row).filter(Boolean).reverse()
  if (snapshot.value?.table_row && !rows.find(row => row.time === snapshot.value.table_row.time && row.event === snapshot.value.table_row.event)) rows.push(snapshot.value.table_row)
  return rows
})
const tableSnapshotRows = computed(() => {
  const rowsByEvent = new Map()
  snapshots.value.forEach(item => {
    if (item.phase !== 'AFTER') return
    const key = item.event_id || `${item.snapshot_time}-${item.clock}`
    if (!rowsByEvent.has(key)) {
      rowsByEvent.set(key, {
        id: `snapshot-${item.id}`,
        time: item.clock,
        event: item.snapshot?.table_row?.event || item.snapshot?.events_at_time?.map(eventTitle).join('；') || phaseText(item.phase),
        snapshot: item.snapshot,
        eventId: item.event_id,
        sortTime: item.snapshot_time || item.snapshot?.snapshot_time || item.clock,
      })
    }
  })
  const rows = Array.from(rowsByEvent.values()).sort((a, b) => String(a.sortTime).localeCompare(String(b.sortTime)))
  const currentKey = snapshot.value?.table_row?.event || snapshot.value?.events_at_time?.map(eventTitle).join('；') || '当前状态'
  if (snapshot.value && !rows.find(row => row.time === snapshot.value.clock && row.event === currentKey)) {
    rows.push({
      id: `current-${snapshot.value.snapshot_time || snapshot.value.clock}`,
      time: snapshot.value.clock,
      event: currentKey,
      snapshot: snapshot.value,
      sortTime: snapshot.value.snapshot_time || snapshot.value.clock,
    })
  }
  return rows
})
const selectedSnapshot = computed(() => selectedSnapshotItem.value?.snapshot || null)
const snapshotPair = computed(() => {
  const target = selectedSnapshotItem.value
  if (!target?.event_id) return { before: null, after: null }
  return {
    before: snapshots.value.find(item => item.event_id === target.event_id && item.phase === 'BEFORE')?.snapshot || null,
    after: snapshots.value.find(item => item.event_id === target.event_id && item.phase === 'AFTER')?.snapshot || null,
  }
})
const snapshotCompareBoards = computed(() => [
  { title: '事件前', snapshot: snapshotPair.value.before || selectedSnapshot.value || snapshot.value },
  { title: '事件后', snapshot: snapshotPair.value.after || selectedSnapshot.value || snapshot.value },
])
const nextPendingEvent = computed(() => events.value.find(event => event.status === 'PENDING') || null)
const timelineProgress = computed(() => Math.max(0, Math.min(100, sliderSeconds.value / timelineDuration.value * 100)))
const executedFloorSeconds = computed(() => {
  const executed = events.value.filter(event => event.status === 'EXECUTED').map(event => secondsFromTime(event.at))
  return executed.length ? Math.max(...executed) : 0
})
const timelineMarks = computed(() => events.value.map((event, index) => ({
  key: `${event.event_id}-${index}`,
  event,
  left: Math.max(0, Math.min(100, secondsFromTime(event.at) / timelineDuration.value * 100)),
  done: event.status === 'EXECUTED',
  failed: event.status === 'FAILED',
  title: `${event.clock} ${eventTitle(event)} ${event.status}`,
})))
const snapshotRows = computed(() => snapshots.value.map(item => ({
  ...item,
  eventLabel: item.snapshot?.events_at_time?.map(eventTitle).join('；') || item.event_id || '当前状态',
})))

function clockToMinuteOfDay(value, fallback = 0) {
  const match = String(value || '').match(/^(\d{1,2}):(\d{2})/)
  if (!match) return fallback
  const hour = Math.min(23, Math.max(0, Number(match[1])))
  const minute = Math.min(59, Math.max(0, Number(match[2])))
  return hour * 60 + minute
}

function clockToSecondOfDay(value, fallback = 0) {
  const match = String(value || '').trim().match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/)
  if (!match) return fallback
  const hour = Math.min(23, Math.max(0, Number(match[1])))
  const minute = Math.min(59, Math.max(0, Number(match[2])))
  const second = Math.min(59, Math.max(0, Number(match[3] || 0)))
  return hour * 3600 + minute * 60 + second
}

function minuteOfDayFromTime(value) {
  const text = (value || '2026-05-20T06:00:00').slice(11, 16)
  return clockToMinuteOfDay(text, timelineStartMinutes.value)
}

function secondOfDayFromTime(value) {
  const text = (value || '2026-05-20T06:00:00').slice(11, 19)
  return clockToSecondOfDay(text, timelineStartSeconds.value)
}

function secondsFromTime(value) {
  return Math.max(0, Math.min(timelineDuration.value, secondOfDayFromTime(value) - timelineStartSeconds.value))
}

function timeFromSeconds(seconds) {
  const total = timelineStartSeconds.value + Math.max(0, Math.min(timelineDuration.value, Math.floor(Number(seconds) || 0)))
  const hour = Math.floor(total / 3600) % 24
  const minute = Math.floor((total % 3600) / 60)
  const second = total % 60
  return `2026-05-20T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:${String(second).padStart(2, '0')}`
}

function normalizeTimelineBounds() {
  const start = clockToMinuteOfDay(timelineStart.value, 6 * 60)
  const end = clockToMinuteOfDay(timelineEnd.value, 11 * 60)
  timelineStart.value = `${String(Math.floor(start / 60)).padStart(2, '0')}:${String(start % 60).padStart(2, '0')}`
  if (end <= start) {
    const fixed = Math.min(23 * 60 + 59, start + 60)
    timelineEnd.value = `${String(Math.floor(fixed / 60)).padStart(2, '0')}:${String(fixed % 60).padStart(2, '0')}`
    pushActionLog('终点必须晚于起点，已自动调整为起点后一小时', 'info')
  } else {
    timelineEnd.value = `${String(Math.floor(end / 60)).padStart(2, '0')}:${String(end % 60).padStart(2, '0')}`
  }
  sliderSeconds.value = secondsFromTime(simulationTime.value)
}

async function loadState() {
  const data = unwrapResponseData(await getAcceptanceState())
  state.value = data
  if (!isScrubbing.value) {
    sliderSeconds.value = secondsFromTime(data.simulation_time)
  }
}

async function loadEvents() {
  const data = unwrapResponseData(await getAcceptanceEvents())
  events.value = data.events || []
}

async function loadSnapshot() {
  const data = unwrapResponseData(await getAcceptanceSnapshot())
  snapshot.value = data
}

async function loadSnapshots() {
  const data = unwrapResponseData(await getAcceptanceSnapshots())
  snapshots.value = data.snapshots || []
  if (!selectedSnapshotItem.value && snapshots.value.length) {
    selectedSnapshotItem.value = snapshots.value[0]
  }
}

async function loadAll() {
  await loadState()
  await loadEvents()
  await loadSnapshot()
  await loadSnapshots()
}

async function refreshLivePanel() {
  if (isScrubbing.value) return
  await loadState()
  await loadEvents()
  await loadSnapshot()
}

async function enableMode() {
  isRunning.value = false
  await enableAcceptance({ sample_name: parsed.value?.sample_name || state.value?.sample_name || '手动验收' })
  await loadAll()
}

function handleSliderInput() {
  isRunning.value = false
  isScrubbing.value = true
}

async function commitSliderTime() {
  isRunning.value = false
  isScrubbing.value = false
  if (sliderSeconds.value < executedFloorSeconds.value) {
    sliderSeconds.value = executedFloorSeconds.value
    pushActionLog(`不能拖回已执行事件之前；已定位到 ${timeFromSeconds(sliderSeconds.value).slice(11, 19)}`, 'info')
  }
  await setAcceptanceTime({ simulation_time: timeFromSeconds(sliderSeconds.value) })
  await setAcceptanceStatus({ status: 'PAUSED' })
  await loadAll()
}

async function jumpToSpecifiedTime() {
  normalizeTimelineBounds()
  const targetSecondOfDay = clockToSecondOfDay(jumpTimeText.value, timelineStartSeconds.value)
  if (targetSecondOfDay < timelineStartSeconds.value || targetSecondOfDay > timelineEndSeconds.value) {
    pushActionLog(`跳转时间需在 ${timelineStart.value} - ${timelineEnd.value} 范围内`, 'info')
    return
  }
  sliderSeconds.value = targetSecondOfDay - timelineStartSeconds.value
  await commitSliderTime()
}

function nextEventIndex(direction) {
  if (!events.value.length) return -1
  const current = simulationTime.value
  if (direction > 0) return events.value.findIndex(event => event.at > current)
  for (let i = events.value.length - 1; i >= 0; i -= 1) {
    if (events.value[i].at < current) return i
  }
  return -1
}

async function jumpRelative(direction) {
  const index = nextEventIndex(direction)
  if (index < 0) return
  if (direction < 0) return
  await setAcceptanceTime({ simulation_time: events.value[index].at })
  await setAcceptanceStatus({ status: 'PAUSED' })
  await loadAll()
}

async function initializeDatabase() {
  isRunning.value = false
  await initializeAcceptanceDatabase({ user_count: 10 })
  parsed.value = null
  editableEvents.value = []
  await loadAll()
}

async function disableMode() {
  isRunning.value = false
  await disableAcceptance()
  await loadAll()
}

async function executeCurrent() {
  const currentEvents = events.value.filter(event => event.status === 'PENDING' && event.at === simulationTime.value)
  currentEvents.forEach(event => pushActionLog(`执行 ${event.clock} ${eventTitle(event)}`))
  await executeAcceptanceCurrent()
  runningEventId.value = ''
  await loadAll()
}

async function executeUntilNext() {
  const index = nextEventIndex(1)
  const target = index >= 0 ? events.value[index].at : simulationTime.value
  if (index >= 0) pushActionLog(`推进至 ${events.value[index].clock} 后执行`)
  await executeAcceptanceUntil({ target_time: target })
  await loadAll()
}

async function executeAll() {
  isRunning.value = false
  await executeAcceptanceAll()
  await loadAll()
}

async function pauseExecution() {
  isRunning.value = false
  await setAcceptanceStatus({ status: 'PAUSED' })
  await loadState()
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function startExecution() {
  if (isRunning.value) return
  isRunning.value = true
  await setAcceptanceStatus({ status: 'RUNNING' })
  pushActionLog(`开始按 ${playbackSpeed.value}x 推进模拟时间`)
  let localSecond = secondsFromTime(simulationTime.value)
  let lastSentSecond = Math.floor(localSecond)
  let lastTick = Date.now()
  let completed = false
  while (isRunning.value) {
    await loadEvents()
    const next = events.value.find(event => event.status === 'PENDING')
    const targetSecond = next ? Math.max(secondsFromTime(next.at), localSecond) : timelineDuration.value
    while (isRunning.value && localSecond < targetSecond) {
      const now = Date.now()
      const realDelta = Math.max(0, now - lastTick)
      lastTick = now
      const simulatedDelta = realDelta * playbackSpeed.value / 1000
      localSecond = Math.min(targetSecond, localSecond + simulatedDelta)
      const visibleSecond = localSecond >= targetSecond ? Math.floor(targetSecond) : Math.floor(localSecond)
      sliderSeconds.value = visibleSecond
      if (visibleSecond !== lastSentSecond) {
        lastSentSecond = visibleSecond
        await setAcceptanceTime({ simulation_time: timeFromSeconds(visibleSecond), advance_runtime: true })
        await setAcceptanceStatus({ status: 'RUNNING' })
        await loadState()
      }
      await sleep(120)
    }
    if (!isRunning.value) break
    if (!next) {
      await setAcceptanceTime({ simulation_time: timeFromSeconds(timelineDuration.value) })
      await setAcceptanceStatus({ status: 'COMPLETED' })
      completed = true
      break
    }
    runningEventId.value = next.event_id
    if (demoNextEvent.value && canEnableDemo.value) {
      openEventPage(next)
      pushActionLog(`已打开 ${next.clock} 的演示页面：${eventTitle(next)}`, 'info')
    }
    const nextSecond = secondsFromTime(next.at)
    if (nextSecond <= localSecond) {
      const currentTarget = timeFromSeconds(Math.floor(localSecond))
      await setAcceptanceTime({ simulation_time: currentTarget })
      pushActionLog(`补执行 ${next.clock} 至 ${currentTarget.slice(11, 19)} 的待执行事件`)
      await executeAcceptanceUntil({ target_time: currentTarget })
    } else {
      await setAcceptanceTime({ simulation_time: next.at })
      pushActionLog(`到达 ${next.clock}，执行 ${eventTitle(next)}`)
      await executeAcceptanceCurrent()
    }
    if (isRunning.value) {
      await setAcceptanceStatus({ status: 'RUNNING' })
    }
    runningEventId.value = ''
    await loadAll()
    localSecond = secondsFromTime(simulationTime.value)
    lastSentSecond = Math.floor(localSecond)
    lastTick = Date.now()
    await sleep(180)
  }
  isRunning.value = false
  runningEventId.value = ''
  if (!completed) {
    await setAcceptanceStatus({ status: 'PAUSED' })
  }
  await loadAll()
}

function handleFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function parseFile() {
  if (!selectedFile.value) return
  const data = unwrapResponseData(await parseAcceptanceXlsx(selectedFile.value))
  parsed.value = data
  applyScenarioTimeline(data.scenario, data.events || [])
  editableEvents.value = (data.events || []).map(item => ({ ...item }))
  activeTab.value = 'sample'
}

async function confirmEvents() {
  await resetAcceptance({ sample_name: parsed.value?.sample_name || 'xlsx 样例' })
  await saveAcceptanceEvents({ sample_name: parsed.value?.sample_name, events: editableEvents.value })
  await loadAll()
  activeTab.value = 'overview'
}

function selectEvent(event) {
  if (event.at < simulationTime.value) return
  setAcceptanceTime({ simulation_time: event.at }).then(loadAll)
}

function selectSnapshot(item) {
  selectedSnapshotItem.value = item
}

function openAllUserWorkspaces() {
  userEntries.value.forEach((user, index) => {
    window.setTimeout(() => {
      window.open(user.url, `acceptance_user_${user.user_id}`)
    }, index * 120)
  })
  pushActionLog(`已请求打开 ${userEntries.value.length} 个用户工作台`, 'info')
}

function openEventPage(event) {
  const url = eventPageUrl(event)
  if (url) window.open(url, `acceptance_event_${event.vehicle_code || event.station_code || 'admin'}`)
}

function openLinkedBusinessPage() {
  const event = nextPendingEvent.value || events.value.find(item => item.at === simulationTime.value) || events.value[0]
  if (event) openEventPage(event)
}

function exportTableXlsx() {
  window.open(exportAcceptanceXlsxUrl, 'acceptance_export_xlsx')
}

function jumpToEvent(event) {
  if (!event || event.at < simulationTime.value) return
  setAcceptanceTime({ simulation_time: event.at }).then(loadAll)
}

function eventTitle(event) {
  if (!event) return '--'
  return event.raw_text || [event.event_type, event.vehicle_code || event.station_code, event.charge_mode, event.value].filter(Boolean).join(' / ') || event.event_id
}

function applyScenarioTimeline(scenario, scenarioEvents = []) {
  const start = String(scenario?.start_time || '').slice(0, 5)
  const end = String(scenario?.end_time || '').slice(0, 5)
  if (/^\d{2}:\d{2}$/.test(start)) timelineStart.value = start
  if (/^\d{2}:\d{2}$/.test(end)) timelineEnd.value = end
  if (!scenario?.start_time && scenarioEvents.length) {
    const first = scenarioEvents.reduce((min, event) => Math.min(min, minuteOfDayFromTime(event.at)), 24 * 60)
    if (Number.isFinite(first)) timelineStart.value = `${String(Math.floor(first / 60)).padStart(2, '0')}:${String(first % 60).padStart(2, '0')}`
  }
  if (!scenario?.end_time && scenarioEvents.length) {
    const last = scenarioEvents.reduce((max, event) => Math.max(max, minuteOfDayFromTime(event.at)), 0)
    if (Number.isFinite(last)) {
      const padded = Math.min(23 * 60 + 59, last + 30)
      timelineEnd.value = `${String(Math.floor(padded / 60)).padStart(2, '0')}:${String(padded % 60).padStart(2, '0')}`
    }
  }
  normalizeTimelineBounds()
}

function stationFor(snapshotValue, stationCode) {
  return (snapshotValue?.stations || []).find(station => station.station_code === stationCode)
}

function pushActionLog(text, level = 'run') {
  actionLog.value.unshift({ id: `${Date.now()}-${Math.random()}`, text, level })
  actionLog.value = actionLog.value.slice(0, 8)
}

function eventPageUrl(event) {
  if (event.event_type === 'FAULT' || event.event_type === 'RECOVER') {
    return adminEntry.value ? `/admin/records?token=${encodeURIComponent(adminEntry.value.token)}` : '/login'
  }
  const user = userEntries.value.find(item => item.user_id === event.vehicle_code)
  if (!user) return ''
  const path = event.event_type === 'APPLY' ? '/user/workspace' : '/user/task'
  return `${path}?token=${encodeURIComponent(user.token)}`
}

function phaseText(phase) {
  return ({ BEFORE: '事件前', AFTER: '事件后', CURRENT: '当前', FINAL: '最终' }[phase] || phase)
}

function handleExternalAcceptanceEvent() {
  refreshLivePanel()
}

onMounted(() => {
  loadAll()
  refreshTimer = setInterval(refreshLivePanel, 1200)
  window.addEventListener('storage', handleExternalAcceptanceEvent)
})
onUnmounted(() => {
  isRunning.value = false
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  window.removeEventListener('storage', handleExternalAcceptanceEvent)
})
</script>

<style scoped>
.acceptance-page {
  --green: #059669;
  --green-strong: #00895f;
  --green-soft: #ecfdf3;
  --blue: #0b63f6;
  --blue-soft: #eff6ff;
  --red: #e11d48;
  --red-soft: #fff1f2;
  --amber: #f59e0b;
  --ink: #0f172a;
  --muted: #64748b;
  --line: #e5eaf0;
  max-width: 1500px;
  margin: 0 auto;
  padding: 22px 28px 34px;
  color: var(--ink);
  background:
    radial-gradient(circle at 4% 0%, rgba(16, 185, 129, .08), transparent 26%),
    linear-gradient(180deg, #fbfefd 0%, #f8fafc 100%);
}
.page-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 18px; }
.page-head h1 { margin: 0; font-size: 25px; line-height: 1.15; font-weight: 900; letter-spacing: 0; }
.page-head p { margin: 8px 0 0; color: var(--muted); font-size: 14px; }
.head-actions, .control-actions, .quick-links, .speed-group, .tabs { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
button, a { font: inherit; }
.primary-btn, .ghost-btn, .tool-btn {
  height: 38px;
  border-radius: 9px;
  border: 1px solid var(--line);
  padding: 0 14px;
  background: #fff;
  color: #334155;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  letter-spacing: 0;
}
.primary-btn { background: linear-gradient(180deg, #0aa872, #00895f); border-color: #00895f; color: #fff; box-shadow: 0 12px 24px rgba(5,150,105,.22); }
.primary-btn.full { width: 100%; }
.material-icons { font-size: 18px; line-height: 1; }
button:disabled { opacity: .55; cursor: not-allowed; }
.ghost-btn:hover, .tool-btn:hover { border-color: #9ee6ca; color: var(--green-strong); }
.tool-btn.strong { background: #f0fdf8; color: var(--green-strong); border-color: #bdebd6; }
.tool-btn.play { background: var(--blue-soft); color: var(--blue); border-color: #bfdbfe; }
.tool-btn.danger { background: var(--red-soft); color: var(--red); border-color: #fecdd3; }
.tool-btn.wide { min-width: 320px; }
.demo-toggle { height: 38px; display: inline-flex; align-items: center; gap: 8px; padding: 0 14px; border: 1px solid #bdebd6; border-radius: 9px; background: #f0fdf8; color: var(--green-strong); font-size: 13px; font-weight: 850; }
.demo-toggle input { accent-color: var(--green); }
.demo-toggle.disabled { opacity: .55; color: #64748b; border-color: var(--line); background: #f8fafc; }
.status-strip, .control-panel, .event-card, .stations-card, .waiting-card, .upload-card, .events-editor, .history-list, .snapshot-detail, .table-card {
  background: rgba(255,255,255,.92); border: 1px solid var(--line); border-radius: 14px; box-shadow: 0 12px 32px rgba(15,23,42,.06);
}
.status-strip { display: grid; grid-template-columns: repeat(5, minmax(145px, 1fr)) minmax(300px, auto); gap: 1px; overflow: hidden; margin-bottom: 14px; border-color: #b7ebcf; }
.strip-item { padding: 18px 18px; border-right: 1px solid #edf2f7; display: flex; align-items: center; gap: 12px; min-height: 72px; }
.strip-icon { width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto; }
.strip-icon.ok-bg { background: var(--green-soft); color: var(--green); }
.strip-icon.gray-bg { background: #f1f5f9; color: #64748b; }
.label { display: block; color: var(--muted); font-size: 12px; font-weight: 800; margin-bottom: 4px; }
.strip-item strong { display: block; font-size: 20px; line-height: 1.1; font-weight: 900; }
.ok { color: var(--green); }
.bad { color: var(--red); }
.muted { color: #98a2b3; }
.quick-links { justify-content: space-around; gap: 18px; padding: 14px 18px; }
.quick-links a { color: #0f766e; text-decoration: none; font-size: 12px; font-weight: 850; display: grid; justify-items: center; gap: 5px; min-width: 52px; }
.quick-links .material-icons { font-size: 21px; color: var(--green); }
.account-strip {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(260px, 340px) minmax(260px, 380px);
  gap: 14px;
  align-items: center;
  margin-bottom: 14px;
  padding: 18px 20px;
  background: rgba(255,255,255,.92);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(15,23,42,.05);
}
.account-strip h2 { margin: 0; font-size: 16px; font-weight: 900; }
.account-strip p { margin: 6px 0 0; color: var(--muted); font-size: 13px; line-height: 1.55; }
.account-links { grid-column: 1 / -1; display: flex; flex-wrap: nowrap; gap: 8px; overflow: hidden; justify-content: flex-start; padding-top: 2px; }
.account-links a, .more-users { min-width: 72px; height: 34px; padding: 0 12px; border-radius: 7px; background: #f4fdf8; color: #00895f; font-size: 12px; font-weight: 900; text-decoration: none; border: 1px solid #d4f2e2; display: inline-flex; align-items: center; justify-content: center; }
.more-users { min-width: 38px; cursor: pointer; }
.control-panel { padding: 18px 20px; margin-bottom: 14px; }
.timeline-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.timeline-head h2, .card-head h3, .upload-card h3 { margin: 0; font-size: 17px; font-weight: 900; }
.timeline-head p, .upload-card p { margin: 5px 0 0; color: var(--muted); font-size: 13px; }
.timeline-tools { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap; max-width: 760px; }
.timeline-tools label { height: 34px; display: inline-flex; align-items: center; gap: 6px; padding: 0 8px; border: 1px solid var(--line); border-radius: 9px; background: #fff; color: #475569; font-size: 12px; font-weight: 850; }
.timeline-tools input[type='time'] { width: 92px; border: 0; outline: 0; background: transparent; color: var(--ink); font-weight: 900; font: inherit; }
.tool-btn.compact { height: 34px; padding: 0 10px; }
.speed-group button { height: 30px; min-width: 48px; border: 1px solid var(--line); background: #fff; border-radius: 8px; font-weight: 850; color: #475569; }
.speed-group .active { background: var(--green); color: white; border-color: var(--green); box-shadow: 0 8px 18px rgba(5,150,105,.2); }
.timeline-row { display: grid; grid-template-columns: 48px 1fr 48px; align-items: center; gap: 10px; margin: 18px 0 8px; color: #475569; font-size: 13px; font-weight: 900; }
.timeline-frame { position: relative; height: 34px; display: flex; align-items: center; }
.timeline-frame::before { content: ""; position: absolute; left: 0; right: 0; top: 16px; height: 3px; border-radius: 999px; background: #cbd5e1; }
.timeline-fill { position: absolute; left: 0; top: 16px; height: 3px; border-radius: 999px; background: var(--green); pointer-events: none; }
.timeline-mark { position: absolute; top: 10px; z-index: 2; width: 13px; height: 13px; margin-left: -6px; border: 1px solid #fff; border-radius: 50%; background: transparent; box-shadow: inset 0 0 0 2px var(--amber), 0 0 0 1px #fbbf24; padding: 0; cursor: pointer; }
.timeline-mark.done { background: #10b981; box-shadow: 0 0 0 1px #34d399; }
.timeline-mark.failed { background: #ef4444; box-shadow: 0 0 0 1px #f87171; }
input[type='range'] { position: relative; z-index: 3; width: 100%; accent-color: #059669; background: transparent; }
.timeline-meta { display: flex; justify-content: space-between; gap: 16px; color: #475569; font-size: 13px; font-weight: 850; margin-bottom: 12px; }
.integrity-box { margin-top: 12px; padding: 10px 12px; border: 1px solid #fecdd3; border-radius: 10px; background: #fff1f2; color: #be123c; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 12px; font-weight: 780; }
.action-log { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.action-log span { padding: 6px 9px; border-radius: 8px; background: #f8fafc; color: #475467; border: 1px solid #e5e7eb; font-size: 12px; font-weight: 760; }
.action-log .run { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.action-log .info { background: #ecfdf3; color: #047857; border-color: #bbf7d0; }
.tabs { margin: 14px 0 12px; }
.tabs button { height: 40px; border: 1px solid var(--line); background: rgba(255,255,255,.92); border-radius: 9px; padding: 0 16px; display: flex; align-items: center; gap: 8px; font-weight: 850; color: #334155; box-shadow: 0 8px 18px rgba(15,23,42,.04); }
.tabs button.active { background: var(--green-soft); color: var(--green-strong); border-color: #b7ebcf; }
.tabs .material-icons { font-size: 18px; }
.workspace-grid { display: grid; grid-template-columns: 340px minmax(0, 1fr) 290px; gap: 14px; align-items: start; }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 15px 18px; border-bottom: 1px solid #edf2f7; }
.card-head span { color: var(--muted); font-size: 12px; font-weight: 850; }
.event-list { max-height: 560px; overflow: auto; padding: 8px; }
.event-row { width: 100%; display: grid; grid-template-columns: 72px minmax(0, 1fr) auto; gap: 8px; align-items: start; border: 1px solid transparent; background: #fff; border-radius: 9px; padding: 10px 12px; text-align: left; cursor: pointer; }
.event-row:hover, .event-row.current { background: #f0fdf4; border-color: #bbf7d0; }
.event-row.executing { background: #eff6ff; border-color: #93c5fd; box-shadow: inset 3px 0 0 #2563eb; }
.event-row.failed { background: #fff1f2; }
.event-time { color: var(--green-strong); font-weight: 900; font-size: 13px; }
.event-main { font-weight: 850; color: var(--ink); min-width: 0; white-space: normal; overflow-wrap: anywhere; line-height: 1.35; }
.event-status { border-radius: 999px; padding: 3px 7px; font-size: 11px; font-weight: 800; background: #f2f4f7; color: #667085; }
.event-status.EXECUTED { background: #dcfce7; color: #15803d; }
.event-status.PENDING { background: #fef3c7; color: #b45309; }
.event-status.FAILED { background: #ffe4e6; color: #be123c; }
.station-grid { padding: 14px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.station-tile { border: 1px solid #e5ece8; border-radius: 10px; padding: 12px; background: #fbfefc; }
.station-tile.fault { background: #fff1f2; border-color: #fecdd3; }
.station-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.station-top strong { font-size: 14px; }
.station-top span { font-size: 11px; border-radius: 999px; padding: 3px 7px; background: #dcfce7; color: #15803d; font-weight: 800; }
.fault .station-top span { background: #ffe4e6; color: #be123c; }
.lane { display: grid; gap: 7px; }
.slot { min-height: 48px; border-radius: 8px; border: 1px dashed #cbd5d1; display: grid; align-content: center; padding: 7px 9px; color: #98a2b3; font-weight: 750; font-size: 12px; }
.slot.occupied { border-style: solid; background: #fff; color: #344054; }
.slot b { font-size: 13px; }
.slot small { color: #667085; margin-top: 2px; }
.waiting-list { padding: 10px; display: grid; gap: 8px; max-height: 560px; overflow: auto; }
.waiting-item { display: grid; grid-template-columns: 42px 45px 48px 1fr; align-items: center; gap: 6px; border: 1px solid #e8efeb; border-radius: 10px; padding: 9px; background: #fff; }
.waiting-item em { font-style: normal; font-weight: 850; font-size: 11px; border-radius: 999px; padding: 3px 7px; text-align: center; }
.waiting-item em.FAST { background: #dbeafe; color: #1d4ed8; }
.waiting-item em.SLOW { background: #ffedd5; color: #c2410c; }
.fault-list { padding-top: 0; }
.fault-queue-card { min-height: 42px; display: flex; align-items: center; gap: 8px; border: 1px solid #fed7aa; border-radius: 8px; padding: 7px 9px; background: #fff7ed; color: #334155; font-weight: 820; }
.fault-queue-card b { color: var(--ink); font-weight: 900; }
.fault-queue-card span { color: #64748b; flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere; }
.fault-queue-card em { margin-left: auto; font-style: normal; border-radius: 999px; padding: 2px 7px; color: #c2410c; background: #ffedd5; font-size: 10px; font-weight: 900; white-space: nowrap; }
.empty { color: #98a2b3; text-align: center; padding: 24px 0; font-size: 13px; }
.sample-grid { display: grid; grid-template-columns: 380px minmax(0, 1fr); gap: 14px; align-items: start; }
.upload-card { padding: 20px; display: grid; gap: 14px; min-height: 410px; align-content: start; }
.upload-zone { height: 130px; border: 1px dashed #a7e0c7; border-radius: 10px; background: #fbfffd; display: grid; place-items: center; align-content: center; gap: 8px; color: #0f766e; text-align: center; cursor: pointer; }
.upload-zone .material-icons { font-size: 36px; color: #34c88a; }
.upload-zone strong { font-size: 13px; color: var(--ink); }
.upload-zone small { color: var(--muted); font-size: 12px; }
.file-input { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.file-line { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 13px; }
.file-pick { height: 30px; padding: 0 12px; border-radius: 8px; background: var(--green-soft); color: var(--green-strong); border: 1px solid #bdebd6; display: inline-flex; align-items: center; font-size: 12px; font-weight: 900; cursor: pointer; }
.warning-box { padding: 10px; border-radius: 10px; background: #fffbeb; color: #92400e; font-size: 12px; font-weight: 700; }
.editor-table { overflow: auto; max-height: 600px; }
.editor-head, .editor-row { display: grid; grid-template-columns: 52px 210px 1.15fr 150px 90px 120px 120px 90px; gap: 10px; align-items: center; padding: 9px 18px; min-width: 1080px; }
.editor-head { color: #475569; font-size: 12px; font-weight: 900; border-bottom: 1px solid #edf2ef; background: #fbfcfd; }
.editor-row { border-bottom: 1px solid #f1f5f3; }
.editor-row input, .editor-row select { height: 32px; border: 1px solid #dfe8e3; border-radius: 7px; padding: 0 10px; background: #fff; font-weight: 720; color: var(--ink); }
.snapshot-grid { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 16px; align-items: start; }
.history-list { max-height: 520px; overflow: hidden; }
.history-list .card-head { position: sticky; top: 0; z-index: 2; background: #fff; }
.snapshot-row { width: 100%; display: grid; grid-template-columns: 82px 1fr auto; gap: 10px; align-items: center; border: 0; border-bottom: 1px solid #edf2ef; background: #fff; padding: 12px 16px; text-align: left; cursor: pointer; }
.snapshot-row:hover, .snapshot-row.active { background: #f0fdf4; box-shadow: inset 3px 0 0 #10b981; }
.snapshot-row.failed { background: #fff7f7; }
.snapshot-row small { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ink); font-weight: 820; }
.snapshot-row em { font-style: normal; color: var(--green-strong); background: var(--green-soft); border-radius: 999px; padding: 3px 8px; font-size: 11px; font-weight: 900; }
.snapshot-clock { color: var(--green-strong); font-weight: 900; }
.snapshot-row b { display: none; }
.compare-grid { padding: 16px 20px 20px; display: grid; grid-template-columns: minmax(0, 1fr) 40px minmax(0, 1fr); gap: 12px; align-items: center; }
.compare-grid::before { content: "arrow_forward"; font-family: "Material Icons"; grid-column: 2; grid-row: 1; width: 36px; height: 36px; border-radius: 50%; background: var(--green-soft); color: var(--green); display: flex; align-items: center; justify-content: center; font-size: 28px; }
.compare-grid .snapshot-board:first-child { grid-column: 1; }
.compare-grid .snapshot-board:last-child { grid-column: 3; }
.snapshot-board { border: 1px solid #e5ece8; border-radius: 12px; overflow: hidden; background: #fbfefc; }
.snapshot-board-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-bottom: 1px solid #edf2ef; background: #fff; }
.snapshot-board-head strong { font-size: 14px; font-weight: 900; }
.snapshot-board-head span { color: var(--muted); font-size: 12px; font-weight: 850; }
.mini-stations { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; padding: 12px; }
.mini-station { border: 1px solid #e5ece8; border-radius: 10px; padding: 10px; background: #fff; }
.mini-station.fault { background: #fff1f2; border-color: #fecdd3; }
.mini-station-top { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 8px; font-size: 12px; font-weight: 900; }
.mini-station-top span { color: var(--green-strong); background: var(--green-soft); border-radius: 999px; padding: 2px 7px; font-weight: 900; font-size: 10px; }
.mini-lane { display: grid; gap: 6px; }
.mini-slot { min-height: 38px; border: 1px solid #e5ece8; border-radius: 8px; padding: 6px 8px; display: grid; align-content: center; color: #98a2b3; font-size: 11px; font-weight: 750; background: #fbfcfd; }
.mini-slot.occupied { border-style: solid; color: #344054; }
.mini-slot b { font-size: 12px; }
.mini-slot small { color: #667085; }
.mini-waiting { border-top: 1px solid #edf2ef; padding: 10px 12px; display: grid; gap: 8px; }
.mini-waiting b { font-size: 12px; }
.mini-waiting div { display: flex; flex-wrap: wrap; gap: 6px; }
.mini-waiting span { padding: 4px 7px; border-radius: 8px; background: #f8fafc; color: #475467; font-size: 11px; font-weight: 700; }
.table-card { overflow: hidden; }
.acceptance-table-card { overflow: auto; max-height: 680px; }
.card-actions { display: inline-flex; align-items: center; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.acceptance-table { min-width: 1760px; }
.acceptance-table th:nth-child(1) { width: 110px; }
.acceptance-table th:nth-child(2) { width: 190px; }
.acceptance-table th:nth-child(n+3):nth-child(-n+7) { width: 260px; }
.acceptance-table th:last-child { width: 270px; }
th, td { border-top: 1px solid #edf2ef; padding: 10px 12px; vertical-align: top; white-space: normal; font-size: 12px; line-height: 1.45; overflow: hidden; }
th { position: sticky; top: 0; z-index: 2; color: #475569; background: #fbfcfd; text-align: left; font-weight: 900; }
td { color: #344054; background: #fff; }
.acceptance-table tr:hover td { background: #fbfefc; }
.time-cell { color: var(--green-strong); font-weight: 900; font-variant-numeric: tabular-nums; }
.event-cell { color: var(--ink); font-weight: 900; }
.table-slot { min-height: 38px; display: grid; gap: 6px; align-content: start; min-width: 0; }
.table-slot.empty { align-content: center; }
.table-slot.fault { color: var(--red); }
.charge-chip { min-height: 32px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; width: 100%; min-width: 0; box-sizing: border-box; padding: 6px 8px; border: 1px solid #cdeee0; border-radius: 8px; background: #f4fdf8; color: #334155; font-weight: 820; }
.charge-chip b { color: var(--ink); font-weight: 900; }
.charge-chip span { color: #64748b; white-space: normal; overflow-wrap: anywhere; flex: 1 1 110px; min-width: 0; }
.charge-chip em { margin-left: auto; font-style: normal; border-radius: 999px; padding: 2px 7px; color: #00895f; background: #dff9ed; font-size: 10px; font-weight: 900; white-space: nowrap; }
.charge-chip em.QUEUED { background: #f1f5f9; color: #475569; }
.charge-chip.fault-queue-chip { border-color: #fed7aa; background: #fff7ed; }
.charge-chip.fault-queue-chip em { color: #c2410c; background: #ffedd5; }
.empty-text { display: inline-flex; min-height: 30px; align-items: center; color: #64748b; }
.danger-text { color: var(--red); font-weight: 900; }
.waiting-cell-stack { display: grid; gap: 8px; }
.fault-table-list { display: grid; gap: 6px; }
.waiting-pills { display: flex; flex-wrap: wrap; gap: 6px; }
.waiting-pills span { min-height: 28px; display: inline-flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 8px; border: 1px solid #fed7aa; background: #fff7ed; color: #7c2d12; font-weight: 850; }
.waiting-pills b { color: var(--ink); }
.waiting-pills em { font-style: normal; border-radius: 999px; padding: 2px 6px; font-size: 10px; font-weight: 900; }
.waiting-pills em.FAST { color: #0369a1; background: #e0f2fe; }
.waiting-pills em.SLOW { color: #c2410c; background: #ffedd5; }
:deep(.snapshot-board) { border: 1px solid #e5ece8; border-radius: 12px; overflow: hidden; background: #fbfefc; min-width: 0; }
:deep(.snapshot-board-head) { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-bottom: 1px solid #edf2ef; background: #fff; }
:deep(.snapshot-board-head strong) { font-size: 14px; font-weight: 900; }
:deep(.snapshot-board-head span) { color: var(--muted); font-size: 12px; font-weight: 850; }
:deep(.mini-stations) { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; padding: 12px; }
:deep(.mini-station) { border: 1px solid #e5ece8; border-radius: 10px; padding: 10px; background: #fff; min-width: 0; }
:deep(.mini-station.fault) { background: #fff1f2; border-color: #fecdd3; }
:deep(.mini-station-top) { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 12px; font-weight: 900; }
:deep(.mini-station-top span) { color: var(--green-strong); background: var(--green-soft); border-radius: 999px; padding: 2px 7px; font-weight: 900; font-size: 10px; white-space: nowrap; }
:deep(.mini-lane) { display: grid; gap: 6px; }
:deep(.mini-slot) { min-height: 38px; border: 1px solid #e5ece8; border-radius: 8px; padding: 6px 8px; display: grid; align-content: center; color: #98a2b3; font-size: 11px; font-weight: 750; background: #fbfcfd; }
:deep(.mini-slot.occupied) { color: #344054; background: #fff; border-color: #cdeee0; }
:deep(.mini-slot b) { font-size: 12px; font-weight: 900; }
:deep(.mini-slot small) { color: #667085; margin-top: 2px; }
:deep(.mini-waiting) { border-top: 1px solid #edf2ef; padding: 10px 12px; display: grid; gap: 8px; }
:deep(.mini-waiting b) { font-size: 12px; }
:deep(.mini-waiting div) { display: flex; flex-wrap: wrap; gap: 6px; }
:deep(.mini-waiting span) { padding: 4px 7px; border-radius: 8px; background: #f8fafc; color: #475467; font-size: 11px; font-weight: 700; }
.snapshot-board :deep(.snapshot-board-head) { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-bottom: 1px solid #edf2ef; background: #fff; }
.snapshot-board :deep(.snapshot-board-head strong) { font-size: 14px; font-weight: 900; }
.snapshot-board :deep(.snapshot-board-head span) { color: var(--muted); font-size: 12px; font-weight: 850; }
.snapshot-board :deep(.mini-stations) { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; padding: 12px; }
.snapshot-board :deep(.mini-station) { border: 1px solid #e5ece8; border-radius: 10px; padding: 10px; background: #fff; min-width: 0; }
.snapshot-board :deep(.mini-station.fault) { background: #fff1f2; border-color: #fecdd3; }
.snapshot-board :deep(.mini-station-top) { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 12px; font-weight: 900; }
.snapshot-board :deep(.mini-station-top span) { color: var(--green-strong); background: var(--green-soft); border-radius: 999px; padding: 2px 7px; font-weight: 900; font-size: 10px; white-space: nowrap; }
.snapshot-board :deep(.mini-lane) { display: grid; gap: 6px; }
.snapshot-board :deep(.mini-slot) { min-height: 38px; border: 1px solid #e5ece8; border-radius: 8px; padding: 6px 8px; display: grid; align-content: center; color: #98a2b3; font-size: 11px; font-weight: 750; background: #fbfcfd; }
.snapshot-board :deep(.mini-slot.occupied) { color: #344054; background: #fff; border-color: #cdeee0; }
.snapshot-board :deep(.mini-slot b) { font-size: 12px; font-weight: 900; }
.snapshot-board :deep(.mini-slot small) { color: #667085; margin-top: 2px; }
.snapshot-board :deep(.mini-waiting) { border-top: 1px solid #edf2ef; padding: 10px 12px; display: grid; gap: 8px; }
.snapshot-board :deep(.mini-waiting b) { font-size: 12px; }
.snapshot-board :deep(.mini-waiting div) { display: flex; flex-wrap: wrap; gap: 6px; }
.snapshot-board :deep(.mini-waiting span) { padding: 4px 7px; border-radius: 8px; background: #f8fafc; color: #475467; font-size: 11px; font-weight: 700; }
@media (max-width: 1180px) {
  .workspace-grid, .sample-grid, .snapshot-grid, .account-strip { grid-template-columns: 1fr; }
  .compare-grid { grid-template-columns: 1fr; }
  .compare-grid::before { display: none; }
  .compare-grid .snapshot-board:first-child, .compare-grid .snapshot-board:last-child { grid-column: auto; }
  .status-strip { grid-template-columns: repeat(2, 1fr); }
  .timeline-meta { display: grid; }
  .quick-links { justify-content: flex-start; }
  .account-links { justify-content: flex-start; }
  .account-links { grid-column: auto; }
}
</style>

<style>
.snapshot-board-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-bottom: 1px solid #edf2ef; background: #fff; }
.snapshot-board-head strong { font-size: 14px; font-weight: 900; }
.snapshot-board-head span { color: #64748b; font-size: 12px; font-weight: 850; }
.mini-stations { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; padding: 12px; }
.mini-station { border: 1px solid #e5ece8; border-radius: 10px; padding: 10px; background: #fff; min-width: 0; }
.mini-station.fault { background: #fff1f2; border-color: #fecdd3; }
.mini-station-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 12px; font-weight: 900; }
.mini-station-top span { color: #00895f; background: #ecfdf3; border-radius: 999px; padding: 2px 7px; font-weight: 900; font-size: 10px; white-space: nowrap; }
.mini-lane { display: grid; gap: 6px; }
.mini-slot { min-height: 38px; border: 1px solid #e5ece8; border-radius: 8px; padding: 6px 8px; display: grid; align-content: center; color: #98a2b3; font-size: 11px; font-weight: 750; background: #fbfcfd; }
.mini-slot.occupied { color: #344054; background: #fff; border-color: #cdeee0; }
.mini-slot b { font-size: 12px; font-weight: 900; }
.mini-slot small { color: #667085; margin-top: 2px; }
.mini-waiting { border-top: 1px solid #edf2ef; padding: 10px 12px; display: grid; gap: 8px; }
.mini-waiting b { font-size: 12px; }
.mini-waiting div { display: flex; flex-wrap: wrap; gap: 6px; }
.mini-waiting span { padding: 4px 7px; border-radius: 8px; background: #f8fafc; color: #475467; font-size: 11px; font-weight: 700; }
</style>
