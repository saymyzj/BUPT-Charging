<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="brand-icon"><span class="material-icons">bolt</span></div>
        <div>
          <div class="brand-title">充电调度系统</div>
          <div class="brand-sub">管理端</div>
        </div>
      </div>

      <nav class="side-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="{ active: $route.path === item.path }"
        >
          <span class="material-icons menu-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="system-card">
          <div class="sys-status-row">
            <span class="sys-dot"></span>
            <span class="sys-status-text">系统运行正常</span>
          </div>
          <div class="sys-info-row">
            <span class="sys-info-label">在线设备</span>
            <span class="sys-info-val">{{ onlineCount }} / {{ totalCount }}</span>
          </div>
          <div class="sys-bar"><div class="sys-bar-fill" :style="{ width: onlineRate + '%' }"></div></div>
        </div>
        <div class="admin-user">
          <div class="user-avatar">{{ username.charAt(0) }}</div>
          <div class="user-info">
            <div class="user-name">{{ username }}</div>
            <div class="user-role">管理员</div>
          </div>
          <button class="user-logout" @click="handleLogout" title="退出登录"><span class="material-icons">logout</span></button>
        </div>
      </div>
    </aside>

    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile, getStations } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { clearAuthSession } from '@/utils/authSession'

const router = useRouter()
const username = ref('admin')

const menuItems = [
  { path: '/admin/overview', label: '总览', icon: 'grid_view' },
  { path: '/admin/config', label: '系统配置', icon: 'settings' },
  { path: '/admin/records', label: '设备控制', icon: 'ev_station' },
  { path: '/admin/users', label: '用户管理', icon: 'group' },
  { path: '/admin/statistics', label: '报表统计', icon: 'bar_chart' },
]

const uptime = ref('--')
const onlineCount = ref(0)
const totalCount = ref(0)
const onlineRate = ref(0)

async function loadSidebarStatus() {
  try {
    const res = await getStations()
    const data = unwrapResponseData(res)
    const stations = Array.isArray(data) ? data : (data.stations || [])
    const running = stations.filter(s => s.station_status === 'RUNNING').length
    totalCount.value = stations.length
    onlineCount.value = running
    onlineRate.value = stations.length ? Math.round(running / stations.length * 100) : 0
  } catch (_) { /* silent */ }
}

function handleLogout() {
  clearAuthSession()
  router.push('/login')
}

async function loadProfile() {
  try {
    const res = await getProfile()
    const data = unwrapResponseData(res)
    if (data.code === undefined || data.code === 0) {
      username.value = data.username || 'admin'
    }
  } catch (_) {
    /* silent */
  }
}

onMounted(() => {
  loadProfile()
  loadSidebarStatus()
})
</script>

<style scoped>
.admin-shell {
  height: 100vh;
  overflow: hidden;
  display: grid;
  grid-template-columns: 198px minmax(0, 1fr);
  background: linear-gradient(180deg, #ffffff 0%, #f7fbf9 100%);
}

.admin-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 20px 14px;
  border-right: 1px solid #e5e7eb;
  background: linear-gradient(180deg, #ffffff 0%, #f4fbf7 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 20;
}

.brand {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 26px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #059669, #10b981);
  box-shadow: 0 6px 18px rgba(5,150,105,.28);
  flex: 0 0 auto;
}
.brand-icon .material-icons { font-size: 22px; }

.brand-title {
  font-size: 18px;
  font-weight: 850;
  line-height: 1.2;
  white-space: nowrap;
  color: #101828;
}

.brand-sub {
  margin-top: 4px;
  color: #667085;
  font-size: 13px;
}

.side-menu {
  display: grid;
  gap: 8px;
}

.side-menu a {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border-radius: 10px;
  color: #475467;
  font-size: 14px;
  font-weight: 650;
  text-decoration: none;
  transition: .2s ease;
}

.side-menu a:hover {
  background: #f7faf8;
  color: #101828;
}

.side-menu a.active {
  color: #059669;
  background: rgba(16,185,129,.1);
}

.menu-icon {
  font-size: 20px;
  opacity: .85;
  flex: 0 0 auto;
}
.side-menu a.active .menu-icon { opacity: 1; }

.sidebar-footer {
  margin-top: auto;
  display: grid;
  gap: 12px;
  padding-top: 18px;
}

/* System status card */
.system-card {
  padding: 12px 14px;
  border: 1px solid #e7efe9;
  border-radius: 14px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.sys-status-row { display: flex; align-items: center; gap: 7px; }
.sys-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16,185,129,.2);
  flex-shrink: 0;
  animation: sysPulse 2s ease-in-out infinite;
}
@keyframes sysPulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(16,185,129,.2); }
  50% { box-shadow: 0 0 0 5px rgba(16,185,129,.1); }
}
.sys-status-text { font-size: 12px; font-weight: 700; color: #101828; }
.sys-info-row { display: flex; justify-content: space-between; align-items: center; }
.sys-info-label { font-size: 11px; color: #9ca3af; }
.sys-info-val { font-size: 11px; font-weight: 700; color: #344054; }
.sys-bar { height: 4px; background: #f3f4f6; border-radius: 999px; overflow: hidden; margin-top: 2px; }
.sys-bar-fill { height: 100%; background: linear-gradient(90deg, #10b981, #34d399); border-radius: 999px; transition: width 0.4s; }

/* User row */
.admin-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #edf0ee;
  border-radius: 14px;
  background: #fff;
}
.user-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: #d1fae5; color: #059669;
  display: grid; place-items: center;
  font-size: 14px; font-weight: 800;
  flex-shrink: 0; text-transform: uppercase;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 13px; font-weight: 700; color: #101828; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-role { font-size: 11px; color: #10b981; font-weight: 600; margin-top: 1px; }
.user-logout {
  background: none; border: 1px solid #fecaca; cursor: pointer;
  color: #ef4444; padding: 4px 6px; border-radius: 8px; transition: 0.15s;
  display: flex; align-items: center;
}
.user-logout .material-icons { font-size: 17px; }
.user-logout:hover { background: #fef2f2; border-color: #fca5a5; }

.admin-main {
  min-width: 0;
  overflow-y: auto;
  height: 100%;
  background: #f4f7f6;
}

@media (max-width: 900px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: relative;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid #e5e7eb;
  }

  .side-menu {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
