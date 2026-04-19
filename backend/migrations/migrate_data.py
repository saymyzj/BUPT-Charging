#!/usr/bin/env python3
"""
数据库迁移工具
用于从旧版本数据库迁移到新版本（V2）
支持：V1 -> V2 迁移

迁移内容：
1. 创建新表（system_scenario_config）
2. 添加新字段到现有表
3. 迁移现有数据
4. 创建索引

使用方法：
    python migrate_data.py

作者：成员 B
日期：2026-04-02
"""

import sqlite3
import os
import sys
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'charging_system.db')
MIGRATION_SCHEMA = os.path.join(os.path.dirname(__file__), 'init_schema_v2.sql')


def check_database_exists():
    """检查数据库是否存在"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库不存在: {DB_PATH}")
        print("提示：如果是新部署，直接运行 init_schema_v2.sql 即可")
        return False
    return True


def check_table_exists(conn, table_name):
    """检查表是否存在"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def check_column_exists(conn, table_name, column_name):
    """检查字段是否存在"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def get_migration_version(conn):
    """获取当前迁移版本"""
    try:
        cursor = conn.cursor()
        # 尝试查询 system_scenario_config 表判断版本
        if check_table_exists(conn, 'system_scenario_config'):
            return 'V2'
        return 'V1'
    except:
        return 'V1'


def migrate_v1_to_v2(conn):
    """
    执行 V1 -> V2 迁移
    """
    cursor = conn.cursor()
    print("🚀 开始执行 V1 -> V2 迁移...")
    
    # 1. 创建 system_scenario_config 表
    print("📋 步骤 1/6: 创建 system_scenario_config 表...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_scenario_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name TEXT NOT NULL,
            fast_station_count INTEGER DEFAULT 2,
            slow_station_count INTEGER DEFAULT 3,
            waiting_area_capacity INTEGER DEFAULT 6,
            station_queue_mode TEXT DEFAULT 'UNIFORM_CAPACITY'
                CHECK(station_queue_mode IN ('UNIFORM_CAPACITY', 'STATION_SNAPSHOT')),
            station_queue_capacity INTEGER DEFAULT 3,
            is_active INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ system_scenario_config 表创建成功")
    
    # 2. 插入默认场景配置
    print("📋 步骤 2/6: 插入默认场景配置...")
    cursor.execute("""
        INSERT OR IGNORE INTO system_scenario_config (
            config_name, fast_station_count, slow_station_count, 
            waiting_area_capacity, station_queue_mode, 
            station_queue_capacity, is_active, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        '默认场景',
        2, 3, 6,
        'UNIFORM_CAPACITY',
        3,
        1,
        '从V1迁移的默认配置：2个快充桩，3个慢充桩'
    ))
    print("   ✅ 默认场景配置插入成功")
    
    # 3. 为 charging_station 表添加新字段
    print("📋 步骤 3/6: 更新 charging_station 表...")
    new_columns = [
        ('initial_queue_length', 'INTEGER DEFAULT 0'),
        ('initial_status', 'TEXT DEFAULT \'IDLE\''),
        ('initial_remaining_seconds', 'INTEGER'),
        ('scenario_id', 'INTEGER')
    ]
    
    for col_name, col_type in new_columns:
        if not check_column_exists(conn, 'charging_station', col_name):
            cursor.execute(f"""
                ALTER TABLE charging_station 
                ADD COLUMN {col_name} {col_type}
            """)
            print(f"   ✅ 添加字段: {col_name}")
        else:
            print(f"   ⏭️  字段已存在: {col_name}")
    
    # 更新现有充电桩的 scenario_id
    cursor.execute("""
        UPDATE charging_station 
        SET scenario_id = 1 
        WHERE scenario_id IS NULL
    """)
    print("   ✅ 更新充电桩 scenario_id 关联")
    
    # 4. 为 charge_request 表添加新字段
    print("📋 步骤 4/6: 更新 charge_request 表...")
    new_columns = [
        ('waiting_pool_type', 'TEXT'),
        ('scenario_id', 'INTEGER')
    ]
    
    for col_name, col_type in new_columns:
        if not check_column_exists(conn, 'charge_request', col_name):
            cursor.execute(f"""
                ALTER TABLE charge_request 
                ADD COLUMN {col_name} {col_type}
            """)
            print(f"   ✅ 添加字段: {col_name}")
        else:
            print(f"   ⏭️  字段已存在: {col_name}")
    
    # 5. 更新 scheduler_config 表（添加优先级权重配置）
    print("📋 步骤 5/6: 更新 scheduler_config 表...")
    new_configs = [
        ('PRIORITY_WEIGHT_A', '1.0'),
        ('PRIORITY_WEIGHT_B', '0.5'),
        ('PRIORITY_WEIGHT_C', '1.0'),
        ('PRIORITY_WEIGHT_D', '0.3'),
        ('PRIORITY_WEIGHT_E', '0.8')
    ]
    
    for key, value in new_configs:
        cursor.execute("""
            INSERT OR IGNORE INTO scheduler_config (config_key, config_value)
            VALUES (?, ?)
        """, (key, value))
    print("   ✅ 优先级权重配置添加成功")
    
    # 6. 创建索引
    print("📋 步骤 6/6: 创建索引...")
    indexes = [
        ("idx_charge_request_scenario", "charge_request(scenario_id)"),
        ("idx_charge_request_pool_type", "charge_request(waiting_pool_type)"),
        ("idx_station_scenario", "charging_station(scenario_id)"),
        ("idx_scenario_active", "system_scenario_config(is_active)")
    ]
    
    for idx_name, idx_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            print(f"   ✅ 创建索引: {idx_name}")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  索引创建失败（可能已存在）: {idx_name}")
    
    conn.commit()
    print("\n✅ V1 -> V2 迁移完成！")
    return True


def verify_migration(conn):
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    cursor = conn.cursor()
    
    # 检查表
    tables = ['system_scenario_config', 'charging_station', 'charge_request']
    for table in tables:
        if check_table_exists(conn, table):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count} 条记录")
        else:
            print(f"   ❌ {table}: 表不存在")
    
    # 检查场景配置
    cursor.execute("SELECT * FROM system_scenario_config WHERE is_active = 1")
    active_scenario = cursor.fetchone()
    if active_scenario:
        print(f"\n📊 当前激活场景:")
        print(f"   名称: {active_scenario[1]}")
        print(f"   快充桩: {active_scenario[2]} 个")
        print(f"   慢充桩: {active_scenario[3]} 个")
        print(f"   等待区容量: {active_scenario[4]}")
        print(f"   队列模式: {active_scenario[5]}")


def backup_database():
    """备份数据库"""
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"💾 数据库已备份到: {backup_path}")
        return backup_path
    return None


def main():
    """主函数"""
    print("=" * 60)
    print("智能充电桩调度计费系统 - 数据库迁移工具")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    # 检查数据库
    if not check_database_exists():
        sys.exit(1)
    
    # 备份数据库
    backup_path = backup_database()
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # 检查当前版本
        current_version = get_migration_version(conn)
        print(f"📌 当前数据库版本: {current_version}")
        
        if current_version == 'V2':
            print("\n✅ 数据库已经是 V2 版本，无需迁移")
            verify_migration(conn)
        else:
            # 执行迁移
            print("\n🚀 开始迁移...")
            if migrate_v1_to_v2(conn):
                verify_migration(conn)
                print("\n🎉 迁移成功完成！")
                if backup_path:
                    print(f"💡 如有问题，可使用备份恢复: {backup_path}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"\n❌ 迁移失败: {e}")
        if backup_path:
            print(f"💡 可使用备份恢复: {backup_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
