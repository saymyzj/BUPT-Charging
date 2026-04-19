# 成员B Day 1：V3.0 差异总表

> 日期：2026-04-19
> 结论基线：以 `docs/` 当前冻结文档为准；如 `Markdown` 与 `openapi.yaml` 冲突，以 `Markdown` 为准。
> 适用范围：成员B负责的服务端、状态机、数据输出、批量模拟、部署支撑。

## 1. 当前状态判断

如果以当前 V3.0 文档为唯一标准，成员B当前状态应判断为：

- 后端工程骨架可复用
- V2 口径接口和服务大量仍在
- V3.0 正式接口组尚未收口
- V3.0 正式状态机、等候区/桩队列模型、详单计费、管理端和部署支撑均未完成

一句话判断：

当前仓库不是“V3 已完成待收尾”，而是“旧后端骨架可复用，但正式 V3 后端仍需系统性重写”。

## 2. 文档基线与冲突处理

本次 Day 1 核对使用以下文档作为正式依据：

- `docs/冻结接口文档.md`
- `docs/功能设计.md`
- `docs/系统验收接口与测试输入规范说明.md`
- `docs/故障与扩展场景指南.md`
- `docs/部署上线手册.md`
- `docs/openapi.yaml`

核对结论：

- `docs/冻结接口文档.md` 明确写的是 `POST /api/test/batch-simulate` 与 `GET /api/health`
- `docs/系统验收接口与测试输入规范说明.md`、`docs/功能设计.md`、`docs/部署上线手册.md` 也与上述路径一致
- `docs/openapi.yaml` 目前仍写成 `POST /api/batch/simulate` 与 `GET /health`

因此 Day 1 的正式口径应采用：

- `POST /api/test/batch-simulate`
- `GET /api/health`

并将 `docs/openapi.yaml` 的上述两处视为待同步修正项。

## 3. V3.0 正式接口清单

### 3.1 用户端与认证

| 模块 | 方法 | 路径 | 备注 |
|------|------|------|------|
| Auth | POST | `/api/auth/register` | 注册，必须包含 `battery_capacity` |
| Auth | POST | `/api/auth/login` | 登录 |
| UserRequest | POST | `/api/request/create` | 创建请求，返回 `queue_number` |
| UserRequest | GET | `/api/request/status/{request_id}` | 查询排队/桩位/预估时间 |
| UserRequest | PUT | `/api/request/mode` | 等候区修改模式 |
| UserRequest | PUT | `/api/request/energy` | 等候区修改电量 |
| UserRequest | POST | `/api/request/cancel` | 等候区取消 |
| UserRequest | POST | `/api/request/stop` | 充电区提前结束/取消 |
| UserRequest | GET | `/api/request/detail/{request_id}` | 查询详单 |

### 3.2 管理端

| 模块 | 方法 | 路径 | 备注 |
|------|------|------|------|
| Admin | GET | `/api/admin/system/config` | 查看系统配置 |
| Admin | PUT | `/api/admin/system/dispatch-mode` | 切换扩展调度模式 |
| Admin | PUT | `/api/admin/system/fault-dispatch-mode` | 切换故障策略 |
| Admin | GET | `/api/admin/stations` | 查看全部充电桩状态 |
| Admin | POST | `/api/admin/stations/{station_code}/start` | 启动充电桩 |
| Admin | POST | `/api/admin/stations/{station_code}/shutdown` | 关闭充电桩 |
| Admin | POST | `/api/admin/stations/{station_code}/fault` | 标记故障 |
| Admin | POST | `/api/admin/stations/{station_code}/recover` | 故障恢复 |
| Admin | GET | `/api/admin/stations/{station_code}/queue` | 查看单桩队列 |
| AdminUser | GET | `/api/admin/users` | 用户列表 |
| AdminUser | GET | `/api/admin/users/{user_id}` | 单用户信息 |
| AdminUser | PUT | `/api/admin/users/{user_id}/battery-capacity` | 修改电池容量 |
| Admin | GET | `/api/admin/reports?granularity=day|week|month` | 报表 |

