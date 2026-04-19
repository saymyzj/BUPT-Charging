# 成员B Day 2：状态机与数据模型冻结方案

> 日期：2026-04-19
> 结论基线：以 `docs/功能设计.md`、`docs/冻结接口文档.md`、`docs/调度模块输入输出约定.md`、`docs/系统验收接口与测试输入规范说明.md`、`docs/故障与扩展场景指南.md` 为准。
> 目标：冻结成员B负责范围内的 V3.0 状态机落地方案、目标数据模型、数据库迁移清单。

## 1. 当前状态判断

如果以 V3.0 文档为标准，当前数据库和状态模型仍是 V2 口径：

- `charge_request` 仍围绕 `PENDING / WAITING / CALLED / CONFIRMED / NO_SHOW / FAULT_REQUEUE`
- `charging_station` 仍围绕 `IDLE / RESERVED / WAITING_TO_LEAVE`
- `system_scenario_config` 仍使用 `UNIFORM_CAPACITY / STATION_SNAPSHOT`
- `billing_record` 仍以 `energy_fee / time_fee / occupancy_fee / payment_status` 为核心
- `user` 表仍无 `battery_capacity`，却保留了已废弃的 `balance`

因此 Day 2 的正式结论是：

- V3 需要重建状态枚举
- V3 需要重建核心表结构
- V2 业务数据不做“无损升级”假设

## 2. 冻结原则

### 2.1 状态机冻结原则

1. 公开可见状态只允许使用 V3 正式枚举
2. 调度内部允许存在“故障重排集合”“批量调度集合”等临时上下文，但这些不是公开状态，不写成请求正式状态
3. 终态只允许 `COMPLETED / COMPLETED_EARLY / CANCELLED / FAULT_INTERRUPTED`
4. `FAULT_INTERRUPTED` 只用于“已经开始充电后被故障中断”的本次详单终态

### 2.2 数据建模冻结原则

1. 对外 ID 与内部主键分离
2. 公开字段优先与冻结文档同名
3. 不再围绕中央等待池建模
4. 不再单独维护账单表，详单是唯一费用事实源
5. 报表按详单聚合生成，不单独落报表明细表
6. 场景参数不再以“场景配置中心”作为正式运行模型

### 2.3 默认迁移原则

Day 2 冻结采用以下默认策略：

- 保留并迁移用户账号数据
- 不迁移旧请求状态流转数据
- 不迁移旧账单/支付数据到 V3 正式表
- 充电桩运行态、等待池数据、旧场景配置全部重建

原因：

- V2 与 V3 状态语义不兼容
- V2 账单模型与 V3 详单模型不兼容
- V2 场景配置模型与 V3 启动配置模型不兼容

## 3. 后端状态机实现表

## 3.1 请求状态机实现表

