-- ============================================
-- 智能充电桩调度计费系统 - 数据库初始化脚本
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'USER' CHECK(role IN ('USER', 'ADMIN')),
    balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 充电桩表
CREATE TABLE IF NOT EXISTS charging_station (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_code TEXT UNIQUE NOT NULL,
    station_type TEXT NOT NULL CHECK(station_type IN ('FAST', 'SLOW')),
    power_kw REAL NOT NULL,
    status TEXT DEFAULT 'IDLE' CHECK(status IN ('IDLE', 'RESERVED', 'CHARGING', 'WAITING_TO_LEAVE', 'FAULT')),
    current_request_id INTEGER,
    available_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_request_id) REFERENCES charge_request(id)
);

-- 充电请求表
CREATE TABLE IF NOT EXISTS charge_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    charge_mode TEXT NOT NULL CHECK(charge_mode IN ('FAST', 'SLOW')),
    request_energy REAL NOT NULL,
    remaining_energy REAL DEFAULT 0.0,
    actual_energy REAL DEFAULT 0.0,
    battery_limit_energy REAL DEFAULT 100.0,
    status TEXT DEFAULT 'PENDING' CHECK(status IN (
        'PENDING', 'WAITING', 'CALLED', 'CONFIRMED', 'CHARGING',
        'COMPLETED', 'COMPLETED_EARLY', 'INTERRUPTED', 'CANCELLED',
        'NO_SHOW', 'FAULT_REQUEUE'
    )),
    submit_time TIMESTAMP NOT NULL,
    estimated_wait_seconds INTEGER DEFAULT 0,
    estimated_start_time TIMESTAMP,
    estimated_finish_time TIMESTAMP,
    estimated_service_seconds INTEGER DEFAULT 0,
    last_called_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    assigned_station_id INTEGER,
    actual_service_seconds INTEGER DEFAULT 0,
    priority_score REAL DEFAULT 0.0,
    retry_count INTEGER DEFAULT 0,
    no_show_count INTEGER DEFAULT 0,
    fault_requeue_flag INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (assigned_station_id) REFERENCES charging_station(id)
);

-- 充电会话表
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

-- 计费记录表
CREATE TABLE IF NOT EXISTS billing_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    billing_mode TEXT DEFAULT 'ENERGY' CHECK(billing_mode IN ('ENERGY', 'TIME')),
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

-- 调度事件日志表
CREATE TABLE IF NOT EXISTS scheduler_event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    request_id TEXT,
    station_id TEXT,
    event_payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知表
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

-- 调度配置表
CREATE TABLE IF NOT EXISTS scheduler_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 初始数据插入
-- ============================================

-- 插入充电桩初始数据（2个快充桩，3个慢充桩）
INSERT OR IGNORE INTO charging_station (station_code, station_type, power_kw) VALUES
('FAST_01', 'FAST', 30.0),
('FAST_02', 'FAST', 30.0),
('SLOW_01', 'SLOW', 7.0),
('SLOW_02', 'SLOW', 7.0),
('SLOW_03', 'SLOW', 7.0);

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
('OCCUPANCY_START_AFTER_MINUTES', '10');

-- 插入测试用户（可选）
INSERT OR IGNORE INTO user (username, password_hash, role, balance) VALUES
('admin', 'pbkdf2:sha256:600000$...', 'ADMIN', 1000.0),
('test_user', 'pbkdf2:sha256:600000$...', 'USER', 500.0);