### 3.3 验收与部署

| 模块 | 方法 | 路径 | 备注 |
|------|------|------|------|
| BatchSimulate | POST | `/api/test/batch-simulate` | 按 V3 验收输入结构执行批量模拟 |
| Health | GET | `/api/health` | 返回统一响应包络 |

## 4. 当前代码已有接口清单

基于当前蓝图注册与路由文件核对，仓库现有接口如下：

### 4.1 已存在且路径与 V3 部分重合

| 方法 | 当前路径 | 文件 | 现状判断 |
|------|------|------|------|
| POST | `/api/auth/register` | `backend/app/routes/auth.py` | 路径可复用，但字段不齐 |
| POST | `/api/auth/login` | `backend/app/routes/auth.py` | 路径可复用，但响应字段需收口 |
| POST | `/api/request/create` | `backend/app/routes/request.py` | 路径可复用，但响应与模型错误 |
| GET | `/api/request/status/{request_id}` | `backend/app/routes/request.py` | 路径可复用，但状态语义是旧版 |

### 4.2 已存在但属于旧口径、不可继续向前补

| 方法 | 当前路径 | 文件 | 旧口径问题 |
|------|------|------|------|
| GET | `/health` | `backend/app/routes/health.py` | 路径缺少 `/api`，且无统一包络 |
| GET | `/api/auth/profile` | `backend/app/routes/auth.py` | 依赖旧 `balance` 视角，非 Day 1 正式清单 |
| POST | `/api/request/cancel_queue` | `backend/app/routes/request.py` | 应改为 `/api/request/cancel` |
| POST | `/api/request/confirm_arrival` | `backend/app/routes/request.py` | V3 已废弃 |
| POST | `/api/request/interrupt_charge` | `backend/app/routes/request.py` | 应改为 `/api/request/stop` |
| POST | `/api/request/confirm_leave` | `backend/app/routes/request.py` | V3 已废弃 |
| GET | `/api/request/result/{request_id}` | `backend/app/routes/request.py` | 旧 `detail + bill` 组合结构 |
| POST | `/api/request/pay` | `backend/app/routes/request.py` | 模拟支付链路已废弃 |
| GET | `/api/stations/overview` | `backend/app/routes/stations.py` | 路径与字段均不对齐 V3 |
| POST | `/api/batch/simulate` | `backend/app/routes/batch_simulate.py` | 路径和输入结构均不对 |
| POST | `/api/admin/scenario` 等一组 | `backend/app/routes/admin.py` | 旧场景配置中心模型 |
| GET | `/api/admin/waiting-pools/status` | `backend/app/routes/admin.py` | 旧等待池模型 |
| GET | `/api/admin/waiting-pools/statistics` | `backend/app/routes/admin.py` | 旧等待池模型 |
| GET | `/api/admin/system/status` | `backend/app/routes/admin.py` | 输出围绕旧场景配置 |

### 4.3 当前代码完全缺失的 V3 接口

| 方法 | 目标路径 |
|------|------|
| PUT | `/api/request/mode` |
| PUT | `/api/request/energy` |
| POST | `/api/request/cancel` |
| POST | `/api/request/stop` |
| GET | `/api/request/detail/{request_id}` |
| GET | `/api/admin/system/config` |
| PUT | `/api/admin/system/dispatch-mode` |
| PUT | `/api/admin/system/fault-dispatch-mode` |
| GET | `/api/admin/stations` |
| POST | `/api/admin/stations/{station_code}/start` |
| POST | `/api/admin/stations/{station_code}/shutdown` |
| POST | `/api/admin/stations/{station_code}/fault` |
| POST | `/api/admin/stations/{station_code}/recover` |
| GET | `/api/admin/stations/{station_code}/queue` |
| GET | `/api/admin/users` |
| GET | `/api/admin/users/{user_id}` |
| PUT | `/api/admin/users/{user_id}/battery-capacity` |
| GET | `/api/admin/reports` |
| POST | `/api/test/batch-simulate` |
| GET | `/api/health` |