| 状态 | 状态含义 | 必填字段 | 允许触发事件 | 下一个状态 | 落库动作 |
|------|------|------|------|------|------|
| `WAITING_AREA` | 请求已进入等候区，尚未进入某桩固定队列 | `request_id`、`queue_number`、`charge_mode`、`request_energy`、`request_status`、`waiting_area_order` | 创建请求、修改模式、修改电量、等候区取消、普通调度取头车 | `WAITING_AREA` / `CANCELLED` / `QUEUED` | 创建时生成 `queue_number`；修改模式时生成新排队号并重排到新模式队尾；修改电量时保留排队号；取消时不生成详单 |
| `QUEUED` | 已进入某充电桩固定队列但尚未开始充电 | `station_code`、`station_queue_position`、`estimated_start_time`、`estimated_finish_time` | 队首开始充电、充电区取消/提前结束、故障重排 | `CHARGING` / `COMPLETED_EARLY` / `QUEUED` | 进入桩队列时清空 `waiting_area_order`；队首启动时写入 `charging_session`；用户停止时允许生成 0 电量详单；故障重排时保持正式状态为 `QUEUED`，只更新桩绑定和队列位置 |
| `CHARGING` | 正在充电 | `station_code`、`station_queue_position=1`、`start_time` | 正常充满、提前结束、桩故障 | `COMPLETED` / `COMPLETED_EARLY` / `FAULT_INTERRUPTED` | 开始充电时创建会话；结束时更新 `actual_energy`、`charge_duration_seconds`，并生成详单 |
| `COMPLETED` | 正常充满结束 | 终态详单字段齐全 | 无 | 终态 | 生成详单；更新桩累计指标；释放桩队列空位 |
| `COMPLETED_EARLY` | 充电区取消或提前结束后的结算终态 | 终态详单字段齐全 | 无 | 终态 | 生成详单；若停止前未开始充电，则 `actual_energy=0`、`charge_duration_seconds=0`、`start_time=stop_time=操作时刻` |
| `CANCELLED` | 等候区取消 | `request_id`、`request_status` | 无 | 终态 | 不生成详单；释放等候区名额 |
| `FAULT_INTERRUPTED` | 已开始充电后因桩故障中断，本次详单终态 | 终态详单字段齐全 | 无 | 终态 | 生成 `FAULT_INTERRUPTED` 详单；若仍有剩余电量，创建一条新请求重新进入 `WAITING_AREA` |

### 3.1.1 请求状态机补充冻结

1. `queue_number` 只在 `WAITING_AREA` 创建或修改模式时生成，且同模式单调递增不复用。
2. `station_queue_position` 采用 1 开始计数，且 `1` 表示“当前充电位”。
3. `charging_queue_len` 包含充电位，因此某桩合法位置范围是 `1..charging_queue_len`。
4. 请求进入 `QUEUED` 后，`front_waiting_count` 应按“同模式等候区在前车辆数”计算，不等于桩队列内前车数。
5. `QUEUED` 遇故障时不新增公开状态，使用调度内部“故障重排集合”处理。

### 3.1.2 关于 `QUEUED` 故障的冻结决策

`docs/功能设计.md` 的状态表写过 `QUEUED -> FAULT_INTERRUPTED`，但 `docs/故障与扩展场景指南.md` 明确给出了更细的口径：

- 已开始充电的车辆，故障时生成 `FAULT_INTERRUPTED` 详单
- 未开始充电、仅占据队列位置的车辆，不生成 `FAULT_INTERRUPTED`，而是直接进入重排集合

Day 2 正式冻结采用后一种更细口径，原因如下：

- 与详单字段字典一致，避免出现没有真实 `start_time / stop_time` 的伪故障详单
- 与故障场景用例一致
- 保持 7 个正式请求状态不被临时调度过程污染

## 3.2 充电桩状态机实现表

| 状态 | 状态含义 | 允许触发事件 | 下一个状态 | 落库动作 |
|------|------|------|------|------|
| `RUNNING` | 正常可调度 | 空闲关闭、标记故障 | `SHUTDOWN` / `FAULT` | 关闭前必须校验无充电中车辆且队列为空；故障时暂停等候区叫号 |
| `SHUTDOWN` | 管理员主动关闭，不参与调度 | 启动 | `RUNNING` | 启动后恢复参与同模式调度 |
| `FAULT` | 故障停用，不参与调度 | 故障恢复 | `RUNNING` | 恢复后若其它同类型桩存在未开始充电车辆，按时间顺序统一重排 |

### 3.2.1 桩状态机补充冻结

1. V3 不再使用 `IDLE / RESERVED / WAITING_TO_LEAVE` 作为公开状态。
2. “是否正在充电”“队列是否为空”属于运行时派生信息，不再额外提升为桩正式状态。
3. 管理端 `GET /api/admin/stations` 中的 `current_request_id`、`queue_length` 是运行态字段，不改变桩正式状态只有 3 个这一事实。

## 4. V3.0 目标数据模型冻结

## 4.1 `user` 用户表

### 4.1.1 保留字段

- `id`
- `username`
- `password_hash`
- `role`
- `created_at`

### 4.1.2 新增字段

- `user_id`：对外业务编号，如 `U001`
- `battery_capacity`
- `updated_at`

### 4.1.3 删除字段

- `balance`

### 4.1.4 冻结结论

V3 的用户表必须能直接支撑：

- 注册接口返回 `user_id`
- 用户列表返回 `battery_capacity`
- 用户维护接口修改车辆电池总容量

## 4.2 `charge_request` 请求表

### 4.2.1 必保留字段

- `id`
- `request_id`
- `user_id` 或等价内部用户外键
- `charge_mode`
- `request_energy`
- `actual_energy`
- `estimated_wait_seconds`
- `estimated_start_time`
- `estimated_finish_time`
- `created_at`
- `updated_at`

### 4.2.2 必新增或重命名字段

- `request_status`：替代旧 `status`
- `queue_number`
- `waiting_area_order`
- `station_id` 或等价内部桩外键
- `station_code_cache` 可选
- `station_queue_position`
- `request_time`：替代旧 `submit_time`
- `charge_start_time`
- `charge_stop_time`
- `charge_duration_seconds`：替代旧 `actual_service_seconds`
- `fault_source_request_id` 可选，用于续充链路追踪

### 4.2.3 必删除字段

- `remaining_energy`
- `battery_limit_energy`
- `waiting_pool_type`
- `scenario_id`
- `last_called_at`
- `confirmed_at`
- `priority_score`
- `retry_count`
- `no_show_count`
- `fault_requeue_flag`

### 4.2.4 冻结结论

`charge_request` 是 V3 的核心公开业务实体，必须直接表达：

- 排队号
- 等候区顺序
- 桩队列位置
- 正式请求状态
- 用户可见的预估时间

不再承担：

- 中央等待池状态
- 叫号 / 到场确认
- 过号重试
- 故障重排标记

## 4.3 `charging_station` 充电桩表

### 4.3.1 必保留字段

- `id`
- `station_code`
- `power_kw`
- `created_at`
- `updated_at`

### 4.3.2 必新增或重命名字段

- `charge_mode`：替代旧 `station_type`
- `station_status`：替代旧 `status`
- `queue_capacity`：等于当前 `charging_queue_len`
- `current_queue_length`
- `current_request_id` 可选缓存
- `total_charge_count`
- `total_charge_seconds`
- `total_charge_energy`

### 4.3.3 可保留的内部缓存字段

- `available_time`

### 4.3.4 必删除字段

- `initial_queue_length`
- `initial_status`
- `initial_remaining_seconds`
- `scenario_id`

### 4.3.5 冻结结论

V3 的桩表不再服务于“场景快照初始化”，而是服务于：

- 正式运行态管理
- 队列容量约束
- 报表统计
- 管理端状态查看

### 4.3.6 功率冻结

- 快充桩：`30 kW`
- 慢充桩：`10 kW`

当前 `init_schema_v2.sql` 中慢充默认功率仍是 `7.0`，Day 2 认定这属于必须修正项。

## 4.4 `request_detail` 详单表

### 4.4.1 冻结决策

V3 不再沿用 `billing_record` 作为正式结算模型，而是新建 `request_detail` 表，详单即费用事实源。

### 4.4.2 必备字段

- `id`
- `detail_id`
- `request_id` 或等价内部请求外键
- `user_id` 或等价内部用户外键
- `station_code`
- `actual_energy`
- `charge_duration_seconds`
- `start_time`
- `stop_time`
- `detail_generated_at`
- `charge_fee`
- `service_fee`
- `total_fee`
- `request_status`
- `created_at`

### 4.4.3 约束

1. `CANCELLED` 不生成详单。
2. `COMPLETED / COMPLETED_EARLY / FAULT_INTERRUPTED` 必生成详单。
3. 不再额外维护账单表。
4. 用户历史详单、请求详情、报表都从该表出发。

