# 成员B Day 11：扩展调度与批量模拟

## 交付范围

Day 11 完成增量三验收能力：

- `PUT /api/admin/system/dispatch-mode`
- `NORMAL`
- `EXT_SINGLE_BATCH`
- `EXT_FULL_BATCH`
- `POST /api/test/batch-simulate`
- 批量输入场景参数对齐冻结文档
- 批量回放支持 `events`

同时保留旧兼容路径：

- `POST /api/batch/simulate`

正式验收以 `POST /api/test/batch-simulate` 为准。

## 调度模式切换

```http
PUT /api/admin/system/dispatch-mode
```

请求体：

```json
{
  "dispatch_mode": "EXT_SINGLE_BATCH"
}
```

合法值：

- `NORMAL`
- `EXT_SINGLE_BATCH`
- `EXT_FULL_BATCH`

规则：

- 仅管理员可调用。
- 非法值返回 `1001`。
- 修改成功后写入 `scheduler_event_log`，事件类型为 `ADMIN_UPDATE_DISPATCH_MODE`。
- `GET /api/admin/system/config` 会返回当前 `dispatch_mode`。

## 扩展调度

### NORMAL

仍沿用 Day 5 主流程：

- 同模式内取等候区头车。
- 在同模式可用桩中选择最短完成时间的桩。
- 自动推进 `WAITING_AREA -> QUEUED -> CHARGING -> COMPLETED`。

### EXT_SINGLE_BATCH

单次联合调度：

- 仅在同模式内调度。
- 快充请求只进入快充桩，慢充请求只进入慢充桩。
- 不再强制按等候区排队号选头车。
- 在本批候选请求与本模式空位中选择总完成代价更小的组合。

当前实现策略：

- 对 `FAST` 与 `SLOW` 分别调度。
- 每次从当前等待集合与可用空位中选择 `workload + self_charge_time` 最小的组合。
- 组合代价相同时按服务时间、排队号、桩编号稳定排序。

### EXT_FULL_BATCH

批量调度：

- 不区分快充/慢充请求。
- 任意请求可进入任意类型充电桩。
- 使用实际目标桩功率计算服务时间。
- 每次从全站等待集合与全站空位中选择 `workload + self_charge_time` 最小的组合。

示例：慢充请求在 `EXT_FULL_BATCH` 下可以被分配到快充桩，详单仍按实际承载桩功率计费。

## 批量模拟接口

```http
POST /api/test/batch-simulate
```

输入结构：

```json
{
  "test_case_id": "CASE_001",
  "scenario": {
    "fast_station_count": 3,
    "slow_station_count": 2,
    "waiting_area_capacity": 6,
    "charging_queue_len": 2,
    "dispatch_mode": "NORMAL",
    "fault_dispatch_mode": "TIME_ORDER"
  },
  "users": [
    {
      "user_id": "U001",
      "request_time": "2026-04-19T10:00:00",
      "charge_mode": "FAST",
      "request_energy": 20.0
    }
  ],
  "events": [
    {
      "at": "2026-04-19T10:20:00",
      "type": "FAULT",
      "station_code": "FAST_01"
    }
  ]
}
```

场景字段已对齐冻结文档：

- `fast_station_count`
- `slow_station_count`
- `waiting_area_capacity`
- `charging_queue_len`
- `dispatch_mode`
- `fault_dispatch_mode`

返回结构：

```json
{
  "test_case_id": "CASE_001",
  "scenario": {
    "fast_station_count": 3,
    "slow_station_count": 2,
    "waiting_area_capacity": 6,
    "charging_queue_len": 2,
    "dispatch_mode": "NORMAL",
    "fault_dispatch_mode": "TIME_ORDER"
  },
  "summary": {
    "total_users": 1,
    "completed_users": 1,
    "rejected_users": 0,
    "avg_wait_seconds": 0.0,
    "avg_finish_seconds": 2400.0,
    "total_finish_seconds": 2400,
    "station_utilization": 0.2
  },
  "results": [
    {
      "user_id": "U001",
      "request_id": "REQ0001",
      "queue_number": "F1",
      "final_status": "COMPLETED",
      "estimated_wait_seconds": 0,
      "accepted": true,
      "detail": {
        "detail_id": "DETAIL0001",
        "station_code": "FAST_01",
        "actual_energy": 20.0,
        "total_fee": 34.5,
        "request_status": "COMPLETED"
      }
    }
  ]
}
```

