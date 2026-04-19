# 成员B Day 6：分时计费与详单

## 1. 目标

Day 6 的目标是完成 V3 正式计费口径与详单输出，落实以下能力：

- 以 `request_detail` 作为唯一费用事实源
- 按峰/平/谷分时电价计算 `charge_fee`
- 按统一单价计算 `service_fee`
- 输出 `GET /api/request/detail/{request_id}`

## 2. 本日完成内容

### 2.1 V3 详单模型已接入主流程

当前后端已正式使用 `request_detail` 表承接详单，不再沿用旧 `billing_record` 作为正式结算模型。

详单当前会在请求进入以下终态后自动生成：

- `COMPLETED`

已实现字段与冻结文档对齐：

- `detail_id`
- `detail_generated_at`
- `station_code`
- `actual_energy`
- `charge_duration_seconds`
- `start_time`
- `stop_time`
- `charge_fee`
- `service_fee`
- `total_fee`
- `request_status`

### 2.2 分时计费规则已落地

当前已按冻结文档实现分时电价：

- 峰时：`10:00-15:00`、`18:00-21:00`，单价 `1.0`
- 平时：`07:00-10:00`、`15:00-18:00`、`21:00-23:00`，单价 `0.7`
- 谷时：`23:00-07:00`，单价 `0.4`

计费实现规则：

1. 读取 `start_time` 与 `stop_time`
2. 按峰/平/谷边界切分充电时段
3. 每段按 `功率 × 秒数 ÷ 3600` 计算实际度数
4. 每段度数乘对应电价后求和为 `charge_fee`

同时：

- `service_fee = 0.8 × actual_energy`
- `total_fee = charge_fee + service_fee`

### 2.3 查询详单接口已完成

已实现：

- `GET /api/request/detail/{request_id}`

接口行为如下：

- 仅请求所属用户本人或管理员可查询
- 若请求不存在，返回错误
- 若详单尚未生成，返回“详单尚未生成”
- 若请求已完成但详单缺失，会在查询时补生成后返回

### 2.4 调度完成事件已接入详单生成

当前 `NORMAL` 调度主流程在请求完成时，会自动：

- 更新 `charge_request` 为 `COMPLETED`
- 回写 `actual_energy`
- 回写 `charge_stop_time`
- 回写 `charge_duration_seconds`
- 更新 `charging_session`
- 生成 `request_detail`

因此 Day 5 与 Day 6 已形成完整闭环：

- `QUEUED -> CHARGING -> COMPLETED -> request_detail`

## 3. 主要实现位置

本次主实现集中在：

- `backend/app/services/billing_service.py`
- `backend/app/services/queue_model.py`
- `backend/app/routes/request.py`

其中：

- `billing_service.py` 负责 V3 分时计费与详单生成/查询
- `queue_model.py` 负责在完成事件中触发详单落库
- `request.py` 负责暴露 `GET /api/request/detail/{request_id}`

## 4. 测试结果

本日新增并通过的重点校验包括：

- 请求完成后自动生成详单
- 详单接口返回字段与冻结文档一致
- 跨平时/峰时时段的充电请求按分段计费正确计算

关键验证场景：

- `2026-04-19 09:50:00` 开始快充 `20.0 kWh`
- `30 kW` 下充电 40 分钟，到 `10:30:00` 完成
- 其中：
  - `09:50-10:00` 为平时，计 `5 kWh × 0.7 = 3.5`
  - `10:00-10:30` 为峰时，计 `15 kWh × 1.0 = 15.0`
  - `charge_fee = 18.5`
  - `service_fee = 16.0`
  - `total_fee = 34.5`

执行结果：

- `python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts`
  - 9 个测试通过
- `python -m unittest discover -s backend/tests`
  - 全量通过，结果为 `OK (skipped=2)`

## 5. Day 6 结论

Day 6 已完成的正式边界：

- V3 分时计费已落地
- `request_detail` 已成为正式详单来源
- 查询详单接口已可用
- 完成请求可自动生成详单并返回费用结果

仍留给后续阶段的内容：

- `COMPLETED_EARLY` 详单生成
- `FAULT_INTERRUPTED` 详单生成
- Day 7 管理员系统配置与桩状态查看接口
