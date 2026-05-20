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
            <div class="kpi-sub" v-if="activeCount">当前有活跃充电</div>
          </div>
          <div class="kpi-icon" :class="activeCount > 0 ? 'red' : 'gray'">
            <span class="material-icons">{{ activeCount > 0 ? 'bolt' : 'check_circle' }}</span>
          </div>
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
                  <td><span class="uid mono">{{ u.user_id }}</span></td>
                  <td>{{ u.username }}</td>
                  <td class="mono">{{ capacityText(u) }}</td>
                  <td><span class="tag" :class="u.role === 'ADMIN' ? 'admin' : 'user'">{{ u.role }}</span></td>
                  <td>{{ fmtDate(u.created_at) }}</td>
                  <td>
                    <span class="chip" :class="{ active: u.has_active_request }">{{ u.has_active_request ? '有' : '无' }}</span>
                  </td>
                  <td>
                    <div class="op">
                      <a @click="toggleDetail(u.user_id)" :class="{ 'op-loading': detailLoading[u.user_id] }">
                        {{ expandedDetails[u.user_id] ? '收起' : '详情' }}
                      </a>
                      <a v-if="u.role !== 'ADMIN'" class="warn" @click="editCapacity(u)"
                         :class="{ muted: u.has_active_request }"
                         :title="u.has_active_request ? '该用户有活跃请求，暂不可修改容量' : ''">修改容量</a>
                      <span v-else class="op-na">不适用</span>
                    </div>
                  </td>
                </tr>
                <tr v-if="expandedDetails[u.user_id]" class="detail-row">
                  <td colspan="7">
                    <div class="inline-detail">
                      <div class="detail-grid">
                        <div class="dg-item"><span class="dg-key">用户ID</span><span class="dg-val mono">{{ expandedDetails[u.user_id].user_id }}</span></div>
                        <div class="dg-item"><span class="dg-key">用户名</span><span class="dg-val">{{ expandedDetails[u.user_id].username }}</span></div>
                        <div class="dg-item"><span class="dg-key">电池容量</span><span class="dg-val mono">{{ capacityText(expandedDetails[u.user_id]) }}</span></div>
                        <div class="dg-item"><span class="dg-key">角色</span><span class="dg-val">{{ expandedDetails[u.user_id].role }}</span></div>
                      </div>
                      <div class="detail-history" v-if="detailRows(expandedDetails[u.user_id]).length">
                        <h4>历史详单</h4>
                        <div class="table-scroll">
                          <table class="t-sm">
                            <thead><tr><th>详单ID</th><th>桩位</th><th>电量</th><th>总费用</th><th>终态</th></tr></thead>
                            <tbody>
                              <tr v-for="d in detailRows(expandedDetails[u.user_id])" :key="d.detail_id">
                                <td class="mono">{{ d.detail_id }}</td>
                                <td>{{ d.station_code }}</td>
                                <td class="mono">{{ d.actual_energy }} kWh</td>
                                <td class="mono">¥{{ (d.total_fee || 0).toFixed(2) }}</td>
                                <td>{{ d.request_status }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
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
  <ActionDialog v-bind="dialog" @confirm="confirmDialog" @cancel="cancelDialog" />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getUsers, getUserDetail, updateBatteryCapacity } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import ActionDialog from '@/components/ActionDialog.vue'
import { useActionDialog } from '@/composables/useActionDialog'

const { dialog, openConfirm, openInput, openMessage, confirmDialog, cancelDialog } = useActionDialog()

const users = ref([])
const loading = ref(false)
const expandedDetails = ref({})
const detailLoading = ref({})
const searchQuery = ref('')

const filteredUsers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter(u =>
    String(u.user_id).toLowerCase().includes(q) ||
    (u.username || '').toLowerCase().includes(q)
  )
})

