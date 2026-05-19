<template>
  <div class="page">
    <div class="page-head">
      <h1>用户管理</h1>
      <p>查看用户列表、详情，维护车辆电池容量</p>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="material-icons">search</span>
          <input type="text" v-model="searchQuery" placeholder="搜索用户ID / 用户名" />
        </div>
      </div>
      <button class="btn-refresh" :disabled="loading" @click="loadUsers">
        <span class="material-icons">refresh</span>刷新
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载中…</div>

    <template v-else-if="users.length">
      <!-- KPI Cards -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">用户总数</div>
            <div class="kpi-val mono">{{ users.length }}</div>
          </div>
          <div class="kpi-icon green"><span class="material-icons">group</span></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">ADMIN 数</div>
            <div class="kpi-val mono">{{ adminCount }}</div>
            <div class="kpi-sub">系统权限账号</div>
          </div>
          <div class="kpi-icon gold"><span class="material-icons">admin_panel_settings</span></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">USER 数</div>
            <div class="kpi-val mono">{{ userCount }}</div>
            <div class="kpi-sub" v-if="users.length">占比 {{ (userCount / users.length * 100).toFixed(1) }}%</div>
          </div>
          <div class="kpi-icon blue"><span class="material-icons">person</span></div>
        </div>
        <div class="kpi-card" :class="{ 'kpi-alert': activeCount > 0 }">
          <div class="kpi-left">
            <div class="kpi-label">活跃请求</div>
            <div class="kpi-val mono">{{ activeCount }}</div>
            <div class="kpi-sub">有充电请求的用户</div>
          </div>
          <div class="kpi-icon" :class="activeCount > 0 ? 'red' : 'gray'"><span class="material-icons">pending_actions</span></div>
        </div>
      </div>

      <!-- Table Panel -->
      <div class="panel">
        <div class="panel-head">
          <h2>用户列表</h2>
          <span class="panel-count">共 {{ filteredUsers.length }} 条</span>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>用户ID</th>
                <th>用户名</th>
                <th>电池容量</th>
                <th>角色</th>
                <th>创建时间</th>
                <th>活跃请求</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="u in filteredUsers" :key="u.user_id">
                <tr>
                  <td class="uid">{{ u.user_id }}</td>
                  <td>{{ u.username }}</td>
                  <td class="mono">{{ capacityText(u) }}</td>
                  <td><span class="tag" :class="u.role === 'ADMIN' ? 'admin' : 'user'">{{ u.role }}</span></td>
                  <td>{{ fmtDate(u.created_at) }}</td>
                  <td><span class="chip" :class="u.has_active_request ? 'active' : ''">{{ u.has_active_request ? '有' : '无' }}</span></td>
                  <td>
                    <div class="op">
                      <a href="#" @click.prevent="toggleDetail(u.user_id)"
                        :class="{ 'op-loading': detailLoading[u.user_id] }">
                        {{ expandedDetails[u.user_id] ? '收起' : (detailLoading[u.user_id] ? '加载中' : '详情') }}
                      </a>
                      <a v-if="u.role !== 'ADMIN'" href="#" class="warn"
                        @click.prevent="editCapacity(u)"
                        :class="{ muted: u.has_active_request }"
                        :title="u.has_active_request ? '该用户有活跃请求，暂不可修改容量' : ''">
                        修改容量
                      </a>
                      <span v-else class="op-na">不适用</span>
                    </div>
                  </td>
                </tr>
                <tr v-if="expandedDetails[u.user_id]" class="detail-row">
                  <td colspan="7">
                    <div class="inline-detail">
                      <div class="detail-grid">
                        <div class="dg-item"><span class="dg-key">用户ID</span><span class="dg-val">{{ expandedDetails[u.user_id].user_id }}</span></div>
                        <div class="dg-item"><span class="dg-key">用户名</span><span class="dg-val">{{ expandedDetails[u.user_id].username }}</span></div>
                        <div class="dg-item"><span class="dg-key">电池容量</span><span class="dg-val mono">{{ capacityText(expandedDetails[u.user_id]) }}</span></div>
                        <div class="dg-item"><span class="dg-key">角色</span><span class="dg-val">{{ expandedDetails[u.user_id].role }}</span></div>
                      </div>
                      <div class="detail-history" v-if="detailRows(expandedDetails[u.user_id]).length">
                        <h4>历史详单</h4>
                        <table class="t-sm">
                          <thead><tr><th>详单ID</th><th>桩位</th><th>电量</th><th>总费用</th><th>终态</th></tr></thead>
                          <tbody>
                            <tr v-for="d in detailRows(expandedDetails[u.user_id])" :key="d.detail_id">
                              <td>{{ d.detail_id }}</td>
                              <td>{{ d.station_code }}</td>
                              <td class="mono">{{ d.actual_energy }} kWh</td>
                              <td class="mono">¥{{ (d.total_fee || 0).toFixed(2) }}</td>
                              <td>{{ d.request_status }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div v-else class="empty-detail">暂无历史详单</div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <div class="footer-row">
          <div>提示：容量修改与用户权限变更将记录在变更记录中。</div>
          <span>共 {{ filteredUsers.length }} 条</span>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">暂无用户数据</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getUsers, getUserDetail, updateBatteryCapacity } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'

const users = ref([])
const loading = ref(false)
const expandedDetails = ref({})
const detailLoading = ref({})
const searchQuery = ref('')

const adminCount = computed(() => users.value.filter(u => u.role === 'ADMIN').length)
const userCount = computed(() => users.value.filter(u => u.role !== 'ADMIN').length)
const activeCount = computed(() => users.value.filter(u => u.has_active_request).length)
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const q = searchQuery.value.toLowerCase()
  return users.value.filter(u =>
    String(u.user_id).toLowerCase().includes(q) || (u.username || '').toLowerCase().includes(q)
  )
})

