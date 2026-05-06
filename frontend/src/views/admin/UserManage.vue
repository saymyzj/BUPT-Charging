<template>
  <div class="page">
    <div class="page-head">
      <h1>用户管理</h1>
      <p>查看用户列表、详情，维护车辆电池容量</p>
    </div>

    <div class="toolbar">
      <button class="btn btn-primary" @click="loadUsers">刷新</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

    <table class="t" v-if="!loading && users.length">
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
        <tr v-for="u in users" :key="u.user_id">
          <td><strong>{{ u.user_id }}</strong></td>
          <td>{{ u.username }}</td>
          <td>{{ capacityText(u) }}</td>
          <td><span class="role-badge" :class="u.role === 'ADMIN' ? 'admin' : 'user'">{{ u.role }}</span></td>
          <td>{{ fmtDate(u.created_at) }}</td>
          <td>
            <span class="active-badge" :class="u.has_active_request ? 'yes' : 'no'">{{ u.has_active_request ? '有' : '无' }}</span>
          </td>
          <td class="action-cell">
            <button class="btn-sm btn-blue" @click="viewDetail(u.user_id)">详情</button>
            <button
              class="btn-sm btn-green"
              v-if="u.role !== 'ADMIN'"
              @click="editCapacity(u)"
              :disabled="u.has_active_request"
              :title="u.has_active_request ? '该用户有活跃请求，暂不可修改容量' : ''"
            >修改容量</button>
            <span v-else class="muted">不适用</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Detail Modal -->
    <div class="modal-overlay" v-if="showModal" @click.self="showModal=false">
      <div class="modal-card">
        <div class="modal-head"><h3>用户详情</h3><button class="modal-close" @click="showModal=false">&times;</button></div>
        <div class="modal-body" v-if="userDetail">
          <div class="detail-grid">
            <div class="dg-item"><span class="dg-key">用户ID</span><span class="dg-val">{{ userDetail.user_id }}</span></div>
            <div class="dg-item"><span class="dg-key">用户名</span><span class="dg-val">{{ userDetail.username }}</span></div>
            <div class="dg-item"><span class="dg-key">电池容量</span><span class="dg-val">{{ capacityText(userDetail) }}</span></div>
            <div class="dg-item"><span class="dg-key">角色</span><span class="dg-val">{{ userDetail.role }}</span></div>
          </div>
          <div v-if="userDetail.historical_details && userDetail.historical_details.length" style="margin-top:16px;">
            <h4 style="font-size:13px;font-weight:600;margin-bottom:10px;">历史详单</h4>
            <table class="t-sm">
              <thead><tr><th>详单ID</th><th>桩位</th><th>电量</th><th>总费用</th><th>终态</th></tr></thead>
              <tbody>
                <tr v-for="d in userDetail.historical_details" :key="d.detail_id">
                  <td>{{ d.detail_id }}</td>
                  <td>{{ d.station_code }}</td>
                  <td>{{ d.actual_energy }} kWh</td>
                  <td>¥{{ (d.total_fee || 0).toFixed(2) }}</td>
                  <td>{{ d.request_status }}</td>
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
import { ref, onMounted } from 'vue'
import { getUsers, getUserDetail, updateBatteryCapacity } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'

const users = ref([])
const loading = ref(false)
const showModal = ref(false)
const userDetail = ref(null)

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
  } catch (_) { /* silent */ }
  loading.value = false
}

async function viewDetail(userId) {
  showModal.value = true
  userDetail.value = null
  try {
    const res = await getUserDetail(userId)
    const data = unwrapResponseData(res)
    userDetail.value = data
  } catch (_) { /* silent */ }
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
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 20px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }
.toolbar { margin-bottom: 16px; }
.btn { padding: 8px 18px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.12s; }
.btn-primary { background: #10b981; color: white; }
.btn-primary:hover { background: #059669; }
.loading-text { color: #9ca3af; font-size: 14px; padding: 40px 0; text-align: center; }

table.t { width: 100%; border-collapse: collapse; background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; }
table.t th { text-align: left; padding: 12px 14px; font-size: 11px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e5e7eb; background: #f8faf9; }
table.t td { padding: 12px 14px; font-size: 13px; border-bottom: 1px solid #f3f4f6; color: #374151; }
table.t td strong { color: #111827; font-weight: 700; }
table.t tr:last-child td { border-bottom: none; }

.role-badge { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.role-badge.admin { background: #fef3c7; color: #92400e; }
.role-badge.user { background: #ecfdf5; color: #059669; }
.active-badge { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.active-badge.yes { background: #fef2f2; color: #ef4444; }
.active-badge.no { background: #f3f4f6; color: #6b7280; }

.action-cell { display: flex; gap: 6px; }
.btn-sm { padding: 5px 10px; border-radius: 6px; border: 1px solid; font-size: 11px; font-weight: 600; cursor: pointer; transition: 0.12s; background: white; }
.btn-sm:disabled { opacity: 0.35; cursor: not-allowed; }
.muted { font-size: 12px; color: #9ca3af; }
.btn-green { border-color: #d1fae5; color: #059669; }
.btn-green:hover:not(:disabled) { background: #ecfdf5; }
.btn-blue { border-color: #bfdbfe; color: #3b82f6; }
.btn-blue:hover { background: #eff6ff; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-card { background: white; border-radius: 16px; width: 640px; max-height: 80vh; overflow-y: auto; }
.modal-head { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid #e5e7eb; }
.modal-head h3 { font-size: 16px; font-weight: 700; }
.modal-close { background: none; border: none; font-size: 24px; cursor: pointer; color: #9ca3af; }
.modal-body { padding: 20px 24px; }

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #e5e7eb; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.dg-item { display: flex; justify-content: space-between; padding: 12px 14px; background: white; }
.dg-key { font-size: 13px; color: #6b7280; }
.dg-val { font-size: 13px; font-weight: 600; color: #111827; }

.t-sm { width: 100%; border-collapse: collapse; font-size: 12px; }
.t-sm th { text-align: left; padding: 8px; color: #9ca3af; border-bottom: 1px solid #e5e7eb; font-weight: 500; }
.t-sm td { padding: 8px; border-bottom: 1px solid #f3f4f6; color: #374151; }
</style>
