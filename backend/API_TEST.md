# API接口测试文档

> 本文档记录所有接口的测试用例和curl命令示例

## 基础信息

- 基础URL: `http://localhost:8080`
- 响应格式: `{"code": 0, "message": "success", "data": {}}`
- 错误码: code >= 1000 表示错误

---

## 1. 健康检查接口

### GET /health

**功能**: 检查服务是否正常运行

**curl命令**:
```bash
curl -s http://localhost:8080/health
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "timestamp": "2026-03-31T10:00:00"
  }
}
```

---

## 2. 提交充电请求

### POST /api/request/create

**功能**: 用户提交充电请求

**curl命令**:
```bash
curl -s -X POST http://localhost:8080/api/request/create \
  -H "Content-Type: application/json" \
  -d '{
    "request_time": "2026-03-31T10:00:00",
    "charge_mode": "FAST",
    "request_energy": 20.0
  }'
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "REQ001",
    "status": "WAITING",
    "estimated_wait_seconds": 600,
    "estimated_start_time": "2026-03-31T10:10:00",
    "estimated_finish_time": "2026-03-31T11:10:00"
  }
}
```

**错误场景测试 - 参数缺失**:
```bash
curl -s -X POST http://localhost:8080/api/request/create \
  -H "Content-Type: application/json" \
  -d '{
    "charge_mode": "FAST"
  }'
```

**预期错误响应**:
```json
{
  "code": 1001,
  "message": "Invalid parameters",
  "data": {
    "errors": ["Missing required field: request_time", "Missing required field: request_energy"]
  }
}
```

**错误场景测试 - 非法charge_mode**:
```bash
curl -s -X POST http://localhost:8080/api/request/create \
  -H "Content-Type: application/json" \
  -d '{
    "request_time": "2026-03-31T10:00:00",
    "charge_mode": "SUPER_FAST",
    "request_energy": 20.0
  }'
```

**预期错误响应**:
```json
{
  "code": 1001,
  "message": "Invalid parameters",
  "data": {
    "errors": ["charge_mode must be FAST or SLOW"]
  }
}
```

---

## 3. 查询请求状态

### GET /api/request/status/{request_id}

**功能**: 查询指定请求的状态

**curl命令**:
```bash
curl -s http://localhost:8080/api/request/status/REQ001
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "REQ001",
    "status": "PENDING",
    "station_id": null,
    "estimated_wait_seconds": 0,
    "last_called_time": null
  }
}
```

**错误场景测试 - 请求不存在**:
```bash
curl -s http://localhost:8080/api/request/status/REQ999
```

**预期错误响应**:
```json
{
  "code": 1002,
  "message": "Request not found",
  "data": {}
}
```

---

## 4. 取消排队

### POST /api/request/cancel_queue

**功能**: 用户取消排队中的请求

**前置条件**: 需要先创建一个请求，且状态为WAITING或CALLED

**curl命令**:
```bash
curl -s -X POST http://localhost:8080/api/request/cancel_queue \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "cancel_time": "2026-03-31T10:05:00"
  }'
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "REQ001",
    "status": "CANCELLED"
  }
}
```

**错误场景测试 - 请求不存在**:
```bash
curl -s -X POST http://localhost:8080/api/request/cancel_queue \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ999",
    "cancel_time": "2026-03-31T10:05:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1002,
  "message": "Request not found",
  "data": {}
}
```

**错误场景测试 - 状态不允许取消**:
```bash
# 先创建一个请求
curl -s -X POST http://localhost:8080/api/request/create \
  -H "Content-Type: application/json" \
  -d '{
    "request_time": "2026-03-31T10:00:00",
    "charge_mode": "FAST",
    "request_energy": 20.0
  }'

# 假设返回REQ002，然后直接尝试取消（需要先模拟状态变更）
# 这里仅作为示例，实际测试需要配合调度模块
```

---

## 5. 确认到场

### POST /api/request/confirm_arrival

**功能**: 用户确认到达充电桩

**前置条件**: 请求状态必须为CALLED

**curl命令**:
```bash
curl -s -X POST http://localhost:8080/api/request/confirm_arrival \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "confirm_time": "2026-03-31T10:09:00"
  }'
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "REQ001",
    "status": "CONFIRMED",
    "station_id": "FAST_01"
  }
}
```

**错误场景测试 - 请求不存在**:
```bash
curl -s -X POST http://localhost:8080/api/request/confirm_arrival \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ999",
    "confirm_time": "2026-03-31T10:09:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1002,
  "message": "Request not found",
  "data": {}
}
```

