from flask import Blueprint
from datetime import datetime
from app.utils.response import success_response

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    用于验证服务是否正常运行，以及跨设备连通性测试
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "status": "ok",
                "timestamp": "2026-03-31T10:00:00"
            }
        }
    """
    return success_response({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })
