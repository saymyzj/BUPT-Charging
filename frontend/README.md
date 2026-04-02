# 前端说明（当前实现口径）

> 文档版本：V2.0  
> 更新日期：2026-04-02  
> 适用范围：当前 `develop` 分支的真实前端状态

---

## 1. 文档定位

本文档用于说明前端当前在 `develop` 分支上的真实实现状态。

请与以下文档配合阅读：

- [冻结接口文档](/Users/zhoujia/code/SE/ChargingPile/docs/冻结接口文档.md)
- [Fix本地联调](/Users/zhoujia/code/SE/ChargingPile/docs/04-02/Fix本地联调.md)
- [前端实现版文档](/Users/zhoujia/code/SE/ChargingPile/frontend/冻结接口文档_前端实现版.md)

---

## 2. 当前已完成内容

### 2.1 用户端

当前已可真实演示：

- 登录页入口跳转
- 工作台提交充电请求
- 当前任务页轮询真实状态
- 叫号倒计时展示
- 确认到场
- 中断充电
- 确认离场
- 详单 / 账单展示
- 支付

### 2.2 管理端

当前已完成：

- 管理端总览页 UI
- 记录中心 UI
- 系统配置 UI
- 统计分析 UI
- 用户管理 UI

当前说明：

- 管理端主要仍是静态演示页面
- 未完善按钮已补充明确提示，不再“点了没反应”

---

## 3. 当前真实联调状态

### 3.1 已真实联调的接口

- `GET /health`
- `POST /api/request/create`
- `GET /api/request/status/{request_id}`
- `POST /api/request/cancel_queue`
- `POST /api/request/confirm_arrival`
- `POST /api/request/interrupt_charge`
- `POST /api/request/confirm_leave`
- `GET /api/request/result/{request_id}`
- `POST /api/request/pay`

### 3.2 当前仍未完成真实接入的部分

- 登录 / 注册真实鉴权
- 账户中心真实数据
- 管理端真实数据接口

---

## 4. 本地运行

### 4.1 安装依赖

```bash
cd /Users/zhoujia/code/SE/ChargingPile/frontend
npm install
```

### 4.2 启动开发服务器

```bash
cd /Users/zhoujia/code/SE/ChargingPile/frontend
npm run dev
```

默认访问：

- `http://127.0.0.1:3000`
- `http://localhost:3000`

### 4.3 配套后端

前端联调时需要后端同时启动：

```bash
cd /Users/zhoujia/code/SE/ChargingPile/backend
DATABASE_PATH=/tmp/charging_fix_20260402.db python3 run.py
```

---

## 5. 当前页面说明

### 5.1 登录页

- 输入 `admin` 可进入管理端演示入口
- 输入任意非 `admin` 用户名可进入用户端演示入口
- 当前主要用于页面跳转，不代表真实鉴权已完成

### 5.2 用户工作台

- 可真实提交请求
- 会保存后端返回的预测结果
- 提交后跳转任务页

### 5.3 用户任务页

- 以后端状态为主
- 不再以前端本地推进作为主逻辑
- 会根据后端结果展示等待、叫号、结算和支付流程

### 5.4 管理端页面

- 当前主要承担展示与答辩演示作用
- 未完善按钮会直接提示“功能未完善 / 静态演示”

---

## 6. 当前统一结论

- 前端当前已具备用户端最小闭环演示能力
- 管理端当前以静态展示为主
- 不再使用“中期验收 / 联调基准”口径
- 当前文档以 `develop` 分支的真实状态为准
