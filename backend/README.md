# 智能充电桩调度计费系统 - 后端说明

> 文档版本：V2.0  
> 更新日期：2026-04-02  
> 适用范围：当前 `develop` 分支真实后端实现

---

## 1. 文档定位

本文档用于说明当前后端在 `develop` 分支上的真实状态，作为组内统一口径。

请与以下文档配合阅读：

- [系统验收接口与测试输入规范说明](/Users/zhoujia/code/SE/ChargingPile/docs/系统验收接口与测试输入规范说明.md)
- [冻结接口文档](/Users/zhoujia/code/SE/ChargingPile/docs/冻结接口文档.md)
- [调度模块输入输出约定](/Users/zhoujia/code/SE/ChargingPile/docs/调度模块输入输出约定.md)
- [Fix本地联调](/Users/zhoujia/code/SE/ChargingPile/docs/04-02/Fix本地联调.md)

---

## 2. 当前已完成内容

### 2.1 场景与基础能力

- 已支持动态场景配置：
  - 快充桩数量
  - 慢充桩数量
  - 全局共享等待区容量
  - `UNIFORM_CAPACITY`
  - `STATION_SNAPSHOT`
- 已实现快充/慢充双等待池
- 已实现调度模块最小闭环
- 已实现批量模拟基础执行引擎

### 2.2 当前可用接口

- `GET /health`
- `POST /api/request/create`
- `GET /api/request/status/{request_id}`
- `POST /api/request/cancel_queue`
- `POST /api/request/confirm_arrival`
- `POST /api/request/interrupt_charge`
- `POST /api/request/confirm_leave`
- `GET /api/request/result/{request_id}`
- `POST /api/request/pay`
- `GET /api/stations/overview`
- `POST /api/batch/simulate`

### 2.3 当前可演示主线

- 用户提交充电请求
- 返回预计等待/开始/结束时间
- 状态轮询
- 叫号与确认到场
- 充电结束 / 中断后结算
- 详单与账单生成
- 支付
- 批量模拟返回 `summary + results`

---

## 3. 当前仍为简化实现的部分

- 调度算法是课程项目阶段的最小可用版本，不是最终优化版
- 状态自动推进仍有为演示闭环服务的简化处理
- 管理端接口仍未完整接入真实数据
- 批量模拟已可返回真实结构，但仍是阶段性实现

---

## 4. 本地启动

### 4.1 安装依赖

```bash
cd /Users/zhoujia/code/SE/ChargingPile/backend
pip install -r requirements.txt
```

### 4.2 启动服务

建议使用临时数据库启动：

```bash
cd /Users/zhoujia/code/SE/ChargingPile/backend
DATABASE_PATH=/tmp/charging_fix_20260402.db python3 run.py
```

服务默认监听：

- `http://127.0.0.1:8080`

### 4.3 健康检查

```bash
curl http://127.0.0.1:8080/health
```

预期返回：

```json
{
  "status": "ok",
  "timestamp": "2026-04-02T21:00:00"
}
```

---

## 5. 当前后端目录重点

- [run.py](/Users/zhoujia/code/SE/ChargingPile/backend/run.py)
- [request.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/routes/request.py)
- [batch_simulate.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/routes/batch_simulate.py)
- [health.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/routes/health.py)
- [scheduler_engine.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/services/scheduler_engine.py)
- [waiting_pool.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/services/waiting_pool.py)
- [config_manager.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/services/config_manager.py)
- [scenario_adapter.py](/Users/zhoujia/code/SE/ChargingPile/backend/app/services/scenario_adapter.py)

---

## 6. 当前统一结论

- 后端当前已经具备最小闭环演示能力
- 当前后端口径已经切换为“最终验收 / 系统验收”
- 不再以旧版“联合验收”文档和阶段表述作为实现依据
