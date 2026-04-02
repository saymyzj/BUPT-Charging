# 智能充电桩调度计费系统

**文档版本**: V1.0  
**编写日期**: 2026-04-02  
**编写人**: 成员 B（服务端负责人/场景适配负责人）  
**审核状态**: 待审核

---

## 一、已完成的部分

### 周期 1：数据库与基础架构修正（Day 1-2）

#### 1.1 数据库 Schema V2 升级

| 模块 | 完成内容 | 文件位置 |
|------|----------|----------|
| 场景配置表 | 新增 `system_scenario_config` 表，支持动态场景配置 | `migrations/init_schema_v2.sql` |
| 充电桩表增强 | 新增 `initial_queue_length`, `initial_status` 等字段 | `migrations/init_schema_v2.sql` |
| 充电请求表 | 新增 `estimated_service_seconds`, `scenario_id` 等字段 | `migrations/init_schema_v2.sql` |
| 数据迁移工具 | 实现 V1 到 V2 的数据迁移脚本 | `migrations/migrate_data.py` |

#### 1.2 枚举值更新

- `WaitingPoolType`: 支持 `FAST_POOL`, `SLOW_POOL`
- `StationQueueMode`: 支持 `UNIFORM_CAPACITY`, `STATION_SNAPSHOT`
- `ChargeMode`: 快充 30kW，慢充 7kW
- `RequestStatus`: `PENDING`, `WAITING`, `CALLED`, `CHARGING`, `COMPLETED`, `CANCELLED`, `INTERRUPTED`, `COMPLETED_EARLY`
- `StationStatus`: `IDLE`, `OCCUPIED`, `WAITING_TO_LEAVE`, `OFFLINE`

#### 1.3 核心模块实现

| 模块 | 功能描述 | 状态 |
|------|----------|------|
| `config_manager.py` | 场景配置的 CRUD 管理 | ✅ 完成 |
| `waiting_pool.py` | 双等待池管理（FAST/SLOW），共享容量控制 | ✅ 完成 |
| `helpers.py` | 工具函数，解决循环导入问题 | ✅ 完成 |

---

### 周期 2：场景适配层实现（Day 3-4）

#### 2.1 场景适配器核心

| 组件 | 功能描述 | 状态 |
|------|----------|------|
| `ScenarioAdapter` 类 | 适配器模式，统一处理两种输入格式 | ✅ 完成 |
| `adapt_uniform_capacity()` | 统一容量模式适配 | ✅ 完成 |
| `adapt_station_snapshot()` | 桩级快照模式适配 | ✅ 完成 |
| `initialize_waiting_pools()` | 初始化等待池 | ✅ 完成 |
| `reset_scenario()` | 场景重置 | ✅ 完成 |

#### 2.2 场景参数解析器

| 组件 | 功能描述 | 状态 |
|------|----------|------|
| `scenario_parser.py` | 解析批量模拟中的场景参数 | ✅ 完成 |
| `user_behavior_parser.py` | 解析用户行为时间线和事件序列 | ✅ 完成 |
| `UserBehaviorConfig` 类 | 定义单个用户完整行为配置 | ✅ 完成 |

---

### 周期 3：现有接口适配与批量模拟基础（Day 5-6）

#### 3.1 请求接口适配

| 接口 | 路径 | 适配内容 | 状态 |
|------|------|----------|------|
| 创建请求 | `POST /api/request/create` | 容量检查、池类型记录、临时预测值计算 | ✅ 完成 |
| 查询状态 | `GET /api/request/status/{id}` | 返回池类型和队列位置 | ✅ 完成 |
| 取消排队 | `POST /api/request/cancel_queue` | 从等待池移除 | ✅ 完成 |
| 确认到场 | `POST /api/request/confirm_arrival` | 状态流转 | ✅ 完成 |
| 中断充电 | `POST /api/request/interrupt_charge` | 记录中断原因 | ✅ 完成 |
| 确认挪车 | `POST /api/request/confirm_leave` | 超时检测 | ✅ 完成 |
| 查询结果 | `GET /api/request/result/{id}` | 详单/账单生成 | ✅ 完成 |
| 支付账单 | `POST /api/request/pay` | 支付状态更新 | ✅ 完成 |

#### 3.2 新增接口

| 接口 | 路径 | 功能描述 | 状态 |
|------|------|----------|------|
| 健康检查 | `GET /health` | 系统状态检查 | ✅ 完成 |
| 充电桩总览 | `GET /api/stations/overview` | 返回所有充电桩状态和等待队列 | ✅ 完成 |
| 批量模拟 | `POST /api/batch/simulate` | 批量模拟框架（V3.0） | ✅ 框架完成 |

#### 3.3 预测值计算逻辑

创建请求时的预测值计算：

```
预计等待时间 = 队列中人数 × 5分钟（300秒）
预计开始时间 = 当前时间 + 等待时间
预计服务时长 = 电量 / 功率 × 60分钟
预计完成时间 = 开始时间 + 服务时长
```

- 快充功率：30kW
- 慢充功率：7kW

