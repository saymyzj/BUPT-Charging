<template>
  <div class="admin-wrapper">
    <nav class="topnav">
      <div class="brand">⚡ 智能充电桩调度计费系统 · 管理端</div>
      <div class="tabs">
        <router-link to="/admin/overview" class="nav-tab">运营总览</router-link>
        <router-link to="/admin/records" class="nav-tab">记录中心</router-link>
        <router-link to="/admin/config" class="nav-tab">系统配置</router-link>
        <router-link to="/admin/statistics" class="nav-tab active">统计分析</router-link>
        <router-link to="/admin/users" class="nav-tab">用户管理</router-link>
      </div>
      <div class="right">
        <span class="alert-badge">🔔 告警<span class="dot">2</span></span>
        <span>管理员: 张三</span>
        <span>{{ clock }}</span>
      </div>
    </nav>

    <div class="page-content">
      <div class="header-section">
        <h2>统计分析</h2>
        <div class="filter-group">
          <button class="filter-btn active">今天</button>
          <button class="filter-btn">本周</button>
          <button class="filter-btn">本月</button>
          <button class="filter-btn">全年</button>
        </div>
      </div>

      <!-- KPI Overview -->
      <div class="kpi-cards">
        <div class="kpi-card">
          <div class="kpi-title">总营收</div>
          <div class="kpi-val gold">¥ 8,421.50</div>
          <div class="kpi-trend">↑ 12% 同比昨天</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">累计充电量</div>
          <div class="kpi-val teal">1,204.5 kWh</div>
          <div class="kpi-trend">↑ 8% 同比昨天</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">完单率</div>
          <div class="kpi-val">94.2%</div>
          <div class="kpi-trend trend-down">↓ 1.3% 同比昨天</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">平均等待时间</div>
          <div class="kpi-val terr">12分34秒</div>
          <div class="kpi-trend trend-down">↓ 2分0秒 同比昨天</div>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="charts-grid">
        <div class="chart-box full-width">
          <div class="chart-header">
            <h3>24小时充电量分布</h3>
          </div>
          <div class="chart-body">
            <!-- Mock Bar Chart -->
            <div class="mock-chart">
              <div class="bar-container" v-for="i in 24" :key="i">
                <div class="bar-fill" :style="{ height: Math.random() * 80 + 20 + '%' }"></div>
                <div class="bar-label">{{ i - 1 }}时</div>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-box">
          <div class="chart-header">
            <h3>快慢充使用占比</h3>
          </div>
          <div class="chart-body flex-center">
            <!-- Mock Pie Info -->
            <div class="stats-row">
              <div class="stats-dot fast"></div>
              <div class="stats-label">快充桩单数</div>
              <div class="stats-num">68% <span class="sub">(124单)</span></div>
            </div>
            <div class="stats-row">
              <div class="stats-dot slow"></div>
              <div class="stats-label">慢充桩单数</div>
              <div class="stats-num">32% <span class="sub">(59单)</span></div>
            </div>
          </div>
        </div>

        <div class="chart-box">
          <div class="chart-header">
            <h3>故障原因分析</h3>
          </div>
          <div class="chart-body flex-center">
            <div class="stats-row">
              <div class="stats-dot fault-red"></div>
              <div class="stats-label">设备离线</div>
              <div class="stats-num">45%</div>
            </div>
            <div class="stats-row">
              <div class="stats-dot fault-org"></div>
              <div class="stats-label">通信超时</div>
              <div class="stats-num">35%</div>
            </div>
            <div class="stats-row">
              <div class="stats-dot fault-yel"></div>
              <div class="stats-label">过载保护</div>
              <div class="stats-num">20%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

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
</script>

<style scoped>
.admin-wrapper {
  --bg: #faf8f5; --card: #ffffff; --primary: #2d6a4f; --secondary: #c45d3e;
  --accent: #d4a853; --text: #2c2c2c; --text2: #7a7a7a; --shadow: 0 4px 12px rgba(120,80,40,0.08);
  --nav-bg: #f5f0e8; --radius: 10px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column;
}
h2, h3, h4 { font-family: Georgia, serif; }

