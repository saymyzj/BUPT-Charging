# 成员B最终验收修改清单

> 适用对象：成员B  
> 职责范围：Flask 后端、SQLite、场景参数加载、批量模拟、详单/账单/报表输出、后端部署支撑  
> 检查依据：当前仓库 `docs/` 与 `docs/B-docs/`  
> 检查日期：2026-04-19

## 一、检查结论

成员B负责的 V3 后端主线能力已经基本落地，包括：

- 用户认证与请求主流程接口
- `WAITING_AREA -> QUEUED -> CHARGING -> COMPLETED` 主状态流
- 修改模式、修改电量、等候区取消、充电区提前结束
- 峰平谷计费与 `charge_fee / service_fee / total_fee` 详单输出
- 管理端系统配置、桩状态、单桩队列、用户维护、报表接口
- 故障策略、故障标记、恢复、重调度
- `NORMAL / EXT_SINGLE_BATCH / EXT_FULL_BATCH`
- `POST /api/test/batch-simulate`
- `GET /api/health`

现有回归命令：

```bash
python -m unittest discover -s backend/tests
```

当前结果：

```text
Ran 34 tests
OK (skipped=2)
```

但最终验收前仍存在若干必须处理或必须说明的差异点。

## 二、口径确认项

### 2.1 当前最终冻结口径

当前仓库文档以 V3.0 最终冻结口径为准：

- 批量模拟正式输入使用 `scenario + users`
- 正式场景字段为：
  - `fast_station_count`
  - `slow_station_count`
  - `waiting_area_capacity`
  - `charging_queue_len`
  - `dispatch_mode`
  - `fault_dispatch_mode`
- `waiting_area_capacity` 表示系统全局等候区容量
- 正式运行模型是“等候区 + 每桩固定队列”
- 详单/账单字段为：
  - `charge_fee`
  - `service_fee`
  - `total_fee`
- summary 至少需要：
  - `avg_wait_seconds`
  - `avg_finish_seconds`
  - `station_utilization`
  - 当前实现也已输出 `total_finish_seconds`

### 2.2 与旧口径冲突的内容

以下内容在当前 `docs/` 与 `docs/B-docs/` 中被视为废弃或非正式验收口径：

- `FAST_POOL / SLOW_POOL` 作为正式模型
- 中央等待池作为正式运行模型
- `UNIFORM_CAPACITY / STATION_SNAPSHOT` 作为正式运行模型
- `station_queue_capacity` 作为最终批量模拟字段
- `energy_fee / time_fee / occupancy_fee`
- 模拟支付、虚拟余额
- `CALLED / CONFIRMED / NO_SHOW / WAITING_TO_LEAVE / FAULT_REQUEUE`

若验收老师仍要求兼容 `station_queue_capacity`、`UNIFORM_CAPACITY`、`STATION_SNAPSHOT`，需要单独作为“外部兼容层”实现，不能将其描述为当前正式内部模型。

## 三、必须修改项

### P0-1 默认 SQLite 库与 V3 schema 不兼容

现象：

- 使用默认 `backend/charging_system.db` 直接创建 Flask 应用会失败。
- 使用默认 `backend/charging_system_test.db` 也存在旧 schema 不兼容风险。
- 当前测试通过依赖临时 V3 schema，并不能证明默认仓库数据库可直接用于验收启动。

影响：

- 部署验收或本地演示若不显式设置新的 `DB_PATH`，后端可能无法启动。

修改建议：

- [ ] 上线与演示统一使用全新 V3 SQLite 文件。
- [ ] 在部署手册和成员B最终说明中明确：不得直接复用旧 V1/V2 SQLite。
- [ ] 若必须保留旧库，补充迁移脚本或清库初始化流程。
- [ ] `.env.example` 中给出推荐 `DB_PATH`。
- [ ] 验收前执行一次 fresh DB 启动冒烟。

验收标准：

```bash
DB_PATH=<fresh-v3-db> python -m app
```

能够正常启动，且：

```http
GET /api/health
```

返回 `code=0`。

### P0-2 批量模拟未真正执行 `waiting_area_capacity` 容量约束

现象：

- `POST /api/test/batch-simulate` 要求输入 `waiting_area_capacity`。
- 当前代码会校验并回显该字段。
- 但批量插入用户时没有按全局等候区容量拒绝或标记超容量请求。

影响：

- 批量模拟场景中，`waiting_area_capacity` 可能只是展示字段，不是有效约束。
- 与“等候区容量是正式场景参数”的验收口径不完全一致。

修改建议：

