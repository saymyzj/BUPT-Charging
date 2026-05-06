# 成员C前端审核意见回复

> 回复日期：2026-05-06  
> 回复对象：`docs/review/成员C前端审核意见.md`  
> 说明范围：仅说明并处理前端目录内问题；不修改后端代码。

---

## 一、总体回复

已根据审核意见重新核对当前前端实现。当前前端主体页面和冻结接口调用基本保持可用，审核意见中指出的报表字段读取、前端 README 路由说明、完成度表述过满等问题已在前端侧完成修正。

仍需说明的是，历史账单列表、当前活跃请求恢复、支付状态闭环属于冻结接口未覆盖的增强能力。当前前端只能用浏览器本地记录作为临时兜底，不能声明为完整后端闭环。

---

## 二、已完成整改项

### 1. 报表接口字段读取

审核意见指出 `frontend/src/views/admin/Statistics.vue` 将报表数据错读为 `data.reports`。

当前已修正为优先读取 `data.rows`，并兼容旧字段：

```js
reports.value = Array.isArray(data) ? data : (data.rows || data.reports || [])
```

当前状态：

- 日报、周报、月报均调用 `GET /api/admin/reports?granularity=...`。
- 前端优先使用冻结接口规定的 `data.rows`。
- 无数据时才显示“暂无数据”。

### 2. 前端 README 路由与组件说明

审核意见指出 `/user/account`、`/user/bills`、`Account.vue`、`Profile.vue` 描述混淆。

当前 `frontend/README.md` 已修正为：

| 路由 | 实际组件 | 当前含义 |
|------|----------|----------|
| `/user/account` | `Profile.vue` | 账户中心 / 个人资料 / 当前浏览器记录过的历史账单入口 |
| `/user/bills` | `Account.vue` | 当前或单个账单详情页 |

项目结构说明也已同步：

- `Profile.vue`：账户中心
- `Account.vue`：账单详情

### 3. 前端完成度表述

审核意见指出“全部页面均已接入真实 API”等表述过满。

当前 `frontend/README.md` 与 `frontend/冻结接口文档_前端实现版.md` 已改为更准确的描述：

- 冻结接口范围内的大部分用户端和管理端页面已接入真实 API。
- 历史账单列表当前使用本地 `request_id` 兜底。
- 支付状态当前为前端本地模拟。
- 活跃请求恢复需要后端补充接口后才能完整闭环。

### 4. 联调端口说明

当前前端代码中 `frontend/vite.config.js` 的代理目标为：

```js
target: 'http://127.0.0.1:5000'
```

`frontend/README.md` 已同步说明：

- 前端开发服务器默认访问 `http://localhost:3000`
- 后端默认监听 `http://127.0.0.1:5000`
- Vite 将 `/api` 和 `/health` 代理到后端 `5000` 端口

本次回复不修改后端目录文件。

---

## 三、当前仍存在但属于接口能力缺口的问题

### 1. 历史账单列表

当前实现位置：`frontend/src/views/user/Profile.vue`

当前状态：

- 页面标题处已提示“当前浏览器已记录的请求”。
- 前端通过 `localStorage.request_ids` 和当前 `localStorage.request_id` 获取本地记录过的请求编号。
- 再逐个调用 `GET /api/request/detail/{request_id}` 获取单个详单。

当前限制：

- 换浏览器后历史记录不可恢复。
- 清除缓存后历史记录不可恢复。
- 用户在其他设备提交的请求不会出现在当前浏览器。
- 这不是完整的服务端历史账单列表。

后续建议：

```http
GET /api/request/details
```

或：

```http
GET /api/auth/profile/bills
```

后端提供该接口后，前端应以服务端返回列表作为主数据源，本地记录仅作为兼容兜底。

### 2. 当前活跃请求恢复

当前实现位置：

- `frontend/src/views/user/Workspace.vue`
- `frontend/src/views/user/Task.vue`

