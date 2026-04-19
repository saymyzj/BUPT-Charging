# 成员B Day 5：普通调度主流程

## 1. 目标

Day 5 的目标是打通 V3 `NORMAL` 普通调度主流程，完成以下正式能力：

- 新请求创建后触发普通调度
- 某桩队列出现空位后继续普通调度
- 队首请求进入 `CHARGING`
- 充电完成后进入 `COMPLETED`

## 2. 本日完成内容

### 2.1 `NORMAL` 调度规则已落地

当前后端已按文档实现以下普通调度规则：

1. 仅在同模式内调度
2. 先取该模式等候区头车
3. 在所有同模式且仍有空位的桩队列中计算“等待时间 + 自身充电时间”
4. 将请求加入总完成时长最短的桩队列

若多个候选桩的完成总时长相同，则按 `station_code` 升序稳定选择。

### 2.2 创建请求事件已接入普通调度

`POST /api/request/create` 在完成请求落库后，会以该请求的 `request_time` 作为事件时刻触发 `NORMAL` 调度。

因此当前主流程已具备：

- 新请求创建时自动补位
- 旧请求若在该事件时刻之前已完成，会先结算并释放空位
- 新请求随后再进入最优同模式桩队列

说明：

- 创建接口返回体仍保持 Day 3/冻结文档要求的最小字段集
- 实际最新状态应以 `GET /api/request/status/{request_id}` 为准

### 2.3 `QUEUED -> CHARGING -> COMPLETED` 已打通

普通调度主流程已支持：

- 队首 `QUEUED` 请求在可开始时自动转为 `CHARGING`
- `CHARGING` 请求在预计完成时自动转为 `COMPLETED`
- 完成后自动释放队首位置
- 后继队列位置自动前移
- 新的队首请求自动进入 `CHARGING`

### 2.4 充电桩运行信息同步

当前调度过程中会同步维护：

- `current_queue_length`
- `current_request_id`
- `available_time`
- `total_charge_count`
- `total_charge_seconds`
- `total_charge_energy`

这意味着 Day 7 管理员侧查看桩状态时，可以直接复用这批运行字段。

## 3. 主要实现位置

本次主实现集中在：

- `backend/app/services/queue_model.py`
- `backend/app/routes/request.py`

其中 `queue_model.py` 当前已承担：

- 等候区预测
- 固定桩队列维护
- `NORMAL` 普通调度
- 队首启动
- 完成结算前的状态推进

## 4. 测试结果

本日新增并通过的重点场景包括：

- 创建请求后自动进入普通调度
- 三个快充桩空闲时，前三辆车分别进入三个不同桩
- 第四辆车按“最短完成时间”进入最优桩队列
- 到达前车完成时刻后，后车自动从 `QUEUED` 提升为 `CHARGING`
- 已完成请求进入 `COMPLETED`

执行结果：

- `python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts`
  - 8 个测试通过
- `python -m unittest discover -s backend/tests`
  - 全量通过，结果为 `OK (skipped=2)`

## 5. Day 5 结论

Day 5 已完成的正式边界：

- `NORMAL` 普通调度已可运行
- 新请求创建事件已接入普通调度
- 固定桩队列的状态推进已打通
- `QUEUED -> CHARGING -> COMPLETED` 已形成最小可运行闭环

仍留给后续阶段的内容：

- Day 6：详单生成与分时计费
- Day 8：取消、修改模式、修改电量、提前结束
- Day 9：故障调度与故障恢复
- Day 11：扩展调度模式
