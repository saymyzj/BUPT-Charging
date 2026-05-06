# 成员C前端审核意见

审核时间：2026-05-06  
审核对象：`origin/feature/c-frontend-testing` 最新远程提交 `903457b`  
审核方式：未合并到本地 `develop`，通过远程分支对比和临时 worktree 审查；在临时目录执行 `npm install` 后，`npm run build` 通过。

## 一、总体结论

成员C这一版前端已经完成了较大范围的 V3.0 页面落地，用户端、管理端、路由守卫、状态枚举和大部分冻结接口调用都已经接入。整体方向是正确的，不能简单判定为“没有按冻结文档做”。

但当前版本仍不能认定为完全符合冻结文档要求，原因如下：

1. 报表页存在明确的冻结接口字段接错问题。
2. 前端代码、前端 README、后端 README 之间存在联调端口和路由说明不一致。
3. 用户历史账单、活跃请求恢复、支付状态等能力属于冻结接口未覆盖的增强能力，成员C目前采用本地兜底，不能作为最终完整闭环。
4. 成员C新增文档中有“全部已接入真实 API”的表述，但部分页面仍依赖浏览器本地记录或模拟状态，表述偏满。

责任判断：

- 成员B后端没有明显违反冻结接口文档。
- 成员C大部分接口选择是按冻结接口来的，但有前端字段接错和文档未同步问题。
- 部分体验不完整不是成员B违反冻结接口，而是冻结接口本身没有定义对应能力，需要作为后续接口增强项处理。

## 二、成员C已经完成的内容

### 1. 用户端页面

成员C已完成以下用户端页面或路由：

| 页面 | 路由 | 完成情况 | 说明 |
|------|------|----------|------|
| 登录 / 注册 | `/login` | 已完成 | 使用真实 `POST /api/auth/login` 和 `POST /api/auth/register` |
| 用户工作台 | `/user/workspace` | 已完成主体功能 | 支持提交充电请求、展示创建结果、保存 `request_id`、轮询状态 |
| 当前请求 | `/user/task` | 已完成主体功能 | 支持状态展示、刷新、修改模式、修改电量、取消、提前结束 |
| 账户中心 | `/user/account` | 已新增 | 展示用户基本信息和本地记录过的账单列表 |
| 账单详情 | `/user/bills` | 已新增 | 展示单个当前请求详单，并提供前端本地模拟支付 |

对应冻结接口接入情况：

| 冻结接口 | 页面 | 成员C接入情况 | 审核结论 |
|----------|------|----------------|----------|
| `POST /api/auth/login` | 登录 | 已接入 | 符合 |
| `POST /api/auth/register` | 注册 | 已接入 | 符合 |
| `GET /api/auth/profile` | 账户 / 当前请求 | 已接入 | 符合 |
| `POST /api/request/create` | 工作台 | 已接入 | 符合 |
| `GET /api/request/status/{request_id}` | 工作台 / 当前请求 | 已接入 | 符合 |
| `PUT /api/request/mode` | 当前请求 | 已接入 | 符合 |
| `PUT /api/request/energy` | 当前请求 | 已接入 | 符合 |
| `POST /api/request/cancel` | 当前请求 | 已接入 | 符合 |
| `POST /api/request/stop` | 当前请求 | 已接入 | 基本符合 |
| `GET /api/request/detail/{request_id}` | 账单 | 已接入 | 单个详单符合，历史列表不完整 |

### 2. 管理端页面

成员C已完成以下管理端页面：

| 页面 | 路由 | 完成情况 | 说明 |
|------|------|----------|------|
| 管理总览 | `/admin/overview` | 已完成主体功能 | 展示桩状态卡片，支持查看单桩队列 |
| 系统配置 | `/admin/config` | 已完成主体功能 | 展示系统参数，支持调度模式和故障策略切换 |
| 设备控制 | `/admin/records` | 已完成主体功能 | 支持启动、关闭、标记故障、恢复 |
| 用户管理 | `/admin/users` | 已完成主体功能 | 支持用户列表、详情、修改电池容量 |
| 报表统计 | `/admin/statistics` | 页面已完成，但接口字段接错 | 当前会显示不出真实报表数据 |