当前状态：

- 前端依赖本地 `request_id` 查询 `GET /api/request/status/{request_id}`。
- 如果提交请求时后端返回“已有活跃请求”，但本地没有 `request_id`，前端只能记录 `active_request_conflict` 并展示提示。

当前限制：

- 用户换浏览器、清缓存、退出后重新登录时，若本地缺少 `request_id`，无法自行恢复已有活跃请求详情。
- 该限制来自冻结接口没有提供“按当前登录用户查询活跃请求”的能力。

后续建议：

```http
GET /api/request/active
```

无活跃请求时返回 `data: null`，有活跃请求时返回当前请求状态结构。

### 3. 支付状态

当前实现位置：

- `frontend/src/views/user/Account.vue`
- `frontend/src/views/user/Profile.vue`

当前状态：

- 账单详情页提供“立即支付”按钮。
- 支付结果通过浏览器本地 `bill_paid_*` 记录。
- 页面文案已说明“后端暂未提供支付接口，当前按钮先使用前端本地模拟支付”。

当前限制：

- 换浏览器或清缓存后支付状态丢失。
- 管理端和报表无法获得可信支付状态。
- 不能避免真实业务中的重复支付或并发支付。

后续建议：

如果项目需要真实支付闭环，应新增后端接口，例如：

```http
POST /api/request/detail/{detail_id}/pay
GET /api/request/detail/{detail_id}/payment
```

如果项目不要求真实支付，则应继续明确“详单即最终账单，支付状态仅为前端演示状态”。

---

## 四、当前前端仍需后续整理的问题


### 1. 账单详情页只读取当前 `request_id`

当前 `frontend/src/views/user/Account.vue` 只从 `localStorage.request_id` 读取请求编号，因此 `/user/bills` 当前更准确地说是“当前请求账单详情页”。

如果后续希望从账户中心账单列表进入任意历史账单详情，建议支持：

```text
/user/bills?request_id=REQ0001
```

或改为路由参数：

```text
/user/bills/:request_id
```

### 2. 退出登录时本地兜底数据未全部清理

当前用户端退出登录只清理鉴权与用户信息：

- `auth_token`
- `user_role`
- `user_id`
- `username`

但没有清理：

- `request_id`
- `request_ids`
- `active_request_conflict`
- `bill_paid_*`

这可能导致同一浏览器切换账号后看到上一个用户的本地兜底账单或支付状态。建议后续增加统一的前端本地状态清理逻辑，或按用户维度隔离本地键。


---

## 五、验收建议

建议后续按以下前端流程补充验证：

- 使用真实后端跑通登录、注册、提交请求。
- 验证 `WAITING_AREA` 状态下修改模式、修改电量、取消请求。
- 验证 `QUEUED` 和 `CHARGING` 状态下提前结束。
- 验证 `COMPLETED`、`COMPLETED_EARLY`、`FAULT_INTERRUPTED` 三类详单展示。
- 验证报表 `day / week / month` 三个粒度均能读取后端 `rows` 数据。
- 验证账户中心仅展示当前浏览器已记录请求，并将该限制作为冻结接口限制记录。
- 验证退出登录后重新登录时当前请求能否恢复；若不能，应记录为缺少 `GET /api/request/active` 接口导致。

---

## 六、结论

当前前端已经完成审核意见中明确属于前端侧的主要修复：

1. 报表字段读取已改为优先读取 `data.rows`。
2. `frontend/README.md` 已同步真实路由、组件和端口说明。
3. 前端文档已去除“全部真实 API”类过满表述。
4. 历史账单、活跃请求恢复、支付状态已明确标注为前端本地兜底或模拟能力。

剩余问题主要不是冻结接口范围内的前端接错，而是接口能力缺口和文档进一步同步问题。若最终验收要求完整历史账单、跨浏览器活跃请求恢复或真实支付状态，需要组内确认并补充后端接口。