const adminCount = computed(() => users.value.filter(u => u.role === 'ADMIN').length)
const userCount = computed(() => users.value.filter(u => u.role !== 'ADMIN').length)
const activeCount = computed(() => users.value.filter(u => u.has_active_request).length)

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
  if (u.role === 'ADMIN') {
    await openMessage({ title: '无法修改', message: '管理员账号没有车辆电池容量', severity: 'warning' })
    return
  }
  if (u.has_active_request) {
    await openMessage({ title: '无法修改', message: '该用户有活跃请求，不可修改', severity: 'warning' })
    return
  }
  const val = await openInput({
    title: '修改电池容量',
    message: `用户 ${u.username}，当前容量 ${u.battery_capacity} kWh`,
    inputLabel: '新电池容量 (kWh)',
    inputPlaceholder: '输入新容量',
    inputType: 'number',
    inputMin: 0.1,
    inputStep: 0.1,
    inputValue: u.battery_capacity,
    confirmText: '确认修改',
  })
  if (val == null) return
  const num = parseFloat(val)
  if (!num || num <= 0) {
    await openMessage({ title: '输入无效', message: '容量必须大于 0', severity: 'danger' })
    return
  }
  try {
    const res = await updateBatteryCapacity(u.user_id, { battery_capacity: num })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) {
      await openMessage({ title: '修改失败', message: data.message || '修改失败', severity: 'danger' })
      return
    }
    await loadUsers()
  } catch (e) {
    const code = e?.response?.data?.code
    const msg = code === 1010 ? '用户有活跃请求，不可修改车辆电池容量' : (e?.response?.data?.message || '修改失败')
    await openMessage({ title: '修改失败', message: msg, severity: 'danger' })
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 22px; }
.page-head h1 { margin: 0; font-size: 26px; font-weight: 900; letter-spacing: -.5px; color: #111827; }
.page-head p { margin: 5px 0 0; font-size: 13px; color: #6b7280; }
.mono { font-family: "SF Mono", ui-monospace, Consolas, monospace; }

/* Toolbar */
.toolbar {
  display: flex; justify-content: space-between; align-items: center;
  gap: 12px; flex-wrap: wrap; margin-bottom: 18px;
}
.toolbar-left { display: flex; gap: 10px; align-items: center; }
.search-box {
  width: 280px; height: 38px;
  border: 1px solid #edf0f2; border-radius: 10px;
  background: #fff; display: flex; align-items: center;
  gap: 8px; padding: 0 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.search-box .material-icons { font-size: 18px; color: #98a2b3; }
.search-box input { border: none; outline: none; width: 100%; font-size: 13px; color: #344054; font-family: inherit; background: transparent; }
.search-box input::placeholder { color: #98a2b3; }
.btn-refresh {
  height: 38px; border-radius: 10px;
  border: 1px solid #edf0f2; background: #fff;
  padding: 0 16px; color: #344054; font-weight: 700;
  display: flex; align-items: center; gap: 6px;
  cursor: pointer; font-family: inherit; font-size: 13px;
}
.btn-refresh .material-icons { font-size: 16px; }
.btn-refresh:hover { background: #f9fafb; border-color: #d0d5dd; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

.loading-state, .empty-state { color: #9ca3af; font-size: 14px; padding: 60px 0; text-align: center; }

/* KPI Cards */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px; }
.kpi-card {
  min-height: 100px; padding: 18px;
  border: 1px solid #f1f5f9; border-radius: 18px; background: white;
  display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;
  box-shadow: 0 10px 28px rgba(16,24,40,.06);
}
.kpi-left { min-width: 0; }
.kpi-label { font-size: 13px; color: #667085; font-weight: 600; margin-bottom: 8px; }
.kpi-val { font-size: 28px; font-weight: 900; color: #111827; line-height: 1; letter-spacing: -.03em; }
.kpi-sub { font-size: 11px; color: #98a2b3; margin-top: 6px; }
.kpi-icon {
  width: 46px; height: 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.kpi-icon .material-icons { font-size: 22px; }
.kpi-icon.green { background: #ecfdf5; color: #1f8f60; }
.kpi-icon.gold { background: #fffbeb; color: #d8a23a; }
.kpi-icon.blue { background: #eff6ff; color: #4f86f7; }
.kpi-icon.red { background: #fef2f2; color: #ef4444; }
.kpi-icon.gray { background: #f4f4f5; color: #98a2b3; }
.kpi-alert { border-color: #fecaca; }

/* Panel */
.panel {
  background: white; border: 1px solid #f1f5f9; border-radius: 18px;
  overflow: hidden; box-shadow: 0 10px 28px rgba(16,24,40,.06);
}
.panel-head {
  padding: 16px 20px; border-bottom: 1px solid #f1f5f9;
  display: flex; align-items: center; justify-content: space-between;
}
.panel-head h2 { margin: 0; font-size: 15px; font-weight: 700; color: #111827; }
.panel-count { font-size: 12px; color: #98a2b3; }
.table-scroll { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; font-size: 13px; color: #344054; }
thead { background: #f9fafb; }
th { padding: 12px 16px; text-align: left; font-size: 11px; font-weight: 600; color: #98a2b3; text-transform: uppercase; letter-spacing: .5px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }
td { padding: 13px 16px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f9fafb; }

.uid { font-weight: 700; color: #111827; }
.tag { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.tag.admin { background: #fffbeb; color: #b45309; }
.tag.user { background: #ecfdf5; color: #059669; }
.chip { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; background: #f3f4f6; color: #6b7280; }
.chip.active { background: #fef2f2; color: #ef4444; }

.op { display: flex; gap: 12px; align-items: center; }
.op a { color: #1f8f60; font-weight: 600; font-size: 12px; cursor: pointer; text-decoration: none; }
.op a:hover { text-decoration: underline; }
.op a.warn { color: #d97706; }
.op a.muted { opacity: .4; pointer-events: none; }
.op-na { font-size: 12px; color: #98a2b3; }
.op-loading { opacity: .5; }

/* Detail row */
.detail-row td { background: #f9fafb; padding: 0 !important; }
.inline-detail { padding: 18px 20px 20px; border-top: 1px solid #f1f5f9; }
.detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1px;
  background: #f1f5f9; border: 1px solid #f1f5f9; border-radius: 12px; overflow: hidden;
}
.dg-item { display: flex; justify-content: space-between; padding: 12px 16px; background: white; }
.dg-key { font-size: 13px; color: #667085; }
.dg-val { font-size: 13px; font-weight: 700; color: #111827; }
.detail-history { margin-top: 16px; }
.detail-history h4 { font-size: 13px; font-weight: 700; margin: 0 0 10px; color: #344054; }
.empty-detail { margin-top: 14px; color: #98a2b3; font-size: 12px; }

.t-sm { width: 100%; border-collapse: collapse; font-size: 12px; }
.t-sm th { text-align: left; padding: 8px 12px; color: #98a2b3; border-bottom: 1px solid #f1f5f9; font-weight: 600; font-size: 11px; }
.t-sm td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; color: #344054; }

.footer-row {
  padding: 12px 20px; border-top: 1px solid #f1f5f9;
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; color: #98a2b3;
}
</style>