## 5. 接口差异矩阵

### 5.1 可复用但必须重写实现细节的接口

| V3 接口 | 当前代码 | 处理动作 | 原因 |
|------|------|------|------|
| `/api/auth/register` | 已有同路径 | 复用路径，重写字段 | 需补 `battery_capacity`、`created_at`，去掉旧余额依赖 |
| `/api/auth/login` | 已有同路径 | 复用路径，重写响应 | 字段需对齐冻结文档 |
| `/api/request/create` | 已有同路径 | 复用路径，重写逻辑 | 当前仍写入旧 `WAITING` 和等待池模型 |
| `/api/request/status/{request_id}` | 已有同路径 | 复用路径，重写输出 | 当前仍暴露 `CALLED/CONFIRMED` 语义 |

### 5.2 需要“旧接口下线，新接口重建”的接口

| 当前接口 | 目标接口 | 处理动作 | 说明 |
|------|------|------|------|
| `/api/request/cancel_queue` | `/api/request/cancel` | 删除旧接口，重建新接口 | 终态与校验规则已变化 |
| `/api/request/interrupt_charge` | `/api/request/stop` | 删除旧接口，重建新接口 | V3 合并“充电区取消/提前结束” |
| `/api/request/result/{request_id}` | `/api/request/detail/{request_id}` | 删除旧接口，重建新接口 | 旧结构是 `detail + bill`，V3 只保留详单费用切片 |
| `/api/batch/simulate` | `/api/test/batch-simulate` | 删除旧接口，重建新接口 | 路径、输入结构、事件语义都变了 |
| `/health` | `/api/health` | 删除旧接口，重建新接口 | 路径和响应包络都不符合 V3 |
| `/api/stations/overview` | `/api/admin/stations` | 删除旧接口，重建新接口 | 应收口到管理端接口组 |

### 5.3 需要直接新增的 V3 接口

| 接口组 | 新增接口 |
|------|------|
| UserRequest | `/api/request/mode`、`/api/request/energy` |
| Admin System | `/api/admin/system/config`、`/api/admin/system/dispatch-mode`、`/api/admin/system/fault-dispatch-mode` |
| Admin Station | `/api/admin/stations/{station_code}/start`、`/shutdown`、`/fault`、`/recover`、`/queue` |
| Admin User | `/api/admin/users`、`/api/admin/users/{user_id}`、`/api/admin/users/{user_id}/battery-capacity` |
| Admin Report | `/api/admin/reports` |

### 5.4 必须彻底删除、不能继续补丁式扩展的接口

| 接口 | 原因 |
|------|------|
| `/api/request/confirm_arrival` | `CALLED/CONFIRMED` 已不属于 V3 正式状态机 |
| `/api/request/confirm_leave` | `WAITING_TO_LEAVE` 已不属于 V3 正式状态机 |
| `/api/request/pay` | 模拟支付/虚拟余额已废弃 |
| `/api/admin/scenario*` 全组 | “场景配置中心”不是 V3 正式管理口径 |
| `/api/admin/waiting-pools/*` | V3 没有中央等待池/快慢池暴露口径 |
| `/api/admin/system/status` | 输出建立在旧场景摘要与等待池之上 |

## 6. 模型与实现差异清单

### 6.1 状态枚举差异

当前 `backend/app/enums.py` 仍包含以下旧状态或旧语义：

- 请求状态：`PENDING`、`WAITING`、`CALLED`、`CONFIRMED`、`INTERRUPTED`、`NO_SHOW`、`FAULT_REQUEUE`
- 桩状态：`IDLE`、`RESERVED`、`CHARGING`、`WAITING_TO_LEAVE`
- 等待池类型：`FAST_POOL`、`SLOW_POOL`
- 队列模式：`UNIFORM_CAPACITY`、`STATION_SNAPSHOT`
- 支付状态：`UNPAID`、`PAID`、`FAILED`

