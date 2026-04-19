# 成员B Day 12：部署支撑与最终回归清单

## 交付范围

Day 12 完成后端上线与彩排支撑：

- `GET /api/health`
- 部署环境变量读取
- 日志目录初始化
- 监听地址与端口配置
- systemd 启动入口对齐
- V3 全链路回归

## 健康检查

正式接口：

```http
GET /api/health
```

兼容接口：

```http
GET /health
```

响应结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "timestamp": "2026-04-19T16:54:45"
  }
}
```

说明：

- 已对齐 `部署上线手册.md` 的 `/api/health` 验收项。
- 响应使用项目统一成功 envelope。

## 部署配置读取

后端已读取以下环境变量：

| 环境变量 | 用途 | 默认值 |
|---|---|---|
| `FAST_CHARGING_PILE_NUM` | 快充桩数量 | `3` |
| `TRICKLE_CHARGING_PILE_NUM` | 慢充桩数量 | `2` |
| `WAITING_AREA_SIZE` | 等候区容量 | `6` |
| `CHARGING_QUEUE_LEN` | 每桩固定队列长度 | `2` |
| `DISPATCH_MODE` | 调度模式 | `NORMAL` |
| `FAULT_DISPATCH_MODE` | 故障调度策略 | `TIME_ORDER` |
| `DB_PATH` | SQLite 数据库路径 | `backend/charging_system.db` |
| `LISTEN_HOST` | Flask 监听地址 | `127.0.0.1` |
| `LISTEN_PORT` | Flask 监听端口 | `5000` |
| `LOG_DIR` | 后端日志目录 | `backend/logs` |
| `SECRET_KEY` | JWT 签名密钥 | 开发默认值 |
| `JWT_EXPIRATION_HOURS` | JWT 过期小时数 | `24` |

兼容说明：

- `DB_PATH` 优先级高于旧变量 `DATABASE_PATH`。
- `TEST_DATABASE_PATH` 仍用于测试配置。
- 新库初始化时会按环境变量生成桩数量、队列长度、调度模式和故障策略。

## 日志、监听与启动

已新增：

- `backend/.env.example`
- `backend/logs/.gitkeep`
- `backend/app/__main__.py`

启动方式：

```bash
python -m app
```

或开发方式：

```bash
python run.py
```

运行时行为：

- 自动创建 `DB_PATH` 父目录。
- 自动创建 `LOG_DIR`。
- 写入滚动日志文件 `backend.log`，单文件 5MB，保留 5 个轮转文件。
- 监听地址和端口来自 `LISTEN_HOST / LISTEN_PORT`。

这与 `部署上线手册.md` 中 systemd 模板保持一致：

```ini
ExecStart=/opt/charging/backend/venv/bin/python -m app
EnvironmentFile=/opt/charging/backend/.env
```

## 与部署手册核对

已对齐项：

- `/api/health` 返回 `code=0`。
- `.env` 字段与手册一致。
- Flask 默认监听 `127.0.0.1:5000`，适配 Nginx `/api/` 反代。
- SQLite 默认使用 `DB_PATH` 指向 `/var/lib/charging/charging_system.db`。
- 日志目录使用 `LOG_DIR=/var/log/charging`。
- 后端支持 `python -m app` 作为 systemd 启动入口。
- 当前部署方案不依赖 OSS。

注意项：

- 仓库默认 `backend/charging_system.db` 与 `backend/charging_system_test.db` 已刷新为 V3 schema。
- 启动时会检测 SQLite 是否满足 V3 必要表/字段；若发现旧 V1/V2 schema，会先将旧库重命名为 `.legacy-<timestamp>.bak`，再初始化 fresh V3 库。
- 若生产环境希望禁止自动重建旧库，可设置 `AUTO_REBUILD_INCOMPATIBLE_DB=0`，此时遇到不兼容 schema 会直接失败并提示迁移。
- 现阶段默认迁移策略仍遵守 Day 2 结论：迁账号，不迁旧业务运行态。

## 成员B V3 回归清单

### 认证与用户

- [x] 注册用户
- [x] 登录并获取 token
- [x] 查询 profile
- [x] 管理员查看用户列表
- [x] 管理员查看用户详情与历史详单
- [x] 管理员修改车辆电池容量
- [x] 用户存在活跃请求时禁止修改电池容量，返回 `1010`

### 请求主流程

- [x] 创建请求并分配 `F/T` 排队号
- [x] 单用户禁止创建第二个活跃请求
- [x] 状态查询返回 V3 字段
- [x] 等候区预测
- [x] 固定桩队列预测
- [x] 普通调度 `WAITING_AREA -> QUEUED -> CHARGING -> COMPLETED`
- [x] 最短完成时间选桩
- [x] 完成后队首提升

### 修改、取消、提前结束

- [x] 等候区修改模式并重新排队
- [x] 等候区修改电量并保留排队号
- [x] 等候区取消，最终态 `CANCELLED`，不生成详单
- [x] 排队中提前结束，生成 0 电量 `COMPLETED_EARLY` 详单
- [x] 充电中提前结束，按实际时长生成 `COMPLETED_EARLY` 详单

### 计费与详单

- [x] 正常完成生成详单
- [x] 峰平谷分时计费
- [x] 服务费 `0.8 × actual_energy`
- [x] `charge_fee / service_fee / total_fee` 字段正确
- [x] `COMPLETED / COMPLETED_EARLY / FAULT_INTERRUPTED` 详单状态正确

### 管理端与桩控制

- [x] 系统配置查询
- [x] 桩列表查询
- [x] 单桩队列查询
- [x] 管理员鉴权
- [x] 启动空闲桩并触发补位
- [x] 关闭空闲桩
- [x] 忙碌桩关闭返回 `1007`
- [x] 调度模式切换
- [x] 故障策略切换

### 故障与恢复

- [x] `PRIORITY` 故障链路
- [x] `TIME_ORDER` 故障链路
- [x] 故障中断生成 `FAULT_INTERRUPTED` 详单
- [x] 剩余电量生成新请求
- [x] 未开始车辆不生成故障详单
- [x] 恢复时按时间顺序重排

### 扩展调度与验收

- [x] `NORMAL`
- [x] `EXT_SINGLE_BATCH`
- [x] `EXT_FULL_BATCH`
- [x] `POST /api/test/batch-simulate`
- [x] 批量输入场景字段对齐冻结文档
- [x] 批量模拟支持事件
- [x] `waiting_area_capacity` 约束影响批量模拟结果
- [x] 批量模拟超容量用户输出 `REJECTED_WAITING_AREA_FULL`
- [x] 批量模拟输出 `events_result`
- [x] 故障中断原请求输出 `followup_request_id / followup_request_ids`
- [x] 批量模拟输出 `summary/results/detail`
- [x] V1/V2 旧服务已从 `backend/app/services` 移出到 `backend/remove/services`
- [x] 活跃枚举仅保留 V3 公开状态与模式
- [x] 遗留 `/api/stations/overview` 已改为 V3 schema 只读兼容接口

### 部署支撑

- [x] `GET /api/health`
- [x] 读取 `DB_PATH`
- [x] 读取 `LISTEN_HOST / LISTEN_PORT`
- [x] 读取 `LOG_DIR`
- [x] 自动创建日志目录
- [x] `python -m app` 启动入口
- [x] `.env.example`
- [x] 默认 SQLite 文件为 V3 schema
- [x] 旧 SQLite schema 自动备份并重建 fresh V3

## 回归命令与结果

目标契约回归：

```bash
python -m unittest backend.tests.test_auth_minimal backend.tests.test_frozen_contracts
```

结果：

```text
Ran 32 tests
OK
```

全量回归：

```bash
python -m unittest discover -s backend/tests
```

结果：

```text
Ran 34 tests
OK (skipped=2)
```

部署配置冒烟：

```text
GET /api/health -> code=0
DB_PATH -> 临时 SQLite 文件
LOG_DIR -> 临时 logs 目录
LISTEN_HOST/LISTEN_PORT -> 127.0.0.1 5012
charging_station -> FAST 2 / SLOW 1 / queue_capacity 3
scheduler_config -> EXT_SINGLE_BATCH / PRIORITY
```

默认库兼容性冒烟：

```text
backend/charging_system.db -> V3 schema
backend/charging_system_test.db -> V3 schema
create_app('development') + GET /api/health -> code=0
legacy SQLite temp db -> backed up to .legacy-<timestamp>.bak and rebuilt as V3
```
