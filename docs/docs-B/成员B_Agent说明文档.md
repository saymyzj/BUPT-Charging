# 成员B Agent说明文档

## 1. 文档用途

本文档用于给 AI / Agent 提供成员B当前阶段的唯一工作上下文。  
AI 在协助成员B时，必须：

- 严格以当前 `docs/` 为唯一依据
- 不再引用旧“中央等待池 + 动态分配”口径
- 明确成员B当前真实进度
- 明确成员B接下来要做什么
- 明确成员B从今天到项目完成的每日任务

---

## 2. 当前唯一有效依据

后续分析、规划、实现、联调、验收、上线一律以当前 `docs/` 为准：

1. `docs/需求调整与重构冻结说明.md`
2. `docs/冻结接口文档.md`
3. `docs/功能设计.md`
4. `docs/增量设计.md`
5. `docs/小组分工指南.md`
6. `docs/架构设计.md`
7. `docs/调度算法.md`
8. `docs/调度模块输入输出约定.md`
9. `docs/系统验收接口与测试输入规范说明.md`
10. `docs/部署上线手册.md`
11. `docs/故障与扩展场景指南.md`
12. `docs/openapi.yaml`

### 2.1 旧口径处理规则

根据 `docs/需求调整与重构冻结说明.md`：

- 旧文档已整体归档到 `docs_已弃用/`
- 旧文档只用于历史追溯
- 旧文档不再作为当前实现、联调、验收和上线依据

因此 AI 必须把以下旧概念视为**已废弃**：

- 中央等待池
- `FAST_POOL` / `SLOW_POOL`
- `CALLED` / `CONFIRMED` / `NO_SHOW` / `WAITING_TO_LEAVE` / `FAULT_REQUEUE`
- `energy_fee / time_fee / occupancy_fee`
- 模拟支付 / 虚拟余额
- `UNIFORM_CAPACITY` / `STATION_SNAPSHOT` 作为正式运行模型

---

## 3. V3.0 新口径的核心结论

这是 AI 必须先理解的内容。

### 3.1 正式运行模型

系统正式采用：

- 等候区
- 充电区
- 每个充电桩一条固定长度为 `ChargingQueueLen` 的队列

正式模型**不再**是中央等待池。

### 3.2 排队号语义

- 快充用户生成 `F1、F2、...`
- 慢充用户生成 `T1、T2、...`
- 同模式排队号单调递增，不复用
- 排队号是普通调度、故障调度、用户展示、验收回放的唯一顺序依据

### 3.3 普通调度

普通模式下：

1. 只在对应模式内调度
2. 当某同模式充电桩队列出现空位时，从该模式等候区取排队号最靠前车辆
3. 将该车辆加入能使其“等待时间 + 自身充电时间”最短的同模式桩队列

### 3.4 故障调度

系统正式支持两种故障策略：

- `PRIORITY`
- `TIME_ORDER`

故障恢复后，统一按**时间顺序**重排。

### 3.5 扩展调度

系统正式支持三种调度模式：

- `NORMAL`
- `EXT_SINGLE_BATCH`
- `EXT_FULL_BATCH`

### 3.6 计费口径

账单正式口径为：

- `charge_fee`
- `service_fee`
- `total_fee`

分时电价：

- 峰时：`1.0`
- 平时：`0.7`
- 谷时：`0.4`
- 服务费单价：`0.8`

### 3.7 部署上线口径

部署已纳入冻结范围，正式方案为：

- 单台阿里云 ECS 一体化部署
- `Nginx` 托管前端并反代 `/api`
- Flask 后端运行在内网端口
- SQLite 继续保留
- 必须 HTTPS
- 使用 `systemd`
- 单域名同源

---

## 4. 成员B身份与职责边界

## 4.1 成员B固定身份

根据 `docs/小组分工指南.md`，成员B身份为：

- 服务端负责人
- 状态机负责人
- 数据输出负责人
- 后端部署支撑负责人

## 4.2 成员B主责范围

成员B负责：

1. 用户认证与请求受理
2. 等候区状态与桩队列状态机
3. 计费与详单
4. 报表输出
5. 管理端控制接口
6. 后端服务化与生产配置支持

具体功能范围：

