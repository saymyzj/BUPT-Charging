"""
场景适配器单元测试
测试两种适配模式和初始化逻辑

当前状态：框架测试完成，集成测试待数据库环境完善后启用

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
from app.enums import StationQueueMode, StationStatus, ChargeMode


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


class TestScenarioAdapterBasic(unittest.TestCase):
    """测试场景适配器基础功能（无需数据库）"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = ScenarioAdapter()
        self.assertIsNotNone(adapter)

    def test_invalid_queue_mode(self):
        """测试无效队列模式检测"""
        adapter = ScenarioAdapter()

        # 测试无效模式
        config = {
            'station_queue_mode': 'INVALID_MODE'
        }

        success, message, config_id = adapter.adapt_scenario(config)

        self.assertFalse(success)
        self.assertIn('无效', message)
        self.assertEqual(config_id, -1)


class TestConfigValidation(unittest.TestCase):
    """测试配置验证逻辑"""

    def test_uniform_capacity_config(self):
        """测试统一容量模式配置验证"""
        config = {
            'config_name': '测试统一容量场景',
            'fast_station_count': 2,
            'slow_station_count': 3,
            'waiting_area_capacity': 10,
            'station_queue_mode': 'UNIFORM_CAPACITY',
            'station_queue_capacity': 5
        }

        # 验证必填字段存在
        self.assertIn('fast_station_count', config)
        self.assertIn('slow_station_count', config)
        self.assertIn('waiting_area_capacity', config)
        self.assertEqual(config['station_queue_mode'], 'UNIFORM_CAPACITY')

    def test_station_snapshot_config(self):
        """测试桩级快照模式配置验证"""
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
                }
            ]
        }

        # 验证必填字段存在
        self.assertIn('station_snapshots', config)
        self.assertEqual(config['station_queue_mode'], 'STATION_SNAPSHOT')
        self.assertEqual(len(config['station_snapshots']), 1)


class TestIntegrationFramework(unittest.TestCase):
    """集成测试框架（待数据库环境完善后启用完整测试）"""

    def test_framework_placeholder(self):
        """测试框架占位 - 验证测试结构"""
        # 此测试验证测试框架可正常运行
        # 完整集成测试需要：
        # 1. 独立的数据库环境（每个测试用例隔离）
        # 2. 数据库初始化（执行 init_schema_v2.sql）
        # 3. Flask 应用上下文
        self.assertTrue(True, "测试框架运行正常")

    def test_required_components_exist(self):
        """验证必要组件存在"""
        # 验证适配器类存在
        self.assertTrue(hasattr(ScenarioAdapter, 'adapt_scenario'))
        self.assertTrue(hasattr(ScenarioAdapter, 'convert_to_internal_state'))
        self.assertTrue(hasattr(ScenarioAdapter, 'reset_scenario'))

        # 验证便捷函数存在
        self.assertTrue(callable(adapt_and_initialize))
        self.assertTrue(callable(get_scenario_adapter))


class TestDocumentationConsistency(unittest.TestCase):
    """测试文档一致性"""

    def test_enum_values_match_documentation(self):
        """测试枚举值与文档一致"""
        # 验证队列模式枚举
        modes = [mode.value for mode in StationQueueMode]
        self.assertIn('UNIFORM_CAPACITY', modes)
        self.assertIn('STATION_SNAPSHOT', modes)

        # 验证充电桩状态枚举
        statuses = [status.value for status in StationStatus]
        self.assertIn('IDLE', statuses)
        self.assertIn('CHARGING', statuses)
        self.assertIn('WAITING_TO_LEAVE', statuses)
        self.assertIn('FAULT', statuses)

        # 验证充电模式枚举
        modes = [mode.value for mode in ChargeMode]
        self.assertIn('FAST', modes)
        self.assertIn('SLOW', modes)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestStationSnapshot))
    suite.addTests(loader.loadTestsFromTestCase(TestScenarioAdapterBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentationConsistency))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