**错误场景测试 - 状态不是CALLED**:
```bash
# 使用刚创建的PENDING状态请求
curl -s -X POST http://localhost:8080/api/request/confirm_arrival \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "confirm_time": "2026-03-31T10:09:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1003,
  "message": "Request is not in CALLED status",
  "data": {}
}
```

---

## 6. 中断充电

### POST /api/request/interrupt_charge

**功能**: 用户主动中断充电

**前置条件**: 请求状态必须为CHARGING

**curl命令**:
```bash
curl -s -X POST http://localhost:8080/api/request/interrupt_charge \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "interrupt_time": "2026-03-31T10:40:00"
  }'
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "REQ001",
    "status": "INTERRUPTED",
    "actual_energy": 12.5,
    "actual_service_seconds": 1800
  }
}
```

**错误场景测试 - 请求不存在**:
```bash
curl -s -X POST http://localhost:8080/api/request/interrupt_charge \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ999",
    "interrupt_time": "2026-03-31T10:40:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1002,
  "message": "Request not found",
  "data": {}
}
```

**错误场景测试 - 状态不是CHARGING**:
```bash
curl -s -X POST http://localhost:8080/api/request/interrupt_charge \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "interrupt_time": "2026-03-31T10:40:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1003,
  "message": "Request is not in CHARGING status",
  "data": {}
}
```

---

## 7. 确认挪车

### POST /api/request/confirm_leave

**功能**: 用户确认挪车离开

**前置条件**: 请求状态必须为WAITING_TO_LEAVE

**curl命令**:
```bash
curl -s -X POST http://localhost:8080/api/request/confirm_leave \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "leave_time": "2026-03-31T11:15:00"
  }'
```

**预期响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "REQ001",
    "status": "COMPLETED"
  }
}
```

**错误场景测试 - 请求不存在**:
```bash
curl -s -X POST http://localhost:8080/api/request/confirm_leave \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ999",
    "leave_time": "2026-03-31T11:15:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1002,
  "message": "Request not found",
  "data": {}
}
```

**错误场景测试 - 状态不是WAITING_TO_LEAVE**:
```bash
curl -s -X POST http://localhost:8080/api/request/confirm_leave \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ001",
    "leave_time": "2026-03-31T11:15:00"
  }'
```

**预期错误响应**:
```json
{
  "code": 1003,
  "message": "Request is not in WAITING_TO_LEAVE status",
  "data": {}
}
```

---

## 完整流程测试脚本

```bash
#!/bin/bash

BASE_URL="http://localhost:8080"

echo "=== 1. 健康检查 ==="
curl -s ${BASE_URL}/health | jq .

echo -e "\n=== 2. 创建充电请求 ==="
CREATE_RESULT=$(curl -s -X POST ${BASE_URL}/api/request/create \
  -H "Content-Type: application/json" \
  -d '{
    "request_time": "2026-03-31T10:00:00",
    "charge_mode": "FAST",
    "request_energy": 20.0
  }')
echo $CREATE_RESULT | jq .
REQUEST_ID=$(echo $CREATE_RESULT | jq -r '.data.request_id')

echo -e "\n=== 3. 查询请求状态 ==="
curl -s ${BASE_URL}/api/request/status/${REQUEST_ID} | jq .

echo -e "\n=== 4. 取消排队 ==="
curl -s -X POST ${BASE_URL}/api/request/cancel_queue \
  -H "Content-Type: application/json" \
  -d "{\n    \"request_id\": \"${REQUEST_ID}\",\n    \"cancel_time\": \"2026-03-31T10:05:00\"\n  }" | jq .

echo -e "\n=== 5. 再次查询状态（应为CANCELLED） ==="
curl -s ${BASE_URL}/api/request/status/${REQUEST_ID} | jq .

# 注意：以下接口需要特定状态才能测试
# interrupt_charge 需要 CHARGING 状态
# confirm_leave 需要 WAITING_TO_LEAVE 状态
# 完整流程测试需要配合调度模块
```

---

## 错误码对照表

| 错误码 | 含义 | 使用场景 |
|--------|------|----------|
| 0 | 成功 | 正常返回 |
| 1001 | 请求参数错误 | 字段缺失、类型错误、非法值 |
| 1002 | 请求不存在 | request_id找不到 |
| 1003 | 当前状态不允许该操作 | 状态机非法跳转 |
| 1004 | 过号，无法确认到场 | 确认时已过号 |
| 1005 | 已取消，无法继续操作 | 对取消状态的操作 |
| 1006 | 充电桩故障 | 桩故障时操作 |
| 1007 | 支付失败 | 余额不足等 |
| 1099 | 服务器内部错误 | 未捕获异常 |
