-- ============================================
-- 智能充电桩调度计费系统 - 数据库初始化脚本 V2
-- 版本：V2.0
-- 更新日期：2026-04-02
-- 说明：支持系统单机验收模式，桩数量可配置
-- ============================================

-- 用户表（保持不变）
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'USER' CHECK(role IN ('USER', 'ADMIN')),
    balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 新增：系统场景配置表
-- 支持动态配置验收场景参数
-- ============================================
CREATE TABLE IF NOT EXISTS system_scenario_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT NOT NULL,                           -- 配置名称（如"默认场景"、"验收场景A"）
    fast_station_count INTEGER DEFAULT 2,                -- 快充桩数量
    slow_station_count INTEGER DEFAULT 3,                -- 慢充桩数量
    waiting_area_capacity INTEGER DEFAULT 6,             -- 等待区总容量（快充+慢充共享）
    station_queue_mode TEXT DEFAULT 'UNIFORM_CAPACITY'   -- 队列模式：UNIFORM_CAPACITY（统一容量）/ STATION_SNAPSHOT（桩级快照）
        CHECK(station_queue_mode IN ('UNIFORM_CAPACITY', 'STATION_SNAPSHOT')),
    station_queue_capacity INTEGER DEFAULT 3,            -- 统一容量模式下：每桩排队容量上限
    is_active INTEGER DEFAULT 0,                         -- 是否为当前激活配置（0=否，1=是）
    description TEXT,                                    -- 配置描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 充电桩表（增强版）
CREATE TABLE IF NOT EXISTS charging_station (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_code TEXT UNIQUE NOT NULL,                   -- 桩编号（如 FAST_01, SLOW_01）
    station_type TEXT NOT NULL CHECK(station_type IN ('FAST', 'SLOW')),
    power_kw REAL NOT NULL,                              -- 额定功率（kW）
    
    -- 当前运行状态
    status TEXT DEFAULT 'IDLE' 
        CHECK(status IN ('IDLE', 'RESERVED', 'CHARGING', 'WAITING_TO_LEAVE', 'FAULT')),
    current_request_id INTEGER,                          -- 当前服务请求ID
    available_time TIMESTAMP,                            -- 最早可用时间
    
    -- 新增：初始状态字段（用于场景快照模式初始化）
    initial_queue_length INTEGER DEFAULT 0,              -- 初始排队人数
    initial_status TEXT DEFAULT 'IDLE',                  -- 初始状态
    initial_remaining_seconds INTEGER,                   -- 当前用户剩余秒数（快照模式用）
    scenario_id INTEGER,                                 -- 关联的场景配置ID
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_request_id) REFERENCES charge_request(id),
    FOREIGN KEY (scenario_id) REFERENCES system_scenario_config(id)
);

-- 充电请求表（增强版）
CREATE TABLE IF NOT EXISTS charge_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,                     -- 请求编号（如 REQ001）
    user_id INTEGER,                                     -- 用户ID
    
    -- 充电需求
    charge_mode TEXT NOT NULL CHECK(charge_mode IN ('FAST', 'SLOW')),
    request_energy REAL NOT NULL,                        -- 申请充电量（调度预测用）
    remaining_energy REAL DEFAULT 0.0,                   -- 剩余待充电量
    actual_energy REAL DEFAULT 0.0,                      -- 实际充电量（结算用）
    battery_limit_energy REAL DEFAULT 100.0,             -- 车辆可充上限
    
    -- 请求状态
    status TEXT DEFAULT 'PENDING' 
        CHECK(status IN (
            'PENDING', 'WAITING', 'CALLED', 'CONFIRMED', 'CHARGING',
            'COMPLETED', 'COMPLETED_EARLY', 'INTERRUPTED', 'CANCELLED',
            'NO_SHOW', 'FAULT_REQUEUE'
        )),
    
    -- 新增：等待池类型
    waiting_pool_type TEXT CHECK(waiting_pool_type IN ('FAST_POOL', 'SLOW_POOL')),
    scenario_id INTEGER,                                 -- 关联的场景配置ID
    
    -- 时间戳
    submit_time TIMESTAMP NOT NULL,                      -- 提交时间
    estimated_wait_seconds INTEGER DEFAULT 0,            -- 预计等待秒数
    estimated_start_time TIMESTAMP,                      -- 预计开始时间
    estimated_finish_time TIMESTAMP,                     -- 预计完成时间
    estimated_service_seconds INTEGER DEFAULT 0,         -- 预计服务时长
    last_called_at TIMESTAMP,                            -- 最后叫号时间
    confirmed_at TIMESTAMP,                              -- 确认到场时间
    assigned_station_id INTEGER,                         -- 分配的充电桩ID
    actual_service_seconds INTEGER DEFAULT 0,            -- 实际服务秒数
    
    -- 调度相关
    priority_score REAL DEFAULT 0.0,                     -- 当前优先级分数
    retry_count INTEGER DEFAULT 0,                       -- 重试次数
    no_show_count INTEGER DEFAULT 0,                     -- 过号次数
    fault_requeue_flag INTEGER DEFAULT 0,                -- 故障重排标记
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (assigned_station_id) REFERENCES charging_station(id),
    FOREIGN KEY (scenario_id) REFERENCES system_scenario_config(id)
);

