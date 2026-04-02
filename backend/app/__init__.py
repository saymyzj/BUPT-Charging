from flask import Flask
from flask_cors import CORS
from app.config import config


def create_app(config_name='default'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
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
    from app.routes.request import request_bp
    from app.routes.stations import stations_bp
    from app.routes.batch_simulate import batch_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(request_bp, url_prefix='/api/request')
    app.register_blueprint(stations_bp, url_prefix='/api/stations')
    app.register_blueprint(batch_bp, url_prefix='/api/batch')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # 初始化数据库
    from app.utils.db import init_db
    init_db(app)
    
    return app
