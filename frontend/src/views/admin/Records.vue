<template>
  <div class="records-wrapper">
    <!-- TOP NAV -->
    <nav class="topnav">
      <div class="brand">⚡ 智能充电桩调度计费系统 · 管理端</div>
      <div class="tabs">
        <router-link to="/admin/overview" class="nav-tab">运营总览</router-link>
        <router-link to="/admin/records" class="nav-tab active">记录中心</router-link>
        <router-link to="/admin/config" class="nav-tab">系统配置</router-link>
        <router-link to="/admin/statistics" class="nav-tab">统计分析</router-link>
        <router-link to="/admin/users" class="nav-tab">用户管理</router-link>
      </div>
      <div class="right">
        <span class="alert-badge">🔔 告警<span class="dot">2</span></span>
        <span>管理员: 张三</span>
        <span>{{ clock }}</span>
      </div>
    </nav>

    <!-- STATS STRIP -->
    <div class="stats-strip">
      <div class="stat-item">今日请求 <span class="val">31</span>笔</div>
      <div class="stat-item">完成 <span class="val teal">23</span>笔(74.2%)</div>
      <div class="stat-item">异常 <span class="val terr">8</span>笔(25.8%)</div>
      <div class="stat-item">收入 <span class="val gold">¥1,247.50</span></div>
      <div class="stat-item">平均处理 <span class="val">45</span>分<span class="val">18</span>秒</div>
    </div>

    <!-- FILTER BAR -->
    <div class="filter-bar">
      <div class="pill-group">
        <div class="pill" :class="{active: timeFilter === 'today'}" @click="timeFilter = 'today'">今天</div>
        <div class="pill" :class="{active: timeFilter === '7d'}" @click="timeFilter = '7d'">近7天</div>
        <div class="pill" :class="{active: timeFilter === '30d'}" @click="timeFilter = '30d'">近30天</div>
        <div class="pill" :class="{active: timeFilter === 'custom'}" @click="timeFilter = 'custom'">自定义</div>
      </div>
      <select class="filter-select" v-model="modeFilter">
        <option value="all">模式: 全部</option>
        <option value="fast">快充</option>
        <option value="slow">慢充</option>
      </select>
      <select class="filter-select" v-model="statusFilter">
        <option value="all">状态: 全部</option>
        <option value="ongoing">进行中</option>
        <option value="done">已完成</option>
        <option value="error">异常</option>
      </select>
      <select class="filter-select" v-model="pileFilter">
        <option value="all">充电桩: 全部</option>
        <option value="FAST_01">FAST_01</option>
        <option value="FAST_02">FAST_02</option>
        <option value="SLOW_01">SLOW_01</option>
        <option value="SLOW_02">SLOW_02</option>
        <option value="SLOW_03">SLOW_03</option>
      </select>
      <input class="search-input" placeholder="搜索编号/用户..." v-model="searchQuery">
    </div>

    <!-- MAIN PANELS -->
    <div class="main-panels">
      <!-- LEFT LIST -->
      <div class="left-panel">
        <div class="list-scroll">
          <div
            v-for="(r, i) in pagedRequests"
            :key="r.id"
            class="req-card stagger"
            :class="{ selected: selectedReq && selectedReq.id === r.id }"
            :style="{ animationDelay: i * 0.04 + 's' }"
            @click="selectReq(r)"
          >
            <span class="req-id">{{ r.id }}</span>
            <span class="user-badge">{{ r.user }}</span>
            <span class="mode-badge" :class="r.mode === '快充' ? 'fast' : 'slow'">{{ r.mode }}</span>
            <span class="energy">{{ r.actual !== null ? r.actual + 'kWh' : r.need + 'kWh' }}</span>
            
            <span class="status-badge" :class="statusClass(r.status)">
              <span v-if="r.status === '充电中'" class="dot-anim"></span>
              <span v-if="r.status === '已支付'">✓ </span>
              {{ r.status }}
            </span>

            <span class="time">{{ r.time }}</span>
            <span class="fee">{{ r.fee !== null ? '¥' + r.fee.toFixed(2) : '-' }}</span>
          </div>
        </div>
        <div class="pagination" v-if="filteredRequests.length > 0">
          显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredRequests.length) }} 共 {{ filteredRequests.length }} 条 &nbsp;|&nbsp;
          <a href="#" @click.prevent="currentPage > 1 && currentPage--">&laquo;</a>
          <a href="#" v-for="p in totalPages" :key="p" :class="{active: currentPage === p}" @click.prevent="currentPage = p">{{ p }}</a>
          <a href="#" @click.prevent="currentPage < totalPages && currentPage++">&raquo;</a>
        </div>
      </div>
      
      <!-- RIGHT DETAIL -->
      <div class="right-panel">
        <div v-if="!selectedReq" class="detail-placeholder">
          📋 点击左侧请求查看详情
        </div>
        <template v-else>
          <div class="timeline-steps fade-in">
            <template v-for="(name, i) in stepNames" :key="name">
              <div v-if="i > 0" class="step-line" :class="{ completed: i <= currentStepIdx }"></div>
              <div class="step-wrap">
                <div class="step-dot" :class="{ completed: i < currentStepIdx, current: i === currentStepIdx }">
                  {{ i < currentStepIdx ? '✓' : (i + 1) }}
                </div>
                <div class="step-label">{{ name }}</div>
              </div>
            </template>
          </div>

          <!-- Charging Status -->
          <div v-if="selectedReq.status === '充电中'" class="progress-wrap fade-in">
            <h4 style="font-family: Georgia, serif; font-size: 14px; color: var(--primary); margin-bottom: 8px;">实时充电状态</h4>
            <div style="display: flex; justify-content: space-between; font-size: 13px; color: var(--text2); margin-bottom: 4px;">
              <span>{{ selectedReq.id }} - {{ selectedReq.user }}</span>
              <span>{{ selectedReq.pile }}</span>
            </div>
            <div class="progress-bar-outer">
              <div class="progress-bar-inner" :style="{ width: getPercentage(selectedReq) + '%' }"></div>
            </div>
            <div class="progress-info">
              <span>{{ selectedReq.actual || 0 }}kWh / {{ selectedReq.need }}kWh</span>
              <span>{{ getPercentage(selectedReq) }}%</span>
            </div>
            <div style="margin-top: 12px; font-size: 13px; color: var(--text2);">
              <span>模式: <b>{{ selectedReq.mode }}</b></span>&nbsp;&nbsp;
              <span>费用: <b style="color: var(--primary)">¥{{ selectedReq.fee ? selectedReq.fee.toFixed(2) : '-' }}</b></span>&nbsp;&nbsp;
              <span>开始时间: <b>{{ selectedReq.time }}</b></span>
            </div>
          </div>

          <!-- Detail Table -->
          <div v-else class="detail-section fade-in">
            <h4>请求详情</h4>
            <table class="detail-table">
              <tr><td>请求编号</td><td>{{ selectedReq.id }}</td></tr>
              <tr><td>用户</td><td>{{ selectedReq.user }}</td></tr>
              <tr><td>充电模式</td><td><span class="mode-badge" :class="selectedReq.mode === '快充' ? 'fast' : 'slow'">{{ selectedReq.mode }}</span></td></tr>
              <tr><td>需求电量</td><td>{{ selectedReq.need }}kWh</td></tr>
              <tr><td>实际电量</td><td>{{ selectedReq.actual !== null ? selectedReq.actual + 'kWh' : '-' }}</td></tr>
              <tr><td>请求时间</td><td>{{ detailData[selectedReq.id]?.reqTime || '2026-04-01 ' + selectedReq.time }}</td></tr>
              
              <template v-if="detailData[selectedReq.id]">
                <tr><td>叫号时间</td><td>{{ detailData[selectedReq.id].callTime }}</td></tr>
                <tr><td>确认时间</td><td>{{ detailData[selectedReq.id].confirmTime }}</td></tr>
                <tr><td>开始充电</td><td>{{ detailData[selectedReq.id].startTime }}</td></tr>
                <tr><td>结束时间</td><td>{{ detailData[selectedReq.id].endTime }}</td></tr>
              </template>
              
              <tr><td>充电桩</td><td>{{ selectedReq.pile }}</td></tr>
              <tr>
                <td>状态</td>
                <td>
                  <span class="status-badge" :class="statusClass(selectedReq.status)">
                    <span v-if="selectedReq.status === '已支付'">✓ </span>
                    {{ selectedReq.status }}
                  </span>
                </td>
              </tr>
            </table>

            <!-- Bill Info (If fee exists) -->
            <template v-if="selectedReq.fee !== null">
              <h4 style="border-top: 1px solid #f0ebe3; margin-top: 8px;">账单信息</h4>
              <table class="detail-table">
                <tr><td>计费模式</td><td>{{ detailData[selectedReq.id]?.billMode || '按电量' }}</td></tr>
                <tr><td>电费</td><td>¥{{ selectedReq.fee.toFixed(2) }}</td></tr>
                <tr><td>时长费</td><td>¥{{ detailData[selectedReq.id]?.timeFee.toFixed(2) || '0.00' }}</td></tr>
                <tr><td>占位费</td><td>¥{{ detailData[selectedReq.id]?.occFee.toFixed(2) || '0.00' }}</td></tr>
                <tr><td>合计</td><td class="bill-total">¥{{ (detailData[selectedReq.id]?.total || selectedReq.fee).toFixed(2) }}</td></tr>
                <tr>
                  <td>支付状态</td>
                  <td>
                    <span class="status-badge" :class="statusClass(detailData[selectedReq.id]?.payStatus || (selectedReq.status === '已支付' ? '已支付' : '未支付'))">
                      <span v-if="detailData[selectedReq.id]?.payStatus === '已支付' || selectedReq.status === '已支付'">✓ </span>
                      {{ detailData[selectedReq.id]?.payStatus || (selectedReq.status === '已支付' ? '已支付' : '未支付') }}
                    </span>
                  </td>
                </tr>
              </table>
            </template>
          </div>
        </template>
      </div>
    </div>

    <!-- EVENT LOG -->
    <div class="event-section">
      <div class="event-header" @click="eventsOpen = !eventsOpen">
        <h4>事件日志 (20条)</h4>
        <span class="event-arrow" :class="{ open: eventsOpen }">▼</span>
      </div>
      <div class="event-preview" v-show="!eventsOpen">
        <div class="event-mini" v-for="(e, i) in events.slice(0, 3)" :key="i">
          <span>{{ e.time.slice(0, 8) }}</span>
          <span class="event-type" :class="eventTypeClass(e.type)">{{ e.type }}</span>
          <span>{{ e.desc }}</span>
        </div>
      </div>
      <div class="event-list" :class="{ open: eventsOpen }">
        <div class="event-row" v-for="(e, i) in events" :key="i">
          <span class="event-time">{{ e.time }}</span>
          <span class="event-type" :class="eventTypeClass(e.type)">{{ e.type }}</span>
          <span class="event-desc">{{ e.desc }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const clock = ref('')
let clockInterval = null

onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval)
})