function fmtDate(t) {
  if (!t) return '--'
  try { return new Date(t).toLocaleDateString('zh-CN') } catch { return t }
}

function capacityText(user) {
  if (!user || user.role === 'ADMIN') return '不适用'
  return `${user.battery_capacity} kWh`
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUsers()
    const data = unwrapResponseData(res)
    users.value = Array.isArray(data) ? data : (data.users || [])
    expandedDetails.value = {}
  } catch (_) { /* silent */ }
  loading.value = false
}

async function toggleDetail(userId) {
  if (expandedDetails.value[userId]) {
    const next = { ...expandedDetails.value }
    delete next[userId]
    expandedDetails.value = next
    return
  }

  detailLoading.value = { ...detailLoading.value, [userId]: true }
  try {
    const res = await getUserDetail(userId)
    const data = unwrapResponseData(res)
    expandedDetails.value = { ...expandedDetails.value, [userId]: data }
  } catch (_) { /* silent */ }
  detailLoading.value = { ...detailLoading.value, [userId]: false }
}

function detailRows(detail) {
  return detail?.historical_details || detail?.details || []
}

async function editCapacity(u) {
  if (u.role === 'ADMIN') { alert('管理员账号没有车辆电池容量'); return }
  if (u.has_active_request) { alert('该用户有活跃请求，不可修改'); return }
  const val = prompt(`当前电池容量: ${u.battery_capacity} kWh\n输入新容量:`, u.battery_capacity)
  if (!val) return
  const num = parseFloat(val)
  if (!num || num <= 0) { alert('容量必须大于 0'); return }
  try {
    const res = await updateBatteryCapacity(u.user_id, { battery_capacity: num })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '修改失败'); return }
    await loadUsers()
  } catch (e) {
    const code = e?.response?.data?.code
    if (code === 1010) alert('用户有活跃请求，不可修改车辆电池容量')
    else alert(e?.response?.data?.message || '修改失败')
  }
}

onMounted(loadUsers)
</script>

<style scoped>
* { box-sizing: border-box; }
.mono { font-family: "SF Mono", Consolas, monospace; }

