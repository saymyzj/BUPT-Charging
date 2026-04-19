-- ============================================
-- 智能充电桩调度计费系统 - 数据库初始化脚本 V3（Day 3 最小闭环）
-- 版本：V3.0
-- 日期：2026-04-19
-- 说明：支撑认证、创建请求、状态查询的最小可运行基线
-- ============================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    battery_capacity REAL NOT NULL CHECK (battery_capacity > 0),
    role TEXT NOT NULL DEFAULT 'USER' CHECK(role IN ('USER', 'ADMIN')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS charging_station (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_code TEXT UNIQUE NOT NULL,
    charge_mode TEXT NOT NULL CHECK(charge_mode IN ('FAST', 'SLOW')),
    power_kw REAL NOT NULL CHECK(power_kw > 0),
    station_status TEXT NOT NULL DEFAULT 'RUNNING'
        CHECK(station_status IN ('RUNNING', 'SHUTDOWN', 'FAULT')),
    queue_capacity INTEGER NOT NULL DEFAULT 2 CHECK(queue_capacity >= 1),
    current_queue_length INTEGER NOT NULL DEFAULT 0 CHECK(current_queue_length >= 0),
    current_request_id INTEGER,
    available_time TIMESTAMP,
    total_charge_count INTEGER NOT NULL DEFAULT 0,
    total_charge_seconds INTEGER NOT NULL DEFAULT 0,
    total_charge_energy REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_request_id) REFERENCES charge_request(id)
);

CREATE TABLE IF NOT EXISTS charge_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    charge_mode TEXT NOT NULL CHECK(charge_mode IN ('FAST', 'SLOW')),
    request_energy REAL NOT NULL CHECK(request_energy > 0 AND request_energy <= 300),
    actual_energy REAL NOT NULL DEFAULT 0.0,
    request_status TEXT NOT NULL
        CHECK(request_status IN (
            'WAITING_AREA', 'QUEUED', 'CHARGING',
            'COMPLETED', 'COMPLETED_EARLY', 'CANCELLED', 'FAULT_INTERRUPTED'
        )),
    queue_number TEXT UNIQUE NOT NULL,
    waiting_area_order INTEGER,
    station_id INTEGER,
    station_queue_position INTEGER,
    request_time TIMESTAMP NOT NULL,
    estimated_wait_seconds INTEGER,
    estimated_start_time TIMESTAMP,
    estimated_finish_time TIMESTAMP,
    charge_start_time TIMESTAMP,
    charge_stop_time TIMESTAMP,
    charge_duration_seconds INTEGER NOT NULL DEFAULT 0,
    fault_source_request_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (station_id) REFERENCES charging_station(id),
    FOREIGN KEY (fault_source_request_id) REFERENCES charge_request(id)
);

CREATE TABLE IF NOT EXISTS charging_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    actual_energy REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'CHARGING', 'COMPLETED', 'COMPLETED_EARLY', 'FAULT_INTERRUPTED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES charge_request(id),
    FOREIGN KEY (station_id) REFERENCES charging_station(id)
);

CREATE TABLE IF NOT EXISTS request_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detail_id TEXT UNIQUE NOT NULL,
    request_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    station_code TEXT NOT NULL,
    actual_energy REAL NOT NULL DEFAULT 0.0,
    charge_duration_seconds INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP NOT NULL,
    detail_generated_at TIMESTAMP NOT NULL,
    charge_fee REAL NOT NULL DEFAULT 0.0,
    service_fee REAL NOT NULL DEFAULT 0.0,
    total_fee REAL NOT NULL DEFAULT 0.0,
    request_status TEXT NOT NULL
        CHECK(request_status IN ('COMPLETED', 'COMPLETED_EARLY', 'FAULT_INTERRUPTED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES charge_request(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS scheduler_event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    request_id TEXT,
    station_id TEXT,
    event_payload TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS scheduler_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO charging_station (
    station_code, charge_mode, power_kw, station_status, queue_capacity
) VALUES
('FAST_01', 'FAST', 30.0, 'RUNNING', 2),
('FAST_02', 'FAST', 30.0, 'RUNNING', 2),
('FAST_03', 'FAST', 30.0, 'RUNNING', 2),
('SLOW_01', 'SLOW', 10.0, 'RUNNING', 2),
('SLOW_02', 'SLOW', 10.0, 'RUNNING', 2);

INSERT OR IGNORE INTO scheduler_config (config_key, config_value) VALUES
('dispatch_mode', 'NORMAL'),
('fault_dispatch_mode', 'TIME_ORDER'),
('peak_price', '1.0'),
('flat_price', '0.7'),
('valley_price', '0.4'),
('service_fee_unit_price', '0.8');

CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_charge_request_user_status ON charge_request(user_id, request_status);
CREATE INDEX IF NOT EXISTS idx_charge_request_mode_status_order ON charge_request(charge_mode, request_status, waiting_area_order);
CREATE INDEX IF NOT EXISTS idx_charge_request_queue_number ON charge_request(queue_number);
CREATE INDEX IF NOT EXISTS idx_charging_station_mode_status ON charging_station(charge_mode, station_status);
CREATE INDEX IF NOT EXISTS idx_request_detail_request ON request_detail(request_id);
CREATE INDEX IF NOT EXISTS idx_request_detail_generated_at ON request_detail(detail_generated_at);
