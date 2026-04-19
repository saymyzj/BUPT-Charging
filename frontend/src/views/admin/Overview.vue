<template>
  <div class="admin-c-wrapper">
    

<!-- Top Navigation -->
<nav class="top-nav">
  <div class="nav-brand">⚡ 智能充电桩调度计费系统 · 管理端</div>
  <div class="nav-tabs">
    <router-link to="/admin/overview" class="nav-tab active">运营总览</router-link>
    <router-link to="/admin/records" class="nav-tab">记录中心</router-link>
    <router-link to="/admin/config" class="nav-tab">系统配置</router-link>
    <router-link to="/admin/statistics" class="nav-tab">统计分析</router-link>
    <router-link to="/admin/users" class="nav-tab">用户管理</router-link>
  </div>
  <div class="nav-right">
    <span class="nav-alert">🔔 告警<span class="badge">2</span></span>
    <span>管理员: 张三</span>
    <span class="nav-clock">{{ clock }}</span>
  </div>
</nav>

<div class="page-layout">
  <div class="content-area">
    <!-- KPI Strip -->
    <div class="kpi-strip">
      <div class="kpi-item">
        <span class="kpi-item-label">充电桩在线率</span>
        <span class="kpi-item-value">{{ displayKpis.onlineRate }}%</span>
        <span class="kpi-item-trend neutral">4/5 在线</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-item-label">今日完成</span>
        <span class="kpi-item-value">{{ displayKpis.todayCompleted }} 笔</span>
        <span class="kpi-item-trend up">↑ +3</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-item-label">等待人数</span>
        <span class="kpi-item-value">7人</span>
        <span class="kpi-item-trend neutral">快3 慢4</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-item-label">平均等待</span>
        <span class="kpi-item-value">12:32</span>
        <span class="kpi-item-trend up">↓ -2分</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-item-label">今日营收</span>
        <span class="kpi-item-value">¥1,247.50</span>
        <span class="kpi-item-trend up">↑ 15%</span>
      </div>
    </div>

    <!-- Inner Tab Bar -->
    <div class="tab-bar" id="tabBar">
      <button class="tab-btn" @click="switchTab('0', $event)" :class="{active: activeTab === '0'}">充电桩监控</button>
      <button class="tab-btn" @click="switchTab('1', $event)" :class="{active: activeTab === '1'}">队列管理</button>
      <button class="tab-btn" @click="switchTab('2', $event)" :class="{active: activeTab === '2'}">运营数据</button>
      <div class="tab-indicator" id="tabIndicator" :style="{ left: indicatorLeft + 'px', width: indicatorWidth + 'px' }"></div>
    </div>

    <!-- Tab 0: Charging Pile Monitor -->
    <div class="tab-content" id="tab-0" :class="{active: activeTab === '0'}">
      <div class="pile-grid">
        <!-- FAST_01 -->
        <div class="pile-card">
          <div class="pile-card-header">
            <span class="pile-code">FAST_01</span>
            <span class="pile-type-badge fast">快充 30kW</span>
          </div>
          <div class="pile-card-status">
            <span class="status-indicator charging"></span>
            <span class="status-text charging">充电中</span>
          </div>
          <div class="pile-card-body">
            <div class="pile-progress-bar"><div class="pile-progress-fill charging" :style="{ width: animationsReady ? '78%' : '0' }"></div></div>
            <div class="pile-info-grid">
              <span class="pile-info-label">用户</span><span class="pile-info-val">user_003</span>
              <span class="pile-info-label">电量</span><span class="pile-info-val">23.4 / 30 kWh</span>
              <span class="pile-info-label">预计完成</span><span class="pile-info-val">14:32</span>
              <span class="pile-info-label">当前费用</span><span class="pile-info-val" style="color:var(--primary)">¥35.10</span>
            </div>
          </div>
          <div class="pile-card-actions">
            <button class="pile-action-btn fault" @click="showModal('标记故障', '确定将 FAST_01 标记为故障状态吗？该桩将停止服务。', 'danger')">标记故障</button>
          </div>
        </div>

        <!-- FAST_02 -->
        <div class="pile-card gold-border">
          <div class="pile-card-header">
            <span class="pile-code">FAST_02</span>
            <span class="pile-type-badge fast">快充 30kW</span>
          </div>
          <div class="pile-card-status">
            <span class="status-indicator waiting"></span>
            <span class="status-text waiting">等待离场</span>
          </div>
          <div class="pile-card-body">
            <div class="pile-progress-bar"><div class="pile-progress-fill full" :style="{ width: animationsReady ? '100%' : '0' }"></div></div>
            <div class="pile-info-grid">
              <span class="pile-info-label">用户</span><span class="pile-info-val">user_007</span>
              <span class="pile-info-label">电量</span><span class="pile-info-val">30 / 30 kWh</span>
            </div>
            <div class="pile-overtime-info">超时 2 分钟 · 占位费 ¥1.00</div>
          </div>
          <div class="pile-card-actions">
            <button class="pile-action-btn fault" @click="showModal('标记故障', '确定将 FAST_02 标记为故障状态吗？', 'danger')">标记故障</button>
          </div>
        </div>

        <!-- SLOW_01 -->
        <div class="pile-card">
          <div class="pile-card-header">
            <span class="pile-code">SLOW_01</span>
            <span class="pile-type-badge slow">慢充 7kW</span>
          </div>
          <div class="pile-card-status">
            <span class="status-indicator charging"></span>
            <span class="status-text charging">充电中</span>
          </div>
          <div class="pile-card-body">
            <div class="pile-progress-bar"><div class="pile-progress-fill charging" :style="{ width: animationsReady ? '45%' : '0' }"></div></div>
            <div class="pile-info-grid">
              <span class="pile-info-label">用户</span><span class="pile-info-val">user_001</span>
              <span class="pile-info-label">电量</span><span class="pile-info-val">6.75 / 15 kWh</span>
              <span class="pile-info-label">预计完成</span><span class="pile-info-val">16:20</span>
              <span class="pile-info-label">当前费用</span><span class="pile-info-val" style="color:var(--primary)">¥10.13</span>
            </div>
          </div>
          <div class="pile-card-actions">
            <button class="pile-action-btn fault" @click="showModal('标记故障', '确定将 SLOW_01 标记为故障状态吗？', 'danger')">标记故障</button>
          </div>
        </div>

        <!-- SLOW_02 -->
        <div class="pile-card">
          <div class="pile-card-header">
            <span class="pile-code">SLOW_02</span>
            <span class="pile-type-badge slow">慢充 7kW</span>
          </div>
          <div class="pile-card-status">
            <span class="status-indicator idle"></span>
            <span class="status-text idle">空闲</span>
          </div>
          <div class="pile-card-body">
            <div class="pile-idle-center">空闲就绪<br><span style="font-size:12px;color:#aaa">上次使用: 13:45</span></div>
          </div>
          <div class="pile-card-actions">
            <button class="pile-action-btn fault" @click="showModal('标记故障', '确定将 SLOW_02 标记为故障状态吗？', 'danger')">标记故障</button>
          </div>
        </div>

        <!-- SLOW_03 -->
        <div class="pile-card fault-border">
          <div class="pile-card-header">
            <span class="pile-code">SLOW_03</span>
            <span class="pile-type-badge slow">慢充 7kW</span>
          </div>
          <div class="pile-card-status">
            <span class="status-indicator fault"></span>
            <span class="status-text fault">故障</span>
          </div>
          <div class="pile-card-body">
            <div class="pile-fault-info">14:18 通信超时<br><span style="font-size:12px">设备无响应，已自动停止服务</span></div>
          </div>
          <div class="pile-card-actions">
            <button class="pile-action-btn restore" @click="showModal('恢复充电桩', '确定将 SLOW_03 恢复为正常状态吗？请确认故障已排除。', 'confirm')">恢复</button>
          </div>
        </div>
      </div>

      <!-- Compact events below grid -->
      <div class="compact-events">
        <div class="compact-events-title">最近事件</div>
        <div class="compact-event-list">
          <div class="compact-event"><span class="compact-event-time">14:23:15</span><span class="compact-event-badge call">叫号</span><span>user_005 已被叫号</span></div>
          <div class="compact-event"><span class="compact-event-time">14:21:08</span><span class="compact-event-badge complete">充电完成</span><span>FAST_01 user_003 充电完成</span></div>
          <div class="compact-event"><span class="compact-event-time">14:18:45</span><span class="compact-event-badge fault">故障</span><span>SLOW_03 通信超时</span></div>
          <div class="compact-event"><span class="compact-event-time">14:15:22</span><span class="compact-event-badge request">新请求</span><span>user_012 快充25kWh</span></div>
          <div class="compact-event"><span class="compact-event-time">14:12:33</span><span class="compact-event-badge leave">离场提醒</span><span>user_007 等待离场</span></div>
        </div>
      </div>
    </div>

    <!-- Tab 1: Queue Management -->
    <div class="tab-content" id="tab-1" :class="{active: activeTab === '1'}">
      <div class="queue-columns">
        <!-- Fast Queue -->
        <div class="queue-panel">
          <div class="queue-panel-header">
            <div class="queue-panel-title">快充队列 <span class="queue-count-badge fast">3</span></div>
          </div>
          <div class="queue-panel-body">
            <div class="queue-user-card">
              <span class="queue-user-rank fast">1</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_005</div>
                <div class="queue-user-meta">需求 25kWh · 等待 8分12秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill fast" style="width:78%"></div></div>
                <div class="queue-priority-score">2.35</div>
              </div>
            </div>
            <div class="queue-user-card">
              <span class="queue-user-rank fast">2</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_009</div>
                <div class="queue-user-meta">需求 30kWh · 等待 5分45秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill fast" style="width:61%"></div></div>
                <div class="queue-priority-score">1.82</div>
              </div>
            </div>
            <div class="queue-user-card">
              <span class="queue-user-rank fast">3</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_012</div>
                <div class="queue-user-meta">需求 20kWh · 等待 2分10秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill fast" style="width:38%"></div></div>
                <div class="queue-priority-score">1.15</div>
              </div>
            </div>
          </div>
          <button class="queue-call-btn fast" @click="showModal('手动叫号', '确定对快充队列首位用户 user_005 进行叫号吗？', 'confirm')">手动叫号 — user_005</button>
        </div>

        <!-- Slow Queue -->
        <div class="queue-panel">
          <div class="queue-panel-header">
            <div class="queue-panel-title">慢充队列 <span class="queue-count-badge slow">4</span></div>
          </div>
          <div class="queue-panel-body">
            <div class="queue-user-card">
              <span class="queue-user-rank slow">1</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_008</div>
                <div class="queue-user-meta">需求 15kWh · 等待 11分20秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill slow" style="width:87%"></div></div>
                <div class="queue-priority-score">2.61</div>
              </div>
            </div>
            <div class="queue-user-card">
              <span class="queue-user-rank slow">2</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_010</div>
                <div class="queue-user-meta">需求 20kWh · 等待 7分55秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill slow" style="width:64%"></div></div>
                <div class="queue-priority-score">1.93</div>
              </div>
            </div>
            <div class="queue-user-card">
              <span class="queue-user-rank slow">3</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_011</div>
                <div class="queue-user-meta">需求 10kWh · 等待 4分30秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill slow" style="width:48%"></div></div>
                <div class="queue-priority-score">1.45</div>
              </div>
            </div>
            <div class="queue-user-card">
              <span class="queue-user-rank slow">4</span>
              <div class="queue-user-info">
                <div class="queue-user-name">user_013</div>
                <div class="queue-user-meta">需求 18kWh · 等待 1分15秒</div>
              </div>
              <div class="queue-priority-section">
                <div class="queue-priority-label">优先级</div>
                <div class="queue-priority-bar-bg"><div class="queue-priority-fill slow" style="width:29%"></div></div>
                <div class="queue-priority-score">0.88</div>
              </div>
            </div>
          </div>
          <button class="queue-call-btn slow" @click="showModal('手动叫号', '确定对慢充队列首位用户 user_008 进行叫号吗？', 'confirm')">手动叫号 — user_008</button>
        </div>
      </div>

      <div class="queue-stats">
        <div class="queue-stat-item">
          <div class="queue-stat-val">12:32</div>
          <div class="queue-stat-label">平均等待时间</div>
        </div>
        <div class="queue-stat-item">
          <div class="queue-stat-val">7</div>
          <div class="queue-stat-label">总等待人数</div>
        </div>
        <div class="queue-stat-item">
          <div class="queue-stat-val" style="color:var(--primary)">↓ 趋缓</div>
          <div class="queue-stat-label">队列趋势</div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Operations Data -->
    <div class="tab-content" id="tab-2" :class="{active: activeTab === '2'}">
      <div class="metrics-top-grid">
        <div class="metric-card">
          <div class="metric-card-val">{{ displayMetrics.m1 }}%</div>
          <div class="metric-card-label">利用率</div>
          <div class="metric-card-trend" style="color:var(--primary)">▲ 良好</div>
        </div>
        <div class="metric-card">
          <div class="metric-card-val">45:18</div>
          <div class="metric-card-label">平均完成时间</div>
          <div class="metric-card-trend" style="color:var(--primary)">▼ 优化中</div>
        </div>
        <div class="metric-card">
          <div class="metric-card-val">22:05</div>
          <div class="metric-card-label">最长等待时间</div>
          <div class="metric-card-trend" style="color:var(--secondary)">▲ 偏高</div>
        </div>
        <div class="metric-card">
          <div class="metric-card-val">{{ displayMetrics.m2 }}</div>
          <div class="metric-card-label">吞吐量 (次/h)</div>
          <div class="metric-card-trend" style="color:var(--primary)">▲ 正常</div>
        </div>
        <div class="metric-card">
          <div class="metric-card-val">{{ displayMetrics.m3 }}%</div>
          <div class="metric-card-label">偏差率</div>
          <div class="metric-card-trend" style="color:var(--accent)">— 可接受</div>
        </div>
        <div class="metric-card">
          <div class="metric-card-val">{{ displayMetrics.m4 }}</div>
          <div class="metric-card-label">今日总服务次数</div>
          <div class="metric-card-trend" style="color:var(--primary)">▲ 增长</div>
        </div>
      </div>

      <div class="ops-chart-section">
        <div class="ops-chart-title">今日运营统计</div>
        <div class="ops-chart-body">
          <div class="ops-bar-row" v-for="stat in opsStats" :key="stat.label">
            <span class="ops-bar-label">{{ stat.label }}</span>
            <div class="ops-bar-track">
              <div class="ops-bar-fill" :class="stat.color" :style="{ width: animationsReady ? (stat.count / opsTotal * 100) + '%' : '0' }">
                <span v-show="animationsReady">{{ stat.count }}</span>
              </div>
            </div>
            <span class="ops-bar-count">{{ stat.count }}</span>
          </div>
        </div>
      </div>

      <div class="export-section">
        <button class="export-btn" @click="showModal('导出报表', '将导出今日运营数据报表（CSV格式），确认导出？', 'confirm')">导出报表</button>
      </div>
    </div>
  </div>

  <!-- Right Sidebar: Event Feed -->
  <aside class="right-sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">实时动态</span>
      <span class="sidebar-live"><span class="sidebar-live-dot"></span> 实时</span>
    </div>
    <div class="sidebar-events">
      <div v-for="(ev, index) in eventsData" :key="index" class="sidebar-event" :class="{ new: ev.isNew }">
        <div class="sidebar-event-time">{{ ev.time }}</div>
        <div class="sidebar-event-row">
          <span class="sidebar-event-badge" :class="ev.type">{{ ev.typeName }}</span>
          <span class="sidebar-event-desc">{{ ev.desc }}</span>
        </div>
      </div>
    </div>
  </aside>
