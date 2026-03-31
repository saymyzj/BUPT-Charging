import os


class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or os.path.join(BASE_DIR, 'charging_system.db')
    
    # JWT配置
    JWT_EXPIRATION_HOURS = 24
    
    # 调度参数（单位：分钟）
    T_CALL_MINUTES = 5                    # 叫号后用户确认时间
    CONFIRM_TIMEOUT_MINUTES = 3           # 确认到场超时时间
    ARRIVAL_TIMEOUT_MINUTES = 5           # 到场超时时间
    LEAVE_BUFFER_MINUTES = 10             # 挪车缓冲时间
    
    # 计费参数
    BILLING_MODE = 'ENERGY'               # 计费模式：ENERGY（按电量）或 TIME（按时间）
    ENERGY_PRICE = 1.5                    # 电费单价（元/kWh）
    TIME_PRICE = 0.0                      # 时间费单价（元/分钟）
    OCCUPANCY_PRICE = 0.5                 # 占位费单价（元/分钟）
    OCCUPANCY_START_AFTER_MINUTES = 10    # 占位费开始计算时间（充电完成后）


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = ':memory:'  # 内存数据库


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
