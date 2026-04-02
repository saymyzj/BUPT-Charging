# Fix本地联调

## 一、本次收口做了什么

### 1. 后端收口

修改文件：

- `backend/app/routes/health.py`
- `backend/app/routes/request.py`
- `backend/app/utils/db.py`
- `backend/app/services/waiting_pool.py`

本次修复点：

1. `/health` 改为裸结构返回，与冻结接口文档一致。
2. 数据库初始化优先加载 `init_schema_v2.sql`，避免本地联调仍走旧表结构。
3. 修复 `waiting_pool.py` 中场景配置同时混用 `dict` / 对象属性导致的创建请求报错。
4. `status` 接口补充联调必需字段：
   - `submit_time`
   - `charge_mode`
   - `request_energy`
   - `estimated_start_time`
   - `estimated_finish_time`
   - `charge_start_time`
   - `charge_end_time`
   - `actual_energy`
5. 在状态查询前加入简化自动推进：
   - `WAITING -> CALLED`
   - `CHARGING -> COMPLETED`
6. `confirm_arrival` 收口为：
   - 确认到场成功后直接进入 `CHARGING`
   - 创建 `charging_session`
   - 更新充电桩状态
7. `interrupt_charge` 调整为中断后进入待离场语义，便于结算链路继续向下走。
8. `confirm_leave` 扩大到允许 `INTERRUPTED` 状态完成离场。

### 2. 前端收口

修改文件：

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/api/request.js`
- `frontend/src/api/charging.js`
- `frontend/src/router/index.js`
- `frontend/src/views/user/Workspace.vue`
- `frontend/src/views/user/Task.vue`

本次修复点：

1. `vue-router` 版本改为 `^4.2.0`，并同步锁文件。
2. 清理 `request.js` 中残留的无效占位内容，保留统一响应返回。
3. `charging.js` 去掉重复 `/api` 前缀，改成和 `baseURL: /api` 一致的调用方式。
4. 根路由 `/` 改回跳转 `/login`。
5. `Workspace.vue` 提交请求后保存真实的：
   - `estimated_wait_seconds`
   - `estimated_start_time`
   - `estimated_finish_time`
6. `Task.vue` 从“前端本地推进状态”改为“以后端状态为主”：
   - 轮询真实 `status`
   - 消费真实预计等待/开始/结束时间
   - 消费真实 `station_id`
   - 消费真实 `queue_position`
   - 消费真实详单/账单
7. 保留页面结构和交互外观，但把状态推进主逻辑切回后端。
8. 给未完善功能补了显式提示，避免“点了没反应”：
   - 管理端总览中的故障 / 恢复 / 手动叫号 / 导出
   - 系统配置中的保存按钮
   - 统计分析中的时间筛选
   - 用户管理中的导出 / 详情
   - 账户中心中的充值 / 修改密码 / 车辆管理 / 账单明细 / 导出
   - 登录页中的注册 / 忘记密码

## 二、本地联调结果

### 0. 如何运行

#### 后端启动

在终端 1 执行：

```bash
cd /Users/zhoujia/code/SE/ChargingPile/backend
DATABASE_PATH=/tmp/charging_fix_20260402.db python3 run.py
```

启动后可先访问：

- `http://127.0.0.1:8080/health`

若返回：

```json
{
  "status": "ok",
  "timestamp": "..."
}
```

说明后端已正常启动。

#### 前端启动

在终端 2 执行：

```bash
cd /Users/zhoujia/code/SE/ChargingPile/frontend
npm install
npm run dev
```

浏览器打开：

- `http://127.0.0.1:3000`
或
- `http://localhost:3000`

#### 浏览器建议演示顺序

1. 进入 `/login`
2. 输入任意非 `admin` 用户名登录
3. 进入 `/user/workspace`
4. 提交一个小电量请求，建议：
   - 快充 `0.1 kWh`
   - 或快充 `1 kWh`
5. 跳转到 `/user/task`
6. 查看预计等待、叫号倒计时、充电、结算
7. 依次测试：
   - 确认到场
   - 确认离场
   - 支付

如需看管理端演示，可登录名输入 `admin`。
注意：管理端当前仍以静态展示为主，未完善按钮会弹出“功能未完善”提示。

### 1. 后端语法检查

已通过：

```bash
python3 -m compileall backend/app/routes/request.py backend/app/routes/health.py backend/app/utils/db.py backend/app/services/scheduler_engine.py
```

### 2. 本地接口联调

后端以临时数据库启动：

```bash
DATABASE_PATH=/tmp/charging_fix_20260402.db python3 run.py
```

已验证成功：

1. `GET /health`
2. `POST /api/request/create`
3. `GET /api/request/status/{id}`
4. `POST /api/request/confirm_arrival`
5. `POST /api/request/confirm_leave`
6. `GET /api/request/result/{id}`
7. `POST /api/request/pay`
8. `POST /api/batch/simulate`

联调观测结论：

- 创建请求已返回真实预测结果
- 状态查询已能返回前端任务页需要的关键字段
- 确认到场后可进入充电
- 充电结束后可进入结算
- 详单/账单可生成
- 支付可成功
- 批量模拟可返回 `summary + results`

### 3. 前端构建验证

已通过：

```bash
npm install
npm install --package-lock-only
npm run build
```

构建结果：

- 前端可完成生产构建
- `Task.vue` 修复后未出现编译错误

## 三、当前已完成、可演示的功能

### 1. 用户端最小闭环

当前可真实演示：

1. 登录页入口跳转
2. 工作台提交充电请求
3. 后端返回真实预测结果：
   - `request_id`
   - `estimated_wait_seconds`
   - `estimated_start_time`
   - `estimated_finish_time`
4. 当前任务页轮询真实状态
5. 叫号阶段倒计时展示
6. 确认到场
7. 充电阶段展示
8. 确认离场
9. 详单 / 账单生成
10. 支付

### 2. 后端接口与调度演示

当前可真实演示：

1. `GET /health`
2. `POST /api/request/create`
3. `GET /api/request/status/{id}`
4. `POST /api/request/confirm_arrival`
5. `POST /api/request/interrupt_charge`
6. `POST /api/request/confirm_leave`
7. `GET /api/request/result/{id}`
8. `POST /api/request/pay`
9. `POST /api/batch/simulate`

### 3. 批量模拟

当前可真实演示：

1. 接收正式 `scenario + users` 输入
2. 返回 `summary + results`
3. 返回核心统计字段：
   - `total_users`
   - `completed_users`
   - `avg_wait_seconds`
   - `avg_finish_seconds`
   - `total_finish_seconds`
   - `station_utilization`

### 4. 管理端

当前可演示：

1. 管理端页面整体 UI
2. 总览 / 记录中心 / 系统配置 / 统计分析 / 用户管理的静态展示
3. 未完善功能的明确提示

## 四、当前仍保留的简化

1. 当前状态推进仍是“课程项目最小闭环”，不是完整工业级状态机。
2. 自动叫号、自动结束充电逻辑目前是为了本地联调和演示闭环做的最小化实现。
3. 管理端仍主要是静态展示页，未做完整真实接口联调。
4. 批量模拟已经能返回真实结构，但仍采用当前阶段允许的简化策略。

## 五、下一步要做什么

1. 用真实浏览器完整录一遍用户端闭环。
2. 再检查一轮页面文案和状态展示细节。
3. 如时间允许，继续接管理端真实接口。
4. 如时间允许，补一版批量模拟结果展示页。
