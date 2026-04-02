<template>
  <div class="admin-wrapper">
    <nav class="topnav">
      <div class="brand">⚡ 智能充电桩调度计费系统 · 管理端</div>
      <div class="tabs">
        <router-link to="/admin/overview" class="nav-tab">运营总览</router-link>
        <router-link to="/admin/records" class="nav-tab">记录中心</router-link>
        <router-link to="/admin/config" class="nav-tab">系统配置</router-link>
        <router-link to="/admin/statistics" class="nav-tab">统计分析</router-link>
        <router-link to="/admin/users" class="nav-tab active">用户管理</router-link>
      </div>
      <div class="right">
        <span class="alert-badge">🔔 告警<span class="dot">2</span></span>
        <span>管理员: 张三</span>
        <span>{{ clock }}</span>
      </div>
    </nav>

    <div class="page-content">
      <div class="header-section">
        <h2>用户管理</h2>
        <div class="filter-bar">
          <input type="text" class="search-input" placeholder="搜索用户名或工号...">
          <select class="filter-select">
            <option>状态: 全部</option>
            <option>正常</option>
            <option>已封禁</option>
          </select>
          <button class="action-btn">导出名单</button>
        </div>
      </div>

      <div class="table-card">
        <table class="user-table">
          <thead>
            <tr>
              <th>用户ID</th>
              <th>用户名</th>
              <th>注册时间</th>
              <th>累计充电次数</th>
              <th>账户余额</th>
              <th>当前状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(u, index) in users" :key="index">
              <td class="font-mono">{{ u.id }}</td>
              <td class="font-bold">{{ u.name }}</td>
              <td>{{ u.regTime }}</td>
              <td>{{ u.chargeCount }}</td>
              <td class="font-bold">¥ {{ u.balance.toFixed(2) }}</td>
              <td>
                <span class="status-badge" :class="u.status === '正常' ? 'active' : 'banned'">
                  {{ u.status }}
                </span>
              </td>
              <td class="actions">
                <button class="text-btn primary">详情</button>
                <button v-if="u.status === '正常'" class="text-btn danger" @click="u.status = '已封禁'">封禁</button>
                <button v-else class="text-btn" @click="u.status = '正常'">解封</button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <div class="pagination">
          <span>共 86 名用户</span>
          <div class="pages">
            <button class="page-btn" disabled>&lt;</button>
            <button class="page-btn active">1</button>
            <button class="page-btn">2</button>
            <button class="page-btn">3</button>
            <button class="page-btn">...</button>
            <button class="page-btn">9</button>
            <button class="page-btn">&gt;</button>
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

const users = ref([
  { id: 'USR_1001', name: 'user_001', regTime: '2026-01-12', chargeCount: 24, balance: 156.40, status: '正常' },
  { id: 'USR_1002', name: 'user_002', regTime: '2026-01-15', chargeCount: 18, balance: 40.00, status: '正常' },
  { id: 'USR_1003', name: 'user_003', regTime: '2026-02-03', chargeCount: 42, balance: 350.80, status: '正常' },
  { id: 'USR_1004', name: 'user_004', regTime: '2026-02-18', chargeCount: 5, balance: -15.00, status: '已封禁' },
  { id: 'USR_1005', name: 'user_005', regTime: '2026-03-01', chargeCount: 12, balance: 88.50, status: '正常' },
  { id: 'USR_1006', name: 'user_006', regTime: '2026-03-09', chargeCount: 9, balance: 25.00, status: '正常' },
  { id: 'USR_1007', name: 'user_007', regTime: '2026-03-21', chargeCount: 31, balance: 110.25, status: '正常' },
  { id: 'USR_1008', name: 'user_008', regTime: '2026-03-22', chargeCount: 1, balance: 0.00, status: '正常' }
])
</script>

<style scoped>
.admin-wrapper {
  --bg: #faf8f5; --card: #ffffff; --primary: #2d6a4f; --secondary: #c45d3e;
  --accent: #d4a853; --text: #2c2c2c; --text2: #7a7a7a; --shadow: 0 4px 12px rgba(120,80,40,0.08);
  --nav-bg: #f5f0e8; --radius: 10px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column;
}
h2 { font-family: Georgia, serif; }

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

.filter-bar { display: flex; gap: 12px; }
.search-input { padding: 8px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; width: 240px; outline: none; }
.search-input:focus { border-color: var(--primary); }
.filter-select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; outline: none; background: #fff; }
.action-btn { padding: 8px 18px; border: none; border-radius: 6px; background: var(--primary); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
.action-btn:hover { opacity: 0.9; }

/* TABLE */
.table-card { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; display: flex; flex-direction: column; }
.user-table { width: 100%; border-collapse: collapse; text-align: left; }
.user-table th { padding: 16px 24px; font-size: 13px; color: var(--primary); font-weight: 600; background: var(--nav-bg); border-bottom: 1px solid #e8e0d8; }
.user-table td { padding: 16px 24px; font-size: 14px; color: var(--text); border-bottom: 1px solid #f0ebe4; transition: background 0.2s; }
.user-table tbody tr:hover td { background: #faf8f5; }
.font-mono { font-family: monospace; color: var(--text2); }
.font-bold { font-weight: 600; }

.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.status-badge.active { background: rgba(45,106,79,.1); color: var(--primary); }
.status-badge.banned { background: rgba(196,93,62,.1); color: var(--secondary); }

.actions { display: flex; gap: 12px; }
.text-btn { background: none; border: none; font-size: 13px; cursor: pointer; font-weight: 600; color: var(--text2); transition: color 0.2s; }
.text-btn:hover { text-decoration: underline; }
.text-btn.primary { color: var(--primary); }
.text-btn.danger { color: var(--secondary); }

.pagination { padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #e8e0d8; background: #faf8f5; font-size: 13px; color: var(--text2); }
.pages { display: flex; gap: 4px; }
.page-btn { min-width: 28px; height: 28px; border: 1px solid #ddd; background: #fff; border-radius: 4px; display: flex; justify-content: center; align-items: center; cursor: pointer; color: var(--text); transition: all 0.2s; }
.page-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); font-weight: 600; }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
