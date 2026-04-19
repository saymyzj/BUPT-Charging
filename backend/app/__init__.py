from flask import Flask
from flask_cors import CORS
from app.config import config
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _configure_runtime_dirs(app):
    db_parent = Path(app.config['DATABASE_PATH']).expanduser().resolve().parent
    log_dir = Path(app.config['LOG_DIR']).expanduser().resolve()
    db_parent.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)


def _configure_logging(app):
    log_dir = Path(app.config['LOG_DIR']).expanduser().resolve()
    handler = RotatingFileHandler(
        log_dir / 'backend.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def create_app(config_name='default'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    _configure_runtime_dirs(app)
    _configure_logging(app)
    
    # 启用CORS，支持跨设备访问
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 注册蓝图
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.request import request_bp
    from app.routes.stations import stations_bp
    from app.routes.batch_simulate import batch_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(request_bp, url_prefix='/api/request')
    app.register_blueprint(stations_bp, url_prefix='/api/stations')
    app.register_blueprint(batch_bp, url_prefix='/api/test')
    app.register_blueprint(batch_bp, url_prefix='/api/batch', name='batch_legacy')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # 初始化数据库
    from app.utils.db import init_db
    init_db(app)
    
    return app
