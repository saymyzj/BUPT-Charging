# 成员B Day 10：管理端后端能力闭环

## 交付范围

Day 10 完成增量二与增量三的管理端后端能力：

- `POST /api/admin/stations/{station_code}/start`
- `POST /api/admin/stations/{station_code}/shutdown`
- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `PUT /api/admin/users/{user_id}/battery-capacity`
- `GET /api/admin/reports?granularity=day|week|month`

## 充电桩启动/关闭

### 启动充电桩

```http
POST /api/admin/stations/{station_code}/start
```

返回核心字段：

```json
{
  "station_code": "SLOW_02",
  "station_status": "RUNNING",
  "scheduled": []
}
```

规则：

- 仅管理员可调用。
- 目标桩不存在返回 `1002`。
- 启动 `SHUTDOWN` 桩后，该桩恢复为 `RUNNING`。
- 启动后会触发同模式故障重排集合补位，再触发普通 `NORMAL` 补位。
- 若目标桩处于 `FAULT`，当前实现复用故障恢复链路，等价于恢复该桩。
- 请求体可选 `start_time`，用于验收与测试的确定性回放；不传则使用当前时间。

### 关闭充电桩

```http
POST /api/admin/stations/{station_code}/shutdown
```

返回核心字段：

```json
{
  "station_code": "SLOW_02",
  "station_status": "SHUTDOWN"
}
```

规则：

- 仅管理员可调用。
- 目标桩不存在返回 `1002`。
- 严格按冻结文档执行：仅允许该桩空闲且队列为空时关闭。
- 如果存在 `CHARGING` 或 `QUEUED` 请求，返回 `1007`。
- 关闭成功后，该桩不再参与普通调度和状态预测。
- 请求体可选 `shutdown_time`，用于验收与测试的确定性回放；不传则使用当前时间。

## 用户与车辆维护

### 查看用户列表

```http
GET /api/admin/users?page=1&page_size=20
```

返回结构：

```json
{
  "total": 2,
  "page": 1,
  "page_size": 20,
  "users": [
    {
      "user_id": "U001",
      "username": "user_001",
      "battery_capacity": 60.0,
      "role": "USER",
      "created_at": "2026-04-19T10:00:00",
      "has_active_request": false
    }
  ]
}
```

说明：

- `has_active_request` 以 `WAITING_AREA / QUEUED / CHARGING` 为活跃状态集合。
- 支持分页，`page_size` 最大 100。

### 查看单个用户

```http
GET /api/admin/users/{user_id}
```

返回结构：

```json
{
  "user_id": "U001",
  "username": "user_001",
  "battery_capacity": 60.0,
  "role": "USER",
  "created_at": "2026-04-19T10:00:00",
  "has_active_request": false,
  "historical_details": []
}
```

说明：

- `historical_details` 按 `detail_generated_at` 倒序返回该用户历史详单。
- 为兼容 `openapi.yaml` 的旧字段名，响应中同时保留 `details`，内容与 `historical_details` 一致。

### 修改车辆电池容量

```http
PUT /api/admin/users/{user_id}/battery-capacity
```

请求体：

```json
{
  "battery_capacity": 75.0
}
```

返回：

```json
{
  "user_id": "U001",
  "battery_capacity": 75.0,
  "updated": true
}
```

规则：

- 用户不存在返回 `1002`。
- `battery_capacity <= 0` 返回 `1001`。
- 用户存在活跃请求时返回 `1010`。
- 修改成功后写入 `scheduler_event_log`，事件类型为 `ADMIN_UPDATE_BATTERY_CAPACITY`。

## 报表

```http
GET /api/admin/reports?granularity=day|week|month
```

返回结构：

```json
{
  "granularity": "day",
  "rows": [
    {
      "time_key": "2026-04-19",
      "station_code": "FAST_01",
      "total_charge_count": 1,
      "total_charge_seconds": 2400,
      "total_charge_energy": 20.0,
      "total_charge_fee": 18.5,
      "total_service_fee": 16.0,
      "total_fee": 34.5
    }
  ]
}
```

聚合来源：

- 只统计 `request_detail`。
- `total_charge_count` 统计所有已生成详单，包括 `COMPLETED / COMPLETED_EARLY / FAULT_INTERRUPTED`。
- 时间粒度基于 `detail_generated_at`。
- `day`：`YYYY-MM-DD`。
- `week`：ISO 周，`YYYY-Www`。
- `month`：`YYYY-MM`。
- 金额与电量按桩、按粒度汇总后保留两位小数。

## 代码入口

- `backend/app/routes/admin.py`
- `backend/app/services/queue_model.py`
- `backend/tests/test_frozen_contracts.py`

## 验证结果

```bash
python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts
```

结果：

```text
Ran 27 tests
OK
```

```bash
python -m unittest discover -s backend/tests
```

结果：

```text
Ran 29 tests
OK (skipped=2)
```