- `F-U01` 注册与登录
- `F-U02` 提交充电请求
- `F-U03` 查看本车排队信息
- `F-U04` 修改充电模式
- `F-U05` 修改请求电量
- `F-U06` 等候区取消请求
- `F-U07` 充电区取消 / 提前结束
- `F-U08` 查看详单
- `F-A01` 启动/关闭充电桩
- `F-A02` 查看充电桩状态
- `F-A03` 查看单桩队列车辆信息
- `F-A05` 故障策略切换
- `F-A06` 故障标记与恢复
- `F-A07` 用户与车辆信息维护
- `F-A08` 报表接口
- `F-J02` 批量模拟接口
- `DEPLOY-BE` 后端服务化

## 4.3 成员B不主导的内容

成员B不主导：

- 最终要求解释和冻结
- 调度算法规则拍板
- 排队号语义拍板
- 前端页面实现
- 页面审查
- 答辩展示主讲

---

## 5. 当前代码与新 docs 的差异结论

本节是 AI 最容易误判的地方。

当前仓库里的后端代码仍大量保留旧模型特征，主要表现为：

### 5.1 当前代码中仍存在的旧口径残留

经对 `backend/app/routes/*.py` 和 `backend/app/services/*.py` 的快速核对，当前代码仍包含：

- `FAST_POOL` / `SLOW_POOL`
- `CALLED`
- `CONFIRMED`
- `NO_SHOW`
- `WAITING_TO_LEAVE`
- `FAULT_REQUEUE`
- `energy_fee / time_fee / occupancy_fee`
- `payment_status`
- `balance`
- `/health`
- `/api/batch/simulate`
- `/api/request/cancel_queue`
- `/api/request/confirm_arrival`
- `/api/request/interrupt_charge`
- `/api/request/confirm_leave`
- `/api/request/result/{request_id}`
- `/api/request/pay`

这些都说明：**当前实际代码主干仍然是旧 V2 口径，不是新的 V3 正式口径。**

### 5.2 当前代码缺失或尚未按 V3 实现的内容

当前正式文档要求但代码尚未完成收口的重点包括：

- `/api/health`
- `/api/test/batch-simulate`
- `/api/request/mode`
- `/api/request/energy`
- `/api/request/cancel`
- `/api/request/stop`
- `/api/request/detail/{request_id}`
- `/api/admin/system/config`
- `/api/admin/system/dispatch-mode`
- `/api/admin/system/fault-dispatch-mode`
- `/api/admin/stations/{station_code}/start`
- `/api/admin/stations/{station_code}/shutdown`
- `/api/admin/stations/{station_code}/fault`
- `/api/admin/stations/{station_code}/recover`
- `/api/admin/stations`
- `/api/admin/stations/{station_code}/queue`
- `/api/admin/users`
- `/api/admin/users/{user_id}`
- `/api/admin/users/{user_id}/battery-capacity`
- `/api/admin/reports`

此外，当前代码还未真正切换到：

- 等候区 + 每桩固定队列模型
- `F/T` 排队号语义
- 7 个正式请求状态
- `charge_fee + service_fee + total_fee`
- `charging_queue_len` 场景参数
- 新故障策略与扩展模式边界
- 新部署支撑结构

---

## 6. 成员B目前进度

## 6.1 总体判断

如果以当前 **V3.0 文档** 为唯一标准，成员B当前进度应判断为：

- 重构前文档冻结：已完成
- 后端工程骨架：已完成
- V3.0 业务重构：未完成
- 当前处于：**阶段零后半段到增量一前半段**

换句话说：

**成员B当前不是“后端已经基本完成”，而是“旧版后端可复用工程基础已在，但正式 V3.0 口径的服务端重构还没有完成”。**

## 6.2 当前可复用的已有基础

这些是成员B当前已经拥有、可直接复用的资产：

### 6.2.1 后端基础设施

- Flask 工程骨架已存在
- SQLite 基础能力已存在
- 认证模块已有最小实现基础
- 路由结构、响应结构、基础测试框架已存在
- 后端服务可启动

### 6.2.2 可复用的工程能力

- 数据库初始化能力
- 枚举与校验器框架
- 合同构造器 / 响应构造器思路
- 基础测试体系
- 部分管理员接口骨架

### 6.2.3 可复用的协作成果

- `develop` 作为公共集成基线
- 现有前后端目录结构
- 现有基础认证与接口封装习惯
- 现有文档管理结构

## 6.3 当前已经不应继续沿用的实现

以下内容虽然“代码里有”，但不能再算成员B有效进度：

- 中央等待池实现
- 快慢池共享容量模型
- `confirm_arrival / confirm_leave / interrupt_charge / pay`
- 虚拟余额和模拟支付
- 旧 `detail / bill / summary` 结构
- 旧批量模拟输入结构和旧事件语义
- 旧故障重排模型

## 6.4 当前成员B真实进度拆解

### 已完成

1. 后端工程骨架和基础设施
2. 最小认证骨架
3. 一部分基础数据库与路由组织方式
4. 基础测试框架
5. 文档阅读与重构条件具备

### 部分完成

1. 用户认证可复用，但字段需对齐新文档
2. 请求接口已有旧版本骨架，但需整体改造
3. 管理端接口有旧场景配置类骨架，但方向需切换
4. 批量模拟有旧框架，但路径、输入、算法、输出都需重做

### 未完成

1. 正式请求状态机
2. 等候区 + 每桩队列模型
3. `F/T` 排队号与前车数量语义
4. 新接口组
5. 新详单与计费规则
6. 新报表接口
7. 新故障接口与策略切换
8. 扩展调度接口与模式切换
9. V3.0 部署支撑落地

---

## 7. 成员B接下来进度规划

## 7.1 总体目标

成员B接下来的目标不是修补旧模型，而是：

**在当前工程骨架上，将后端重构到 V3.0 正式 docs 口径，并完成成员B负责范围内的接口、状态机、数据输出与后端部署支撑。**

## 7.2 推进原则

成员B后续推进必须遵守：

1. 先对齐文档，再改代码
2. 先重构模型与状态机，再补接口
3. 先打通增量一主流程，再做故障和扩展
4. 先让后端与新 docs 一致，再考虑旧代码兼容
5. 先完成正式接口，不再继续堆旧接口

## 7.3 阶段规划

### 阶段零：重构开工前冻结复核

成员B需要先完成：

1. 复核新接口文档可实现性
2. 复核状态机是否覆盖主流程、故障和扩展边界
3. 复核后端服务化与配置项是否支持部署上线

### 阶段一：增量一

必须完成：

1. 认证接口
2. 创建请求与状态查询
3. 排队号、前车数量、状态输出
4. 分时计费与详单基础输出
5. 管理员查看系统配置与桩状态

### 阶段二：增量二

必须完成：

1. 修改模式
2. 修改电量
3. 等候区取消
4. 充电区提前结束并结算
5. 故障标记、恢复和重调度接口
6. 充电桩启动/关闭接口

### 阶段三：增量三

必须完成：

1. 扩展调度接口与配置
2. 报表接口
3. 用户与车辆信息维护
4. 生产配置、日志与服务管理支持
5. ECS 后端部署验证

## 7.4 近期优先级

当前优先级必须是：

### P0

- 彻底停止再往旧中央等待池模型上补功能
- 建立新的 V3.0 数据模型、状态枚举和接口清单
- 打通增量一主流程

### P1

- 完成等候区修改 / 取消 / 提前结束
- 完成故障策略和故障恢复

### P2

- 完成扩展模式
- 完成报表和用户车辆维护
- 完成部署支撑

---

## 8. 成员B每日固定动作

以下动作每天都必须执行。

### 8.1 开工前

1. 同步代码：

```bash
git checkout develop
git pull origin develop
git checkout feature/b-backend-integration
git merge develop
git status
```

2. 重新阅读今天要对照的文档：

- `docs/需求调整与重构冻结说明.md`
- `docs/冻结接口文档.md`
- `docs/功能设计.md`
- `docs/调度算法.md`

3. 跑基础回归，确认工程骨架没坏：

```bash
python -m unittest backend.tests.test_auth_minimal
```

> 说明：旧测试大多验证旧模型，不能把“旧测试通过”当成“V3 已完成”。

4. 只给今天设一个主任务，最多一个副任务。

### 8.2 编码中

每天编码时必须反复检查：

1. 我是不是还在实现旧中央等待池？
2. 我今天改的是不是 V3 正式接口？
3. 我今天是否在围绕 7 个正式请求状态做事？
4. 我今天的计费是不是 `charge_fee + service_fee + total_fee`？
5. 我今天是否在让部署上线更可行？

### 8.3 收工前

1. 跑当天新增或修改的测试
2. 记录：
   - 今天完成什么
   - 今天验证什么
   - 今天还差什么
   - 明天先做什么
3. 提交代码：

```bash
git status
git add .
git commit -m "feat: xxx"
git push origin feature/b-backend-integration
```

---

## 9. 成员B从今天到项目完成的每日任务

以下是建议的 12 天重构收口任务表。  
如果实际可用天数更少，就按顺序压缩，不要换顺序。

### Day 1：建立 V3.0 差异清单

目标：

- 明确新 docs 和当前代码的差异，不再误把旧实现当进度

任务：

1. 列出 V3.0 正式接口清单
2. 列出当前代码已有接口清单
3. 做一份“保留 / 删除 / 重写 / 复用”矩阵
4. 列出旧模型中必须停止继续开发的模块：
   - `waiting_pool.py`
   - 旧 `scheduler_engine.py` 中中央等待池逻辑
   - 旧支付链路
   - 旧 `summary/detail/bill`

产出：

- V3.0 差异总表
- 成员B重构任务矩阵

### Day 2：冻结新的数据模型和状态机落地方案

目标：

- 先把成员B负责的后端数据结构和状态机方案定下来

任务：

1. 对照 `docs/功能设计.md §7`
2. 确认请求状态：
   - `WAITING_AREA`
   - `QUEUED`
   - `CHARGING`
   - `COMPLETED`
   - `COMPLETED_EARLY`
   - `CANCELLED`
   - `FAULT_INTERRUPTED`
3. 确认桩状态：
   - `RUNNING`
   - `SHUTDOWN`
   - `FAULT`
4. 设计或调整数据库字段：
   - `queue_number`
   - `waiting_area_order`
   - `station_queue_position`
   - `charging_queue_len`
   - 详单字段
   - 报表字段

产出：

- 成员B后端状态机实现表
- 数据库迁移清单

### Day 3：完成认证与创建请求最小闭环

目标：

- 打通增量一的入口链路

任务：

1. 对齐 `POST /api/auth/register`
2. 对齐 `POST /api/auth/login`
3. 实现或改造 `POST /api/request/create`
4. 创建请求时输出：
   - `request_id`
   - `queue_number`
   - `request_status`
   - `front_waiting_count`
5. 加入 `battery_capacity`
6. 确认同一用户同时最多一个活跃请求

产出：

- 认证链路
- 创建请求链路

### Day 4：完成状态查询与等候区模型

目标：

- 后端真正切到“等候区 + 每桩固定队列”

任务：

1. 实现 `GET /api/request/status/{request_id}`
2. 输出：
   - `queue_number`
   - `charge_mode`
   - `request_energy`
   - `request_status`
   - `front_waiting_count`
   - `station_code`
   - `station_queue_position`
   - `estimated_wait_seconds`
   - `estimated_start_time`
   - `estimated_finish_time`
3. 落地等候区顺序结构
4. 落地每桩固定长度队列结构

产出：

- V3 状态查询接口
- 等候区与桩队列基础实现

### Day 5：完成普通调度主流程

目标：

- 打通增量一的核心调度主线

任务：

1. 按 `NORMAL` 实现：
   - 同模式头车优先
   - 同模式最短完成时长分配
2. 实现桩队列出现空位时触发调度
3. 实现 `QUEUED -> CHARGING -> COMPLETED`
4. 加入快充 30kW、慢充 10kW

产出：

- 普通调度主流程可跑通

### Day 6：完成分时计费与详单

目标：

- 把旧账单体系替换成 V3 新详单体系

任务：

1. 删除或停用旧：
   - `energy_fee`
   - `time_fee`
   - `occupancy_fee`
   - `payment_status`
2. 实现新字段：
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
3. 按峰平谷拆分计费
4. 实现 `GET /api/request/detail/{request_id}`

产出：

- 新详单接口
- 新计费逻辑

### Day 7：完成管理员基础接口

目标：

- 打通增量一管理员端必需接口

任务：

1. 实现 `GET /api/admin/system/config`
2. 实现 `GET /api/admin/stations`
3. 实现 `GET /api/admin/stations/{station_code}/queue`
4. 让输出字段严格对齐冻结文档

产出：

- 管理员基础查看接口

### Day 8：完成修改模式 / 电量 / 取消 / 提前结束

目标：

- 打通增量二用户侧特殊操作

任务：