#### 3.4 状态一致性保证

| 位置 | 状态值 | 说明 |
|------|--------|------|
| 数据库 `charge_request.status` | `WAITING` | 创建时直接写入 |
| `create` 接口响应 | `WAITING` | 与数据库一致 |
| `status` 接口响应 | 从数据库读取 | 实时反映当前状态 |

---

## 二、未完成的部分

### 2.1 调度模块对接（依赖成员 A）

| 功能 | 说明 | 依赖方 |
|------|------|--------|
| 真实预测时间计算 | 调用调度模块获取准确的预计等待时间 | 成员 A |
| 重调度触发 | 充电完成后触发调度算法重新分配 | 成员 A |
| 批量模拟执行引擎 | 时间序列模拟和状态推进 | 成员 A |

### 2.2 状态机确认（需与成员 A 确认）

- `PENDING` 状态是否必要？当前创建请求后直接为 `WAITING`
- 状态流转规则的最终确认

### 2.3 批量模拟完整实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 场景参数解析 | ✅ 完成 | `scenario_parser.py` |
| 用户行为解析 | ✅ 完成 | `user_behavior_parser.py` |
| 模拟执行引擎 | ⏳ 待实现 | 依赖调度模块 |
| 结果收集与返回 | ⏳ 待实现 | 依赖执行引擎 |

---

## 三、待与 A 对接的部分

### 3.1 调度模块接口约定

| 接口 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `get_estimated_wait_time` | charge_mode, request_energy | estimated_wait_seconds | 创建请求时计算预测时间 |
| `trigger_reschedule` | station_id | void | 充电完成后重调度 |
| `simulate_timeline` | scenario_config, user_behaviors | simulation_result | 批量模拟执行 |

### 3.2 状态机定义确认

- 确认 `PENDING` 状态是否需要保留
- 确认 `WAITING_TO_LEAVE` 状态的使用场景
- 确认各状态之间的流转条件

### 3.3 批量模拟协作

- 成员 A 负责：模拟执行引擎、时间推进、状态更新
- 成员 B 负责：场景参数解析、用户行为解析、结果格式化

---

## 四、待与 C 对接的部分

### 4.1 前端页面接口

| 页面 | 所需接口 | 状态 |
|------|----------|------|
| 充电桩总览页 | `GET /api/stations/overview` | ✅ 已完成 |
| 请求创建页 | `POST /api/request/create` | ✅ 已完成 |
| 状态查询页 | `GET /api/request/status/{id}` | ✅ 已完成 |
| 详单/账单页 | `GET /api/request/result/{id}` | ✅ 已完成 |

### 4.2 接口文档确认

- 确认前端需要的字段是否完整
- 确认错误码提示信息的展示方式
- 确认页面跳转和状态刷新的逻辑

---

## 五、技术债务与优化项

### 5.1 当前技术债务

| 问题 | 影响 | 优先级 | 计划解决时间 |
|------|------|--------|--------------|
| 预测值为临时计算 | 精度不高 | 中 | 调度模块接入后 |
| TODO 注释未处理 | 代码整洁度 | 低 | 后续迭代 |

### 5.2 性能优化点

- 数据库查询优化（添加索引）
- 等待池状态缓存
- 批量操作的事务处理

---

## 六、附录

### 6.1 已冻结接口清单

| 序号 | 接口路径 | 方法 | 功能描述 |
|------|----------|------|----------|
| 1 | `/health` | GET | 健康检查 |
| 2 | `/api/request/create` | POST | 创建充电请求 |
| 3 | `/api/request/status/{id}` | GET | 查询请求状态 |
| 4 | `/api/request/confirm_arrival` | POST | 确认到场 |
| 5 | `/api/request/cancel_queue` | POST | 取消排队 |
| 6 | `/api/request/interrupt_charge` | POST | 中断充电 |
| 7 | `/api/request/confirm_leave` | POST | 确认挪车 |
| 8 | `/api/request/result/{id}` | GET | 查询结果/详单 |
| 9 | `/api/request/pay` | POST | 支付账单 |
| 10 | `/api/stations/overview` | GET | 充电桩总览 |
| 11 | `/api/batch/simulate` | POST | 批量模拟 |

### 6.2 代码文件清单

**数据库与迁移**:
- `migrations/init_schema_v2.sql`
- `migrations/migrate_data.py`

**核心服务**:
- `app/services/config_manager.py`
- `app/services/waiting_pool.py`
- `app/services/scenario_adapter.py`
- `app/services/scenario_parser.py`
- `app/services/user_behavior_parser.py`
- `app/services/billing_service.py`

**工具模块**:
- `app/utils/helpers.py`
- `app/utils/response.py`
- `app/utils/validators.py`
- `app/utils/db.py`

**路由接口**:
- `app/routes/health.py`
- `app/routes/request.py`
- `app/routes/stations.py`
- `app/routes/batch_simulate.py`
- `app/routes/admin.py`

**枚举定义**:
- `app/enums.py`

---

**文档结束**