</div>

<!-- Modal -->
<div class="modal-overlay" :class="{ show: modal.show }" @click.self="closeModal">
  <div class="modal-box">
    <div class="modal-title">{{ modal.title }}</div>
    <div class="modal-text">{{ modal.text }}</div>
    <div class="modal-actions">
      <button class="modal-btn cancel" @click="closeModal">取消</button>
      <button class="modal-btn" :class="modal.type" @click="confirmStaticAction">确认</button>
    </div>
  </div>
</div>



  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { ElMessage } from 'element-plus';

const clock = ref('');
let clockInterval = null;

function updateClock() {
  clock.value = new Date().toLocaleTimeString('zh-CN', { hour12: false });
}

const modal = ref({ show: false, title: '', text: '', type: 'confirm' });
function showModal(title, text, type) {
  modal.value = { show: true, title, text, type };
}
function closeModal() {
  modal.value.show = false;
}
function confirmStaticAction() {
  ElMessage.info(`${modal.value.title} 当前仍为静态演示功能，尚未接真实后端接口`);
  closeModal();
}

const activeTab = ref('0');
const indicatorLeft = ref(0);
const indicatorWidth = ref(0);
const animationsReady = ref(false);

const kpis = ref({ onlineRate: 80, todayCompleted: 23 });
const displayKpis = ref({ onlineRate: 0, todayCompleted: 0 });
const displayMetrics = ref({ m1: 0, m2: 0, m3: 0, m4: 0 });