## 4.5 `scheduler_config` 配置表

### 4.5.1 保留用途

`scheduler_config` 在 V3 中只保留“运行时策略与计费常量”用途。

### 4.5.2 建议保留键

- `dispatch_mode`
- `fault_dispatch_mode`
- `peak_price`
- `flat_price`
- `valley_price`
- `service_fee_unit_price`

### 4.5.3 不再继续扩展的旧键

- `T_CALL_MINUTES`
- `CONFIRM_TIMEOUT_MINUTES`
- `ARRIVAL_TIMEOUT_MINUTES`
- `LEAVE_BUFFER_MINUTES`
- `BILLING_MODE`
- `TIME_PRICE`
- `OCCUPANCY_PRICE`
- `OCCUPANCY_START_AFTER_MINUTES`
- `PRIORITY_WEIGHT_A/B/C/D/E`

## 4.6 `scheduler_event_log` 事件日志表

### 4.6.1 保留并扩展

该表可保留，但用途从“调度内部日志”扩展为“系统事件日志”。

### 4.6.2 新事件类型至少包含

- `REQUEST_CREATED`
- `REQUEST_MODE_UPDATED`
- `REQUEST_ENERGY_UPDATED`
- `REQUEST_CANCELLED`
- `REQUEST_STOPPED`
- `REQUEST_COMPLETED`
- `REQUEST_FAULT_INTERRUPTED`
- `STATION_STARTED`
- `STATION_SHUTDOWN`
- `STATION_FAULTED`
- `STATION_RECOVERED`
- `DISPATCH_MODE_UPDATED`
- `FAULT_DISPATCH_MODE_UPDATED`
- `USER_BATTERY_CAPACITY_UPDATED`

## 4.7 报表落地方式冻结

Day 2 冻结为：

- 不新建 `report` 表
- `GET /api/admin/reports` 直接从 `request_detail` 按粒度聚合
- 为报表查询增加索引即可

建议索引：

- `request_detail(detail_generated_at)`
- `request_detail(station_code, detail_generated_at)`
- `charge_request(user_id, request_status)`

## 5. 数据模型调整矩阵

| 表 | 动作 | 冻结结论 |
|------|------|------|
| `user` | 重建 | 去掉 `balance`，补 `user_id`、`battery_capacity` |
| `charge_request` | 重建 | 切到 V3 请求状态、排队号、等候区顺序、桩队列位置 |
| `charging_station` | 重建 | 切到 `station_status`、`queue_capacity`、统计字段 |
| `charging_session` | 部分复用 | 仅保留“充电开始/结束/实际电量”用途 |
| `billing_record` | 废弃 | 由 `request_detail` 替代 |
| `system_scenario_config` | 废弃 | 正式运行不再依赖场景配置中心 |
| `scheduler_config` | 收缩复用 | 仅保留调度模式、故障策略、分时价格、服务费单价 |
| `scheduler_event_log` | 复用扩展 | 升级为系统事件日志 |
| `notification` | 暂不处理 | 非 Day 2 核心 |

## 6. 数据库迁移清单

## 6.1 迁移前置决策

1. 以 `backend/migrations/init_schema_v3.sql` 作为新基线
2. 新增 `backend/migrations/migrate_v2_to_v3.py`
3. 默认采用“迁账号、弃业务运行态、重建桩与请求数据”的迁移策略

## 6.2 具体迁移步骤

| 步骤 | 动作 | 结果 |
|------|------|------|
| 1 | 备份现有 `charging_system.db` | 保留 V2 回滚点 |
| 2 | 导出 `user` 表基础数据 | 准备迁移账号 |
| 3 | 新建 V3 `user` 表 | 补 `user_id`、`battery_capacity` |
| 4 | 回填 `user_id` | 按 `U001/U002/...` 生成，不复用 |
| 5 | 回填 `battery_capacity` | 若历史可推断则取最近有效值，否则统一默认值并标记待维护 |
| 6 | 新建 V3 `charging_station` 表 | 以启动参数生成桩；慢充功率改为 `10` |
| 7 | 新建 V3 `charge_request` 表 | 按新字段定义创建 |
| 8 | 新建 `request_detail` 表 | 替代 `billing_record` |
| 9 | 保留或重建 `charging_session` | 去掉旧中断/挪车语义依赖 |
| 10 | 收缩 `scheduler_config` | 仅写入 V3 必需键 |
| 11 | 归档旧 `billing_record`、`system_scenario_config` | 不再作为正式运行表 |
| 12 | 创建 V3 索引 | 支撑状态查询、报表、用户活跃请求校验 |
| 13 | 重写初始数据 | 管理员账号、默认桩、默认价格与模式 |
| 14 | 跑 Day 3 之前的最小回归 | 注册、登录、创建请求、状态查询 |

## 6.3 字段级迁移清单

### 6.3.1 `user`

- 保留：`username`、`password_hash`、`role`、`created_at`
- 新增：`user_id`、`battery_capacity`、`updated_at`
- 删除：`balance`

### 6.3.2 `charge_request`

- 保留：`request_id`、`request_energy`、`actual_energy`、预估时间字段
- 重命名：`status -> request_status`、`submit_time -> request_time`、`actual_service_seconds -> charge_duration_seconds`
- 新增：`queue_number`、`waiting_area_order`、`station_queue_position`、`charge_start_time`、`charge_stop_time`
- 删除：`waiting_pool_type`、`scenario_id`、`battery_limit_energy`、`priority_score`、`retry_count`、`no_show_count`、`fault_requeue_flag`、`last_called_at`、`confirmed_at`

### 6.3.3 `charging_station`

- 保留：`station_code`、`power_kw`
- 重命名：`station_type -> charge_mode`、`status -> station_status`
- 新增：`queue_capacity`、`current_queue_length`、`total_charge_count`、`total_charge_seconds`、`total_charge_energy`
- 删除：`initial_queue_length`、`initial_status`、`initial_remaining_seconds`、`scenario_id`

### 6.3.4 `billing_record`

- 迁移策略：不迁移为正式表
- 处理方式：归档后由 `request_detail` 完全替代

## 6.4 无损迁移边界说明

以下内容 Day 2 明确认定为“不做无损迁移”：

- 旧中央等待池顺序
- 旧 `CALLED / CONFIRMED / NO_SHOW / FAULT_REQUEUE` 状态
- 旧场景配置
- 旧支付状态
- 旧账单明细

理由：

- 这些语义在 V3 中已不存在或已换轨
- 强行迁移会把错误模型继续带入 V3

## 7. Day 2 产出结论

Day 2 已冻结以下内容：

1. 成员B正式请求状态机落地方案
2. 成员B正式桩状态机落地方案
3. V3 目标数据模型
4. 新旧表结构处理矩阵
5. 数据库迁移清单

## 8. Day 3 最优先动作

下一步建议直接进入 Day 3，顺序如下：

1. 先重写 `backend/app/enums.py`
2. 再起 `init_schema_v3.sql`
3. 改 `auth.py`，补 `battery_capacity`
4. 改 `request.py`，只先打通 `create + status`
5. 新增最小 V3 契约测试，替换旧 `confirm_arrival` 契约测试

## 9. 可执行检查清单

- [x] 已冻结 7 个正式请求状态
- [x] 已冻结 3 个正式桩状态
- [x] 已明确 `QUEUED` 故障时的正式落库规则
- [x] 已冻结 `user / charge_request / charging_station / request_detail` 的目标结构
- [x] 已确认 `billing_record`、`system_scenario_config` 不再作为正式模型
- [x] 已给出数据库迁移清单
- [ ] Day 3：认证与创建请求最小闭环实现
