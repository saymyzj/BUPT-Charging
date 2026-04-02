from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    用于验证服务是否正常运行，以及跨设备连通性测试

    Returns:
        {
            "status": "ok",
            "timestamp": "2026-03-31T10:00:00"
        }
    """
    # 注意：/health 接口使用裸结构返回，不套用统一响应格式
    # 这是为了最基础的连通性检查，即使响应包装逻辑出错也能正常返回
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })
