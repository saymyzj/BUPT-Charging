# 智能充电桩调度计费系统

<<<<<<< HEAD
北京邮电大学软件工程课程项目：智能充电桩调度计费系统。

本项目当前已经从“联合验收”口径切换到“最终验收 / 系统验收”口径，核心设计围绕以下目标展开：

- 支持快充 / 慢充两类请求
- 充电桩数量作为验收时可灵活设置的超参数
- 支持等待区容量、队列参数、桩级初始状态快照等场景化输入
- 内部采用中央等待池 + 动态调度
- 对外兼容两种“充电桩排队队列长度”解释
- 输出统一详单、账单与评测指标

技术栈当前定稿为：

- 前端：Vue
- 后端：Python + Flask
- 数据库：SQLite
- 通信：HTTP + JSON

---

## 当前项目口径

### 1. 最终验收要求

根据老师目前确认的最终要求：

1. 快充桩数量、慢充桩数量是可配置超参数
2. 一般调度目标是让单个用户本次总时长最短
3. 扩展调度目标是让多台车辆总时长尽量最短
4. 测试用例会给出快慢充桩数量、等待区车位容量、以及“充电桩排队队列长度”相关描述
5. 不再进行多组联合验收

### 2. 当前系统设计选择

当前项目内部采用：

- `FAST_POOL`：快充等待池
- `SLOW_POOL`：慢充等待池
- 动态分配最终桩号
- 事件驱动重调度

同时，对外输入兼容两种队列描述：

1. `UNIFORM_CAPACITY`
说明：题目给出统一“队列长度”，解释为每个桩的统一排队容量上限

2. `STATION_SNAPSHOT`
说明：题目直接给出某个桩正在充电、有几人排队、某个桩空闲等状态快照

### 3. 等候区容量口径

当前文档已经统一为：

- `waiting_area_capacity` 表示系统全局等候区总容量
- 快充等待池和慢充等待池共享该容量
- 不是快充池和慢充池分别独立拥有一个容量

---

## 当前核心文档

请优先阅读以下文档：

1. [功能设计](./docs/功能设计.md)
2. [架构设计](./docs/架构设计.md)
3. [调度算法](./docs/调度算法.md)
4. [系统验收接口与测试输入规范说明](./docs/系统验收接口与测试输入规范说明.md)
5. [冻结接口文档](./docs/冻结接口文档.md)
6. [小组分工指南](./docs/小组分工指南.md)
7. [智能充电桩调度计费系统_增量模型前提条件确认文档_V4](./docs/智能充电桩调度计费系统_增量模型前提条件确认文档_V4.md)

---

## 当前静态 HTML 参考页

成员A负责 UI 方向、静态 HTML 参考页和页面审查。

当前静态参考稿主要放在：

- `front/ui-static-ac/`
- `front/ui-static-ref/`

它们的用途是：

- 作为成员C实现 Vue 页面时的视觉和结构参考
- 作为页面审查和优化时的对照稿
- 作为答辩展示风格方向的基础参考

说明：

- 这些静态页是“参考稿”，不是最终框架代码
- 成员C负责将其转化为完整页面实现
- 成员A负责继续审查成员C的完整页面并提出优化意见

---

## 协作入口

组内协作请优先遵守以下顺序：

1. 先看 [小组分工指南](./docs/小组分工指南.md)
2. 再看 [冻结接口文档](./docs/冻结接口文档.md)
3. 再看 [系统验收接口与测试输入规范说明](./docs/系统验收接口与测试输入规范说明.md)
4. 然后看 [功能设计](./docs/功能设计.md)
5. 再看 [架构设计](./docs/架构设计.md)
6. 最后看 [调度算法](./docs/调度算法.md)

当前分支约定：

- `main`：稳定版本
- `develop`：集成开发分支
- `feature/a-algorithm-ui-review`：成员A分支
- `feature/b-backend-integration`：成员B分支
- `feature/c-frontend-testing`：成员C分支

当前阶段约定：

- `main` 和 `develop` 应保持一致
- 个人开发在各自 `feature/*` 分支进行
- 稳定后统一合并回 `develop` 和 `main`

---

## 仓库快速启动

远程仓库：

`https://github.com/saymyzj/BUPT-Charging`

建议使用 SSH：

```bash
git clone git@github.com:saymyzj/BUPT-Charging.git
cd BUPT-Charging
git fetch origin
git branch -a
```

每天开始开发前：

```bash
git checkout develop
git pull origin develop
git checkout <自己的分支名>
git merge develop
git status
```

提交更新：

```bash
git status
git add .
git commit -m "feat: 完成xxx"
git push origin <自己的分支名>
```

更详细的 Git 教程见：

- [小组分工指南](./docs/小组分工指南.md)

---

## 提供给成员A的 AI Prompt

下面这段 prompt 可以直接发给自己的 AI。

```text
我正在参与一个北京邮电大学软件工程课程项目：智能充电桩调度计费系统。

请严格基于当前仓库中的文档和静态参考稿进行分析和指导，不要脱离现有设计另起炉灶。

你必须优先阅读以下内容：

1. README.md
2. docs/小组分工指南.md
3. docs/冻结接口文档.md
4. docs/系统验收接口与测试输入规范说明.md
5. docs/功能设计.md
6. docs/架构设计.md
7. docs/调度算法.md
8. docs/智能充电桩调度计费系统_增量模型前提条件确认文档_V4.md
9. front/ui-static-ac/
10. front/ui-static-ref/

我的身份是“成员A / 组长”，我的固定职责是：

- 算法负责人
- 统一口径负责人
- 展示负责人
- UI 方向与页面审查负责人

当前项目必须遵守以下关键口径：

- 当前是最终验收，不再是多组联合验收
- 快充桩数量和慢充桩数量是可配置超参数
- waiting_area_capacity 是系统全局等候区容量，快充池和慢充池共享
- 内部实现采用 FAST_POOL 和 SLOW_POOL 两个中央等待池
- 对外输入必须兼容两种队列解释：
  1. UNIFORM_CAPACITY
  2. STATION_SNAPSHOT
- 一般目标是单用户本次总时长最短
- 扩展目标是多用户总完成时长尽量最短

我的工作边界是：

- 主导调度算法、状态机、指标定义、输入解释规则
- 提供给成员C静态 HTML 参考页
- 审查成员C提交的完整页面
- 提出页面优化意见
- 不主写服务端全部接口实现
- 不负责把所有 Vue 页面亲自落地

请输出一份详细的工作指导，必须包含：

1. 成员A当前负责什么，不负责什么
2. 当前最重要的算法口径和验收口径
3. 给出成员A的分阶段 TODO LIST，必须拆成：
   - 当务之急
   - 第一阶段：开工前冻结
   - 第二阶段：中期前
   - 第三阶段：最终验收前
   每个阶段都要尽量细化到可以直接执行
4. 如何继续产出静态 HTML 参考页
5. 如何审查成员C的页面实现
6. 如何检查 README、文档、Prompt 和页面风格是否一致
7. 当前最容易产生分歧的地方有哪些
8. Git 上我每天应该怎么操作
9. 请尽量给出按步骤执行的清单，而不是泛泛建议

输出要尽量详细，适合我直接照着执行。
```
=======
**文档版本**: V1.0  
**编写日期**: 2026-04-02  
**编写人**: 成员 B（服务端负责人/场景适配负责人）  
**审核状态**: 待审核
>>>>>>> 3c7e3bed571f87fed0c081ccfea9094f3fe827d9

---

## 一、已完成的部分

<<<<<<< HEAD
下面这段 prompt 可以直接发给自己的 AI。

```text
我正在参与一个北京邮电大学软件工程课程项目：智能充电桩调度计费系统。

请严格基于当前仓库中的文档进行分析和指导，不要脱离现有设计另起炉灶。

你必须优先阅读以下内容：

1. README.md
2. docs/小组分工指南.md
3. docs/冻结接口文档.md
4. docs/系统验收接口与测试输入规范说明.md
5. docs/功能设计.md
6. docs/架构设计.md
7. docs/调度算法.md
8. docs/智能充电桩调度计费系统_增量模型前提条件确认文档_V4.md

我的身份是“成员B”，我的固定职责是：

- 服务端负责人
- 场景适配负责人
- 批量模拟与详单账单输出负责人

当前项目必须遵守以下关键口径：

- 当前是最终验收，不再是多组联合验收
- 批量模拟输入使用 scenario + users 结构
- waiting_area_capacity 是系统全局等候区容量，快充池和慢充池共享
- 系统内部使用 FAST_POOL 和 SLOW_POOL 两个等待池
- 对外输入必须兼容：
  1. UNIFORM_CAPACITY
  2. STATION_SNAPSHOT
- 需要支持 fast_station_count、slow_station_count、waiting_area_capacity、station_queue_capacity 等场景参数
- summary 至少输出 avg_wait_seconds、avg_finish_seconds、station_utilization，并建议输出 total_finish_seconds

我的工作边界是：

- 主要负责 Flask 后端、SQLite、批量模拟、参数化场景初始化、详单和账单输出
- 不主导调度算法规则本身
- 不主导前端页面实现
- 不负责最终 UI 审查

请输出一份详细的工作指导，必须包含：

1. 成员B到底负责什么，不负责什么
2. 给出成员B的分阶段 TODO LIST，必须拆成：
   - 当务之急
   - 第一阶段：开工前冻结
   - 第二阶段：中期前
   - 第三阶段：最终验收前
   每个阶段都要尽量细化到接口、模块和输出物
3. 当前批量模拟输入结构应该如何实现
4. 场景参数初始化应该怎么做
5. 两种队列解释该如何在服务端兼容
6. 详单、账单、summary 应该怎么生成
7. 当前最应该优先完成的接口和模块
8. 现在最容易出错的状态流转有哪些
9. Git 上我每天应该怎么操作
10. 请尽量给出按步骤执行的清单，而不是泛泛建议
=======
### 周期 1：数据库与基础架构修正（Day 1-2）

#### 1.1 数据库 Schema V2 升级

| 模块 | 完成内容 | 文件位置 |
|------|----------|----------|
| 场景配置表 | 新增 `system_scenario_config` 表，支持动态场景配置 | `migrations/init_schema_v2.sql` |
| 充电桩表增强 | 新增 `initial_queue_length`, `initial_status` 等字段 | `migrations/init_schema_v2.sql` |
| 充电请求表 | 新增 `estimated_service_seconds`, `scenario_id` 等字段 | `migrations/init_schema_v2.sql` |
| 数据迁移工具 | 实现 V1 到 V2 的数据迁移脚本 | `migrations/migrate_data.py` |

#### 1.2 枚举值更新

- `WaitingPoolType`: 支持 `FAST_POOL`, `SLOW_POOL`
- `StationQueueMode`: 支持 `UNIFORM_CAPACITY`, `STATION_SNAPSHOT`
- `ChargeMode`: 快充 30kW，慢充 7kW
- `RequestStatus`: `PENDING`, `WAITING`, `CALLED`, `CHARGING`, `COMPLETED`, `CANCELLED`, `INTERRUPTED`, `COMPLETED_EARLY`
- `StationStatus`: `IDLE`, `OCCUPIED`, `WAITING_TO_LEAVE`, `OFFLINE`

#### 1.3 核心模块实现

| 模块 | 功能描述 | 状态 |
|------|----------|------|
| `config_manager.py` | 场景配置的 CRUD 管理 | ✅ 完成 |
| `waiting_pool.py` | 双等待池管理（FAST/SLOW），共享容量控制 | ✅ 完成 |
| `helpers.py` | 工具函数，解决循环导入问题 | ✅ 完成 |

---
>>>>>>> 3c7e3bed571f87fed0c081ccfea9094f3fe827d9

### 周期 2：场景适配层实现（Day 3-4）

#### 2.1 场景适配器核心

| 组件 | 功能描述 | 状态 |
|------|----------|------|
| `ScenarioAdapter` 类 | 适配器模式，统一处理两种输入格式 | ✅ 完成 |
| `adapt_uniform_capacity()` | 统一容量模式适配 | ✅ 完成 |
| `adapt_station_snapshot()` | 桩级快照模式适配 | ✅ 完成 |
| `initialize_waiting_pools()` | 初始化等待池 | ✅ 完成 |
| `reset_scenario()` | 场景重置 | ✅ 完成 |

#### 2.2 场景参数解析器

| 组件 | 功能描述 | 状态 |
|------|----------|------|
| `scenario_parser.py` | 解析批量模拟中的场景参数 | ✅ 完成 |
| `user_behavior_parser.py` | 解析用户行为时间线和事件序列 | ✅ 完成 |
| `UserBehaviorConfig` 类 | 定义单个用户完整行为配置 | ✅ 完成 |

---

### 周期 3：现有接口适配与批量模拟基础（Day 5-6）

#### 3.1 请求接口适配

| 接口 | 路径 | 适配内容 | 状态 |
|------|------|----------|------|
| 创建请求 | `POST /api/request/create` | 容量检查、池类型记录、临时预测值计算 | ✅ 完成 |
| 查询状态 | `GET /api/request/status/{id}` | 返回池类型和队列位置 | ✅ 完成 |
| 取消排队 | `POST /api/request/cancel_queue` | 从等待池移除 | ✅ 完成 |
| 确认到场 | `POST /api/request/confirm_arrival` | 状态流转 | ✅ 完成 |
| 中断充电 | `POST /api/request/interrupt_charge` | 记录中断原因 | ✅ 完成 |
| 确认挪车 | `POST /api/request/confirm_leave` | 超时检测 | ✅ 完成 |
| 查询结果 | `GET /api/request/result/{id}` | 详单/账单生成 | ✅ 完成 |
| 支付账单 | `POST /api/request/pay` | 支付状态更新 | ✅ 完成 |

#### 3.2 新增接口

| 接口 | 路径 | 功能描述 | 状态 |
|------|------|----------|------|
| 健康检查 | `GET /health` | 系统状态检查 | ✅ 完成 |
| 充电桩总览 | `GET /api/stations/overview` | 返回所有充电桩状态和等待队列 | ✅ 完成 |
| 批量模拟 | `POST /api/batch/simulate` | 批量模拟框架（V3.0） | ✅ 框架完成 |

#### 3.3 预测值计算逻辑

创建请求时的预测值计算：

```
预计等待时间 = 队列中人数 × 5分钟（300秒）
预计开始时间 = 当前时间 + 等待时间
预计服务时长 = 电量 / 功率 × 60分钟
预计完成时间 = 开始时间 + 服务时长
```

- 快充功率：30kW
- 慢充功率：7kW

#### 3.4 状态一致性保证

<<<<<<< HEAD
下面这段 prompt 可以直接发给自己的 AI。

```text
我正在参与一个北京邮电大学软件工程课程项目：智能充电桩调度计费系统。

请严格基于当前仓库中的文档和静态 HTML 参考页进行分析和指导，不要脱离现有设计另起炉灶。

你必须优先阅读以下内容：

1. README.md
2. docs/小组分工指南.md
3. docs/冻结接口文档.md
4. docs/系统验收接口与测试输入规范说明.md
5. docs/功能设计.md
6. docs/架构设计.md
7. docs/调度算法.md
8. front/ui-static-ac/  （已经通过审查的静态 HTML 参考页）
9. front/ui-static-ref/ （被归档的但可做参考的静态 HTML 参考页）

我的身份是“成员C”，我的固定职责是：

- 前端负责人
- 管理端负责人
- 测试负责人
- 展示实现负责人

当前项目必须遵守以下关键口径：

- 当前是最终验收，不再是多组联合验收
- 页面实现应严格参考成员A提供的静态 HTML 参考页
- 完整页面实现完成后，需要交给成员A审查
- waiting_area_capacity 是系统全局等候区容量，快充池和慢充池共享
- 页面中涉及的批量模拟结果，要能够展示 avg_wait_seconds、avg_finish_seconds、station_utilization，并建议展示 total_finish_seconds
- 批量模拟场景参数至少包括 fast_station_count、slow_station_count、waiting_area_capacity、station_queue_mode

我的工作边界是：

- 主要负责 Vue 页面、用户端、管理端、展示落地、图表与结果展示
- 负责把静态 HTML 参考稿转化为完整页面
- 负责页面测试、回归测试和展示效果
- 不主导调度算法规则
- 不主导服务端接口语义

请输出一份详细的工作指导，必须包含：

1. 成员C到底负责什么，不负责什么
2. 给出成员C的分阶段 TODO LIST，必须拆成：
   - 当务之急
   - 第一阶段：开工前冻结
   - 第二阶段：中期前
   - 第三阶段：最终验收前
   每个阶段都要尽量细化到页面、测试和展示任务
3. 当前应该优先实现哪些页面
4. 当前静态 HTML 参考稿该如何转成 Vue 页面
5. 每个核心页面应该展示哪些字段和状态
6. 完整页面交给成员A审查前应先自查什么
7. 批量模拟结果 summary 如何展示更清楚
8. 当前测试和回归该怎么做
9. Git 上我每天应该怎么操作
10. 请尽量给出按步骤执行的清单，而不是泛泛建议

输出要尽量详细，适合我直接照着执行。
```

---

## 当前说明

本仓库当前处于“文档口径已基本统一、实现正在继续对齐”的阶段。

接下来所有成员都应优先做这几件事：

1. 不再沿用旧的联合验收口径
2. 统一使用当前系统验收输入规范
3. 保持 `main` 和 `develop` 一致
4. 个人开发只在自己的 `feature/*` 分支推进
5. README、文档、Prompt、静态参考页、最终实现要尽量保持同一套口径
=======
| 位置 | 状态值 | 说明 |
|------|--------|------|
| 数据库 `charge_request.status` | `WAITING` | 创建时直接写入 |
| `create` 接口响应 | `WAITING` | 与数据库一致 |
| `status` 接口响应 | 从数据库读取 | 实时反映当前状态 |

---

## 二、未完成的部分

### 2.1 调度模块对接（依赖成员 A）

| 功能 | 说明 | 依赖方 |
|------|------|--------|
| 真实预测时间计算 | 调用调度模块获取准确的预计等待时间 | 成员 A |
| 重调度触发 | 充电完成后触发调度算法重新分配 | 成员 A |
| 批量模拟执行引擎 | 时间序列模拟和状态推进 | 成员 A |

### 2.2 状态机确认（需与成员 A 确认）

- `PENDING` 状态是否必要？当前创建请求后直接为 `WAITING`
- 状态流转规则的最终确认

### 2.3 批量模拟完整实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 场景参数解析 | ✅ 完成 | `scenario_parser.py` |
| 用户行为解析 | ✅ 完成 | `user_behavior_parser.py` |
| 模拟执行引擎 | ⏳ 待实现 | 依赖调度模块 |
| 结果收集与返回 | ⏳ 待实现 | 依赖执行引擎 |

---

## 三、待与 A 对接的部分

### 3.1 调度模块接口约定

| 接口 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `get_estimated_wait_time` | charge_mode, request_energy | estimated_wait_seconds | 创建请求时计算预测时间 |
| `trigger_reschedule` | station_id | void | 充电完成后重调度 |
| `simulate_timeline` | scenario_config, user_behaviors | simulation_result | 批量模拟执行 |

### 3.2 状态机定义确认

- 确认 `PENDING` 状态是否需要保留
- 确认 `WAITING_TO_LEAVE` 状态的使用场景
- 确认各状态之间的流转条件

### 3.3 批量模拟协作

- 成员 A 负责：模拟执行引擎、时间推进、状态更新
- 成员 B 负责：场景参数解析、用户行为解析、结果格式化

---

## 四、待与 C 对接的部分

### 4.1 前端页面接口

| 页面 | 所需接口 | 状态 |
|------|----------|------|
| 充电桩总览页 | `GET /api/stations/overview` | ✅ 已完成 |
| 请求创建页 | `POST /api/request/create` | ✅ 已完成 |
| 状态查询页 | `GET /api/request/status/{id}` | ✅ 已完成 |
| 详单/账单页 | `GET /api/request/result/{id}` | ✅ 已完成 |

### 4.2 接口文档确认

- 确认前端需要的字段是否完整
- 确认错误码提示信息的展示方式
- 确认页面跳转和状态刷新的逻辑

---

## 五、技术债务与优化项

### 5.1 当前技术债务

| 问题 | 影响 | 优先级 | 计划解决时间 |
|------|------|--------|--------------|
| 预测值为临时计算 | 精度不高 | 中 | 调度模块接入后 |
| TODO 注释未处理 | 代码整洁度 | 低 | 后续迭代 |

### 5.2 性能优化点

- 数据库查询优化（添加索引）
- 等待池状态缓存
- 批量操作的事务处理

---

## 六、附录

### 6.1 已冻结接口清单

| 序号 | 接口路径 | 方法 | 功能描述 |
|------|----------|------|----------|
| 1 | `/health` | GET | 健康检查 |
| 2 | `/api/request/create` | POST | 创建充电请求 |
| 3 | `/api/request/status/{id}` | GET | 查询请求状态 |
| 4 | `/api/request/confirm_arrival` | POST | 确认到场 |
| 5 | `/api/request/cancel_queue` | POST | 取消排队 |
| 6 | `/api/request/interrupt_charge` | POST | 中断充电 |
| 7 | `/api/request/confirm_leave` | POST | 确认挪车 |
| 8 | `/api/request/result/{id}` | GET | 查询结果/详单 |
| 9 | `/api/request/pay` | POST | 支付账单 |
| 10 | `/api/stations/overview` | GET | 充电桩总览 |
| 11 | `/api/batch/simulate` | POST | 批量模拟 |

### 6.2 代码文件清单

**数据库与迁移**:
- `migrations/init_schema_v2.sql`
- `migrations/migrate_data.py`

**核心服务**:
- `app/services/config_manager.py`
- `app/services/waiting_pool.py`
- `app/services/scenario_adapter.py`
- `app/services/scenario_parser.py`
- `app/services/user_behavior_parser.py`
- `app/services/billing_service.py`

**工具模块**:
- `app/utils/helpers.py`
- `app/utils/response.py`
- `app/utils/validators.py`
- `app/utils/db.py`

**路由接口**:
- `app/routes/health.py`
- `app/routes/request.py`
- `app/routes/stations.py`
- `app/routes/batch_simulate.py`
- `app/routes/admin.py`

**枚举定义**:
- `app/enums.py`

---

**文档结束**
>>>>>>> 3c7e3bed571f87fed0c081ccfea9094f3fe827d9
