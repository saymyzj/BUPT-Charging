# 成员C页面设计清单

> 版本：V3.0  
> 负责人：成员C  
> 适用范围：前端页面设计、管理端设计、交互联调、回归测试、展示说明  
> 文档依据：`docs/小组分工指南.md`、`docs/功能设计.md`、`docs/冻结接口文档.md`、`docs/增量设计.md`、`docs/系统验收接口与测试输入规范说明.md`、`docs/部署上线手册.md`

## 1. 设计目标

成员C当前任务不是继续沿用旧页面逻辑，而是把 V3.0 冻结文档中的用户端、管理端、报表、回归和展示要求落到前端。

本设计清单用于回答四个问题：

1. 前端需要有哪些页面。
2. 每个页面展示哪些字段。
3. 每个页面有哪些操作。
4. 每个操作对应哪个正式接口。

正式实现必须遵守：

- 页面、代码、接口字段、验收输入统一使用 V3.0 文档口径。
- 不再把旧“中央等待池”“确认到场”“确认离场”“支付”作为正式主线。
- 不再调用旧接口作为正式实现。
- 页面必须能支撑用户端输出、管理端输出、报表输出和最终展示回归。

## 2. 成员C职责范围

### 2.1 主责内容

- 用户端页面
- 管理端页面
- 图表与报表展示
- 错误提示与交互反馈
- 前后端联调回归
- 演示流程与展示说明
- 前端构建与 Nginx 静态部署配合

### 2.2 配合内容

- 配合组长A确认页面展示口径、状态文案、答辩展示重点。
- 配合成员B确认接口字段、统一响应结构、错误码和示例数据。
- 配合全组完成增量一、增量二、增量三和正式上线前回归。

### 2.3 不主导内容

- 后端接口实现
- 调度算法实现
- 数据库 schema
- 计费逻辑实现
- Flask / systemd 后端服务部署

## 3. 页面与路由总览

优先复用当前前端已有路由。

| 模块 | 页面 | 当前/建议路由 | 对应功能 | 优先级 |
|------|------|---------------|----------|--------|
| 通用 | 登录 / 注册 | `/login` | F-U01 | P0 |
| 用户端 | 工作台 | `/user/workspace` | F-U02、F-U03 | P0 |
| 用户端 | 当前请求 | `/user/task` | F-U03、F-U04、F-U05、F-U06、F-U07 | P0 |
| 用户端 | 详单 / 账户 | `/user/account` | F-U08 | P0 |
| 管理端 | 总览 | `/admin/overview` | F-A02、F-A03 | P0 |
| 管理端 | 系统配置 | `/admin/config` | F-J01、F-A04、F-A05 | P0 |
| 管理端 | 故障与设备控制 | `/admin/records` 或 `/admin/faults` | F-A01、F-A06 | P0 |
| 管理端 | 用户与车辆管理 | `/admin/users` | F-A07 | P0 |
| 管理端 | 报表统计 | `/admin/statistics` | F-A08 | P0 |

## 4. 用户端页面设计

### 4.1 登录 / 注册页

- 功能编号：F-U01
- 路由：`/login`
- 页面目标：完成真实注册、登录，并根据角色进入对应端。

展示字段：

- 用户名 `username`
- 密码 `password`
- 注册时车辆电池容量 `battery_capacity`
- 登录 / 注册切换入口

页面操作：

- 登录
- 注册
- 登录与注册模式切换

接口：

- `POST /api/auth/login`
- `POST /api/auth/register`

成功结果：

- 保存 `token`
- 保存 `user_id`
- 保存 `role`
- `USER` 跳转 `/user/workspace`
- `ADMIN` 跳转 `/admin/overview`

错误提示：

- 用户名为空
- 密码为空
- 注册时电池容量为空或非法
- 后端返回非 `code=0` 时展示 `message`

### 4.2 用户工作台

- 功能编号：F-U02、F-U03
- 路由：`/user/workspace`
- 页面目标：提交充电请求，并展示创建后的排队结果。

展示字段：

- 充电模式 `charge_mode`：`FAST` / `SLOW`
- 请求电量 `request_energy`
- 请求时间 `request_time`
- 请求编号 `request_id`
- 排队号 `queue_number`
- 请求状态 `request_status`
- 前车数量 `front_waiting_count`

页面操作：

