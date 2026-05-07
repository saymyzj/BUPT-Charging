<template>
  <div class="layout">
    <nav class="nav">
      <div class="nav-brand">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#10b981"/></svg>
        <span>充电调度系统 · 管理端</span>
      </div>
      <div class="nav-links">
        <router-link to="/admin/overview" :class="{ active: $route.path === '/admin/overview' }">总览</router-link>
        <router-link to="/admin/config" :class="{ active: $route.path === '/admin/config' }">系统配置</router-link>
        <router-link to="/admin/records" :class="{ active: $route.path === '/admin/records' }">设备控制</router-link>
        <router-link to="/admin/users" :class="{ active: $route.path === '/admin/users' }">用户管理</router-link>
        <router-link to="/admin/statistics" :class="{ active: $route.path === '/admin/statistics' }">报表统计</router-link>
      </div>
      <div class="nav-actions">
        <div class="nav-admin">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-4a2 2 0 00-2-2H6a2 2 0 00-2 2v4a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4"/></svg>
          {{ username }}
        </div>
        <button class="nav-logout" @click="handleLogout">退出</button>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { clearAuthSession } from '@/utils/authSession'

const router = useRouter()
const username = ref('admin')

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
  } catch (_) { /* silent */ }
}

onMounted(loadProfile)
</script>

<style scoped>
.layout { min-height: 100vh; background: #f8faf9; }
.nav { position: sticky; top: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; height: 56px; background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid #e5e7eb; }
.nav-brand { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; color: #111827; letter-spacing: -0.3px; }
.nav-links { display: flex; gap: 2px; }
.nav-links a { padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; color: #6b7280; text-decoration: none; transition: 0.15s; }
.nav-links a.active { color: #059669; background: #ecfdf5; font-weight: 600; }
.nav-links a:hover:not(.active) { color: #1f2937; background: #f3f4f6; }
.nav-actions { display: flex; align-items: center; gap: 8px; }
.nav-admin { display: flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; background: #111827; font-size: 12px; font-weight: 600; color: white; }
.nav-logout { padding: 6px 12px; border-radius: 999px; border: 1px solid #fecaca; background: white; color: #ef4444; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.15s; }
.nav-logout:hover { background: #fef2f2; }
</style>