-- 充电会话表（保持不变）
CREATE TABLE IF NOT EXISTS charging_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    actual_energy REAL DEFAULT 0.0,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'CHARGING', 'COMPLETED', 'INTERRUPTED')),
    interrupt_reason TEXT,
    left_at TIMESTAMP,
    leave_deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES charge_request(id),
    FOREIGN KEY (station_id) REFERENCES charging_station(id)
);

-- 计费记录表（保持不变）
CREATE TABLE IF NOT EXISTS billing_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    billing_mode TEXT DEFAULT 'ENERGY' CHECK(billing_mode IN ('ENERGY', 'TIME', 'MIXED')),
    billing_energy REAL DEFAULT 0.0,
    energy_fee REAL DEFAULT 0.0,
    time_fee REAL DEFAULT 0.0,
    occupancy_fee REAL DEFAULT 0.0,
    total_fee REAL DEFAULT 0.0,
    payment_status TEXT DEFAULT 'UNPAID' CHECK(payment_status IN ('UNPAID', 'PAID', 'FAILED')),
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES charge_request(id)
);

-- 调度事件日志表（保持不变）
CREATE TABLE IF NOT EXISTS scheduler_event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    request_id TEXT,
    station_id TEXT,
    event_payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知表（保持不变）
CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 调度配置表（保持不变）
CREATE TABLE IF NOT EXISTS scheduler_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 初始数据插入
-- ============================================

-- 插入默认场景配置（兼容原有固定配置）
INSERT OR IGNORE INTO system_scenario_config (
    config_name, 
    fast_station_count, 
    slow_station_count, 
    waiting_area_capacity,
    station_queue_mode,
    station_queue_capacity,
    is_active,
    description
) VALUES (
    '默认场景',
    2,
    3,
    6,
    'UNIFORM_CAPACITY',
    3,
    1,  -- 默认激活
    '系统默认配置：2个快充桩，3个慢充桩，等待区容量6'
);

-- 插入充电桩初始数据（动态生成，基于默认场景）
-- 注意：实际初始化时应根据场景配置动态生成
INSERT OR IGNORE INTO charging_station (station_code, station_type, power_kw, scenario_id) VALUES
('FAST_01', 'FAST', 30.0, 1),
('FAST_02', 'FAST', 30.0, 1),
('SLOW_01', 'SLOW', 7.0, 1),
('SLOW_02', 'SLOW', 7.0, 1),
('SLOW_03', 'SLOW', 7.0, 1);

-- 插入默认调度配置
INSERT OR IGNORE INTO scheduler_config (config_key, config_value) VALUES
('T_CALL_MINUTES', '5'),
('CONFIRM_TIMEOUT_MINUTES', '3'),
('ARRIVAL_TIMEOUT_MINUTES', '5'),
('LEAVE_BUFFER_MINUTES', '10'),
('BILLING_MODE', 'ENERGY'),
('ENERGY_PRICE', '1.5'),
('TIME_PRICE', '0.0'),
('OCCUPANCY_PRICE', '0.5'),
('OCCUPANCY_START_AFTER_MINUTES', '10'),
-- 新增：等待池相关配置
('PRIORITY_WEIGHT_A', '1.0'),        -- 等待时间权重
('PRIORITY_WEIGHT_B', '0.5'),        -- 重试补偿权重
('PRIORITY_WEIGHT_C', '1.0'),        -- 故障补偿权重
('PRIORITY_WEIGHT_D', '0.3'),        -- 服务时间权重
('PRIORITY_WEIGHT_E', '0.8');        -- 过号惩罚权重

-- 插入测试用户
INSERT OR IGNORE INTO user (username, password_hash, role, balance) VALUES
('admin', 'pbkdf2:sha256:600000$...', 'ADMIN', 1000.0),
('test_user', 'pbkdf2:sha256:600000$...', 'USER', 500.0);

-- ============================================
-- 创建索引（优化查询性能）
-- ============================================

CREATE INDEX IF NOT EXISTS idx_charge_request_status ON charge_request(status);
CREATE INDEX IF NOT EXISTS idx_charge_request_scenario ON charge_request(scenario_id);
CREATE INDEX IF NOT EXISTS idx_charge_request_pool_type ON charge_request(waiting_pool_type);
CREATE INDEX IF NOT EXISTS idx_station_scenario ON charging_station(scenario_id);
CREATE INDEX IF NOT EXISTS idx_station_status ON charging_station(status);
CREATE INDEX IF NOT EXISTS idx_scenario_active ON system_scenario_config(is_active);
