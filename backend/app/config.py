import os
from pathlib import Path


def _env_int(name, default):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return int(value)


class Config:
    """Base runtime configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = (
        os.environ.get("DB_PATH")
        or os.environ.get("DATABASE_PATH")
        or os.path.join(BASE_DIR, "charging_system.db")
    )
    LOG_DIR = os.environ.get("LOG_DIR") or str(Path(BASE_DIR) / "logs")
    LISTEN_HOST = os.environ.get("LISTEN_HOST") or "127.0.0.1"
    LISTEN_PORT = _env_int("LISTEN_PORT", 5000)
    AUTO_REBUILD_INCOMPATIBLE_DB = os.environ.get("AUTO_REBUILD_INCOMPATIBLE_DB", "1")

    JWT_EXPIRATION_HOURS = _env_int("JWT_EXPIRATION_HOURS", 24)

    FAST_CHARGING_PILE_NUM = _env_int("FAST_CHARGING_PILE_NUM", 3)
    TRICKLE_CHARGING_PILE_NUM = _env_int("TRICKLE_CHARGING_PILE_NUM", 2)
    WAITING_AREA_SIZE = _env_int("WAITING_AREA_SIZE", 6)
    CHARGING_QUEUE_LEN = _env_int("CHARGING_QUEUE_LEN", 2)
    DISPATCH_MODE = os.environ.get("DISPATCH_MODE", "NORMAL")
    FAULT_DISPATCH_MODE = os.environ.get("FAULT_DISPATCH_MODE", "TIME_ORDER")

    # Legacy config values kept for modules not yet removed from the repo.
    T_CALL_MINUTES = 5
    CONFIRM_TIMEOUT_MINUTES = 3
    ARRIVAL_TIMEOUT_MINUTES = 5
    LEAVE_BUFFER_MINUTES = 10
    BILLING_MODE = "ENERGY"
    ENERGY_PRICE = 1.5
    TIME_PRICE = 0.0
    OCCUPANCY_PRICE = 0.5
    OCCUPANCY_START_AFTER_MINUTES = 10


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    DATABASE_PATH = os.environ.get("TEST_DATABASE_PATH") or os.path.join(Config.BASE_DIR, "charging_system_test.db")
    LOG_DIR = os.environ.get("TEST_LOG_DIR") or os.path.join(Config.BASE_DIR, "logs", "test")


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