V3 正式应切换为：

- 请求状态：`WAITING_AREA`、`QUEUED`、`CHARGING`、`COMPLETED`、`COMPLETED_EARLY`、`CANCELLED`、`FAULT_INTERRUPTED`
- 桩状态：`RUNNING`、`SHUTDOWN`、`FAULT`
- 调度模式：`NORMAL`、`EXT_SINGLE_BATCH`、`EXT_FULL_BATCH`
- 故障策略：`PRIORITY`、`TIME_ORDER`

### 6.2 核心业务模型差异

| 维度 | 当前代码 | V3 正式口径 |
|------|------|------|
| 等待模型 | 中央等待池 + `FAST_POOL/SLOW_POOL` | 等候区 + 每桩固定长度队列 |
| 顺序依据 | 池内顺序 + 叫号/确认到场 | `F/T` 排队号是唯一顺序依据 |
| 调度时机 | 围绕 `CALLED/CONFIRMED` | 围绕等候区取头车、桩队列空位补位 |
| 中断语义 | `INTERRUPTED`、`WAITING_TO_LEAVE` | `COMPLETED_EARLY` / `FAULT_INTERRUPTED` |
| 计费模型 | `energy_fee + time_fee + occupancy_fee` | `charge_fee + service_fee + total_fee` |
| 支付模型 | `payment_status`、`balance` | 无模拟支付、无虚拟余额 |
| 场景参数 | `station_queue_mode`、`station_snapshots` | `charging_queue_len`、`dispatch_mode`、`fault_dispatch_mode` |
| 管理端视角 | 场景配置中心 | 只读系统配置 + 运行态控制 + 报表/用户维护 |

## 7. 保留 / 删除 / 重写 / 复用矩阵

| 对象 | 动作 | 优先级 | 说明 |
|------|------|------|------|
| `backend/app/__init__.py` | 复用 | P0 | 保留 Flask 工厂与蓝图注册方式，但要改正确路径前缀 |
| `backend/app/routes/auth.py` | 重写后复用 | P0 | 保留认证入口，字段收口到 V3 |
| `backend/app/routes/request.py` | 重写 | P0 | 当前核心是旧请求状态机，不能增量修补 |
| `backend/app/routes/admin.py` | 重写 | P0 | 当前管理端是旧场景配置模型 |
| `backend/app/routes/stations.py` | 删除并并入 `admin` | P1 | 路由分组不再符合 V3 |
| `backend/app/routes/batch_simulate.py` | 重写 | P1 | 路径、输入、输出、事件语义全变 |
| `backend/app/routes/health.py` | 重写 | P1 | 路径和响应结构都要调整 |
| `backend/app/enums.py` | 重写 | P0 | 状态枚举是 Day 2 的冻结基础 |
| `backend/app/services/waiting_pool.py` | 停止开发，后续删除 | P0 | 旧中央等待池核心模块 |
| `backend/app/services/scheduler_engine.py` | 重写 | P0 | 旧调度主线围绕叫号/确认/过号 |
| `backend/app/services/billing_service.py` | 重写 | P0 | 仍以旧账单和支付链路为核心 |
| `backend/app/services/contract_builders.py` | 重写 | P1 | 当前输出字段对应旧状态和旧账单 |
| `backend/app/services/config_manager.py` | 部分复用，部分重写 | P1 | 可保留配置加载思路，但字段模型需切换到 V3 |
| `backend/app/services/scenario_adapter.py` | 停止开发，后续删除 | P1 | 围绕 `UNIFORM_CAPACITY/STATION_SNAPSHOT` |
| `backend/app/services/scenario_parser.py` | 停止开发，后续删除 | P1 | 批量模拟输入已换成 V3 结构 |
| `backend/app/services/user_behavior_parser.py` | 重写或下沉到测试层 | P2 | 旧 `confirm_arrival/no_show` 事件语义已过期 |
| `backend/app/utils/auth.py`、`db.py`、`response.py` | 复用 | P0 | 基础工程能力可继续用 |