- 选择快充 / 慢充
- 输入请求电量
- 提交充电请求
- 跳转当前请求页

接口：

- `POST /api/request/create`
- `GET /api/request/status/{request_id}`

交互规则：

- `request_energy` 必须大于 0。
- 超出后端允许范围时提示错误码 `1008`。
- 创建成功后展示排队号，并记录当前 `request_id`。

错误提示：

- `1004`：等候区容量已满
- `1005`：当前模式无可用充电桩
- `1008`：请求电量不合法
- `1099`：服务器内部错误

### 4.3 当前请求页

- 功能编号：F-U03、F-U04、F-U05、F-U06、F-U07
- 路由：`/user/task`
- 页面目标：展示当前请求状态，并提供修改、取消和提前结束操作。

展示字段：

- 请求编号 `request_id`
- 排队号 `queue_number`
- 充电模式 `charge_mode`
- 请求电量 `request_energy`
- 请求状态 `request_status`
- 前车数量 `front_waiting_count`
- 充电桩编号 `station_code`
- 桩队列位置 `station_queue_position`
- 预计等待秒数 `estimated_wait_seconds`
- 预计开始时间 `estimated_start_time`
- 预计完成时间 `estimated_finish_time`

页面操作：

- 刷新状态
- 修改充电模式
- 修改请求电量
- 等候区取消
- 充电区取消 / 提前结束
- 查看详单

接口：

- `GET /api/request/status/{request_id}`
- `PUT /api/request/mode`
- `PUT /api/request/energy`
- `POST /api/request/cancel`
- `POST /api/request/stop`
- `GET /api/request/detail/{request_id}`

按钮可用规则：

| 当前状态 | 可用操作 | 禁用操作 |
|----------|----------|----------|
| `WAITING_AREA` | 修改模式、修改电量、取消请求 | 提前结束、查看详单 |
| `QUEUED` | 充电区取消 / 提前结束 | 修改模式、修改电量、等候区取消 |
| `CHARGING` | 充电区取消 / 提前结束 | 修改模式、修改电量、等候区取消 |
| `COMPLETED` | 查看详单 | 所有请求修改类操作 |
| `COMPLETED_EARLY` | 查看详单 | 所有请求修改类操作 |
| `CANCELLED` | 无 | 查看详单、所有请求修改类操作 |
| `FAULT_INTERRUPTED` | 查看详单 | 所有请求修改类操作 |

关键文案：

- `WAITING_AREA`：等候区等待
- `QUEUED`：已进入充电桩队列
- `CHARGING`：正在充电
- `COMPLETED`：正常完成
- `COMPLETED_EARLY`：提前结束完成
- `CANCELLED`：已取消
- `FAULT_INTERRUPTED`：故障中断

### 4.4 详单 / 账户页

- 功能编号：F-U08
- 路由：`/user/account`
- 页面目标：展示详单、账单费用和车辆基础信息。

详单字段：

- 详单编号 `detail_id`
- 详单生成时间 `detail_generated_at`
- 充电桩编号 `station_code`
- 实际充电量 `actual_energy`
- 充电时长 `charge_duration_seconds`
- 开始时间 `start_time`
- 停止时间 `stop_time`
- 充电费 `charge_fee`
- 服务费 `service_fee`
- 总费用 `total_fee`
- 请求终态 `request_status`

接口：

- `GET /api/request/detail/{request_id}`

展示规则：

- `COMPLETED` 有详单。
- `COMPLETED_EARLY` 有详单。
- `FAULT_INTERRUPTED` 有详单。
- `CANCELLED` 不生成详单。
- 本系统不单独实现支付页面，账单费用直接来自详单字段。

## 5. 管理端页面设计

### 5.1 管理总览页

- 功能编号：F-A02、F-A03
- 路由：`/admin/overview`
- 页面目标：展示全部充电桩运行状态，并能查看单桩队列。

充电桩状态字段：

- 充电桩编号 `station_code`
- 充电模式 `charge_mode`
- 桩状态 `station_status`
- 当前服务请求 `current_request_id`
- 队列长度 `queue_length`
- 累计充电次数 `total_charge_count`
- 累计充电时长 `total_charge_seconds`
- 累计充电电量 `total_charge_energy`

单桩队列字段：

