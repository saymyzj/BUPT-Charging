# 成员B Day 9：故障策略与故障恢复

## 交付范围

Day 9 完成增量二故障链路的后端主流程：

- `PUT /api/admin/system/fault-dispatch-mode`
- `POST /api/admin/stations/{station_code}/fault`
- `POST /api/admin/stations/{station_code}/recover`
- `PRIORITY` 故障策略
- `TIME_ORDER` 故障策略
- 故障恢复按时间顺序重排

## 接口冻结

### 1. 切换故障调度策略

```http
PUT /api/admin/system/fault-dispatch-mode
```

请求体：

```json
{
  "fault_dispatch_mode": "PRIORITY"
}
```

合法值：

- `PRIORITY`
- `TIME_ORDER`

返回：

```json
{
  "fault_dispatch_mode": "PRIORITY"
}
```

说明：

- 仅管理员可调用。
- 非法策略返回 `1001`。
- `GET /api/admin/system/config` 会同步返回最新 `fault_dispatch_mode`。

### 2. 上报充电桩故障

```http
POST /api/admin/stations/{station_code}/fault
```

请求体：

```json
{
  "fault_time": "2026-04-19T10:20:00"
}
```

说明：

- `fault_time` 用于验收场景和测试的确定性回放；生产调用未传时使用当前时间。
- 若当前车正在充电且已产生实际电量，则原请求转为 `FAULT_INTERRUPTED` 并生成详单。
- 原请求剩余电量会生成一个新请求，重新进入等待区尾部，使用新的 `request_id` 与 `queue_number`。
- 故障桩中未开始充电的车辆不生成详单，会进入故障重排集合。
- 故障桩状态转为 `FAULT`，不再参与普通调度。

返回核心字段：

```json
{
  "station_code": "FAST_01",
  "station_status": "FAULT",
  "fault_dispatch_mode": "TIME_ORDER",
  "interrupted_request_id": "REQ0001",
  "remaining_request_id": "REQ0007",
  "requeued_request_ids": ["REQ0002", "REQ0004", "REQ0006"],
  "scheduled": [
    {
      "request_id": "REQ0002",
      "target_station_code": "FAST_02"
    }
  ]
}
```

### 3. 恢复充电桩

```http
POST /api/admin/stations/{station_code}/recover
```

请求体：

```json
{
  "recover_time": "2026-04-19T10:30:00"
}
```

说明：

- `recover_time` 用于验收场景和测试的确定性回放；生产调用未传时使用当前时间。
- 恢复时不区分 `PRIORITY / TIME_ORDER`，统一按时间顺序重排。
- 参与恢复重排的是同模式下尚未开始充电的入桩排队车辆，以及故障期间遗留的故障重排等待车辆。
- 若不存在待重排车辆，恢复后的桩会回到 `NORMAL` 普通调度补位。

返回核心字段：

```json
{
  "station_code": "FAST_01",
  "station_status": "RUNNING",
  "requeued_request_ids": ["REQ0002", "REQ0004"],
  "scheduled": [
    {
      "request_id": "REQ0002",
      "target_station_code": "FAST_01"
    }
  ]
}
```

## 策略落地

### PRIORITY

`PRIORITY` 策略只把故障桩中尚未开始充电的车辆放入故障重排集合。集合内车辆会优先于普通等待区车辆补入同模式可用桩，目标桩仍按“最短完成时间”选择。

已充电车辆处理规则：

- 当前充电车辆转为 `FAULT_INTERRUPTED`。
- 按故障时刻生成分时计费详单。
- 剩余电量新建请求，重新进入普通等待区尾部。

未开始车辆处理规则：

- 不生成 `FAULT_INTERRUPTED` 详单。
- 保留原 `request_id` 与 `queue_number`。
- 进入故障重排集合，等待同模式可用桩。

### TIME_ORDER

`TIME_ORDER` 策略会统一抽取同模式所有桩队列中尚未开始充电的车辆，按排队号顺序重排。

参与集合示例：

- 故障桩尾车：`F2`
- 其他同模式桩尾车：`F4 / F6`
- 不包含其他桩正在充电的车：`F3 / F5`
- 不包含故障中已生成剩余电量新请求的原充电车，该新请求回普通等待区尾部

装配规则：

- 按 `F2 < F4 < F6` 的排队号顺序取车。
- 每辆车按当前可用桩的最短完成时间选桩。
- 若容量不足，剩余车辆留在故障重排等待集合，优先级仍高于普通等待区。

### 故障恢复

恢复时统一执行时间顺序重排：

- 先恢复桩状态为 `RUNNING`。
- 结算同模式运行桩在恢复时刻前可完成的请求。
- 抽取同模式中尚未开始充电的固定桩排队车辆。
- 合并故障重排等待集合。
- 按排队号顺序重新装配到所有运行中的同模式桩。
- 重排完成后再执行普通 `NORMAL` 补位。

## 场景对照

已用契约测试覆盖 `docs/故障与扩展场景指南.md` 中 Day 9 主链：

- `F-CASE-01`：`PRIORITY` 下队首故障，当前车生成 `FAULT_INTERRUPTED` 详单，故障桩尾车优先补位。
- `F-CASE-04`：`TIME_ORDER` 下队首故障，`F2 / F4 / F6` 按排队号统一重排。
- `F-CASE-07`：故障恢复后，尚未开始车辆合并恢复桩空位，按时间顺序重排。

本阶段没有实现扩展调度 `EXT_SINGLE_BATCH / EXT_FULL_BATCH` 的完整优化算法；Day 9 仅保证故障链路在 V3 普通固定队列模型下可运行。

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
Ran 22 tests
OK
```

```bash
python -m unittest discover -s backend/tests
```

结果：

```text
Ran 24 tests
OK (skipped=2)
```