对应冻结接口接入情况：

| 冻结接口 | 页面 | 成员C接入情况 | 审核结论 |
|----------|------|----------------|----------|
| `GET /api/admin/system/config` | 系统配置 | 已接入 | 符合 |
| `PUT /api/admin/system/dispatch-mode` | 系统配置 | 已接入 | 符合 |
| `PUT /api/admin/system/fault-dispatch-mode` | 系统配置 | 已接入 | 符合 |
| `GET /api/admin/stations` | 管理总览 / 设备控制 | 已接入 | 符合 |
| `GET /api/admin/stations/{station_code}/queue` | 管理总览 | 已接入 | 符合 |
| `POST /api/admin/stations/{station_code}/start` | 设备控制 | 已接入 | 符合 |
| `POST /api/admin/stations/{station_code}/shutdown` | 设备控制 | 已接入 | 符合 |
| `POST /api/admin/stations/{station_code}/fault` | 设备控制 | 已接入 | 符合 |
| `POST /api/admin/stations/{station_code}/recover` | 设备控制 | 已接入 | 符合 |
| `GET /api/admin/users` | 用户管理 | 已接入 | 符合 |
| `GET /api/admin/users/{user_id}` | 用户管理 | 已接入 | 符合 |
| `PUT /api/admin/users/{user_id}/battery-capacity` | 用户管理 | 已接入 | 符合 |
| `GET /api/admin/reports?granularity=day|week|month` | 报表统计 | 已调用，但字段读取错误 | 不符合 |

### 3. 前端基础能力

成员C已完成：

- 路由结构重整。
- 用户端和管理端布局组件。
- 登录后基于 `auth_token` 和 `user_role` 的路由守卫。
- Axios 请求拦截器，自动携带 `Authorization: Bearer <token>`。
- V3 状态枚举集中到 `frontend/src/constants/enums.js`。
- 多个静态参考页和前端设计说明文档。
- 前端生产构建通过。

## 三、明确不符合冻结接口的问题

### 问题 1：报表接口字段读取错误

严重等级：P1  
责任归属：成员C前端实现问题  
位置：`frontend/src/views/admin/Statistics.vue`

现象：

```js
reports.value = Array.isArray(data) ? data : (data.reports || [])
```

冻结接口文档规定：

```http
GET /api/admin/reports?granularity=day|week|month
```

