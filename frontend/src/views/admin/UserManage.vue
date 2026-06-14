<template>
  <div class="page user-manage-page">
    <div class="page-head">
      <div>
        <h1>用户管理</h1>
        <p>集中查看账号、车辆容量与充电历史，支持直接展开多名用户明细。</p>
      </div>
      <div class="head-tools">
        <div class="search-box">
          <span class="material-icons">search</span>
          <input type="text" v-model="searchQuery" placeholder="搜索用户ID / 用户名" />
        </div>
        <button class="btn-refresh" :disabled="loading" @click="loadUsers">
          <span class="material-icons">refresh</span>刷新
        </button>
        <button class="btn-export" @click="exportAllBills">
          <span class="material-icons">payments</span>导出账单
        </button>
        <button class="btn-export secondary" @click="exportAllDetails">
          <span class="material-icons">download</span>导出详单
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载中…</div>

    <template v-else-if="users.length">
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-label">用户总数</div>
            <div class="kpi-val mono">{{ totalUsers || users.length }}</div>
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
            <div class="kpi-sub" v-if="users.length">本页占比 {{ (userCount / users.length * 100).toFixed(1) }}%</div>
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

      <div class="panel">
        <div class="panel-head">
          <div>
            <h2>用户列表</h2>
            <p>点击详情展开历史详单，多个用户可同时对照。</p>
          </div>
          <div class="panel-tools">
            <label>
              每页
              <select v-model="pageSize" @change="changePageSize">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option value="all">全部</option>
              </select>
            </label>
            <span class="panel-count">显示 {{ filteredUsers.length }} / {{ totalUsers }} 条</span>
          </div>
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
                  <td>
                    <div class="user-cell">
                      <span class="avatar">{{ (u.username || 'U').slice(0, 1).toUpperCase() }}</span>
                      <div>
                        <strong>{{ u.username }}</strong>
                        <small>{{ u.role === 'ADMIN' ? '系统管理员' : '普通用户' }}</small>
                      </div>
                    </div>
                  </td>
                  <td class="mono">{{ capacityText(u) }}</td>
                  <td><span class="tag" :class="u.role === 'ADMIN' ? 'admin' : 'user'">{{ u.role }}</span></td>
                  <td>{{ fmtDate(u.created_at) }}</td>
                  <td>
                    <span class="chip" :class="{ active: u.has_active_request }">{{ u.has_active_request ? '有' : '无' }}</span>
                  </td>
                  <td>
                    <div class="op">
                      <a class="op-detail" @click="toggleDetail(u.user_id)" :class="{ 'op-loading': detailLoading[u.user_id] }">
                        <span class="material-icons">{{ expandedDetails[u.user_id] ? 'expand_less' : 'expand_more' }}</span>
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
                      <div class="detail-head">
                        <div class="user-cell large">
                          <span class="avatar">{{ (expandedDetails[u.user_id].username || 'U').slice(0, 1).toUpperCase() }}</span>
                          <div>
                            <strong>{{ expandedDetails[u.user_id].username }}</strong>
                            <small>{{ expandedDetails[u.user_id].role === 'ADMIN' ? '系统管理员账号' : '用户账号详情' }}</small>
                          </div>
                        </div>
                        <span class="detail-count">历史详单 {{ detailRows(expandedDetails[u.user_id]).length }} 条</span>
                      </div>
                      <div class="detail-grid">
                        <div class="dg-item"><span class="dg-key">用户ID</span><span class="dg-val mono">{{ expandedDetails[u.user_id].user_id }}</span></div>
                        <div class="dg-item"><span class="dg-key">用户名</span><span class="dg-val">{{ expandedDetails[u.user_id].username }}</span></div>
                        <div class="dg-item"><span class="dg-key">电池容量</span><span class="dg-val mono">{{ capacityText(expandedDetails[u.user_id]) }}</span></div>
                        <div class="dg-item"><span class="dg-key">角色</span><span class="dg-val">{{ expandedDetails[u.user_id].role }}</span></div>
                      </div>
                      <div class="detail-history" v-if="detailRows(expandedDetails[u.user_id]).length">
                        <h4>历史详单</h4>
                        <div class="history-list">
                          <article v-for="d in detailRows(expandedDetails[u.user_id])" :key="d.detail_id" class="history-card">
                            <div>
                              <span class="history-id mono">{{ d.detail_id }}</span>
                              <strong>{{ d.station_code || '--' }}</strong>
                            </div>
                            <div class="history-metrics">
                              <span>{{ d.actual_energy }} kWh</span>
                              <span>¥{{ (d.total_fee || 0).toFixed(2) }}</span>
                            </div>
                            <em>{{ d.request_status || '已完成' }}</em>
                          </article>
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
          <div class="pager" v-if="pageSize !== 'all'">
            <button :disabled="currentPage <= 1 || loading" @click="goPage(currentPage - 1)">上一页</button>
            <span>第 {{ currentPage }} / {{ pageCount }} 页</span>
            <button :disabled="currentPage >= pageCount || loading" @click="goPage(currentPage + 1)">下一页</button>
          </div>
          <span v-else>共 {{ filteredUsers.length }} 条</span>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">暂无用户数据</div>
  </div>
  <ActionDialog v-bind="dialog" @confirm="confirmDialog" @cancel="cancelDialog" />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { exportAllUserBillsXlsx, exportAllUserDetailsXlsx, getUsers, getUserDetail, updateBatteryCapacity } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import ActionDialog from '@/components/ActionDialog.vue'
