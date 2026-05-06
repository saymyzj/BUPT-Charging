import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录 - 智能充电桩系统', guest: true }
  },

  // 用户端
  {
    path: '/user',
    component: () => import('../views/user/Layout.vue'),
    redirect: '/user/workspace',
    meta: { requiresAuth: true, role: 'USER' },
    children: [
      { path: 'workspace', name: 'UserWorkspace', component: () => import('../views/user/Workspace.vue'), meta: { title: '工作台' } },
      { path: 'task', name: 'UserTask', component: () => import('../views/user/Task.vue'), meta: { title: '当前请求' } },
      { path: 'account', name: 'UserAccount', component: () => import('../views/user/Profile.vue'), meta: { title: '账户中心' } },
      { path: 'bills', name: 'UserBills', component: () => import('../views/user/Account.vue'), meta: { title: '账单' } },
    ]
  },

  // 管理端
  {
    path: '/admin',
    component: () => import('../views/admin/Layout.vue'),
    redirect: '/admin/overview',
    meta: { requiresAuth: true, role: 'ADMIN' },
    children: [
      { path: 'overview', name: 'AdminOverview', component: () => import('../views/admin/Overview.vue'), meta: { title: '管理总览' } },
      { path: 'config', name: 'AdminConfig', component: () => import('../views/admin/SystemConfig.vue'), meta: { title: '系统配置' } },
      { path: 'records', name: 'AdminRecords', component: () => import('../views/admin/Records.vue'), meta: { title: '设备控制' } },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/UserManage.vue'), meta: { title: '用户管理' } },
      { path: 'statistics', name: 'AdminStatistics', component: () => import('../views/admin/Statistics.vue'), meta: { title: '报表统计' } },
    ]
  },

  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function clearAuthState() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_id')
  localStorage.removeItem('username')
}

router.beforeEach((to, from, next) => {
  // 页面标题
  if (to.meta.title) document.title = to.meta.title

  const token = localStorage.getItem('auth_token')
  const role = localStorage.getItem('user_role')
  const hasValidRole = role === 'USER' || role === 'ADMIN'
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)

  // 需要登录但未登录 → 跳登录
  if (requiresAuth && !token) {
    return next('/login')
  }

  // 有 token 但角色缺失/异常，多半是旧缓存；清理后回登录页，避免无限重定向
  if (requiresAuth && token && !hasValidRole) {
    clearAuthState()
    return next('/login')
  }

  // 已登录访问登录页 → 跳对应首页
  if (to.meta.guest && token && hasValidRole) {
    return next(role === 'ADMIN' ? '/admin/overview' : '/user/workspace')
  }

  // 角色不匹配 → 跳对应首页
  if (to.matched.some(r => r.meta.role) && token && hasValidRole) {
    const requiredRole = to.matched.find(r => r.meta.role)?.meta.role
    if (requiredRole && requiredRole !== role) {
      return next(role === 'ADMIN' ? '/admin/overview' : '/user/workspace')
    }
  }

  next()
})

export default router