- 用户 ID `user_id`
- 电池容量 `battery_capacity`
- 请求电量 `request_energy`
- 排队号 `queue_number`
- 排队时长 `queue_wait_seconds`

页面操作：

- 刷新全部桩状态
- 查看单桩队列详情

接口：

- `GET /api/admin/stations`
- `GET /api/admin/stations/{station_code}/queue`

注意：

- 正式页面不要使用 `/api/stations/overview`。
- 即使后端保留兼容接口，验收主线也必须使用 `/api/admin/stations`。

### 5.2 系统配置与调度页

- 功能编号：F-J01、F-A04、F-A05
- 路由：`/admin/config`
- 页面目标：查看系统配置，切换调度模式和故障策略。

只读配置字段：

- 快充桩数量 `fast_station_count`
- 慢充桩数量 `slow_station_count`
- 等候区容量 `waiting_area_capacity`
- 每桩队列长度 `charging_queue_len`
- 当前调度模式 `dispatch_mode`
- 当前故障策略 `fault_dispatch_mode`

页面操作：

- 切换调度模式
- 切换故障策略
- 刷新配置

接口：

- `GET /api/admin/system/config`
- `PUT /api/admin/system/dispatch-mode`
- `PUT /api/admin/system/fault-dispatch-mode`

调度模式：

- `NORMAL`
- `EXT_SINGLE_BATCH`
- `EXT_FULL_BATCH`

故障策略：

- `PRIORITY`
- `TIME_ORDER`

交互规则：

- 系统基础参数只读，运行时不可修改。
- 运行时只允许切换 `dispatch_mode` 和 `fault_dispatch_mode`。
- 切换成功后刷新配置展示。

### 5.3 故障与设备控制页

- 功能编号：F-A01、F-A06
- 路由：`/admin/records` 或新增 `/admin/faults`
- 页面目标：提供充电桩启动、关闭、故障标记、故障恢复操作。

展示字段：

- 充电桩编号 `station_code`
- 充电模式 `charge_mode`
- 桩状态 `station_status`
- 当前服务请求 `current_request_id`
- 队列长度 `queue_length`
- 当前故障策略 `fault_dispatch_mode`

页面操作：

- 启动充电桩
- 关闭充电桩
- 标记故障
- 恢复故障
- 查看故障后队列变化

接口：

- `POST /api/admin/stations/{station_code}/start`
- `POST /api/admin/stations/{station_code}/shutdown`
- `POST /api/admin/stations/{station_code}/fault`
- `POST /api/admin/stations/{station_code}/recover`
- `GET /api/admin/stations`
- `GET /api/admin/stations/{station_code}/queue`

按钮可用规则：

| 桩状态 | 条件 | 可用操作 |
|--------|------|----------|
| `SHUTDOWN` | 任意 | 启动 |
| `RUNNING` | 空闲且队列为空 | 关闭、标记故障 |
| `RUNNING` | 有服务车辆或队列不为空 | 标记故障 |
| `FAULT` | 任意 | 恢复 |

错误提示：

- `1007`：充电桩未处于可关闭状态。

### 5.4 用户与车辆管理页

- 功能编号：F-A07
- 路由：`/admin/users`
- 页面目标：展示用户列表、用户详情、历史详单，并维护车辆电池容量。

用户列表字段：

- 用户 ID `user_id`
- 用户名 `username`
- 电池容量 `battery_capacity`
- 角色 `role`
- 创建时间 `created_at`
- 是否有活跃请求 `has_active_request`

用户详情字段：

- 用户基本信息
- 历史详单摘要 `historical_details`

页面操作：

- 查看用户列表
- 查看用户详情
- 修改车辆电池容量

接口：

- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `PUT /api/admin/users/{user_id}/battery-capacity`

交互规则：

- `has_active_request=true` 时禁用修改电池容量。
- 仅当用户无 `WAITING_AREA / QUEUED / CHARGING` 请求时允许修改。

错误提示：

- `1010`：用户有活跃请求，不可修改车辆电池容量。

### 5.5 报表统计页

- 功能编号：F-A08
- 路由：`/admin/statistics`
- 页面目标：按日、周、月展示充电桩报表，并提供图表展示。

筛选项：

- 日报 `day`
- 周报 `week`
- 月报 `month`

报表字段：

