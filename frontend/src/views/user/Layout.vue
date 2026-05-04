<template>
  <div class="layout">
    <nav class="nav">
      <div class="nav-brand">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#10b981" />
        </svg>
        <span>充电调度系统</span>
      </div>

      <div class="nav-links">
        <router-link to="/user/workspace" :class="{ active: $route.path === '/user/workspace' }">工作台</router-link>
        <router-link to="/user/task" :class="{ active: $route.path === '/user/task' }">当前请求</router-link>
        <router-link to="/user/bills" :class="{ active: $route.path === '/user/bills' }">账单</router-link>
        <router-link to="/user/account" :class="{ active: $route.path === '/user/account' }">账户</router-link>
      </div>

      <div class="user-menu">
        <button class="nav-user" @click="toggleMenu">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4" />
            <path d="M20 21a8 8 0 10-16 0" />
          </svg>
          {{ username }}
          <span class="chevron">▾</span>
        </button>
        <div class="menu-pop" v-if="menuOpen">
          <button @click="handleLogout">退出登录</button>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const menuOpen = ref(false)
const username = computed(() => {
  const value = localStorage.getItem('username')
  return value && value !== 'undefined' ? value : 'user'
})

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function handleLogout() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_id')
  localStorage.removeItem('username')
  closeMenu()
  router.push('/login')
}
</script>

<style scoped>
.layout { min-height: 100vh; background: #f8faf9; }
.nav { position: sticky; top: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; height: 56px; background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid #e5e7eb; }
.nav-brand { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; color: #111827; letter-spacing: 0; }
.nav-links { display: flex; gap: 2px; }
.nav-links a { padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; color: #6b7280; text-decoration: none; transition: 0.15s; }
.nav-links a.active { color: #059669; background: #ecfdf5; font-weight: 600; }
.nav-links a:hover:not(.active) { color: #1f2937; background: #f3f4f6; }
.user-menu { position: relative; }
.nav-user { display: flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; border: 1px solid #e5e7eb; background: white; font-size: 12px; font-weight: 500; color: #6b7280; cursor: pointer; transition: 0.15s; text-decoration: none; }
.nav-user:hover { border-color: #10b981; color: #059669; }
.chevron { font-size: 12px; line-height: 1; color: #9ca3af; }
.menu-pop { position: absolute; top: calc(100% + 8px); right: 0; width: 112px; padding: 6px; border: 1px solid #e5e7eb; border-radius: 10px; background: white; box-shadow: 0 10px 24px rgba(15,23,42,0.12); }
.menu-pop button { display: block; width: 100%; padding: 9px 10px; border: none; border-radius: 7px; background: transparent; color: #ef4444; font: inherit; font-size: 13px; text-align: left; cursor: pointer; }
.menu-pop button:hover { background: #f3f4f6; color: #dc2626; }
</style>