## 8. 必须停止继续开发的旧模块

以下模块或逻辑不应再继续补功能，只能用于 Day 1 识别历史包袱：

### 8.1 明确停开

- `backend/app/services/waiting_pool.py`
- `backend/app/services/scheduler_engine.py` 中围绕中央等待池、`CALLED`、`CONFIRMED`、`NO_SHOW`、`FAULT_REQUEUE` 的主链逻辑
- `backend/app/services/billing_service.py` 中旧支付、旧账单链路
- `backend/app/services/contract_builders.py` 中旧 `summary/detail/bill` 输出结构
- `backend/app/routes/admin.py` 中 `/scenario*`、`/waiting-pools/*`、`/system/status`
- `backend/app/routes/request.py` 中 `/confirm_arrival`、`/confirm_leave`、`/pay`

### 8.2 停开原因

- 它们建立在 V2 的中央等待池模型上
- 它们依赖已废弃状态枚举
- 它们输出的是已废弃字段
- 继续在这些文件上补逻辑，会把错误模型继续固化进 V3

## 9. 成员B重构任务矩阵

| 任务域 | Day 1 结论 | 下一动作 | 优先级 |
|------|------|------|------|
| 接口冻结对齐 | 已明确 24 个正式接口 | Day 2 先修正接口枚举与数据模型 | P0 |
| 请求状态机 | 当前完全不符合 V3 | 冻结 7 个正式请求状态 | P0 |
| 桩状态机 | 当前仍是 `IDLE/RESERVED/WAITING_TO_LEAVE` | 切换为 `RUNNING/SHUTDOWN/FAULT` | P0 |
| 等候区/桩队列 | 当前仍是等待池 | 建立等候区顺序与每桩固定队列字段 | P0 |
| 计费与详单 | 当前仍是旧账单模型 | 切到 `charge_fee/service_fee/total_fee` | P0 |
| 管理端接口 | 当前基本不可复用 | 先收口 system/stations 基础查看接口 | P1 |
| 故障/扩展调度 | 当前语义错位 | Day 2 先冻结模式边界，再到 Day 9/11 实现 | P1 |
| 批量模拟 | 当前接口和输入结构错误 | 按验收文档重做 | P1 |
| 部署支撑 | 当前健康检查路径不对 | 对齐 `/api/health` 和部署配置项 | P1 |

## 10. Day 1 产出结论

Day 1 已明确两件事：

1. 当前仓库主干仍是 V2 口径，不能再把旧接口和旧状态机视为有效进度。
2. 后续开发应以“重写核心业务模型”为主，而不是在旧等待池、旧账单、旧场景配置模型上继续修补。

## 11. Day 2 最优先动作

建议下一步直接进入 Day 2，并按以下顺序推进：

1. 冻结 `RequestStatus`、`StationStatus`、`DispatchMode`、`FaultDispatchMode`
2. 冻结数据库字段：`queue_number`、`waiting_area_order`、`station_queue_position`、`charging_queue_len`
3. 明确 `detail` 与 `reports` 的字段落库方式
4. 修正文档附件 `docs/openapi.yaml` 中 `health` 与 `batch-simulate` 的路径冲突

## 12. 可执行检查清单

- [x] 已列出 V3.0 正式接口清单
- [x] 已列出当前代码已有接口清单
- [x] 已完成“保留 / 删除 / 重写 / 复用”矩阵
- [x] 已列出必须停止继续开发的旧模块
- [x] 已识别文档内部路径冲突并给出取舍规则
- [ ] Day 2：冻结新状态机与数据库迁移清单
- [ ] Day 3：打通认证与创建请求最小闭环