- 时间粒度键 `time_key`
- 充电桩编号 `station_code`
- 总充电次数 `total_charge_count`
- 总充电时长 `total_charge_seconds`
- 总充电电量 `total_charge_energy`
- 总充电费 `total_charge_fee`
- 总服务费 `total_service_fee`
- 总费用 `total_fee`

页面操作：

- 切换报表粒度
- 刷新报表
- 查看图表

接口：

- `GET /api/admin/reports?granularity=day|week|month`

图表建议：

- 各桩总电量柱状图
- 各桩总费用柱状图
- 各桩充电次数对比图

## 6. 增量任务拆分

### 6.1 增量一：严格主流程闭环

用户端：

- [ ] 注册与登录页
- [ ] 提交充电请求
- [ ] 展示排队号
- [ ] 展示前车数量
- [ ] 展示当前请求状态
- [ ] 展示预计等待、开始、完成时间
- [ ] 详单页面

管理端：

- [ ] 充电桩状态页面
- [ ] 单桩队列详情
- [ ] 系统配置只读展示

验收目标：

- 普通模式主流程可以从页面完整回放。
- 页面不再依赖中央等待池口径。

### 6.2 增量二：特殊场景与故障闭环

用户端：

- [ ] 修改充电模式
- [ ] 修改请求电量
- [ ] 等候区取消
- [ ] 充电区取消 / 提前结束

管理端：

- [ ] 启动充电桩
- [ ] 关闭充电桩
- [ ] 切换故障策略
- [ ] 标记故障
- [ ] 恢复故障
- [ ] 展示故障后的桩状态和队列变化

验收目标：

- `CANCELLED` 和 `COMPLETED_EARLY` 终态展示正确。
- 故障中断详单 `FAULT_INTERRUPTED` 展示正确。

### 6.3 增量三：扩展调度、报表与上线收口

管理端：

- [ ] 切换 `NORMAL`
- [ ] 切换 `EXT_SINGLE_BATCH`
- [ ] 切换 `EXT_FULL_BATCH`
- [ ] 用户与车辆信息维护
- [ ] 报表统计页
- [ ] 图表展示

部署与展示：

- [ ] 前端构建生成 `dist/`
- [ ] 前端请求统一使用同源 `/api`
- [ ] 配合 Nginx 静态托管
- [ ] 输出展示环境与操作说明
- [ ] 完成至少一次公网环境回归

验收目标：

- 扩展模式可切换、可说明、可展示。
- 报表字段完整。
- 前端上线访问正常。

## 7. 正式接口清单

