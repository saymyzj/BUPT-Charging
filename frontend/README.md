# 前端说明

> 文档版本：V3.0  
> 更新日期：2026-05-06  
> 适用范围：当前 `develop` 分支 Vue SPA 前端

---

## 1. 文档定位

本文档说明前端当前在 `develop` 分支上的真实实现状态。

配合阅读：

- [冻结接口文档 - 前端实现版](冻结接口文档_前端实现版.md)
- [成员C页面设计清单](成员C页面设计清单.md)

---

## 2. 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.x | 前端框架 |
| Vite | ^8.x | 构建工具 + 开发服务器 |
| Vue Router | ^4.x | SPA 路由 + 路由守卫 |
| Axios | ^1.x | HTTP 请求 |

> 已移除 Element Plus 依赖，所有页面使用自定义 CSS。

---

## 3. 项目结构

```
src/
├── api/
│   ├── request.js          # Axios 实例（拦截器 + Bearer token）
│   └── charging.js         # 22 个 API 函数（V3 §7 接口清单）
├── constants/
│   └── enums.js            # V3 §9 状态枚举字典
├── router/
│   └── index.js            # 路由定义 + auth/role 守卫
├── views/
│   ├── Login.vue           # Landing 着陆页 + 登录/注册弹窗
│   ├── user/
│   │   ├── Layout.vue      # 用户端顶部导航布局
│   │   ├── Workspace.vue   # 工作台（提交请求 + 状态轮询）
│   │   ├── Task.vue        # 当前请求（进度 + 操作）
│   │   ├── Profile.vue     # 账户中心（个人资料 + 本地历史账单入口）
│   │   └── Account.vue     # 账单详情（单个请求详单 + 本地支付状态）
│   └── admin/
│       ├── Layout.vue      # 管理端顶部导航布局
│       ├── Overview.vue    # 管理总览（桩状态卡片 + 队列查看）
│       ├── SystemConfig.vue# 系统配置（调度模式 + 故障策略）
│       ├── Records.vue     # 设备控制（启动/关闭/故障/恢复）
│       ├── UserManage.vue  # 用户管理（列表 + 详情 + 修改容量）
│       └── Statistics.vue  # 报表统计（日/周/月 + CSS 柱状图）
├── App.vue
└── main.js
```

---

## 4. 已完成内容

### 4.1 用户端

- Landing 着陆页 + 内嵌登录/注册弹窗（`POST /api/auth/login`, `POST /api/auth/register`）
- 工作台提交充电请求（`POST /api/request/create`），5s 轮询状态
- 当前请求页：状态 banner + 关键指标 + 时间线 + 操作按钮
  - 修改充电模式（`PUT /api/request/mode`）
  - 修改充电量（`PUT /api/request/energy`）
  - 取消请求（`POST /api/request/cancel`）
  - 提前结束（`POST /api/request/stop`）
- 账户中心：展示用户资料，并通过本地保存的 `request_id` 兜底展示当前浏览器记录过的历史账单入口
- 账单详情：通过 `GET /api/request/detail/{id}` 展示单个请求详单
- 支付状态当前为前端本地模拟，未接入真实后端支付接口
- 活跃请求恢复当前依赖本地 `request_id`；若跨浏览器或清缓存后恢复，需要后端补充活跃请求查询接口

### 4.2 管理端

- 管理总览：桩状态卡片 + 查看桩队列
- 系统配置：只读参数 + 切换调度模式 + 切换故障策略
- 设备控制：启动/关闭/标记故障/恢复操作
- 用户管理：用户列表 + 详情弹窗 + 修改电池容量
- 报表统计：日/周/月粒度 + 汇总 + CSS 柱状图

冻结接口范围内的大部分用户端和管理端页面已接入真实 API。历史账单列表、支付状态、跨浏览器活跃请求恢复属于冻结接口未完整覆盖的增强能力，当前以前端本地记录作为临时兜底。

---

## 5. 路由与鉴权

| 路由 | 组件 | 角色要求 |
|------|------|----------|
| `/login` | Login.vue | 游客（已登录自动跳转） |
| `/user/workspace` | Workspace.vue | USER |
| `/user/task` | Task.vue | USER |
| `/user/account` | Profile.vue | USER |
| `/user/bills` | Account.vue | USER |
| `/admin/overview` | Overview.vue | ADMIN |
| `/admin/config` | SystemConfig.vue | ADMIN |
| `/admin/records` | Records.vue | ADMIN |
| `/admin/users` | UserManage.vue | ADMIN |
| `/admin/statistics` | Statistics.vue | ADMIN |

路由含义：

- `/user/account`：账户中心 / 个人资料 / 当前浏览器记录过的历史账单入口
- `/user/bills`：当前或单个账单详情页

localStorage 键：

- 鉴权与用户信息：`auth_token`, `user_role`, `user_id`, `username`
- 当前请求兜底：`request_id`, `active_request_conflict`
- 历史账单兜底：`request_ids`
- 本地支付状态：与账单详情页支付演示相关的本地记录

---

## 6. 本地运行

### 6.1 安装依赖

```bash
cd frontend
npm install
```

### 6.2 启动开发服务器

```bash
npm run dev
```

默认访问 `http://localhost:3000`。Vite 代理 `/api` 请求至 `http://127.0.0.1:5000`。

### 6.3 构建

```bash
npm run build
```

产物输出至 `dist/`。

---

## 7. 与 V2.0 的主要差异

| 项目 | V2.0 | V3.0 |
|------|------|------|
| 登录/注册 | 前端模拟跳转 | 真实 API 鉴权 |
| 管理端 | 静态演示 | 冻结接口范围内大部分接入真实 API |
| UI 框架 | Element Plus | 自定义 CSS（绿色新能源主题） |
| 登录页 | 独立双栏布局 | Landing 着陆页 + 弹窗 |
| 路由守卫 | 仅标题更新 | token + role 双重保护 |
| 状态枚举 | V2 冻结接口状态 | V3 §9 状态字典 |
| 接口数量 | 9 个 | 22 个 |

---

## 8. 当前限制与后续接口建议

- 历史账单列表：当前只能展示本浏览器保存过 `request_id` 的请求。若需要完整历史账单，应新增后端列表接口，例如 `GET /api/request/details`。
- 活跃请求恢复：当前依赖本地 `request_id`。若需要用户重新登录后自动恢复服务端已有活跃请求，应新增后端接口，例如 `GET /api/request/active`。
- 支付状态：当前为前端本地模拟。若需要真实支付闭环，应新增支付确认和支付状态查询接口。
- 联调端口：当前前端开发服务器默认访问 `http://localhost:3000`，后端默认监听 `http://127.0.0.1:5000`，Vite 将 `/api` 和 `/health` 代理到后端 `5000` 端口。