import { useActionDialog } from '@/composables/useActionDialog'

const { dialog, openConfirm, openInput, openMessage, confirmDialog, cancelDialog } = useActionDialog()

const users = ref([])
const loading = ref(false)
const expandedDetails = ref({})
const detailLoading = ref({})
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalUsers = ref(0)

const filteredUsers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter(u =>
    String(u.user_id).toLowerCase().includes(q) ||
    (u.username || '').toLowerCase().includes(q)
  )
})

const pageCount = computed(() => {
  if (pageSize.value === 'all') return 1
  return Math.max(1, Math.ceil(totalUsers.value / Number(pageSize.value || 10)))
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
    const requestedPageSize = pageSize.value === 'all' ? 100 : Number(pageSize.value)
    const res = await getUsers({ page: pageSize.value === 'all' ? 1 : currentPage.value, page_size: requestedPageSize })
    const data = unwrapResponseData(res)
    let rows = Array.isArray(data) ? data : (data.users || [])
    const total = Array.isArray(data) ? rows.length : Number(data.total || rows.length)
    totalUsers.value = total
    const loadedPageSize = Array.isArray(data) ? rows.length : Number(data.page_size || requestedPageSize)
    const loadedPageCount = loadedPageSize > 0 ? Math.ceil(total / loadedPageSize) : 1
    if (pageSize.value === 'all' && loadedPageCount > 1) {
      const rest = []
      for (let page = 2; page <= loadedPageCount; page += 1) {
        const pageRes = await getUsers({ page, page_size: loadedPageSize })
        const pageData = unwrapResponseData(pageRes)
        rest.push(...(Array.isArray(pageData) ? pageData : (pageData.users || [])))
      }
      rows = rows.concat(rest)
    }
    users.value = rows
    expandedDetails.value = {}
  } catch (_) { /* silent */ }
  loading.value = false
}

function changePageSize() {
  currentPage.value = 1
  loadUsers()
}

function goPage(page) {
  currentPage.value = Math.max(1, Math.min(pageCount.value, Number(page) || 1))
  loadUsers()
}

watch(searchQuery, () => {
  currentPage.value = 1
})

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