### 7.1 用户端接口

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/request/create`
- `GET /api/request/status/{request_id}`
- `PUT /api/request/mode`
- `PUT /api/request/energy`
- `POST /api/request/cancel`
- `POST /api/request/stop`
- `GET /api/request/detail/{request_id}`

### 7.2 管理端接口

- `GET /api/admin/system/config`
- `PUT /api/admin/system/dispatch-mode`
- `PUT /api/admin/system/fault-dispatch-mode`
- `GET /api/admin/stations`
- `GET /api/admin/stations/{station_code}/queue`
- `POST /api/admin/stations/{station_code}/start`
- `POST /api/admin/stations/{station_code}/shutdown`
- `POST /api/admin/stations/{station_code}/fault`
- `POST /api/admin/stations/{station_code}/recover`
- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `PUT /api/admin/users/{user_id}/battery-capacity`
- `GET /api/admin/reports?granularity=day|week|month`

### 7.3 验收与健康检查接口

- `GET /api/health`
- `POST /api/test/batch-simulate`

说明：`openapi.yaml` 中出现过 `/api/batch/simulate`，但 `冻结接口文档.md` 与场景指南以 `/api/test/batch-simulate` 为准。冲突时按 Markdown 冻结文档执行。

## 8. 禁止继续使用的旧接口

以下接口不能作为 V3 正式页面主线：

- `POST /api/request/cancel_queue`
- `POST /api/request/confirm_arrival`
- `POST /api/request/interrupt_charge`
- `POST /api/request/confirm_leave`
- `GET /api/request/result/{request_id}`
- `POST /api/request/pay`
- `GET /api/stations/overview`

旧页面里如果仍然调用这些接口，需要替换为第 7 节正式接口。

## 9. 状态与文案字典

### 9.1 请求状态

| 状态 | 页面文案 | 页面含义 |
|------|----------|----------|
| `WAITING_AREA` | 等候区等待 | 已提交请求，尚未进入桩队列 |
| `QUEUED` | 桩队列等待 | 已进入某个充电桩队列 |
| `CHARGING` | 正在充电 | 当前车辆正在充电 |
| `COMPLETED` | 正常完成 | 已按请求电量完成 |
| `COMPLETED_EARLY` | 提前结束完成 | 用户提前结束或充电区取消后结算 |
| `CANCELLED` | 已取消 | 等候区取消，不生成详单 |
| `FAULT_INTERRUPTED` | 故障中断 | 因充电桩故障中断并生成详单 |

### 9.2 充电桩状态

| 状态 | 页面文案 |
|------|----------|
| `RUNNING` | 运行中 |
| `SHUTDOWN` | 已关闭 |
| `FAULT` | 故障 |

### 9.3 充电模式

| 状态 | 页面文案 |
|------|----------|
| `FAST` | 快充 |
| `SLOW` | 慢充 |

### 9.4 调度模式

| 状态 | 页面文案 |
|------|----------|
| `NORMAL` | 普通调度 |
| `EXT_SINGLE_BATCH` | 单次联合调度 |
| `EXT_FULL_BATCH` | 批量调度 |

### 9.5 故障策略

| 状态 | 页面文案 |
|------|----------|
| `PRIORITY` | 故障队列优先 |
| `TIME_ORDER` | 时间顺序重排 |

## 10. 回归检查清单

### 10.1 用户端回归

- [ ] 注册成功。
- [ ] 登录成功。
- [ ] 登录后按角色跳转。
- [ ] 创建快充请求成功，返回 `F` 排队号。
- [ ] 创建慢充请求成功，返回 `T` 排队号。
- [ ] 当前请求页展示 `queue_number`。
- [ ] 当前请求页展示 `front_waiting_count`。
- [ ] 当前请求页展示 `request_status`。
- [ ] 当前请求页展示 `station_code`。
- [ ] 当前请求页展示预计等待、开始、完成时间。
- [ ] 等候区可修改模式。
- [ ] 等候区可修改电量。
- [ ] 等候区可取消，状态为 `CANCELLED`。
- [ ] 队列中或充电中可提前结束，状态为 `COMPLETED_EARLY`。
- [ ] 正常完成可查看详单。
- [ ] 提前结束可查看详单。
- [ ] 故障中断可查看详单。
- [ ] 取消请求不展示详单。

### 10.2 管理端回归

- [ ] 管理端总览能加载全部充电桩。
- [ ] 管理端能查看单桩队列。
- [ ] 系统配置页能显示参数。
- [ ] 调度模式可切换。
- [ ] 故障策略可切换。
- [ ] 可启动关闭的充电桩。
- [ ] 有车或有队列时关闭失败并提示。
- [ ] 可标记故障。
- [ ] 可恢复故障。
- [ ] 用户列表能加载。
- [ ] 用户详情能加载。
- [ ] 无活跃请求时可修改电池容量。
- [ ] 有活跃请求时禁止修改电池容量。
- [ ] 报表页能按日、周、月切换。
- [ ] 报表字段完整。
- [ ] 图表能展示报表数据。

### 10.3 部署展示回归

- [ ] `npm run build` 成功。
- [ ] 生成 `dist/`。
- [ ] 前端静态资源可由 Nginx 加载。
- [ ] 浏览器访问前端首页正常。
- [ ] 直接访问子路由能回退到 `index.html`。
- [ ] `/api/health` 返回 `code=0`。
- [ ] `/api` 请求通过同域反代访问后端。

## 11. 最终报告中成员C负责内容

成员C需要准备以下报告材料：

- 前端架构设计
- 页面设计与交互设计
- 用户端页面说明
- 管理端展示说明
- 图表与可视化说明
- 回归测试说明
- 展示流程说明
- 测试结果与展示总结

## 12. 建议实施顺序

1. 对照本文档确认页面和路由。
2. 清理旧接口封装。
3. 接入登录 / 注册真实接口。
4. 完成用户端增量一主流程。
5. 完成管理端桩状态和队列查看。
6. 完成用户端修改、取消、提前结束。
7. 完成管理端设备控制和故障控制。
8. 完成调度模式、故障策略、用户车辆维护。
9. 完成报表统计和图表。
10. 完成前端构建、部署配合和全流程回归。

