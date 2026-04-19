# 成员B Day 4：状态查询与等候区模型

## 1. 目标

Day 4 的目标是把后端状态查询正式切到 V3 口径，并落地“等候区 + 每桩固定长度队列”的基础模型。

对应说明文档中的两项交付：

- V3 状态查询接口
- 等候区与桩队列基础实现

## 2. 本日完成内容

### 2.1 状态查询接口按 V3 输出

已完成 `GET /api/request/status/{request_id}` 的 V3 输出对齐，当前接口返回字段为：

- `request_id`
- `queue_number`
- `charge_mode`
- `request_energy`
- `request_status`
- `front_waiting_count`
- `station_code`
- `station_queue_position`
- `estimated_wait_seconds`
- `estimated_start_time`
- `estimated_finish_time`

其中：

- `front_waiting_count` 基于同模式等候区顺序计算
- `station_code / station_queue_position` 仅在请求已进入某桩固定队列后返回
- `estimated_*` 不再只是数据库占位字段，而是由 Day 4 的队列模型动态推导

### 2.2 落地等候区顺序结构

当前正式使用：

- `charge_request.waiting_area_order`

语义冻结如下：

- 只对 `WAITING_AREA` 请求生效
- 同模式内部按进入等候区的顺序单调递增
- `front_waiting_count` = 同模式下 `waiting_area_order` 更小的请求数
- 请求进入某个充电桩固定队列后，`waiting_area_order` 置空

### 2.3 落地每桩固定长度队列结构

当前正式使用：

- `charging_station.queue_capacity`
- `charging_station.current_queue_length`
- `charge_request.station_id`
- `charge_request.station_queue_position`

语义冻结如下：

- 每个充电桩维护独立固定长度队列
- 队列容量由 `queue_capacity` 控制
- `station_queue_position` 从 1 开始递增
- `current_queue_length` 由队列内 `QUEUED / CHARGING` 请求同步得出

## 3. 新增的 Day 4 行为

### 3.1 等候区请求可返回预测时间

对 `WAITING_AREA` 请求，系统会：

1. 读取同模式可运行充电桩
2. 读取各桩当前 `QUEUED / CHARGING` 工作量
3. 按“等待时间 + 自身充电时间最短”规则进行预测分配
4. 输出该请求的预计等待、预计开始、预计完成时间

说明：

- Day 4 只做预测，不把等待区请求自动推进为 `QUEUED`
- 正式自动调度主流程仍归 Day 5 实现

### 3.2 已入桩请求可返回固定队列位置

对 `QUEUED / CHARGING` 请求，系统会：

- 根据同桩前车剩余工作量计算 `estimated_wait_seconds`
- 返回当前 `station_code`
- 返回当前 `station_queue_position`
- 推导 `estimated_start_time / estimated_finish_time`

### 3.3 提供基础入桩能力

新增队列模型服务后，后端已具备将 `WAITING_AREA` 请求放入某个固定桩队列的基础能力，包含：

- 模式校验
- 桩运行状态校验
- 固定容量校验
- 队列位置分配
- 预计时间写入
- `current_queue_length` 同步

这为 Day 5 的 NORMAL 调度主流程提供了直接复用的底座。

## 4. 测试结果

本日新增并通过的重点校验包括：

- 等候区请求状态查询返回 V3 字段且带预测时间
- 单桩入队后返回固定 `station_code / station_queue_position`
- 单桩超出固定容量时拒绝继续入队

执行结果：

- `python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts`
  - 6 个测试通过
- `python -m unittest discover -s backend/tests`
  - 全量通过，结果为 `OK (skipped=2)`

## 5. Day 4 结论

Day 4 已完成以下边界切换：

- 状态查询接口正式切到 V3 字段集
- 等候区顺序结构正式落地
- 每桩固定长度队列结构正式落地
- 预计等待/开始/完成时间已有统一推导逻辑

仍未在 Day 4 完成、并应留给 Day 5 的内容：

- 空位触发自动调度
- `NORMAL` 正式调度主流程
- `QUEUED -> CHARGING -> COMPLETED` 状态推进