function downloadBlobResponse(res, filename) {
  const blob = res instanceof Blob ? res : res?.data
  if (!blob) return
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

async function exportAllBills() {
  const res = await exportAllUserBillsXlsx()
  downloadBlobResponse(res, 'all-user-bills.xlsx')
}

async function exportAllDetails() {
  const res = await exportAllUserDetailsXlsx()
  downloadBlobResponse(res, 'all-user-action-details.xlsx')
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
.page { max-width: 1320px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.user-manage-page { color: #101828; }
.page-head {
  margin-bottom: 20px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 18px;
  border: 1px solid #e6f1ea;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f4fbf7 100%);
  box-shadow: 0 12px 30px rgba(16,24,40,.055);
}
.page-head h1 { margin: 0; font-size: 24px; font-weight: 900; color: #101828; }
.page-head p { margin: 5px 0 0; font-size: 13px; color: #667085; line-height: 1.55; }
.mono { font-family: "SF Mono", ui-monospace, Consolas, monospace; }

.head-tools { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.search-box {
  width: 280px; height: 38px;
  border: 1px solid #dce8e1; border-radius: 10px;
  background: #fff; display: flex; align-items: center;
  gap: 8px; padding: 0 12px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
}
.search-box .material-icons { font-size: 18px; color: #98a2b3; }
.search-box input { border: none; outline: none; width: 100%; font-size: 14px; color: #344054; font-family: inherit; background: transparent; }
.search-box input::placeholder { color: #98a2b3; }
.btn-refresh,
.btn-export {
  height: 38px; border-radius: 10px;
  border: 1px solid #dce8e1; background: #fff;
  padding: 0 16px; color: #344054; font-weight: 700;
  display: flex; align-items: center; gap: 6px;
  cursor: pointer; font-family: inherit; font-size: 14px;
}
.btn-refresh .material-icons,
.btn-export .material-icons { font-size: 16px; }
.btn-refresh:hover,
.btn-export:hover { background: #f9fafb; border-color: #d0d5dd; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }
.btn-export { color: #047857; border-color: #bdebd6; background: #f0fdf8; }
.btn-export.secondary { color: #2563eb; border-color: #bfdbfe; background: #eff6ff; }

.loading-state, .empty-state { color: #9ca3af; font-size: 15px; padding: 60px 0; text-align: center; }

/* KPI Cards */
.kpi-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.kpi-card {
  min-height: 86px; padding: 14px;
  border: 1px solid #edf2ef; border-radius: 14px; background: white;
  display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;
  box-shadow: 0 8px 22px rgba(16,24,40,.045);
}
.kpi-left { min-width: 0; }
.kpi-label { font-size: 12px; color: #667085; font-weight: 700; margin-bottom: 6px; }
.kpi-val { font-size: 24px; font-weight: 900; color: #101828; line-height: 1; }
.kpi-sub { font-size: 12px; color: #98a2b3; margin-top: 6px; }
.kpi-icon {
  width: 46px; height: 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.kpi-icon .material-icons { font-size: 23px; }
.kpi-icon.green { background: #ecfdf5; color: #1f8f60; }
.kpi-icon.gold { background: #fffbeb; color: #d8a23a; }
.kpi-icon.blue { background: #eff6ff; color: #4f86f7; }
.kpi-icon.red { background: #fef2f2; color: #ef4444; }
.kpi-icon.gray { background: #f4f4f5; color: #98a2b3; }
.kpi-alert { border-color: #fecaca; }

/* Panel */
.panel {
  background: white; border: 1px solid #edf2ef; border-radius: 16px;
  overflow: hidden; box-shadow: 0 12px 30px rgba(16,24,40,.055);
}
.panel-head {
  padding: 14px 18px; border-bottom: 1px solid #edf2ef;
  display: flex; align-items: center; justify-content: space-between;
  background: #fbfefc;
}
.panel-head h2 { margin: 0; font-size: 16px; font-weight: 900; color: #101828; }
.panel-head p { margin: 3px 0 0; color: #667085; font-size: 12px; }
.panel-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.panel-tools label { display: inline-flex; align-items: center; gap: 6px; color: #667085; font-size: 12px; font-weight: 800; }
.panel-tools select {
  height: 30px;
  border: 1px solid #dce8e1;
  border-radius: 8px;
  background: #fff;
  color: #344054;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  padding: 0 8px;
}
.panel-count { font-size: 12px; color: #00895f; font-weight: 800; background: #ecfdf3; border: 1px solid #cdeee0; border-radius: 999px; padding: 4px 9px; }
.table-scroll { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; font-size: 13px; color: #344054; }
thead { background: #f8faf9; }
th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 800; color: #667085; letter-spacing: 0; border-bottom: 1px solid #edf2ef; white-space: nowrap; }
td { padding: 11px 14px; border-bottom: 1px solid #edf2ef; white-space: nowrap; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fbfefc; }

.uid { font-weight: 700; color: #111827; }
.user-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.user-cell strong { display: block; color: #101828; font-size: 13px; font-weight: 850; }
.user-cell small { display: block; margin-top: 2px; color: #98a2b3; font-size: 11px; }
.user-cell.large .avatar { width: 42px; height: 42px; border-radius: 12px; font-size: 17px; }
.user-cell.large strong { font-size: 15px; }
.avatar {
  width: 32px; height: 32px; border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ecfdf3, #e0f2fe);
  color: #047857; font-weight: 900; flex: 0 0 auto;
}
.tag { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.tag.admin { background: #fffbeb; color: #b45309; }
.tag.user { background: #ecfdf5; color: #059669; }
.chip { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: #f3f4f6; color: #6b7280; }
.chip.active { background: #fef2f2; color: #ef4444; }

.op { display: flex; gap: 8px; align-items: center; }
.op a { color: #047857; font-weight: 750; font-size: 13px; cursor: pointer; text-decoration: none; }
.op a:hover { color: #065f46; }
.op-detail { height: 28px; padding: 0 9px; border-radius: 8px; background: #ecfdf3; display: inline-flex; align-items: center; gap: 3px; }
.op-detail .material-icons { font-size: 16px; }
.op a.warn { color: #d97706; }
.op a.muted { opacity: .4; pointer-events: none; }
.op-na { font-size: 13px; color: #98a2b3; }
.op-loading { opacity: .5; }

/* Detail row */
.detail-row td { background: #f6fbf8; padding: 0 !important; }
.inline-detail { padding: 18px 20px 20px; border-top: 1px solid #dff3e8; box-shadow: inset 3px 0 0 #10b981; }
.detail-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.detail-count { color: #047857; background: #ecfdf3; border: 1px solid #cdeee0; border-radius: 999px; padding: 4px 9px; font-size: 12px; font-weight: 850; }
.detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1px;
  background: #e5ece8; border: 1px solid #e5ece8; border-radius: 12px; overflow: hidden;
}
.dg-item { display: flex; justify-content: space-between; padding: 12px 16px; background: white; }
.dg-key { font-size: 14px; color: #667085; }
.dg-val { font-size: 14px; font-weight: 700; color: #111827; }
.detail-history { margin-top: 16px; }
.detail-history h4 { font-size: 13px; font-weight: 900; margin: 0 0 8px; color: #344054; }
.empty-detail { margin-top: 12px; color: #98a2b3; font-size: 12px; }
.history-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; }
.history-card {
  min-height: 80px; padding: 10px; border: 1px solid #e5ece8; border-radius: 12px;
  background: #fff; display: grid; gap: 10px; box-shadow: 0 4px 14px rgba(16,24,40,.035);
}
.history-card > div:first-child { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.history-id { color: #667085; font-size: 13px; }
.history-card strong { color: #101828; }
.history-metrics { display: flex; gap: 8px; flex-wrap: wrap; }
.history-metrics span { padding: 3px 7px; border-radius: 8px; background: #f8fafc; color: #475467; font-size: 12px; font-weight: 750; }
.history-card em { justify-self: start; font-style: normal; color: #047857; background: #ecfdf3; border-radius: 999px; padding: 3px 7px; font-size: 11px; font-weight: 850; }

.footer-row {
  padding: 10px 18px; border-top: 1px solid #f1f5f9;
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; color: #98a2b3;
  gap: 12px;
  flex-wrap: wrap;
}
.pager { display: inline-flex; align-items: center; gap: 8px; color: #344054; font-weight: 800; }
.pager button {
  height: 28px;
  border: 1px solid #dce8e1;
  border-radius: 8px;
  background: #fff;
  color: #047857;
  font: inherit;
  font-size: 12px;
  font-weight: 850;
  padding: 0 10px;
  cursor: pointer;
}
.pager button:disabled { opacity: .45; cursor: not-allowed; }

@media (max-width: 980px) {
  .page-head { align-items: stretch; flex-direction: column; }
  .head-tools, .search-box { width: 100%; }
  .kpi-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .detail-grid { grid-template-columns: 1fr; }
}
</style>