增强输出字段：

- `results[].accepted`：是否被批量模拟接纳进入系统。
- `results[].final_status`：所有用户都有明确终态；未接纳用户为 `REJECTED_WAITING_AREA_FULL`。
- `results[].followup_request_id`：故障中断后生成的首个续充请求编号；无续充时为 `null`。
- `results[].followup_request_ids`：故障中断后生成的所有续充请求编号列表。
- `events_result[]`：事件回放结果摘要，包含 `at / type / station_code / result / dispatch_after_event`。

## 等候区容量约束

`waiting_area_capacity` 是批量模拟的有效约束，不再只是回显字段。

规则：

- 每个到达时刻先处理该时刻之前的事件与调度。
- 同一时刻到达的用户作为一个到达组处理，进入等候区前统一受全局 `waiting_area_capacity` 限制。
- 到达组内部按输入顺序尝试接纳。
- 已接纳用户进入 `WAITING_AREA`，随后再按当前 `dispatch_mode` 调度。
- 超容量用户不写入 `charge_request`，不生成 `request_id / queue_number / detail`。
- 超容量用户仍会出现在 `results` 中，便于验收回放。

超容量结果示例：

```json
{
  "user_id": "U002",
  "request_id": null,
  "queue_number": null,
  "final_status": "REJECTED_WAITING_AREA_FULL",
  "estimated_wait_seconds": 0,
  "accepted": false,
  "reject_reason": "WAITING_AREA_FULL",
  "detail": null
}
```

## Events 支持

当前支持事件：

- `FAULT`
- `RECOVER`
- `RESTORE`
- `START`
- `SHUTDOWN`
- `DISPATCH_MODE`
- `FAULT_DISPATCH_MODE`

事件字段：

- `at`：事件发生时间，ISO8601。
- `type`：事件类型。
- `station_code`：桩事件必填。
- `dispatch_mode`：`DISPATCH_MODE` 事件必填。
- `fault_dispatch_mode`：`FAULT_DISPATCH_MODE` 事件必填。

事件会复用 Day 9/10 已实现的管理端后端能力，因此故障中断、恢复重排、启动补位、关闭拒绝等语义保持一致。

## 实现说明

批量模拟会在当前数据库中重建临时验收环境：

1. 清空运行态表。
2. 按 `scenario` 重建充电桩。
3. 写入调度模式与故障策略。
4. 按 `users[].request_time` 生成用户、请求和 `F/T` 排队号。
5. 按模式执行调度。
6. 回放 `events`。
7. 持续推进至可完成请求全部结算并生成详单。
8. 输出 `summary` 与逐用户 `results`。

事件回放输出：

```json
{
  "events_result": [
    {
      "at": "2026-04-19T10:20:00",
      "type": "FAULT",
      "station_code": "FAST_01",
      "result": {
        "interrupted_request_id": "REQ0001",
        "remaining_request_id": "REQ0004"
      },
      "dispatch_after_event": {
        "dispatch_mode": "NORMAL",
        "scheduled_count": 1
      }
    }
  ]
}
```

## 代码入口

- `backend/app/routes/batch_simulate.py`
- `backend/app/routes/admin.py`
- `backend/app/routes/stations.py`：仅保留 `/api/stations/overview` 遗留只读兼容，正式桩状态接口仍是 `/api/admin/stations`
- `backend/app/services/queue_model.py`
- `backend/tests/test_frozen_contracts.py`

## 验证结果

```bash
python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts
```

结果：

```text
Ran 31 tests
OK
```

```bash
python -m unittest discover -s backend/tests
```

结果：

```text
Ran 33 tests
OK (skipped=2)
```

备注：使用本地应用工厂直接加载仓库中的旧 SQLite 文件时，可能因旧库 schema 与 V3 不兼容而初始化失败；测试环境使用临时 V3 schema，Day 11 能力已通过回归验证。