.page {
  max-width: 1400px; margin: 0 auto;
  padding: 24px 28px 30px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  color: #101828;
}
.page-head { margin-bottom: 18px; }
.page-head h1 { margin: 0; font-size: 28px; font-weight: 850; letter-spacing: -.02em; }
.page-head p { margin: 8px 0 0; font-size: 15px; color: #667085; }

/* Toolbar */
.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; margin: 14px 0 16px;
}
.toolbar-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; min-width: 0; }
.search-box {
  width: min(420px, 58vw); height: 42px;
  border: 1px solid #dde4e8; border-radius: 12px; background: #fff;
  display: flex; align-items: center; gap: 10px; padding: 0 14px;
  box-shadow: 0 1px 0 rgba(16,24,40,.01);
}
.search-box .material-icons { font-size: 18px; color: #98a2b3; }
.search-box input {
  border: 0; outline: none; width: 100%; font-size: 14px; color: #101828;
  font-family: inherit; background: transparent;
}
.search-box input::placeholder { color: #98a2b3; }
.btn-refresh {
  height: 42px; border-radius: 12px;
  border: 1px solid #cdd7e1; background: #fff;
  padding: 0 16px; color: #344054; font-weight: 700;
  display: inline-flex; align-items: center; gap: 8px;
  cursor: pointer; font-family: inherit; font-size: 14px;
}
.btn-refresh .material-icons { font-size: 16px; }
.btn-refresh:hover { background: #f8faf9; border-color: #b8c4cc; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

.loading-state, .empty-state { color: #98a2b3; font-size: 14px; padding: 60px 0; text-align: center; }

/* KPI Cards */
.kpi-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 16px; }
.kpi-card {
  min-height: 104px; padding: 18px 18px 16px;
  border: 1px solid #edf0f2; border-radius: 18px; background: rgba(255,255,255,.96);
  display: flex; justify-content: space-between; gap: 14px;
  box-shadow: 0 10px 28px rgba(16,24,40,.06);
}
.kpi-left { min-width: 0; }
.kpi-label { color: #667085; font-size: 13px; font-weight: 700; }
.kpi-val { margin-top: 8px; font-size: 30px; font-weight: 900; line-height: 1; letter-spacing: -.03em; color: #101828; }
.kpi-sub { margin-top: 10px; color: #98a2b3; font-size: 12px; }
.kpi-icon {
  width: 48px; height: 48px; border-radius: 16px;
  display: grid; place-items: center; flex: 0 0 auto;
}
.kpi-icon .material-icons { font-size: 22px; }
.kpi-icon.green { background: #eaf8f1; color: #1f8f60; }
.kpi-icon.gold { background: #fff8e8; color: #d8a23a; }
.kpi-icon.blue { background: #eef4ff; color: #4f86f7; }
.kpi-icon.red { background: #fff1f1; color: #ef4444; }
.kpi-icon.gray { background: #f2f4f7; color: #667085; }
.kpi-alert { border-color: #ffd1d1; }
.kpi-alert .kpi-label,
.kpi-alert .kpi-val { color: #ef4444; }

/* Panel */
.panel {
  background: rgba(255,255,255,.97); border: 1px solid #edf0f2; border-radius: 18px;
  box-shadow: 0 10px 28px rgba(16,24,40,.06); overflow: hidden;
}
.panel-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 18px 18px 14px; border-bottom: 1px solid #f0f2f4;
}
.panel-head h2 { margin: 0; font-size: 16px; font-weight: 850; color: #101828; }
.panel-count { font-size: 13px; color: #98a2b3; }
.table-scroll { overflow-x: auto; }

/* Table */
table { width: 100%; border-collapse: collapse; }
thead th {
  text-align: left; padding: 14px 18px; font-size: 13px; color: #667085; font-weight: 700;
  background: #fbfcfc; border-bottom: 1px solid #edf0f2; white-space: nowrap;
}
tbody td {
  padding: 16px 18px; border-bottom: 1px solid #f0f2f4;
  font-size: 14px; color: #344054; white-space: nowrap;
}
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover > td { background: #fbfcfc; }
.uid { font-weight: 800; color: #1d2939; }

/* Tag / Chip */
.tag {
  display: inline-flex; align-items: center; justify-content: center; min-width: 64px;
  padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 800;
}
.tag.admin { background: #fff8e8; color: #d8a23a; }
.tag.user { background: #eaf8f1; color: #1f8f60; }
.chip {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 32px; padding: 3px 8px; border-radius: 999px;
  background: #f2f4f7; color: #667085; font-size: 12px; font-weight: 700;
}
.chip.active { background: #fff1f1; color: #ef4444; }

/* Op links */
.op { display: inline-flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.op a { color: #4f86f7; font-weight: 700; font-size: 14px; cursor: pointer; text-decoration: none; }
.op a:hover { text-decoration: underline; }
.op a.warn { color: #1f8f60; }
.op a.muted { color: #98a2b3; pointer-events: none; cursor: default; }
.op a.op-loading { color: #98a2b3; }
.op-na { font-size: 13px; color: #98a2b3; }

/* Footer row */
.footer-row {
  display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center;
  padding: 14px 18px; color: #98a2b3; font-size: 12px;
  border-top: 1px solid #f0f2f4; background: #fff;
}

/* Detail row */
.detail-row > td { background: #fbfcfc; padding: 0 !important; }
.inline-detail { padding: 16px 18px 18px; border-top: 1px solid #f0f2f4; }
.detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1px;
  background: #edf0f2; border: 1px solid #edf0f2; border-radius: 8px; overflow: hidden;
}
.dg-item { display: flex; justify-content: space-between; padding: 12px 14px; background: white; }
.dg-key { font-size: 13px; color: #667085; }
.dg-val { font-size: 13px; font-weight: 700; color: #1d2939; }
.detail-history { margin-top: 16px; }
.detail-history h4 { font-size: 14px; font-weight: 800; margin: 0 0 10px; color: #101828; }
.empty-detail { margin-top: 14px; color: #98a2b3; font-size: 12px; }

/* Sub-table */
.t-sm { width: 100%; border-collapse: collapse; font-size: 13px; }
.t-sm th {
  text-align: left; padding: 10px 12px; color: #667085; font-weight: 700;
  border-bottom: 1px solid #edf0f2; background: #fbfcfc; font-size: 12px;
}
.t-sm td { padding: 10px 12px; border-bottom: 1px solid #f0f2f4; color: #344054; }
.t-sm tr:last-child td { border-bottom: none; }

@media (max-width: 1180px) {
  .kpi-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .search-box { width: 100%; }
  .panel { overflow: auto; }
  table { min-width: 1080px; }
}
@media (max-width: 720px) {
  .page { padding: 18px 14px 24px; }
  .kpi-row { grid-template-columns: 1fr; }
}
</style>
