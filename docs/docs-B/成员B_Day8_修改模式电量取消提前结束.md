# 成员B Day 8：修改模式 / 电量 / 取消 / 提前结束

## 1. 目标

Day 8 的目标是打通增量二的四个用户动作接口：

- `PUT /api/request/mode`
- `PUT /api/request/energy`
- `POST /api/request/cancel`
- `POST /api/request/stop`

## 2. 本日完成内容

### 2.1 等候区修改模式已完成

已实现：

- `PUT /api/request/mode`

当前规则如下：

- 仅允许 `WAITING_AREA`
- 修改后重新生成 `F/T` 排队号
- 请求插入新模式队尾
- 返回：
  - `request_id`
  - `queue_number`
  - `request_status`
  - `front_waiting_count`

补充说明：

- 若目标模式与当前模式相同，则按当前等待态直接返回
- 若目标模式当前无可用运行桩，则返回 `1005`

### 2.2 等候区修改电量已完成

已实现：

- `PUT /api/request/energy`

当前规则如下：

- 仅允许 `WAITING_AREA`
- 保留原 `queue_number` 不变
- 校验 `request_energy ∈ (0, 300]`
- 返回：
  - `request_id`
  - `queue_number`
  - `request_energy`
  - `request_status`
  - `front_waiting_count`

### 2.3 等候区取消已完成

已实现：

- `POST /api/request/cancel`

当前规则如下：

- 仅允许 `WAITING_AREA`
- 成功后状态进入 `CANCELLED`
- 不生成详单
- 返回：
  - `request_id`
  - `request_status`

### 2.4 充电区取消 / 提前结束已完成

已实现：

- `POST /api/request/stop`

当前规则如下：

- 允许状态：`QUEUED`、`CHARGING`
- 成功后统一进入 `COMPLETED_EARLY`
- 自动生成独立详单
- 返回：
  - `request_id`
  - `request_status`

两类场景的落地语义如下：

1. `QUEUED` 停止：
   - 视为未开始充电即退出本次占位
   - 生成 0 电量、0 时长的 `COMPLETED_EARLY` 详单
   - 释放队列位置并触发后续调度

2. `CHARGING` 停止：
   - 按实际已充电时长结算
   - 生成部分电量的 `COMPLETED_EARLY` 详单
   - 释放当前桩并触发后续调度

### 2.5 Day 8 已接入 Day 5 / Day 6 主流程

本次用户动作已经与现有主流程串通：

- 等候区修改模式 / 电量 / 取消后，可继续触发普通调度
- `stop` 后会重排当前固定桩队列
- `stop` 后会触发后续队首推进与等候区补位
- `COMPLETED_EARLY` 已复用 Day 6 的详单与分时计费逻辑

## 3. 主要实现位置

本次主实现集中在：

- `backend/app/routes/request.py`
- `backend/app/services/queue_model.py`
- `backend/tests/test_frozen_contracts.py`

其中：

- `request.py` 承担 Day 8 四个接口主体
- `queue_model.py` 提供 Day 8 需要的桩状态推进与重排入口
- `test_frozen_contracts.py` 锁定 Day 8 契约与主流程行为

## 4. 测试结果

本日新增并通过的重点校验包括：

- 等候区修改模式后重新生成新模式排队号并插入新队尾
- 等候区修改电量后保留原排队号
- 等候区取消后进入 `CANCELLED` 且不生成详单
- `QUEUED` 请求停止后生成 0 电量 `COMPLETED_EARLY` 详单
- `CHARGING` 请求停止后生成部分电量 `COMPLETED_EARLY` 详单

关键验证场景：

- `10:00` 开始快充 `20.0 kWh`
- `10:20` 提前结束
- 以 `30 kW` 计：
  - 实际充电 `1200 s`
  - 实际电量 `10.0 kWh`
  - 峰时 `charge_fee = 10.0`
  - `service_fee = 8.0`
  - `total_fee = 18.0`

执行结果：

- `python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts`
  - 18 个测试通过
- `python -m unittest discover -s backend/tests`
  - 全量通过，结果为 `OK (skipped=2)`

## 5. Day 8 结论

Day 8 已完成的正式边界：

- 用户侧修改模式已可用
- 用户侧修改电量已可用
- 等候区取消已可用
- 充电区取消 / 提前结束已可用
- `COMPLETED_EARLY` 已接入详单与计费闭环

当前实现中的一个工程性假设：

- `POST /api/request/stop` 额外接受未公开的可选字段 `stop_time`，用于测试与确定性结算；若未提供，则回退到当前模型中的可推导时刻

仍留给后续阶段的内容：

- Day 9：故障标记、故障恢复、故障调度策略
- Day 10：启动/关闭充电桩、用户维护、报表接口