function updateClock() {
  clock.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

const timeFilter = ref('today')
const modeFilter = ref('all')
const statusFilter = ref('all')
const pileFilter = ref('all')
const searchQuery = ref('')
const eventsOpen = ref(false)

const selectedReq = ref(null)

const requests = ref([
  {id:'REQ-0031',user:'user_012',mode:'快充',need:25,actual:null,time:'14:15',status:'等待中',pile:'-',fee:null},
  {id:'REQ-0030',user:'user_009',mode:'快充',need:30,actual:null,time:'14:08',status:'等待中',pile:'-',fee:null},
  {id:'REQ-0029',user:'user_005',mode:'快充',need:25,actual:null,time:'13:55',status:'已叫号',pile:'FAST_01',fee:null},
  {id:'REQ-0028',user:'user_003',mode:'快充',need:30,actual:23.4,time:'13:20',status:'充电中',pile:'FAST_01',fee:35.10},
  {id:'REQ-0027',user:'user_007',mode:'快充',need:30,actual:30,time:'12:45',status:'等待离场',pile:'FAST_02',fee:45.00},
  {id:'REQ-0026',user:'user_001',mode:'慢充',need:15,actual:6.75,time:'12:30',status:'充电中',pile:'SLOW_01',fee:10.13},
  {id:'REQ-0025',user:'user_006',mode:'慢充',need:20,actual:20,time:'11:00',status:'已完成',pile:'SLOW_02',fee:30.00},
  {id:'REQ-0024',user:'user_004',mode:'快充',need:25,actual:25,time:'10:30',status:'已完成',pile:'FAST_01',fee:37.50},
  {id:'REQ-0023',user:'user_002',mode:'慢充',need:10,actual:10,time:'10:00',status:'已支付',pile:'SLOW_01',fee:15.00},
  {id:'REQ-0022',user:'user_011',mode:'慢充',need:15,actual:null,time:'09:45',status:'已取消',pile:'-',fee:null},
  {id:'REQ-0021',user:'user_008',mode:'快充',need:30,actual:18.5,time:'09:30',status:'已中断',pile:'FAST_02',fee:27.75},
  {id:'REQ-0020',user:'user_010',mode:'慢充',need:20,actual:null,time:'09:15',status:'未到场',pile:'SLOW_03',fee:null},
  {id:'REQ-0019',user:'user_014',mode:'快充',need:25,actual:25,time:'08:45',status:'已支付',pile:'FAST_01',fee:37.50},
  {id:'REQ-0018',user:'user_015',mode:'慢充',need:12,actual:12,time:'08:20',status:'已支付',pile:'SLOW_02',fee:18.00},
  {id:'REQ-0017',user:'user_016',mode:'快充',need:20,actual:20,time:'08:00',status:'已支付',pile:'FAST_02',fee:30.00}
])

const detailData = {
  'REQ-0025': {
    reqTime:'2026-04-01 11:00', callTime:'11:45', confirmTime:'11:46', startTime:'11:48', endTime:'14:40',
    billMode:'按电量', elecFee:30.00, timeFee:0, occFee:0, total:30.00, payStatus:'已支付'
  }
}

const events = [
  {time:'14:23:15',type:'SCHEDULE',desc:'叫号 user_005 → FAST_01'},
  {time:'14:21:08',type:'CHARGE',desc:'FAST_01 充电完成 user_003 28.5kWh'},
  {time:'14:18:45',type:'FAULT',desc:'SLOW_03 故障 通信超时'},
  {time:'14:15:22',type:'REQUEST',desc:'新请求 user_012 快充 25kWh'},
  {time:'14:12:33',type:'SESSION',desc:'FAST_02 user_007 等待离场'},
  {time:'14:10:18',type:'SCHEDULE',desc:'分配 user_007 → FAST_02'},
  {time:'14:08:05',type:'REQUEST',desc:'新请求 user_009 快充 30kWh'},
  {time:'14:05:42',type:'CHARGE',desc:'SLOW_02 充电完成 user_006 20kWh'},
  {time:'14:03:15',type:'CONFIRM',desc:'user_004 确认到场'},
  {time:'14:01:08',type:'SCHEDULE',desc:'叫号 user_004 → FAST_01'},
  {time:'13:58:22',type:'REQUEST',desc:'新请求 user_011 慢充 15kWh'},
  {time:'13:55:30',type:'SESSION',desc:'SLOW_02 开始充电 user_006'},
  {time:'13:52:18',type:'CANCEL',desc:'user_006_b 取消排队'},
  {time:'13:50:05',type:'REQUEST',desc:'新请求 user_008 慢充 15kWh'},
  {time:'13:45:20',type:'BILLING',desc:'生成账单 REQ-0023 ¥15.00'},
  {time:'13:42:15',type:'PAYMENT',desc:'user_002 支付 REQ-0023'},
  {time:'13:40:00',type:'CHARGE',desc:'SLOW_01 充电完成 user_002 10kWh'},
  {time:'13:35:30',type:'NO_SHOW',desc:'user_010 叫号超时 未到场'},
  {time:'13:32:00',type:'SCHEDULE',desc:'叫号 user_010 → SLOW_03'},
  {time:'13:30:00',type:'INTERRUPT',desc:'user_008_b 中断充电 FAST_02 18.5kWh'}
]

const stepNames = ['已提交','入队等待','已叫号','已确认','充电中','已完成']

const currentStepIdx = computed(() => {
  if (!selectedReq.value) return 0
  const m = {'等待中':1,'已叫号':2,'充电中':4,'等待离场':5,'已完成':5,'已支付':5,'已取消':1,'已中断':4,'未到场':2}
  return m[selectedReq.value.status] ?? 0
})

const filteredRequests = computed(() => {
  return requests.value.filter(r => {
    // Mode filter
    let modePass = true
    if (modeFilter.value === 'fast') modePass = r.mode === '快充'
    if (modeFilter.value === 'slow') modePass = r.mode === '慢充'
    // Status filter
    let statusPass = true
    if (statusFilter.value === 'ongoing') statusPass = ['等待中', '已叫号', '充电中'].includes(r.status)
    if (statusFilter.value === 'done') statusPass = ['已完成', '已支付', '等待离场'].includes(r.status)
    if (statusFilter.value === 'error') statusPass = ['已取消', '已中断', '未到场'].includes(r.status)
    // Pile filter
    let pilePass = true
    if (pileFilter.value !== 'all') pilePass = r.pile === pileFilter.value
    // Search filter
    let searchPass = true
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      searchPass = r.id.toLowerCase().includes(q) || r.user.toLowerCase().includes(q)
    }
    
    return modePass && statusPass && pilePass && searchPass
  })
})

