import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/admin/overview'
  },
  {
    path: '/admin/overview',
    name: 'AdminDashboard',
    component: () => import('../views/admin/Overview.vue'),
    meta: { title: '管理员控制台' }
  },
  {
    path: '/admin/records',
    name: 'AdminRecords',
    component: () => import('../views/admin/Records.vue'),
    meta: { title: '记录中心控制台' }
  },
  {
    path: '/admin/config',
    name: 'AdminConfig',
    component: () => import('../views/admin/SystemConfig.vue'),
    meta: { title: '系统配置' }
  },
  {
    path: '/admin/statistics',
    name: 'AdminStatistics',
    component: () => import('../views/admin/Statistics.vue'),
    meta: { title: '统计分析' }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('../views/admin/UserManage.vue'),
    meta: { title: '用户管理' }
  },
  // 直接访问 /admin（无具体子路径）统一引导到登录页，避免未认证直接访问管理首页
  {
    path: '/admin',
    redirect: '/login'
  },
  
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录 - 智能充电桩系统' }
  },
  // 用户侧
  {
    path: '/user',
    component: () => import('../views/user/Layout.vue'),
    // 访问 /user 仅作为入口，统一跳转到登录页，具体子页面仍可直接访问（/user/workspace 等）
    redirect: '/login',
    children: [
      { path: 'workspace', component: () => import('../views/user/Workspace.vue'), meta: { title: '工作台 - 车主' } },
      { path: 'task', component: () => import('../views/user/Task.vue'), meta: { title: '当前任务 - 车主' } },
      { path: 'account', component: () => import('../views/user/Account.vue'), meta: { title: '账户中心 - 车主' } }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：更改页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router