1. 实现 `PUT /api/request/mode`
2. 实现 `PUT /api/request/energy`
3. 实现 `POST /api/request/cancel`
4. 实现 `POST /api/request/stop`
5. 明确：
   - 等候区取消终态是 `CANCELLED`
   - 充电区取消 / 提前结束终态是 `COMPLETED_EARLY`

产出：

- 增量二用户动作接口

### Day 9：完成故障策略与故障恢复

目标：

- 打通增量二故障链路

任务：

1. 实现 `PUT /api/admin/system/fault-dispatch-mode`
2. 实现 `POST /api/admin/stations/{station_code}/fault`
3. 实现 `POST /api/admin/stations/{station_code}/recover`
4. 实现：
   - `PRIORITY`
   - `TIME_ORDER`
   - 故障恢复按时间顺序重排
5. 对照 `docs/故障与扩展场景指南.md` 跑场景

产出：

- 故障处理主链

### Day 10：完成桩启动/关闭、用户车辆维护、报表

目标：

- 打通增量二和增量三的管理端后端能力

任务：

1. 实现 `POST /api/admin/stations/{station_code}/start`
2. 实现 `POST /api/admin/stations/{station_code}/shutdown`
3. 实现 `GET /api/admin/users`
4. 实现 `GET /api/admin/users/{user_id}`
5. 实现 `PUT /api/admin/users/{user_id}/battery-capacity`
6. 实现 `GET /api/admin/reports?granularity=day|week|month`

产出：

- 管理端后端能力闭环

### Day 11：完成扩展调度与批量模拟

目标：

- 打通增量三验收能力

任务：

1. 实现 `dispatch_mode` 切换
2. 支持：
   - `NORMAL`
   - `EXT_SINGLE_BATCH`
   - `EXT_FULL_BATCH`
3. 实现 `POST /api/test/batch-simulate`
4. 输入结构对齐：
   - `fast_station_count`
   - `slow_station_count`
   - `waiting_area_capacity`
   - `charging_queue_len`
   - `dispatch_mode`
   - `fault_dispatch_mode`
5. 支持 `events`

产出：

- 扩展模式
- 批量模拟接口

### Day 12：完成部署支撑与最终回归

目标：

- 让成员B负责的内容可以进入上线与彩排阶段

任务：

1. 实现 `GET /api/health`
2. 对齐部署配置读取：
   - `FAST_CHARGING_PILE_NUM`
   - `TRICKLE_CHARGING_PILE_NUM`
   - `WAITING_AREA_SIZE`
   - `CHARGING_QUEUE_LEN`
   - `DISPATCH_MODE`
   - `FAULT_DISPATCH_MODE`
   - `DB_PATH`
3. 整理日志目录、监听地址、端口配置
4. 核对与 `部署上线手册.md` 一致
5. 做一次 V3 全链路回归

产出：

- 后端部署支撑完成
- 成员B回归清单

---

## 10. AI协助成员B时必须遵守的执行规则

### 10.1 必须做的事

- 先读 `docs/` 再提建议
- 先判断当前建议是否符合 V3
- 优先帮助成员B从旧模型迁移到新模型
- 优先帮助成员B落地接口、状态机、详单、报表、部署支撑
- 发现旧概念残留时要明确指出

### 10.2 禁止做的事

- 继续沿用中央等待池作为正式模型
- 把旧 `pay / balance / occupancy_fee` 体系当正式实现
- 把旧接口继续往前补
- 把成员B任务转成成员A算法任务或成员C页面任务
- 忽略部署上线要求

### 10.3 默认输出方式

AI 默认应输出：

1. 当前状态判断
2. 与 V3 docs 的差异点
3. 下一步最优先任务
4. 可执行检查清单
5. 若需要，给出精确到文件/接口/字段的改造方案

---

## 11. 成员B最终完成标准

项目结束前，成员B至少应确保以下内容成立：

1. 后端正式切到 V3.0 模型
2. 接口路径和字段对齐新 docs
3. 请求状态机和桩状态机对齐新 docs
4. 计费和详单对齐新 docs
5. 报表对齐新 docs
6. 故障策略和扩展模式对齐新 docs
7. 批量模拟对齐新 docs
8. 后端部署支撑对齐新 docs

---

## 12. 一句话总结

成员B当前的真实状态是：

旧版后端工程骨架还可以复用，但正式 V3.0 要求已经整体换轨；现在的核心任务不是修旧功能，而是基于新 `docs/` 重新完成成员B负责的服务端、状态机、数据输出和部署支撑。