- [ ] 在批量用户进入 `WAITING_AREA` 前检查全局等候区容量。
- [ ] 同一时刻多用户到达时，也要整体考虑容量。
- [ ] 超容量用户需要明确输出结果，例如：
  - 拒绝并返回错误；
  - 或在 `results` 中标记未接纳状态。
- [ ] 文档中明确批量模拟遇到等候区满时的处理规则。
- [ ] 增加容量边界测试。

建议测试用例：

```json
{
  "test_case_id": "CAPACITY_LIMIT",
  "scenario": {
    "fast_station_count": 1,
    "slow_station_count": 0,
    "waiting_area_capacity": 1,
    "charging_queue_len": 1,
    "dispatch_mode": "NORMAL",
    "fault_dispatch_mode": "TIME_ORDER"
  },
  "users": [
    {
      "user_id": "U001",
      "request_time": "2026-04-19T10:00:00",
      "charge_mode": "FAST",
      "request_energy": 20.0
    },
    {
      "user_id": "U002",
      "request_time": "2026-04-19T10:00:00",
      "charge_mode": "FAST",
      "request_energy": 20.0
    }
  ]
}
```

验收标准：

- `waiting_area_capacity` 必须影响模拟结果。
- 超容量行为必须稳定、可解释、可回放。

### P0-3 遗留 `/api/stations/overview` 与 V3 schema 不兼容

现象：

- 当前应用仍注册 `stations_bp`。
- `/api/stations/overview` 使用旧字段：
  - `station_type`
  - `status`
  - `scenario_id`
  - `system_scenario_config`
- V3 schema 中这些字段/表不作为当前主线存在。

影响：

- 该接口不是冻结验收正式接口，但如果前端或演示脚本误调用，会直接失败。

修改建议：

- [ ] 若该接口不再使用，取消注册或标记废弃。
- [ ] 若仍需保留，将其改为读取 V3 表结构：
  - `charging_station.station_code`
  - `charging_station.charge_mode`
  - `charging_station.station_status`
  - `charging_station.current_queue_length`
- [ ] 前端统一改用 `/api/admin/stations` 或正式冻结接口。

验收标准：

- 不存在可被误调用的旧 V2 崩溃接口。
- 最终说明中不再把 `/api/stations/overview` 作为正式接口。

## 四、需要确认后再改的项目

### P1-1 是否兼容 `station_queue_capacity`

当前最终文档使用 `charging_queue_len`。如果验收输入仍可能给 `station_queue_capacity`，建议做输入兼容：

- [ ] 当 `charging_queue_len` 缺失但存在 `station_queue_capacity` 时，将其映射为 `charging_queue_len`。
- [ ] 返回结果仍统一输出 `charging_queue_len`。
- [ ] 文档说明该兼容仅用于旧输入适配。

若严格按当前 docs 验收，则不需要实现。

### P1-2 是否兼容 `UNIFORM_CAPACITY / STATION_SNAPSHOT`

当前仓库中旧 `scenario_adapter.py` 仍存在，但测试已跳过，且代码与 V3 schema 不兼容。

若需要兼容外部输入：

- [ ] 不复用旧 `scenario_adapter.py` 的旧表结构逻辑。
- [ ] 新建或重写 V3 场景适配层。
- [ ] `UNIFORM_CAPACITY` 映射到统一 `charging_queue_len`。
- [ ] `STATION_SNAPSHOT` 映射到 V3 的 `charging_station + charge_request + charging_session` 初始状态。
- [ ] 内部仍保持“等候区 + 每桩固定队列”模型。

若严格按当前 docs 验收，则应说明它们不是正式运行模型。

## 五、建议清理项

### P2-1 清理或隔离旧枚举和旧服务

当前代码中仍保留若干旧概念：

- `FAST_POOL / SLOW_POOL`
- `PaymentStatus`
- `BillingMode`
- `CALLED / CONFIRMED / NO_SHOW / FAULT_REQUEUE`
- `waiting_pool.py`
- `scheduler_engine.py`
- `scenario_adapter.py`
- `scenario_parser.py`
- `config_manager.py` 中旧场景配置逻辑

建议：

- [ ] 不在最终报告中将这些旧模块描述为有效进度。
- [ ] 若时间允许，将旧模块移入 legacy 目录或加明确废弃注释。
- [ ] 确保正式接口不依赖旧表结构。
- [ ] 保留必要兼容代码时，写清“非验收主线”。

### P2-2 加强批量模拟输出字段

当前批量模拟已输出：

- `summary`
- `results`
- `detail`

建议继续补强：

- [ ] 对未完成/未接纳用户给出明确 `final_status`。
- [ ] 对事件回放输出 `events_result` 或调度日志摘要。
- [ ] 对故障中断后生成的新续充请求，在结果中建立关联。

## 六、最终验收前检查清单

### 6.1 接口检查

- [ ] `POST /api/auth/register`
- [ ] `POST /api/auth/login`
- [ ] `POST /api/request/create`
- [ ] `GET /api/request/status/{request_id}`
- [ ] `PUT /api/request/mode`
- [ ] `PUT /api/request/energy`
- [ ] `POST /api/request/cancel`
- [ ] `POST /api/request/stop`
- [ ] `GET /api/request/detail/{request_id}`
- [ ] `GET /api/admin/system/config`
- [ ] `PUT /api/admin/system/dispatch-mode`
- [ ] `PUT /api/admin/system/fault-dispatch-mode`
- [ ] `POST /api/admin/stations/{station_code}/start`
- [ ] `POST /api/admin/stations/{station_code}/shutdown`
- [ ] `POST /api/admin/stations/{station_code}/fault`
- [ ] `POST /api/admin/stations/{station_code}/recover`
- [ ] `GET /api/admin/stations`
- [ ] `GET /api/admin/stations/{station_code}/queue`
- [ ] `GET /api/admin/users`
- [ ] `GET /api/admin/users/{user_id}`
- [ ] `PUT /api/admin/users/{user_id}/battery-capacity`
- [ ] `GET /api/admin/reports?granularity=day|week|month`
- [ ] `POST /api/test/batch-simulate`
- [ ] `GET /api/health`

### 6.2 场景检查

- [ ] 普通调度 `NORMAL`
- [ ] 扩展调度 `EXT_SINGLE_BATCH`
- [ ] 扩展调度 `EXT_FULL_BATCH`
- [ ] 故障策略 `PRIORITY`
- [ ] 故障策略 `TIME_ORDER`
- [ ] 故障恢复按时间顺序重排
- [ ] 等候区取消终态为 `CANCELLED`
- [ ] 充电区取消/提前结束终态为 `COMPLETED_EARLY`
- [ ] 故障中断详单状态为 `FAULT_INTERRUPTED`
- [ ] 慢充功率为 `10kW`
- [ ] 详单字段完整
- [ ] 报表字段完整

### 6.3 批量模拟检查

- [ ] 输入结构为 `scenario + users`
- [ ] 支持 `events`
- [ ] 输出 `summary`
- [ ] 输出 `results`
- [ ] 输出用户 `detail`
- [ ] 输出 `avg_wait_seconds`
- [ ] 输出 `avg_finish_seconds`
- [ ] 输出 `total_finish_seconds`
- [ ] 输出 `station_utilization`
- [ ] `waiting_area_capacity` 能影响结果
- [ ] `charging_queue_len` 能影响每桩队列容量

### 6.4 部署检查

- [ ] 使用新的 V3 SQLite 文件
- [ ] 明确设置 `DB_PATH`
- [ ] 明确设置 `LOG_DIR`
- [ ] 后端可通过 `python -m app` 启动
- [ ] `/api/health` 返回 `code=0`
- [ ] 日志目录自动创建
- [ ] systemd 配置与部署手册一致
- [ ] Nginx `/api` 反代配置一致
- [ ] 发布前存在 SQLite 备份方案

## 七、建议修改顺序

1. 修复或规避默认 SQLite schema 不兼容问题。
2. 修复批量模拟 `waiting_area_capacity` 未生效问题。
3. 移除或修复 `/api/stations/overview` 旧接口。
4. 确认是否需要兼容 `station_queue_capacity`。
5. 确认是否需要兼容 `UNIFORM_CAPACITY / STATION_SNAPSHOT`。
6. 补充对应测试。
7. 更新成员B最终说明与部署说明。
8. 重新运行全量回归。

## 八、最终报告表述建议

可以表述为：

> 成员B负责的 Flask 后端已按 V3 冻结文档完成认证、请求状态机、计费详单、管理端接口、故障恢复、扩展调度、批量模拟和部署支撑。账单口径不单独建表，而是由详单字段 `charge_fee / service_fee / total_fee` 承载。批量模拟正式输入为 `scenario + users`，核心场景字段使用 `charging_queue_len`。旧 `FAST_POOL / SLOW_POOL`、旧支付与旧计费字段不作为最终验收口径。

不建议表述为：

> 系统内部正式使用 `FAST_POOL / SLOW_POOL`。

也不建议表述为：

> 批量模拟正式字段是 `station_queue_capacity`。

除非后续明确新增兼容层并通过测试。
