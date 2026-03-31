# 智能充电桩调度计费系统 - 后端服务

## 项目简介

北京邮电大学软件工程课程项目 - 智能充电桩调度计费系统的 Flask 后端服务。

## 技术栈

- Python 3.9+
- Flask 3.0.0
- Flask-CORS 4.0.0
- SQLite3
- PyJWT 2.8.0

## 目录结构

```
backend/
├── app/                    # 应用主目录
│   ├── __init__.py        # Flask应用初始化
│   ├── config.py          # 配置文件
│   ├── enums.py           # 枚举定义
│   ├── models/            # 数据模型
│   ├── routes/            # 路由/接口
│   │   ├── health.py      # 健康检查
│   │   └── request.py     # 请求相关接口
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
│       ├── db.py          # 数据库工具
│       ├── response.py    # 响应封装
│       └── validators.py  # 输入校验
├── migrations/            # 数据库迁移
│   └── init_schema.sql    # 初始建表SQL
├── tests/                 # 测试文件
├── requirements.txt       # Python依赖
├── run.py                 # 启动入口
└── README.md              # 本文件
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python run.py
```

服务将启动在 `http://0.0.0.0:8080`

### 4. 测试健康检查接口

```bash
curl http://localhost:8080/health
```

预期响应：
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

## API接口

### 健康检查
- `GET /health` - 服务健康检查

### 充电请求
- `POST /api/request/create` - 提交充电请求
- `GET /api/request/status/<request_id>` - 查询请求状态

## 配置说明

配置文件位于 `app/config.py`，支持以下环境：

- `development` - 开发环境（默认）
- `production` - 生产环境
- `testing` - 测试环境

可通过环境变量 `FLASK_ENV` 切换环境。

## 数据库

使用 SQLite3，数据库文件默认位于 `backend/charging_system.db`。

初始化时会自动创建所有表和初始数据。

## 跨设备访问

服务默认监听 `0.0.0.0:8080`，支持局域网内其他设备访问。

获取本机IP：
```bash
# Windows:
ipconfig

# Mac/Linux:
ifconfig | grep inet
```

其他设备访问：`http://<你的IP>:8080/health`

## 开发规范

- 接口返回统一格式：`{code, message, data}`
- code=0 表示成功，code>=1000 表示错误
- 使用 ISO 8601 格式传递时间

## 作者

成员B - 服务端/联合验收负责人