const currentPage = ref(1)
const pageSize = ref(15)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredRequests.value.length / pageSize.value)))

const pagedRequests = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRequests.value.slice(start, start + pageSize.value)
})

watch([timeFilter, modeFilter, statusFilter, pileFilter, searchQuery], () => {
  currentPage.value = 1
})

function selectReq(req) {
  selectedReq.value = req
}

function getPercentage(r) {
  if (r.actual === null) return 0
  return Math.round((r.actual / r.need) * 100)
}

function statusClass(s) {
  const m = {'等待中':'waiting','已叫号':'called','充电中':'charging','等待离场':'wait-leave','已完成':'done','已支付':'paid','已取消':'cancelled','已中断':'interrupted','未支付': 'waiting','未到场':'noshow'}
  return m[s] || ''
}

function eventTypeClass(t) {
  const m = {SCHEDULE:'schedule',CHARGE:'charge',REQUEST:'request',FAULT:'fault',CANCEL:'cancel',NO_SHOW:'noshow',CONFIRM:'confirm',SESSION:'session',BILLING:'billing',PAYMENT:'payment',INTERRUPT:'interrupt'}
  return m[t] || ''
}
</script>

<style scoped>
.records-wrapper {
  --bg: #faf8f5; --card: #ffffff; --primary: #2d6a4f; --secondary: #c45d3e;
  --accent: #d4a853; --text: #2c2c2c; --text2: #7a7a7a; --shadow: 0 4px 12px rgba(120,80,40,0.08);
  --nav-bg: #f5f0e8; --radius: 10px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
}
h1, h2, h3, h4, h5 { font-family: Georgia, serif; }

