<template>
  <div class="user-account-wrapper">
    <!-- Top Nav -->
    <nav class="top-nav">
      <div class="nav-brand">⚡ 智能充电桩调度计费系统</div>
      <div class="nav-center">
        <router-link to="/user/workspace" class="nav-tab">工作台</router-link>
        <router-link to="/user/task" class="nav-tab">当前任务</router-link>
        <router-link to="/user/account" class="nav-tab active">账户中心</router-link>
      </div>
      <div class="nav-right">
        <span>🔔 通知(3)</span>
        <span>用户: 张三</span>
        <span class="logout">退出</span>
      </div>
    </nav>

    <div class="main-wrap">
      <div class="account-content">
        <!-- Dashboard Top Row: Profile & Wallet -->
        <div class="top-row">
          <!-- Profile Card -->
          <div class="card profile-card">
            <div class="profile-header">
              <div class="avatar">张</div>
              <div class="user-info">
                <h3>张三 (Zhang San)</h3>
                <p>普通用户 | ID: UID-8839201</p>
                <span class="tag">正常状态</span>
              </div>
            </div>
            <div class="profile-details">
              <div class="detail-item">
                <span>车辆型号：</span>
                <strong>Tesla Model 3</strong>
              </div>
              <div class="detail-item">
                <span>电池容量：</span>
                <strong>60 kWh</strong>
              </div>
              <div class="detail-item">
                <span>注册时间：</span>
                <strong>2026-01-15</strong>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn btn-outline" @click="notifyUnimplemented('修改密码')">修改密码</button>
              <button class="btn btn-outline" @click="notifyUnimplemented('车辆管理')">车辆管理</button>
            </div>
          </div>

          <!-- Wallet Card -->
          <div class="card wallet-card">
            <h4>账户余额</h4>
            <div class="balance-display">
              <span class="currency">¥</span>
              <span class="amount">128.50</span>
            </div>
            <div class="wallet-stats">
              <div class="stat">
                <span class="label">累计充值</span>
                <span class="val">¥ 500.00</span>
              </div>
              <div class="stat">
                <span class="label">累计消费</span>
                <span class="val">¥ 371.50</span>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn btn-primary" @click="handleRecharge">立即充值</button>
              <button class="btn btn-outline" @click="notifyUnimplemented('账单明细')">账单明细</button>
            </div>
          </div>
        </div>

        <!-- History Records Table -->
        <div class="card history-card">
          <div class="card-header">
            <h4>历史充电详单</h4>
            <div class="header-actions">
              <select class="filter-select" @change="notifyUnimplemented('历史记录筛选')">
                <option>全部记录</option>
                <option>已完成</option>
                <option>已取消</option>
              </select>
              <button class="btn btn-outline" @click="notifyUnimplemented('导出PDF')">导出PDF</button>
            </div>
          </div>
          
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>详单号</th>
                  <th>充电桩号</th>
                  <th>开始时间</th>
                  <th>结束时间</th>
                  <th>充电量 (度)</th>
                  <th>总费用 (元)</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in historyRecords" :key="record.id">
                  <td>{{ record.id }}</td>
                  <td>{{ record.pile }}</td>
                  <td>{{ record.startTime }}</td>
                  <td>{{ record.endTime }}</td>
                  <td>{{ record.amount }}</td>
                  <td class="gold-text">¥ {{ record.cost }}</td>
                  <td>
                    <span :class="['status-badge', record.status === '已完成' ? 'success' : '']">
                      {{ record.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const historyRecords = ref([
  { id: 'REC-23091', pile: 'A-01 (快充)', startTime: '2026-03-30 14:00', endTime: '2026-03-30 15:30', amount: '45.2', cost: '67.80', status: '已完成' },
  { id: 'REC-23085', pile: 'B-03 (慢充)', startTime: '2026-03-28 09:00', endTime: '2026-03-28 17:00', amount: '22.5', cost: '15.75', status: '已完成' },
  { id: 'REC-23012', pile: 'A-02 (快充)', startTime: '2026-03-25 18:30', endTime: '2026-03-25 19:15', amount: '30.0', cost: '45.00', status: '已完成' },
  { id: 'REC-22998', pile: 'C-05 (慢充)', startTime: '2026-03-20 08:30', endTime: '2026-03-20 08:45', amount: '0.0', cost: '0.00', status: '已取消' }
])

function handleRecharge() {
  ElMessage.info('充值功能尚未接真实后端接口，当前仅保留页面展示')
}

function notifyUnimplemented(feature) {
  ElMessage.info(`${feature} 功能尚未完善，当前仅保留静态展示`)
}
</script>

<style scoped>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.user-account-wrapper {
  --bg:#faf8f5;--card:#ffffff;--shadow:0 4px 12px rgba(120,80,40,0.08);
  --primary:#2d6a4f;--secondary:#c45d3e;--accent:#d4a853;
  --text:#2c2c2c;--text2:#7a7a7a;--nav-bg:#f5f0e8;
  --radius:10px;
  --border:#e8e2d9;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}
h1,h2,h3,h4,h5{font-family:Georgia,serif;}

/* NAV */
.top-nav{background:var(--nav-bg);border-bottom:3px solid var(--accent);display:flex;align-items:center;justify-content:space-between;padding:0 32px;height:56px;position:sticky;top:0;z-index:100;width:100%}
.nav-brand{font-family:Georgia,serif;font-size:18px;font-weight:700;color:var(--primary);white-space:nowrap}
.nav-center{display:flex;gap:4px;}
.nav-tab{padding:8px 22px;border-radius:8px;cursor:pointer;font-size:15px;color:var(--text2);transition:all .2s;text-decoration:none;margin:0 2px;}
.nav-tab:hover{color:var(--text);background:rgba(45,106,79,.06);}
.nav-tab.active{color:var(--primary);font-weight:600;background:rgba(45,106,79,.1);}
.nav-right{display:flex;align-items:center;gap:18px;font-size:14px;color:var(--text2);white-space:nowrap}
.nav-right span{cursor:pointer;transition:color .2s;}
.nav-right span:hover{color:var(--text);}
.nav-right .logout{color:var(--secondary);}

/* LAYOUT */
.main-wrap{display:flex;gap:24px;padding:32px;width:100%;max-width:1200px;margin:0 auto;flex:1;}

.account-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.top-row {
  display: flex;
  gap: 24px;
}

.top-row .card {
  flex: 1;
}

/* Profile Card */
.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.avatar {
  width: 64px;
  height: 64px;
  background: var(--primary);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-family: Georgia, serif;
}
.user-info h3 {
  font-size: 20px;
  color: var(--primary);
  margin-bottom: 6px;
}
.user-info p {
  font-size: 13px;
  color: var(--text2);
  margin-bottom: 6px;
}
.tag {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(45,106,79,.1);
  color: var(--primary);
  border-radius: 4px;
  font-size: 12px;
}

.profile-details {
  background: var(--bg);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}
.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}
.detail-item:last-child { margin-bottom: 0; }
.detail-item span { color: var(--text2); }

/* Wallet Card */
.wallet-card h4 {
  font-size: 18px;
  color: var(--text2);
  margin-bottom: 12px;
}
.balance-display {
  color: var(--secondary);
  margin-bottom: 24px;
}
.balance-display .currency {
  font-size: 24px;
  font-weight: bold;
}
.balance-display .amount {
  font-size: 48px;
  font-weight: bold;
  font-family: Georgia, serif;
}
.wallet-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  border-top: 1px solid var(--border);
  padding-top: 16px;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat .label { font-size: 13px; color: var(--text2); }
.stat .val { font-size: 16px; font-weight: bold; color: var(--text); }

/* Actions */
.card-actions {
  display: flex;
  gap: 12px;
}
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all .2s;
  border: none;
}
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover { background: #22523c; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
.btn-outline:hover { background: var(--bg); border-color: #d0c8b8; }

/* History Table */
.history-card { margin-bottom: 40px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.card-header h4 { font-size: 18px; color: var(--primary); }
.header-actions { display: flex; gap: 12px; align-items: center; }
.filter-select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

.table-container {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th {
  background: var(--bg);
  color: var(--text2);
  font-weight: normal;
  text-align: left;
  padding: 12px 16px;
  border-bottom: 2px solid var(--border);
}
td {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
tr:hover td {
  background: var(--bg);
}
.gold-text {
  color: var(--accent);
  font-weight: bold;
}
.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #f1f1f1;
  color: var(--text2);
}
.status-badge.success {
  background: rgba(45,106,79,.1);
  color: var(--primary);
}
</style>
