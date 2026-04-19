# 成员B Day 7：管理员基础接口

## 1. 目标

Day 7 的目标是完成增量一阶段管理员侧最小必需接口，具体包括：

- `GET /api/admin/system/config`
- `GET /api/admin/stations`
- `GET /api/admin/stations/{station_code}/queue`

## 2. 本日完成内容

### 2.1 管理员鉴权已接入

当前 Day 7 管理员接口已统一接入管理员鉴权：

- 必须携带有效登录令牌
- 仅 `role=ADMIN` 用户可访问
- 普通用户访问会返回权限错误

### 2.2 系统配置查看接口已完成

已实现：

- `GET /api/admin/system/config`

当前返回字段与冻结文档对齐：

- `fast_station_count`
- `slow_station_count`
- `waiting_area_capacity`
- `charging_queue_len`
- `dispatch_mode`
- `fault_dispatch_mode`

其中：

- 快慢充桩数量直接从 `charging_station` 统计
- 等候区容量来自运行配置
- 调度模式与故障策略来自 `scheduler_config`

### 2.3 全部充电桩状态接口已完成

已实现：

- `GET /api/admin/stations`

每个桩当前返回字段为：

- `station_code`
- `charge_mode`
- `station_status`
- `current_request_id`
- `queue_length`
- `total_charge_count`
- `total_charge_seconds`
- `total_charge_energy`

说明：

- `current_request_id` 返回的是公开请求编号，如 `REQ0001`
- `queue_length` 直接体现当前固定桩队列长度
- 统计字段复用了 Day 5/Day 6 已维护的桩累计运行数据

### 2.4 单桩队列查看接口已完成

已实现：

- `GET /api/admin/stations/{station_code}/queue`

返回结构为：

- `station_code`
- `queue`

其中 `queue` 内每项包含：

- `user_id`
- `battery_capacity`
- `request_energy`
- `queue_number`
- `queue_wait_seconds`

说明：

- 队列包含当前 `CHARGING` 和 `QUEUED` 请求
- 正在充电的队首车辆 `queue_wait_seconds = 0`
- 后续排队车辆使用当前 `estimated_wait_seconds`

## 3. 主要实现位置

本次主实现集中在：

- `backend/app/routes/admin.py`
- `backend/tests/test_frozen_contracts.py`

其中 `admin.py` 已正式切离旧场景配置/等待池口径，改为 V3 运行态查询接口。

## 4. 测试结果

本日新增并通过的重点校验包括：

- 管理员可查看系统配置快照
- 管理员可查看全部充电桩状态
- 管理员可查看单桩固定队列车辆信息
- 普通用户访问管理员接口会被拒绝

执行结果：

- `python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts`
  - 13 个测试通过
- `python -m unittest discover -s backend/tests`
  - 全量通过，结果为 `OK (skipped=2)`

## 5. Day 7 结论

Day 7 已完成的正式边界：

- 管理员基础查看接口已可用
- 管理员侧字段已对齐 V3 冻结文档
- 管理端查看能力已能直接反映 Day 5/Day 6 的运行态和统计结果

仍留给后续阶段的内容：

- Day 8：修改模式 / 修改电量 / 取消 / 提前结束
- Day 9：故障标记、故障恢复、故障调度策略
- Day 10：启动/关闭充电桩、用户维护、报表接口
