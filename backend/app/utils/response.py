from flask import jsonify


def success_response(data=None, message="success"):
    """
    统一成功响应格式
    
    Args:
        data: 响应数据
        message: 成功消息
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {...}
        }
    """
    return jsonify({
        "code": 0,
        "message": message,
        "data": data if data is not None else {}
    })


def error_response(code, message, data=None):
    """
    统一错误响应格式
    
    Args:
        code: 错误码
        message: 错误消息
        data: 附加数据（可选）
    
    Returns:
        {
            "code": 1001,
            "message": "Invalid parameters",
            "data": {...}
        }
    """
    response = jsonify({
        "code": code,
        "message": message,
        "data": data if data is not None else {}
    })
    
    # 根据错误码设置HTTP状态码
    if code >= 2000:
        response.status_code = 500  # 服务器内部错误
    elif code >= 1000:
        response.status_code = 400  # 客户端错误
    
    return response