/* NAV */
.topnav { background: var(--nav-bg); border-bottom: 3px solid var(--accent); display: flex; align-items: center; justify-content: space-between; padding: 0 28px; height: 56px; position: sticky; top: 0; z-index: 100; }
.topnav .brand { font-family: Georgia, serif; font-size: 16px; font-weight: 700; color: var(--primary); white-space: nowrap; }
.topnav .tabs { display: flex; gap: 4px; position: absolute; left: 50%; transform: translateX(-50%); }
.topnav .tabs a { padding: 8px 18px; border-radius: 6px; text-decoration: none; color: var(--text2); font-size: 14px; transition: all .2s; cursor: pointer; }
.topnav .tabs a:hover { background: rgba(45,106,79,.08); color: var(--primary); }
.topnav .tabs a.active { background: var(--primary); color: #fff; font-weight: 600; }
.topnav .right { display: flex; align-items: center; gap: 18px; font-size: 14px; color: var(--text2); white-space: nowrap; }
.topnav .alert-badge { position: relative; cursor: pointer; }
.topnav .alert-badge .dot { background: var(--secondary); color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 10px; margin-left: 2px; }

/* STATS STRIP */
.stats-strip { background: var(--nav-bg); padding: 14px 28px; display: flex; gap: 24px; align-items: center; border-bottom: 1px solid rgba(212,168,83,.2); }
.stat-item { display: flex; align-items: baseline; gap: 6px; font-size: 14px; color: var(--text2); }
.stat-item .val { font-size: 20px; font-weight: 700; color: var(--text); font-family: Georgia, serif; }
.stat-item .val.teal { color: var(--primary); }
.stat-item .val.terr { color: var(--secondary); }
.stat-item .val.gold { color: var(--accent); }

/* FILTER BAR */
.filter-bar { padding: 14px 28px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.pill-group { display: flex; gap: 0; }
.pill-group .pill { padding: 6px 14px; font-size: 13px; border: 1px solid #ddd; background: #fff; cursor: pointer; transition: all .2s; color: var(--text2); }
.pill-group .pill:first-child { border-radius: 6px 0 0 6px; }
.pill-group .pill:last-child { border-radius: 0 6px 6px 0; border-left: none; }
.pill-group .pill + .pill { border-left: none; }
.pill-group .pill.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.pill-group .pill:hover:not(.active) { background: rgba(45,106,79,.06); }
.filter-select { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; background: #fff; color: var(--text); cursor: pointer; }
.search-input { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; width: 180px; outline: none; transition: border .2s; }
.search-input:focus { border-color: var(--primary); }

/* MAIN PANELS */
.main-panels { display: flex; flex: 1; padding: 0 28px 0 28px; gap: 20px; min-height: 0; }

/* LEFT LIST */
.left-panel { width: 45%; display: flex; flex-direction: column; padding: 16px 0; }
.list-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.req-card { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); padding: 12px 16px; display: flex; align-items: center; gap: 12px; cursor: pointer; transition: all .25s; border-left: 3px solid transparent; }
.req-card:hover { box-shadow: 0 6px 18px rgba(120,80,40,.12); transform: translateY(-1px); }
.req-card.selected { border-left-color: var(--accent); background: #fffbf2; }
.req-card .req-id { font-weight: 700; font-size: 13px; color: var(--primary); min-width: 76px; }
.req-card .user-badge { font-size: 12px; color: var(--text2); min-width: 64px; }
.mode-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.mode-badge.fast { background: rgba(45,106,79,.1); color: var(--primary); }
.mode-badge.slow { background: rgba(212,168,83,.15); color: #a07d2e; }
.req-card .energy { font-size: 13px; color: var(--text); min-width: 60px; text-align: right; }
.status-badge { font-size: 11px; padding: 3px 10px; border-radius: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }
.status-badge.waiting { background: #eee; color: #888; }
.status-badge.called { background: rgba(212,168,83,.15); color: #a07d2e; }
.status-badge.charging { background: rgba(45,106,79,.1); color: var(--primary); }
.status-badge.charging .dot-anim { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); animation: pulse 1.2s infinite; }
.status-badge.wait-leave { background: rgba(212,168,83,.15); color: #a07d2e; }
.status-badge.done { background: rgba(45,106,79,.1); color: var(--primary); }
.status-badge.paid { background: rgba(45,106,79,.12); color: var(--primary); }
.status-badge.cancelled { background: rgba(196,93,62,.1); color: var(--secondary); }
.status-badge.interrupted { background: rgba(196,93,62,.1); color: var(--secondary); }
.status-badge.noshow { background: rgba(196,93,62,.1); color: var(--secondary); }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }
.req-card .time { font-size: 12px; color: var(--text2); min-width: 44px; text-align: right; }
.req-card .fee { font-size: 13px; font-weight: 700; color: var(--text); min-width: 60px; text-align: right; margin-left: auto; }
.pagination { padding: 12px 0; text-align: center; font-size: 13px; color: var(--text2); }
.pagination a { display: inline-block; padding: 4px 10px; margin: 0 2px; border-radius: 4px; text-decoration: none; color: var(--text2); border: 1px solid #ddd; transition: all .2s; }
.pagination a:hover, .pagination a.active { background: var(--primary); color: #fff; border-color: var(--primary); }

/* RIGHT DETAIL */
.right-panel { width: 55%; padding: 16px 0; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
.detail-placeholder { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text2); font-size: 15px; }

/* TIMELINE STEPS */
.timeline-steps { display: flex; align-items: center; justify-content: center; gap: 0; padding: 16px; background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); }
.step { display: flex; align-items: center; gap: 0; }
.step-dot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; border: 2px solid #ddd; color: #ddd; transition: all .3s; }
.step-dot.completed { background: var(--primary); border-color: var(--primary); color: #fff; }
.step-dot.current { background: var(--accent); border-color: var(--accent); color: #fff; animation: stepPulse 2s infinite; }
.step-label { font-size: 11px; color: var(--text2); text-align: center; margin-top: 4px; }
.step-line { width: 40px; height: 2px; background: #ddd; transition: background .3s; margin: 0 8px; transform: translateY(-10px); }
.step-line.completed { background: var(--primary); }
@keyframes stepPulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(212,168,83,.4); } 50% { box-shadow: 0 0 0 6px rgba(212,168,83,0); } }
.step-wrap { display: flex; flex-direction: column; align-items: center; z-index: 1; }

/* DETAIL TABLE */
.detail-section { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; }
.detail-section h4 { padding: 14px 18px; font-size: 14px; border-bottom: 1px solid #f0ebe3; color: var(--primary); margin: 0; }
.detail-table { width: 100%; border-collapse: collapse; }
.detail-table td { padding: 10px 18px; font-size: 13px; border-bottom: 1px solid #f8f4ee; }
.detail-table td:first-child { color: var(--text2); width: 120px; font-weight: 500; }
.detail-table tr:nth-child(even) { background: #fdfcfa; }
.detail-table tr:last-child td { border-bottom: none; }
.bill-total { font-weight: 700; color: var(--primary); font-size: 15px; text-align: left; }

/* PROGRESS BAR */
.progress-wrap { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); padding: 18px; }
.progress-bar-outer { height: 10px; background: #eee; border-radius: 5px; overflow: hidden; margin-top: 8px; }
.progress-bar-inner { height: 100%; background: var(--primary); border-radius: 5px; transition: width 1s ease; }
.progress-info { display: flex; justify-content: space-between; font-size: 13px; color: var(--text2); margin-top: 6px; }

/* EVENT LOG */
.event-section { margin: 0 28px 20px; background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; flex-shrink: 0; }
.event-header { padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; transition: background .2s; user-select: none; }
.event-header:hover { background: #fdfcfa; }
.event-header h4 { font-size: 14px; color: var(--primary); margin: 0; }
.event-arrow { transition: transform .3s; font-size: 14px; color: var(--text2); }
.event-arrow.open { transform: rotate(180deg); }
.event-preview { padding: 0 18px 14px; display: flex; gap: 12px; flex-wrap: wrap; }
.event-mini { font-size: 12px; color: var(--text2); display: flex; align-items: center; gap: 6px; }
.event-list { max-height: 0; overflow: hidden; transition: max-height .4s ease; }
.event-list.open { max-height: 600px; overflow-y: auto; }
.event-row { padding: 8px 18px; display: flex; align-items: center; gap: 12px; font-size: 13px; border-top: 1px solid #f8f4ee; transition: background .2s; }
.event-row:hover { background: #fdfcfa; }
.event-time { color: var(--text2); min-width: 64px; font-family: monospace; font-size: 12px; }
.event-type { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; min-width: 70px; text-align: center; }
.event-type.schedule { background: rgba(45,106,79,.1); color: var(--primary); }
.event-type.charge { background: rgba(45,106,79,.1); color: var(--primary); }
.event-type.request { background: rgba(45,106,79,.15); color: #1b4332; }
.event-type.fault { background: rgba(196,93,62,.1); color: var(--secondary); }
.event-type.cancel { background: rgba(196,93,62,.1); color: var(--secondary); }
.event-type.noshow { background: rgba(196,93,62,.1); color: var(--secondary); }
.event-type.interrupt { background: rgba(196,93,62,.1); color: var(--secondary); }
.event-type.confirm { background: rgba(212,168,83,.15); color: #a07d2e; }
.event-type.session { background: rgba(212,168,83,.15); color: #a07d2e; }
.event-type.billing { background: rgba(212,168,83,.15); color: #a07d2e; }
.event-type.payment { background: rgba(45,106,79,.1); color: var(--primary); }
.event-desc { color: var(--text); }

/* SCROLLBAR */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #ccc; }

/* ANIMATIONS */
.fade-in { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.stagger { opacity: 0; animation: fadeIn .3s ease forwards; }
</style>
