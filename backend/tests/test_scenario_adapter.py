"""
场景适配器单元测试
测试两种适配模式和初始化逻辑

作者：成员 B
日期：2026-04-02
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.scenario_adapter import (
    ScenarioAdapter, StationSnapshot, 
    adapt_and_initialize, get_scenario_adapter
)
from app.services.config_manager import ConfigManager
from app.enums import StationQueueMode, StationStatus, ChargeMode
from app.utils.db import query_db, execute_db
import sqlite3
import tempfile


class TestStationSnapshot(unittest.TestCase):
    """测试桩级快照数据类"""
    
    def test_valid_snapshot(self):
        """测试有效快照"""
        data = {
            'station_code': 'FAST_01',
            'station_type': 'FAST',
            'status': 'CHARGING',
            'current_user_remaining_seconds': 900,
            'queue_length': 3
        }
        snapshot = StationSnapshot(data)
        is_valid, message = snapshot.validate()
        
        self.assertTrue(is_valid)
        self.assertEqual(snapshot.station_code, 'FAST_01')
        self.assertEqual(snapshot.queue_length, 3)
    
    def test_invalid_station_type(self):
        """测试无效桩类型"""
        data = {
            'station_code': 'FAST_01',
            'station_type': 'SUPER_FAST',  # 无效类型
            'status': 'IDLE'
        }
        snapshot = StationSnapshot(data)
        is_valid, message = snapshot.validate()
        
        self.assertFalse(is_valid)
        self.assertIn('无效', message)
    
    def test_negative_queue_length(self):
        """测试负数排队人数"""
        data = {
            'station_code': 'FAST_01',
            'station_type': 'FAST',
            'status': 'IDLE',
            'queue_length': -1
        }
        snapshot = StationSnapshot(data)
        is_valid, message = snapshot.validate()
        
        self.assertFalse(is_valid)


class TestScenarioAdapter(unittest.TestCase):
    """测试场景适配器"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        # 初始化数据库
        from app.utils.db import init_db
        init_db(self.db_path)
        
        self.adapter = ScenarioAdapter()
    
    def tearDown(self):
        """测试后清理"""
        import os
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_adapt_uniform_capacity(self):
        """测试统一容量模式适配"""
        config = {
            'config_name': '测试统一容量场景',
            'fast_station_count': 2,
            'slow_station_count': 3,
            'waiting_area_capacity': 10,
            'station_queue_mode': 'UNIFORM_CAPACITY',
            'station_queue_capacity': 5
        }
        
        success, message, config_id = self.adapter.adapt_scenario(config)
        
        self.assertTrue(success, message)
        self.assertGreater(config_id, 0)
        
        # 验证配置创建
        scenario = ConfigManager.get_config(config_id)
        self.assertIsNotNone(scenario)
        self.assertEqual(scenario.fast_station_count, 2)
        self.assertEqual(scenario.slow_station_count, 3)
        self.assertEqual(scenario.station_queue_mode, 'UNIFORM_CAPACITY')
        
        # 验证充电桩创建
        stations = query_db(
            "SELECT COUNT(*) as cnt FROM charging_station WHERE scenario_id = ?",
            [config_id],
            one=True
        )
        self.assertEqual(stations['cnt'], 5)  # 2快+3慢
    
    def test_adapt_station_snapshot(self):
        """测试桩级快照模式适配"""
        config = {
            'config_name': '测试快照场景',
            'waiting_area_capacity': 8,
            'station_queue_mode': 'STATION_SNAPSHOT',
            'station_snapshots': [
                {
                    'station_code': 'FAST_01',
                    'station_type': 'FAST',
                    'status': 'CHARGING',
                    'current_user_remaining_seconds': 600,
                    'queue_length': 2
                },
                {
                    'station_code': 'FAST_02',
                    'station_type': 'FAST',
                    'status': 'IDLE',
                    'queue_length': 0
                },
                {
                    'station_code': 'SLOW_01',
                    'station_type': 'SLOW',
                    'status': 'CHARGING',
                    'current_user_remaining_seconds': 1200,
                    'queue_length': 1
                }
            ]
        }
        
        success, message, config_id = self.adapter.adapt_scenario(config)
        
        self.assertTrue(success, message)
        self.assertGreater(config_id, 0)
        
        # 验证虚拟请求创建
        virtual_requests = query_db(
            """SELECT COUNT(*) as cnt FROM charge_request 
               WHERE scenario_id = ? AND request_id LIKE 'VIRTUAL_%'""",
            [config_id],
            one=True
        )
        self.assertEqual(virtual_requests['cnt'], 3)  # 2+0+1=3个虚拟请求
    
    def test_invalid_queue_mode(self):
        """测试无效队列模式"""
        config = {
            'station_queue_mode': 'INVALID_MODE'
        }
        
        success, message, config_id = self.adapter.adapt_scenario(config)
        
        self.assertFalse(success)
        self.assertIn('无效', message)
        self.assertEqual(config_id, -1)
    
    def test_convert_to_internal_state(self):
        """测试转换为内部状态"""
        # 先创建一个场景
        config = {
            'config_name': '测试内部状态转换',
            'fast_station_count': 1,
            'slow_station_count': 1,
            'waiting_area_capacity': 5,
            'station_queue_mode': 'UNIFORM_CAPACITY',
            'station_queue_capacity': 3
        }
        
        success, message, config_id = self.adapter.adapt_scenario(config)
        self.assertTrue(success)
        
        # 转换为内部状态
        internal_state = self.adapter.convert_to_internal_state(config_id)
        
        self.assertIsNotNone(internal_state)
        self.assertEqual(internal_state['scenario_id'], config_id)
        self.assertIn('stations', internal_state)
        self.assertIn('waiting_pools', internal_state)
        self.assertIn('capacity', internal_state)
        
        # 验证容量信息
        self.assertEqual(internal_state['capacity']['total'], 5)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        from app.utils.db import init_db
        init_db(self.db_path)
    
    def tearDown(self):
        """测试后清理"""
        import os
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_full_workflow_uniform_capacity(self):
        """测试统一容量模式完整流程"""
        # 1. 适配场景
        config = {
            'config_name': '集成测试-统一容量',
            'fast_station_count': 2,
            'slow_station_count': 2,
            'waiting_area_capacity': 6,
            'station_queue_mode': 'UNIFORM_CAPACITY',
            'station_queue_capacity': 3
        }
        
        success, message, config_id = adapt_and_initialize(config)
        self.assertTrue(success, message)
        
        # 2. 验证场景激活
        active_config = ConfigManager.get_active_config()
        self.assertIsNotNone(active_config)
        self.assertEqual(active_config.id, config_id)
        
        # 3. 验证等待池初始化
        from app.services.waiting_pool import WaitingPoolManager
        manager = WaitingPoolManager()
        status = manager.get_pool_status()
        
        self.assertEqual(status['total_waiting'], 0)  # 统一容量模式初始为空
        self.assertEqual(status['capacity'], 6)
    
    def test_full_workflow_snapshot(self):
        """测试快照模式完整流程"""
        config = {
            'config_name': '集成测试-快照模式',
            'waiting_area_capacity': 10,
            'station_queue_mode': 'STATION_SNAPSHOT',
            'station_snapshots': [
                {
                    'station_code': 'FAST_01',
                    'station_type': 'FAST',
                    'status': 'CHARGING',
                    'current_user_remaining_seconds': 300,
                    'queue_length': 2
                },
                {
                    'station_code': 'SLOW_01',
                    'station_type': 'SLOW',
                    'status': 'IDLE',
                    'queue_length': 0
                }
            ]
        }
        
        success, message, config_id = adapt_and_initialize(config)
        self.assertTrue(success, message)
        
        # 验证虚拟请求进入等待池
        from app.services.waiting_pool import WaitingPoolManager
        manager = WaitingPoolManager()
        status = manager.get_pool_status()
        
        self.assertEqual(status['total_waiting'], 2)  # 2个虚拟请求
        self.assertEqual(status['fast_pool']['count'], 2)
        self.assertEqual(status['slow_pool']['count'], 0)
    
    def test_scenario_reset(self):
        """测试场景重置"""
        # 创建并初始化场景
        config = {
            'config_name': '测试重置',
            'fast_station_count': 1,
            'slow_station_count': 1,
            'waiting_area_capacity': 5,
            'station_queue_mode': 'UNIFORM_CAPACITY',
            'station_queue_capacity': 3
        }
        
        success, message, config_id = adapt_and_initialize(config)
        self.assertTrue(success)
        
        # 添加一些请求到等待池
        from app.services.waiting_pool import WaitingPoolManager
        manager = WaitingPoolManager()
        
        # 创建测试请求
        execute_db("""
            INSERT INTO charge_request (
                request_id, charge_mode, request_energy, status,
                submit_time, waiting_pool_type, scenario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ['TEST_001', 'FAST', 20.0, 'WAITING', 
              '2026-04-02T10:00:00', 'FAST_POOL', config_id])
        
        # 验证请求已添加
        status = manager.get_pool_status()
        self.assertEqual(status['total_waiting'], 1)
        
        # 重置场景
        adapter = get_scenario_adapter()
        reset_success, reset_message = adapter.reset_scenario(config_id)
        self.assertTrue(reset_success, reset_message)
        
        # 验证等待池已清空
        status = manager.get_pool_status()
        self.assertEqual(status['total_waiting'], 0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestStationSnapshot))
    suite.addTests(loader.loadTestsFromTestCase(TestScenarioAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