const opsStats = ref([
  { label: '完成', count: 23, color: 'teal' },
  { label: '取消', count: 4, color: 'rust' },
  { label: '超时', count: 2, color: 'gold' },
  { label: '中断', count: 1, color: 'gray' },
  { label: '故障', count: 1, color: 'rust' }
]);
const opsTotal = computed(() => opsStats.value.reduce((sum, item) => sum + item.count, 0));

function animateCounter(target, field, duration = 1000, isFloat = false) {
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const val = target * eased;
    if (field.startsWith('m')) {
      displayMetrics.value[field] = isFloat ? parseFloat(val.toFixed(1)) : Math.round(val);
    } else {
      displayKpis.value[field] = Math.round(val);
    }
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

const eventsData = ref([
  { time: '14:23:15', type: 'call', typeName: '叫号', desc: 'user_005 已被叫号', isNew: false },
  { time: '14:21:08', type: 'complete', typeName: '充电完成', desc: 'FAST_01 user_003 完成', isNew: false },
  { time: '14:18:45', type: 'fault', typeName: '故障', desc: 'SLOW_03 通信超时', isNew: false },
  { time: '14:15:22', type: 'request', typeName: '新请求', desc: 'user_012 快充25kWh', isNew: false },
  { time: '14:12:33', type: 'leave', typeName: '离场提醒', desc: 'user_007 等待离场', isNew: false },
  { time: '14:10:18', type: 'start', typeName: '开始充电', desc: 'FAST_02→user_007', isNew: false },
  { time: '14:08:05', type: 'request', typeName: '新请求', desc: 'user_009 快充30kWh', isNew: false },
  { time: '14:05:42', type: 'complete', typeName: '充电完成', desc: 'SLOW_02 user_006 完成', isNew: false },
  { time: '14:03:15', type: 'confirm', typeName: '确认到场', desc: 'user_004 已到达', isNew: false },
  { time: '14:01:08', type: 'call', typeName: '叫号', desc: 'user_004 已被叫号', isNew: false },
  { time: '13:58:22', type: 'request', typeName: '新请求', desc: 'user_011 慢充15kWh', isNew: false },
  { time: '13:55:30', type: 'start', typeName: '开始充电', desc: 'SLOW_02→user_006', isNew: false }
]);

const autoEvents = [
  { type: 'request', typeName: '新请求', desc: 'user_015 慢充12kWh' },
  { type: 'confirm', typeName: '确认到场', desc: 'user_005 已到达快充区' },
  { type: 'start', typeName: '开始充电', desc: 'FAST_01→user_005' },
  { type: 'call', typeName: '叫号', desc: 'user_009 已被叫号' },
  { type: 'complete', typeName: '充电完成', desc: 'SLOW_01 user_001 完成' },
  { type: 'leave', typeName: '离场提醒', desc: 'user_003 请尽快驶离' },
  { type: 'request', typeName: '新请求', desc: 'user_016 快充28kWh' },
  { type: 'fault', typeName: '故障恢复', desc: 'SLOW_03 已恢复上线' }
];
let autoIdx = 0;
let eventsInterval = null;

function switchTab(tabVal, event) {
  activeTab.value = tabVal;
  if(event) {
    indicatorLeft.value = event.target.offsetLeft;
    indicatorWidth.value = event.target.offsetWidth;
  }
  animationsReady.value = false;
  
  if (tabVal === '0') {
    displayKpis.value = { onlineRate: 0, todayCompleted: 0 };
  } else if (tabVal === '2') {
    displayMetrics.value = { m1: 0, m2: 0, m3: 0, m4: 0 };
  }
  
  setTimeout(() => {
    animationsReady.value = true;
    if (tabVal === '0') {
      animateCounter(kpis.value.onlineRate, 'onlineRate', 1000);
      animateCounter(kpis.value.todayCompleted, 'todayCompleted', 1200);
    } else if (tabVal === '2') {
      animateCounter(76.4, 'm1', 1200, true);
      animateCounter(4.6, 'm2', 1200, true);
      animateCounter(8.2, 'm3', 1200, true);
      animateCounter(31, 'm4', 1200, false);
    }
  }, 50);
}

onMounted(() => {
  updateClock();
  clockInterval = setInterval(updateClock, 1000);

  setTimeout(() => { 
    animationsReady.value = true; 
    switchTab('0', {target: document.querySelector('.tab-btn.active')}); 
  }, 300);

  eventsInterval = setInterval(() => {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN', { hour12: false });
    const ev = { ...autoEvents[autoIdx % autoEvents.length], time: timeStr, isNew: true };
    eventsData.value.unshift(ev);
    autoIdx++;
    if (eventsData.value.length > 20) eventsData.value.pop();
  }, 5000);
});

onUnmounted(() => {
  clearInterval(clockInterval);
  clearInterval(eventsInterval);
});
</script>

<style scoped>

* { margin: 0; padding: 0; box-sizing: border-box; }
.admin-c-wrapper {
  --bg: #faf8f5;
  --card: #ffffff;
  --primary: #2d6a4f;
  --secondary: #c45d3e;
  --accent: #d4a853;
  --text: #2c2c2c;
  --text-sec: #7a7a7a;
  --shadow: 0 4px 12px rgba(120,80,40,0.08);
  --nav-bg: #f5f0e8;
  --radius: 10px;
}
.admin-c-wrapper { 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
 }
h1, h2, h3, h4, h5 { font-family: Georgia, 'Times New Roman', serif; }

/* Top Nav */
.top-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: var(--nav-bg);
  border-bottom: 3px solid var(--accent);
  height: 56px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
}
.nav-brand { font-family: Georgia, serif; font-size: 18px; font-weight: 700; color: var(--primary); white-space: nowrap; }
.nav-tabs { display: flex; gap: 4px; }
.nav-tab {
  padding: 8px 18px; border-radius: 6px; cursor: pointer;
  font-size: 14px; color: var(--text-sec); transition: all 0.2s;
  border: none; background: none; text-decoration: none;
}
.nav-tab:hover { background: rgba(45,106,79,0.08); color: var(--text); }
.nav-tab.active { background: var(--primary); color: #fff; font-weight: 600; }
.nav-right { display: flex; align-items: center; gap: 16px; font-size: 14px; color: var(--text-sec); white-space: nowrap; }
.nav-alert { position: relative; cursor: pointer; }
.nav-alert .badge {
  position: absolute; top: -6px; right: -8px;
  background: var(--secondary); color: #fff; font-size: 10px;
  padding: 1px 5px; border-radius: 10px;
}
.nav-clock { font-variant-numeric: tabular-nums; font-weight: 600; color: var(--primary); }

/* Layout */
.page-layout {
  margin-top: 56px;
  display: flex;
  justify-content: center;
  min-height: calc(100vh - 56px);
}
.content-area {
  flex: 1;
  margin-right: 250px;
  max-width: 1400px;
  padding: 0 40px;
  margin-left: auto;
}
.right-sidebar {
  width: 250px; position: fixed; top: 56px; right: 0; bottom: 0;
  background: var(--card);
  border-left: 1px solid #e8e0d8;
  box-shadow: -2px 0 12px rgba(120,80,40,0.05);
  display: flex; flex-direction: column;
  z-index: 50;
}

/* KPI Strip */
.kpi-strip {
  background: var(--nav-bg);
  padding: 16px 28px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid #e8e0d8;
  margin: 0 -40px;
}
.kpi-item {
  display: flex; flex-direction: column; align-items: center;
  padding: 0 20px; flex: 1;
  border-right: 1px solid #ddd5c9;
}
.kpi-item:last-child { border-right: none; }
.kpi-item-label { font-size: 12px; color: var(--text-sec); margin-bottom: 4px; }
.kpi-item-value { font-size: 22px; font-weight: 700; color: var(--text); font-family: Georgia, serif; }
.kpi-item-trend { font-size: 11px; margin-top: 3px; font-weight: 600; }
.kpi-item-trend.up { color: var(--primary); }
.kpi-item-trend.down { color: var(--secondary); }
.kpi-item-trend.neutral { color: var(--text-sec); }

/* Inner Tab Bar */
.tab-bar {
  background: var(--card);
  padding: 0 28px;
  display: flex; gap: 0;
  border-bottom: 2px solid #e8e0d8;
  position: relative;
}
.tab-btn {
  padding: 14px 24px; border: none; background: none;
  font-size: 15px; font-weight: 600; color: var(--text-sec);
  cursor: pointer; position: relative; transition: color 0.2s;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--primary); }