响应为：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "granularity": "day",
    "rows": []
  }
}
```

成员B后端实际也返回：

```python
return success_response({"granularity": granularity, "rows": report_rows})
```

问题判断：

- 成员B后端没有违反冻结接口。
- 成员C前端把 `rows` 错读成了 `reports`。
- 这会导致即使后端有报表数据，管理端报表页也显示“暂无数据”。

整改要求：

- 将读取逻辑改为优先读取 `data.rows`。
- 建议兼容旧字段时可以写成：

```js
reports.value = Array.isArray(data) ? data : (data.rows || data.reports || [])
```

验收标准：

- 日报、周报、月报三个 tab 均能显示后端真实返回数据。
- 有数据时表格和柱状图正常显示。
- 无数据时才显示“暂无数据”。

## 四、不是成员B违反冻结接口的问题

### 问题 2：用户历史账单列表缺失

严重等级：P2  
责任归属：冻结接口能力缺口，不是成员B违反冻结接口  
涉及页面：`/user/account`

现状：

成员C希望账户中心展示“当前用户自己的所有历史账单”。但冻结接口只定义了：

```http
GET /api/request/detail/{request_id}
```

该接口只能通过已知 `request_id` 查询单个详单。

冻结接口没有定义：

```http
GET /api/request/details
GET /api/auth/profile/bills
```

因此成员C现在采用本地兜底：

- 提交请求后把 `request_id` 存进浏览器 `localStorage`。
- 账户页读取本地记录过的 `request_id`。
- 再逐个调用 `GET /api/request/detail/{request_id}`。

问题判断：

- 不能判定成员B违反冻结接口，因为冻结接口没有要求提供“当前用户所有账单列表”接口。
- 成员C的兜底方案可以作为临时展示方案，但不能称为完整实现。

当前限制：

- 换浏览器后历史账单丢失。
- 清除缓存后历史账单丢失。
- 用户在其他设备提交的请求不会出现在当前浏览器。
- 未生成详单的请求不会展示。

整改建议：

- 若最终验收要求“完整历史账单”，应由组内追加后端接口：

```http
GET /api/request/details
```

或：

```http
GET /api/auth/profile/bills
```

- 成员C前端接入后，应以服务端返回的账单列表作为主数据源，本地 `request_id` 仅作为兼容兜底。

### 问题 3：当前活跃请求恢复能力缺失

严重等级：P2  
责任归属：冻结接口能力缺口，不是成员B违反冻结接口  
涉及页面：`/user/workspace`、`/user/task`

现状：

成员C当前依赖浏览器本地保存的：

```text
request_id
active_request_conflict
```

来恢复当前请求状态。

如果用户换浏览器、清缓存、退出后重新登录，前端可能只知道后端返回“当前用户已有活跃请求”，但不知道具体 `request_id`，无法调用：

```http
GET /api/request/status/{request_id}
```

冻结接口没有定义：

```http
GET /api/request/active
```

问题判断：

- 这不是成员B没有按冻结接口做。
- 这是冻结接口没有覆盖“按当前登录用户查询活跃请求”的能力。
- 成员C目前提示“本地缺少请求编号，需要管理员结束后重试”，只能算临时兜底，不是完整用户体验。

整改建议：

- 如果最终验收要求用户登录后自动恢复当前请求，应追加后端接口：

```http
GET /api/request/active
```

建议响应：

```json
{
  "code": 0,
  "data": {
    "request_id": "REQ0001",
    "queue_number": "F1",
    "request_status": "CHARGING",
    "charge_mode": "FAST",
    "request_energy": 30,
    "front_waiting_count": 0,
    "station_code": "FAST_01",
    "estimated_wait_seconds": 0,
    "estimated_finish_time": "2026-05-05T00:15:00"
  }
}
```

无活跃请求时返回：

```json
{
  "code": 0,
  "data": null
}
```

### 问题 4：支付状态是前端本地模拟

严重等级：P3  
责任归属：冻结接口未定义支付流程，不是成员B违反冻结接口  
涉及页面：`/user/bills`、`/user/account`

现状：

冻结接口将详单作为最终账单展示，没有正式定义支付接口。成员C前端新增了“立即支付”按钮，并用 `localStorage` 保存支付状态。

问题判断：

- 不能要求成员B提供冻结文档外的支付接口。
- 成员C如果保留支付按钮，必须明确这是演示状态，不应作为真实后端支付闭环。

风险：

- 换浏览器或清缓存后支付状态丢失。
- 管理端和报表无法获得真实支付状态。
- 无法避免重复支付或并发支付。

整改建议：

- 如果项目不要求真实支付，应在页面文案和文档中明确“详单即最终账单，不做真实支付状态”。
- 如果项目要求支付闭环，应新增后端接口，例如：

```http
POST /api/request/detail/{detail_id}/pay
GET /api/request/detail/{detail_id}/payment
```

## 五、文档和实现不一致的问题

### 问题 5：路由文档与真实路由不一致

严重等级：P3  
责任归属：成员C文档同步问题  
位置：`frontend/src/router/index.js`、`frontend/README.md`

真实路由：

| 路由 | 实际组件 |
|------|----------|
| `/user/account` | `Profile.vue` |
| `/user/bills` | `Account.vue` |

但成员C README 中仍写：

| 路由 | 组件 |
|------|------|
| `/user/account` | `Account.vue` |

问题影响：

- 审查、演示、答辩说明会误导使用者。
- 组内成员按 README 验收时，会找错页面。

整改要求：

- 更新 `frontend/README.md` 的项目结构和路由表。
- 明确区分：
  - `/user/account`：账户中心 / 个人资料 / 历史账单入口
  - `/user/bills`：当前或单个账单详情页

### 问题 6：前后端联调端口说明不一致

严重等级：P2  
责任归属：项目文档口径不统一，成员C需要同步前端说明  
位置：`frontend/vite.config.js`、`frontend/README.md`、`backend/README.md`

成员C前端配置：

```js
target: 'http://127.0.0.1:5000'
```

成员C前端 README 写：

```text
Vite 代理 /api 请求至 http://127.0.0.1:8080
```

后端 README 示例也大量使用：

```text
http://127.0.0.1:8080
```

但后端代码默认配置为：

```python
LISTEN_PORT = 5000
```

问题判断：

- 这不是严格意义上的冻结接口字段违规。
- 但会直接影响本地联调，必须统一。

整改建议：

二选一：

1. 如果后端实际运行端口采用默认 `5000`，则更新所有前后端 README 示例为 `5000`。
2. 如果组内约定后端统一跑 `8080`，则修改后端运行配置或环境变量说明，并把 `vite.config.js` 代理改为 `8080`。

验收标准：

- 按 README 启动后端和前端，无需额外猜端口即可完成登录、提交请求、管理端查询。

### 问题 7：前端文档对完成度表述过满

严重等级：P3  
责任归属：成员C文档表述问题  
位置：`frontend/冻结接口文档_前端实现版.md`、`frontend/README.md`

当前文档中有类似表述：

- “所有 Vue 页面均已对接真实 API”
- “用户端 + 管理端全部页面均已接入真实 API”
- “详单与账户（`GET /api/request/detail/{id}`）”

问题：

- 单个详单确实接了真实 API。
- 历史账单列表依赖 `localStorage` 保存的 `request_id`，不是完整真实 API 列表。
- 支付状态依赖 `localStorage`，不是真实 API。
- 活跃请求恢复依赖本地 `request_id`，跨浏览器不可恢复。

整改要求：

- 文档应改为更准确的表述：
  - “冻结接口范围内的大部分页面已接入真实 API”
  - “历史账单列表当前使用本地 `request_id` 兜底”
  - “支付状态当前为前端本地模拟”
  - “活跃请求恢复需要后端补充接口才能完整闭环”

## 六、页面与交互层面的具体问题

### 问题 8：当前请求页无法恢复服务端已有活跃请求

严重等级：P2  
涉及文件：`frontend/src/views/user/Task.vue`、`frontend/src/views/user/Workspace.vue`

现象：

- 如果本地没有 `request_id`，当前请求页只能显示“本地缺少请求编号”。
- 用户无法自行恢复真实活跃请求详情。

整改建议：

- 短期：保留提示，但文档中标为“受冻结接口限制的兜底方案”。
- 长期：等待或推动新增 `GET /api/request/active` 后接入。

### 问题 9：账单页只能展示当前浏览器记住的请求

严重等级：P2  
涉及文件：`frontend/src/views/user/Profile.vue`

现象：

- 页面通过 `localStorage.request_ids` 获取历史请求。
- 无法查询服务端完整历史账单。

整改建议：

- 短期：页面标题或提示中说明“当前浏览器已记录的请求”。
- 长期：接入后端账单列表接口后移除本地兜底作为主逻辑。

### 问题 10：账单详情和账户中心命名容易混淆

严重等级：P3  
涉及文件：`frontend/src/views/user/Account.vue`、`frontend/src/views/user/Profile.vue`、`frontend/src/router/index.js`

现象：

- `Account.vue` 实际是账单详情页。
- `Profile.vue` 实际是账户中心。
- README 又写 `Account.vue` 是“详单与账户”。

整改建议：

- 可考虑将文件命名调整为：
  - `Profile.vue` 或 `AccountCenter.vue`：账户中心
  - `Bills.vue` 或 `BillDetail.vue`：账单详情
- 如果不改文件名，至少在 README 中解释清楚。

## 七、对成员B责任的判定

### 1. 成员B没有明显违反冻结接口

已核对后端实现，成员B已经实现了冻结文档中前端本次主要依赖的接口：

- 登录注册接口
- 用户请求创建、查询、修改、取消、提前结束、详单查询
- 管理端系统配置
- 管理端桩列表和单桩队列
- 管理端桩启停、故障、恢复
- 管理端用户列表、详情、容量修改
- 管理端报表 `day / week / month`

其中报表接口返回 `rows`，与冻结文档一致。

### 2. 成员B缺失的是冻结接口之外的增强接口

以下接口不是冻结文档要求：

- 当前用户历史账单列表
- 当前用户活跃请求恢复
- 支付状态和支付确认
- 完整请求历史

如果项目最终展示需要这些能力，应作为“新增后端需求”处理，而不是认定成员B未按冻结接口完成。

### 3. 成员C应避免把增强需求写成已完成能力

成员C提出这些接口需求是合理的，但在交付文档中应明确：

- 哪些是冻结接口范围内已完成。
- 哪些是前端临时兜底。
- 哪些是需要后端后续补充。

## 八、整改清单

### A. 必须立即修改

- [ ] 修复 `frontend/src/views/admin/Statistics.vue` 报表字段读取：`data.reports` 改为 `data.rows`。
- [ ] 统一前端 README、后端 README、`vite.config.js` 的联调端口说明。
- [ ] 修正 `frontend/README.md` 中 `/user/account`、`/user/bills`、`Account.vue`、`Profile.vue` 的描述。
- [ ] 将“全部页面均已接入真实 API”等过满表述改成准确完成度说明。

### B. 需要组内确认后处理

- [ ] 是否需要新增当前用户历史账单列表接口。
- [ ] 是否需要新增当前用户活跃请求恢复接口。
- [ ] 是否保留支付按钮；如果保留，是否需要后端真实支付接口。
- [ ] 是否把 `/user/account` 和 `/user/bills` 的页面命名进一步统一。

### C. 建议补充验证

- [ ] 使用真实后端跑通用户登录、注册、提交请求。
- [ ] 验证 `WAITING_AREA` 状态下修改模式、修改电量、取消请求。
- [ ] 验证 `QUEUED` 和 `CHARGING` 状态下提前结束。
- [ ] 验证 `COMPLETED`、`COMPLETED_EARLY`、`FAULT_INTERRUPTED` 三类详单展示。
- [ ] 验证管理端桩列表和单桩队列。
- [ ] 验证管理端启停、故障、恢复操作。
- [ ] 验证用户管理列表、详情和修改电池容量。
- [ ] 验证报表 `day / week / month` 三个粒度。
- [ ] 验证退出登录后重新登录时当前请求是否能恢复；若不能，应记录为冻结接口限制。

## 九、最终审核结论

成员C不是完全没有按冻结文档工作。相反，他已经围绕冻结接口完成了大部分前端页面和调用逻辑，整体工作量较大，方向也基本正确。

但当前版本仍存在明确问题：

1. 报表字段接错，这是成员C前端实现问题，必须修。
2. 路由和端口文档不同步，这是成员C交付文档问题，必须修。
3. 历史账单、活跃请求恢复、支付状态只能算前端兜底，不是完整后端闭环。

因此，本次审核建议结论为：

> 成员C前端主体实现基本完成，但尚未达到“完全符合冻结文档并可直接最终验收”的状态。  
> 成员B后端未见明显违反冻结接口的问题；当前暴露出来的账单列表、活跃请求恢复、支付状态等缺口属于冻结接口未覆盖的增强需求，需要组内重新确认是否追加。
