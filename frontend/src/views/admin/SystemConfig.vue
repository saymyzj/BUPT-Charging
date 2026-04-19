<template>
  <div class="admin-wrapper">
    <nav class="topnav">
      <div class="brand">⚡ 智能充电桩调度计费系统 · 管理端</div>
      <div class="tabs">
        <router-link to="/admin/overview" class="nav-tab">运营总览</router-link>
        <router-link to="/admin/records" class="nav-tab">记录中心</router-link>
        <router-link to="/admin/config" class="nav-tab active">系统配置</router-link>
        <router-link to="/admin/statistics" class="nav-tab">统计分析</router-link>
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
        <h2>系统配置</h2>
        <p class="subtitle">调整充电桩数量、参数及费用设置</p>
      </div>

      <div class="config-grid">
        <!-- Pile config -->
        <div class="config-card">
          <div class="card-header">
            <h3>充电桩硬件配置</h3>
            <button class="action-btn" @click="notifyStaticAction('充电桩硬件配置')">保存修改</button>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label>快充桩总数</label>
              <input type="number" value="2" class="form-input">
            </div>
            <div class="form-group">
              <label>快充功率 (kW)</label>
              <input type="number" value="30" class="form-input">
            </div>
            <hr class="divider">
            <div class="form-group">
              <label>慢充桩总数</label>
              <input type="number" value="3" class="form-input">
            </div>
            <div class="form-group">
              <label>慢充功率 (kW)</label>
              <input type="number" value="7" class="form-input">
            </div>
          </div>
        </div>

        <!-- Charging config -->
        <div class="config-card">
          <div class="card-header">
            <h3>调度与队列参数</h3>
            <button class="action-btn" @click="notifyStaticAction('调度与队列参数')">保存修改</button>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label>等候区最大容量 (车辆)</label>
              <input type="number" value="6" class="form-input">
            </div>
            <div class="form-group">
              <label>叫号无响应超时 (分钟)</label>
              <input type="number" value="5" class="form-input">
            </div>
            <div class="form-group">
              <label>故障自动重试次数</label>
              <input type="number" value="3" class="form-input">
            </div>
          </div>
        </div>

        <!-- Pricing config -->
        <div class="config-card full-width">
          <div class="card-header">
            <h3>计费策略配置</h3>
            <button class="action-btn" @click="notifyStaticAction('计费策略配置')">保存计费策略</button>
          </div>
          <div class="card-body price-grid">
            <div class="price-col">
              <h4>高峰期 (10:00-15:00, 18:00-21:00)</h4>
              <div class="form-group">
                <label>电费 (元/度)</label>
                <input type="number" step="0.1" value="1.0" class="form-input">
              </div>
              <div class="form-group">
                <label>服务费 (元/度)</label>
                <input type="number" step="0.1" value="0.8" class="form-input">
              </div>
            </div>
            <div class="price-col">
              <h4>平时段 (07:00-10:00, 15:00-18:00, 21:00-23:00)</h4>
              <div class="form-group">
                <label>电费 (元/度)</label>
                <input type="number" step="0.1" value="0.7" class="form-input">
              </div>
              <div class="form-group">
                <label>服务费 (元/度)</label>
                <input type="number" step="0.1" value="0.8" class="form-input">
              </div>
            </div>
            <div class="price-col">
              <h4>低谷期 (23:00-07:00)</h4>
              <div class="form-group">
                <label>电费 (元/度)</label>
                <input type="number" step="0.1" value="0.4" class="form-input">
              </div>
              <div class="form-group">
                <label>服务费 (元/度)</label>
                <input type="number" step="0.1" value="0.8" class="form-input">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

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

function notifyStaticAction(section) {
  ElMessage.info(`${section} 目前是静态演示区，真实保存接口待后续接入`)
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
.page-content { padding: 32px 40px; max-width: 1200px; margin: 0 auto; width: 100%; flex: 1; }
.header-section { margin-bottom: 24px; }
.header-section h2 { font-size: 24px; color: var(--primary); margin-bottom: 6px; }
.subtitle { font-size: 14px; color: var(--text2); }

.config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.config-card { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; display: flex; flex-direction: column; }
.config-card.full-width { grid-column: 1 / -1; }
.card-header { padding: 16px 24px; background: var(--nav-bg); border-bottom: 1px solid #e8e0d8; display: flex; justify-content: space-between; align-items: center; }
.card-header h3 { font-size: 16px; color: var(--primary); margin: 0; }
.card-body { padding: 24px; flex: 1; }

.action-btn { padding: 6px 16px; border: none; border-radius: 6px; background: var(--primary); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
.action-btn:hover { opacity: 0.9; }

.form-group { margin-bottom: 16px; display: flex; flex-direction: column; gap: 8px; }
.form-group label { font-size: 13px; color: var(--text); font-weight: 500; }
.form-input { padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; transition: border-color 0.2s; outline: none; }
.form-input:focus { border-color: var(--primary); }

.divider { height: 1px; background: #e8e0d8; border: none; margin: 20px 0; }

.price-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; }
.price-col h4 { font-size: 14px; color: var(--secondary); margin-bottom: 16px; white-space: pre-wrap; line-height: 1.5; }
</style>