.tab-indicator {
  position: absolute; bottom: -2px; height: 3px;
  background: var(--accent); border-radius: 2px;
  transition: left 0.35s ease, width 0.35s ease;
}

/* Tab Content */
.tab-content { padding: 24px 28px; display: none; }
.tab-content.active { display: block; animation: fadeSlide 0.35s ease; }
@keyframes fadeSlide {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Pile Cards Grid */
.pile-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
.pile-card {
  background: var(--card); border-radius: var(--radius);
  box-shadow: var(--shadow); overflow: hidden;
  border: 2px solid transparent; transition: all 0.3s;
  opacity: 0; animation: cardFadeIn 0.5s ease forwards;
}
.pile-card:nth-child(1) { animation-delay: 0s; }
.pile-card:nth-child(2) { animation-delay: 0.08s; }
.pile-card:nth-child(3) { animation-delay: 0.16s; }
.pile-card:nth-child(4) { animation-delay: 0.24s; }
.pile-card:nth-child(5) { animation-delay: 0.32s; }
@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.pile-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(120,80,40,0.12); }
.pile-card.fault-border { border-color: var(--secondary); animation: pulseBorder 2s infinite, cardFadeIn 0.5s ease forwards; }
.pile-card.gold-border { border-color: var(--accent); }
@keyframes pulseBorder {
  0%, 100% { border-color: var(--secondary); }
  50% { border-color: #e8a090; }
}
.pile-card-header {
  padding: 16px 18px 10px;
  display: flex; align-items: center; justify-content: space-between;
}
.pile-code { font-family: Georgia, serif; font-size: 20px; font-weight: 700; color: var(--text); }
.pile-type-badge {
  font-size: 11px; padding: 3px 10px; border-radius: 6px;
  font-weight: 600;
}
.pile-type-badge.fast { background: #e8f5e9; color: var(--primary); }
.pile-type-badge.slow { background: #fef3e2; color: #b8860b; }
.pile-card-status {
  padding: 0 18px 6px;
  display: flex; align-items: center; gap: 8px;
}
.status-indicator {
  width: 10px; height: 10px; border-radius: 50%;
}
.status-indicator.charging { background: var(--primary); animation: pulseDot 2s infinite; }
.status-indicator.waiting { background: var(--accent); animation: pulseDot 1.5s infinite; }
.status-indicator.idle { background: #bbb; }
.status-indicator.fault { background: var(--secondary); animation: pulseDot 1s infinite; }
@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.status-text { font-size: 14px; font-weight: 600; }
.status-text.charging { color: var(--primary); }
.status-text.waiting { color: #b8860b; }
.status-text.idle { color: var(--text-sec); }
.status-text.fault { color: var(--secondary); }
.pile-card-body { padding: 6px 18px 16px; }
.pile-progress-bar {
  width: 100%; height: 10px; background: #e8e0d8;
  border-radius: 5px; overflow: hidden; margin-bottom: 8px;
}
.pile-progress-fill {
  height: 100%; border-radius: 5px;
  transition: width 1.5s ease;
}
.pile-progress-fill.charging { background: var(--primary); }
.pile-progress-fill.full { background: var(--accent); }
.pile-info-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px 16px;
  font-size: 13px;
}
.pile-info-label { color: var(--text-sec); }
.pile-info-val { font-weight: 600; text-align: right; }
.pile-idle-center {
  text-align: center; padding: 24px 0; color: var(--text-sec);
  font-size: 15px;
}
.pile-fault-info {
  text-align: center; padding: 12px 0; color: var(--secondary);
  font-size: 14px; font-weight: 600;
}
.pile-overtime-info {
  text-align: center; padding: 8px 0;
  font-size: 13px; color: #b8860b;
}
.pile-card-actions {
  padding: 0 18px 14px;
  display: flex; gap: 8px;
}
.pile-action-btn {
  flex: 1; padding: 8px; border-radius: 8px; border: 1px solid;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s;
  background: transparent;
}
.pile-action-btn.fault { border-color: var(--secondary); color: var(--secondary); }
.pile-action-btn.fault:hover { background: var(--secondary); color: #fff; }
.pile-action-btn.restore { border-color: var(--primary); color: var(--primary); }
.pile-action-btn.restore:hover { background: var(--primary); color: #fff; }

/* Compact Event Strip (below pile grid) */
.compact-events {
  background: var(--nav-bg); border-radius: var(--radius);
  padding: 14px 18px;
}
.compact-events-title {
  font-size: 13px; font-weight: 600; color: var(--text-sec);
  margin-bottom: 8px;
}
.compact-event-list { display: flex; flex-direction: column; gap: 4px; }
.compact-event {
  display: flex; align-items: center; gap: 10px;
  font-size: 12px; padding: 4px 0;
}
.compact-event-time { color: var(--text-sec); font-variant-numeric: tabular-nums; }
.compact-event-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 3px; font-weight: 600;
}
.compact-event-badge.call { background: #e3f2fd; color: #1565c0; }
.compact-event-badge.complete { background: #e8f5e9; color: var(--primary); }
.compact-event-badge.fault { background: #fce4e4; color: var(--secondary); }
.compact-event-badge.request { background: #fef3e2; color: #b8860b; }
.compact-event-badge.leave { background: #f3e5f5; color: #7b1fa2; }

/* Tab 2: Queue Management */
.queue-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.queue-panel {
  background: var(--card); border-radius: var(--radius);
  box-shadow: var(--shadow); overflow: hidden;
}
.queue-panel-header {
  padding: 14px 18px; background: var(--nav-bg);
  border-bottom: 1px solid #e8e0d8;
  display: flex; align-items: center; justify-content: space-between;
}
.queue-panel-title {
  font-family: Georgia, serif; font-size: 16px; font-weight: 700;
  color: var(--primary); display: flex; align-items: center; gap: 8px;
}
.queue-count-badge {
  font-size: 12px; padding: 2px 10px; border-radius: 10px;
  color: #fff; font-weight: 700;
}
.queue-count-badge.fast { background: var(--primary); }
.queue-count-badge.slow { background: var(--accent); }
.queue-panel-body { padding: 12px; }
.queue-user-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: 8px;
  margin-bottom: 8px; background: #faf6f0;
  transition: all 0.2s; cursor: default;
}
.queue-user-card:hover { background: #f3ece0; transform: translateX(4px); }
.queue-user-rank {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 13px; color: #fff; flex-shrink: 0;
}
.queue-user-rank.fast { background: var(--primary); }
.queue-user-rank.slow { background: var(--accent); }
.queue-user-info { flex: 1; }
.queue-user-name { font-weight: 700; font-size: 14px; }
.queue-user-meta { font-size: 12px; color: var(--text-sec); margin-top: 2px; }
.queue-priority-section { text-align: right; min-width: 80px; }
.queue-priority-label { font-size: 11px; color: var(--text-sec); }
.queue-priority-bar-bg {
  width: 80px; height: 6px; background: #e8e0d8; border-radius: 3px;
  overflow: hidden; margin-top: 3px;
}
.queue-priority-fill { height: 100%; border-radius: 3px; }
.queue-priority-fill.fast { background: var(--primary); }
.queue-priority-fill.slow { background: var(--accent); }
.queue-priority-score { font-size: 12px; font-weight: 700; margin-top: 2px; }
.queue-call-btn {
  margin: 8px 14px 14px; padding: 10px; width: calc(100% - 28px);
  border: none; border-radius: 8px; font-size: 14px;
  font-weight: 700; cursor: pointer; transition: all 0.2s;
}
.queue-call-btn.fast { background: var(--primary); color: #fff; }
.queue-call-btn.fast:hover { background: #245a42; }
.queue-call-btn.slow { background: var(--accent); color: #fff; }
.queue-call-btn.slow:hover { background: #c09840; }
.queue-stats {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
  background: var(--card); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 20px;
}
.queue-stat-item { text-align: center; }
.queue-stat-val { font-size: 24px; font-weight: 700; color: var(--primary); font-family: Georgia, serif; }
.queue-stat-label { font-size: 12px; color: var(--text-sec); margin-top: 4px; }

/* Tab 3: Operations Data */
.metrics-top-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;
}
.metric-card {
  background: var(--card); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 22px; text-align: center;
  transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-3px); }
.metric-card-val {
  font-size: 32px; font-weight: 700; color: var(--primary);
  font-family: Georgia, serif;
}
.metric-card-label { font-size: 13px; color: var(--text-sec); margin-top: 6px; }
.metric-card-trend { font-size: 12px; margin-top: 6px; font-weight: 600; }

.ops-chart-section {
  background: var(--card); border-radius: var(--radius);
  box-shadow: var(--shadow); overflow: hidden; margin-bottom: 24px;
}
.ops-chart-title {
  padding: 14px 20px; background: var(--nav-bg);
  font-family: Georgia, serif; font-size: 16px; font-weight: 700;
  color: var(--primary); border-bottom: 1px solid #e8e0d8;
}
.ops-chart-body { padding: 24px; }
.ops-bar-row {
  display: flex; align-items: center; gap: 14px; margin-bottom: 16px;
}
.ops-bar-label { width: 70px; font-size: 14px; font-weight: 600; text-align: right; }
.ops-bar-track {
  flex: 1; height: 32px; background: #f0ebe4; border-radius: 8px;
  overflow: hidden; position: relative;
}
.ops-bar-fill {
  height: 100%; border-radius: 8px;
  display: flex; align-items: center; justify-content: flex-end;
  padding-right: 12px; color: #fff; font-size: 13px; font-weight: 700;
  transition: width 1.2s ease;
}
.ops-bar-fill.teal { background: var(--primary); }
.ops-bar-fill.rust { background: var(--secondary); }
.ops-bar-fill.gold { background: var(--accent); }
.ops-bar-fill.gray { background: var(--text-sec); }
.ops-bar-count { width: 40px; font-size: 16px; font-weight: 700; text-align: center; }

.export-section { text-align: center; padding: 10px 0; }
.export-btn {
  padding: 12px 36px; border: none; border-radius: 8px;
  background: var(--primary); color: #fff; font-size: 15px;
  font-weight: 700; cursor: pointer; transition: all 0.2s;
}
.export-btn:hover { background: #245a42; transform: translateY(-2px); }

/* Right Sidebar */
.sidebar-header {
  padding: 16px 18px;
  border-bottom: 1px solid #e8e0d8;
  display: flex; align-items: center; justify-content: space-between;
}
.sidebar-title {
  font-family: Georgia, serif; font-size: 15px; font-weight: 700;
  color: var(--primary);
}
.sidebar-live {
  display: flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--primary); font-weight: 600;
}
.sidebar-live-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #27ae60;
  animation: pulseDot 1.5s infinite;
}
.sidebar-events {
  flex: 1; overflow-y: auto; padding: 6px 0;
}
.sidebar-event {
  padding: 10px 16px; border-bottom: 1px solid #f8f4ee;
  transition: background 0.2s;
}
.sidebar-event:hover { background: #faf6f0; }
.sidebar-event.new { animation: sideSlide 0.4s ease; }
@keyframes sideSlide {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}
.sidebar-event-time { font-size: 11px; color: var(--text-sec); font-variant-numeric: tabular-nums; }
.sidebar-event-row { display: flex; align-items: center; gap: 6px; margin-top: 3px; }
.sidebar-event-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 3px; font-weight: 600;
}
.sidebar-event-badge.call { background: #e3f2fd; color: #1565c0; }
.sidebar-event-badge.complete { background: #e8f5e9; color: var(--primary); }
.sidebar-event-badge.fault { background: #fce4e4; color: var(--secondary); }
.sidebar-event-badge.request { background: #fef3e2; color: #b8860b; }
.sidebar-event-badge.leave { background: #f3e5f5; color: #7b1fa2; }
.sidebar-event-badge.start { background: #e0f7fa; color: #00838f; }
.sidebar-event-badge.confirm { background: #f0ebe4; color: var(--text-sec); }
.sidebar-event-desc { font-size: 12px; color: var(--text); }

/* Modal */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); z-index: 200;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.3s;
}
.modal-overlay.show { opacity: 1; pointer-events: auto; }
.modal-box {
  background: var(--card); border-radius: var(--radius);
  box-shadow: 0 12px 40px rgba(0,0,0,0.15); padding: 28px; width: 380px;
  transform: scale(0.9); transition: transform 0.3s;
}
.modal-overlay.show .modal-box { transform: scale(1); }
.modal-title { font-family: Georgia, serif; font-size: 18px; font-weight: 700; margin-bottom: 12px; }
.modal-text { font-size: 14px; color: var(--text-sec); margin-bottom: 20px; line-height: 1.6; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.modal-btn {
  padding: 8px 20px; border-radius: 8px; border: none;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.modal-btn.confirm { background: var(--primary); color: #fff; }
.modal-btn.confirm:hover { background: #245a42; }
.modal-btn.cancel { background: #f0ebe4; color: var(--text); }
.modal-btn.cancel:hover { background: #e8e0d8; }
.modal-btn.danger { background: var(--secondary); color: #fff; }
.modal-btn.danger:hover { background: #a84e33; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d4cec4; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #b8b0a4; }


.admin-c-wrapper {
  min-height: 100vh;
  overflow-x: hidden;
  background: var(--bg, #faf8f5);
}
</style>