/* NAV */
.topnav { background: var(--nav-bg); border-bottom: 3px solid var(--accent); display: flex; align-items: center; justify-content: space-between; padding: 0 28px; height: 56px; position: sticky; top: 0; z-index: 100; }
.topnav .brand { font-family: Georgia, serif; font-size: 16px; font-weight: 700; color: var(--primary); white-space: nowrap; }
.topnav .tabs { display: flex; gap: 4px; position: absolute; left: 50%; transform: translateX(-50%); }
.topnav .tabs .nav-tab { padding: 8px 18px; border-radius: 6px; text-decoration: none; color: var(--text2); font-size: 14px; transition: all .2s; cursor: pointer; }
.topnav .tabs .nav-tab:hover { background: rgba(45,106,79,.08); color: var(--primary); }
.topnav .tabs .nav-tab.active { background: var(--primary); color: #fff; font-weight: 600; }
.topnav .right { display: flex; align-items: center; gap: 18px; font-size: 14px; color: var(--text2); white-space: nowrap; }
.topnav .alert-badge { position: relative; cursor: pointer; }
.topnav .alert-badge .dot { background: var(--secondary); color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 10px; margin-left: 2px; }

/* CONTENT */
.page-content { padding: 32px 40px; max-width: 1400px; margin: 0 auto; width: 100%; flex: 1; }
.header-section { margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
.header-section h2 { font-size: 24px; color: var(--primary); margin: 0; }

.filter-group { display: flex; gap: 8px; }
.filter-btn { padding: 6px 16px; border: 1px solid #ddd; background: #fff; border-radius: 6px; font-size: 13px; color: var(--text2); cursor: pointer; transition: all 0.2s; }
.filter-btn:hover { background: #f0ebe4; }
.filter-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }

.kpi-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
.kpi-card { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); padding: 24px; text-align: center; }
.kpi-title { font-size: 14px; color: var(--text2); margin-bottom: 12px; }
.kpi-val { font-size: 28px; font-weight: 700; font-family: Georgia, serif; margin-bottom: 8px; }
.kpi-val.gold { color: var(--accent); }
.kpi-val.teal { color: var(--primary); }
.kpi-val.terr { color: var(--secondary); }
.kpi-trend { font-size: 12px; color: #27ae60; font-weight: 600; }
.kpi-trend.trend-down { color: var(--secondary); }

.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
.chart-box { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; display: flex; flex-direction: column; }
.chart-box.full-width { grid-column: 1 / -1; }
.chart-header { padding: 16px 24px; background: var(--nav-bg); border-bottom: 1px solid #e8e0d8; }
.chart-header h3 { font-size: 16px; color: var(--primary); margin: 0; }
.chart-body { padding: 24px; flex: 1; }
.chart-body.flex-center { display: flex; flex-direction: column; justify-content: center; gap: 16px; min-height: 200px; }

/* Mock Chart */
.mock-chart { height: 260px; display: flex; align-items: flex-end; justify-content: space-between; padding-top: 20px; border-bottom: 1px solid #e8e0d8; }
.bar-container { display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; width: 3%; gap: 8px; }
.bar-fill { width: 100%; background: var(--primary); border-radius: 4px 4px 0 0; transition: height 1s ease; opacity: 0.8; }
.bar-fill:hover { opacity: 1; }
.bar-label { font-size: 11px; color: var(--text2); }

/* Stats Row */
.stats-row { display: flex; align-items: center; background: #faf8f5; padding: 12px 20px; border-radius: 8px; font-size: 14px; }
.stats-dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 12px; }
.stats-dot.fast { background: var(--primary); }
.stats-dot.slow { background: var(--accent); }
.stats-dot.fault-red { background: var(--secondary); }
.stats-dot.fault-org { background: #e67e22; }
.stats-dot.fault-yel { background: #f1c40f; }

.stats-label { flex: 1; color: var(--text); font-weight: 500; }
.stats-num { font-weight: 700; font-family: monospace; font-size: 15px; }
.stats-num .sub { color: var(--text2); font-weight: normal; font-size: 12px; margin-left: 4px; }
</style>
