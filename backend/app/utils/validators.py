from datetime import datetime


def validate_create_request(data):
    """
    校验创建充电请求参数
    
    Args:
        data: 请求体数据
    
    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []
    
    # 必填字段检查
    required = ['request_time', 'charge_mode', 'request_energy']
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # charge_mode校验
    if data['charge_mode'] not in ['FAST', 'SLOW']:
        errors.append("charge_mode must be FAST or SLOW")
    
    # request_energy校验
    try:
        energy = float(data['request_energy'])
        if energy <= 0:
            errors.append("request_energy must be positive")
        if energy > 100:  # 建议上限100kWh
            errors.append("request_energy exceeds maximum (100 kWh)")
    except (ValueError, TypeError):
        errors.append("request_energy must be a number")
    
    # request_time格式校验（ISO 8601）
    try:
        datetime.fromisoformat(data['request_time'].replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        errors.append("request_time must be ISO 8601 format")
    
    return len(errors) == 0, errors


def validate_cancel_request(data):
    """
    校验取消排队请求参数
    
    Args:
        data: 请求体数据
    
    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []
    
    if 'request_id' not in data:
        errors.append("Missing required field: request_id")
    
    if 'cancel_time' not in data:
        errors.append("Missing required field: cancel_time")
    else:
        try:
            datetime.fromisoformat(data['cancel_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append("cancel_time must be ISO 8601 format")
    
    return len(errors) == 0, errors


def validate_confirm_arrival_request(data):
    """
    校验确认到场请求参数
    
    Args:
        data: 请求体数据
    
    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []
    
    if 'request_id' not in data:
        errors.append("Missing required field: request_id")
    
    if 'confirm_time' not in data:
        errors.append("Missing required field: confirm_time")
    else:
        try:
            datetime.fromisoformat(data['confirm_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append("confirm_time must be ISO 8601 format")
    
    return len(errors) == 0, errors


def validate_interrupt_request(data):
    """
    校验中断充电请求参数
    
    Args:
        data: 请求体数据
    
    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []
    
    if 'request_id' not in data:
        errors.append("Missing required field: request_id")
    
    if 'interrupt_time' not in data:
        errors.append("Missing required field: interrupt_time")
    else:
        try:
            datetime.fromisoformat(data['interrupt_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append("interrupt_time must be ISO 8601 format")
    
    return len(errors) == 0, errors


def validate_confirm_leave_request(data):
    """
    校验确认挪车请求参数
    
    Args:
        data: 请求体数据
    
    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []
    
    if 'request_id' not in data:
        errors.append("Missing required field: request_id")
    
    if 'leave_time' not in data:
        errors.append("Missing required field: leave_time")
    else:
        try:
            datetime.fromisoformat(data['leave_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append("leave_time must be ISO 8601 format")
    
    return len(errors) == 0, errors


def validate_pay_request(data):
    """
    校验支付请求参数
    
    Args:
        data: 请求体数据
    
    Returns:
        (is_valid: bool, errors: list)
    """
    errors = []
    
    if 'request_id' not in data:
        errors.append("Missing required field: request_id")
    
    if 'pay_time' not in data:
        errors.append("Missing required field: pay_time")
    else:
        try:
            datetime.fromisoformat(data['pay_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append("pay_time must be ISO 8601 format")
    
    if 'pay_amount' not in data:
        errors.append("Missing required field: pay_amount")
    else:
        try:
            amount = float(data['pay_amount'])
            if amount < 0:
                errors.append("pay_amount must be non-negative")
        except (ValueError, TypeError):
            errors.append("pay_amount must be a number")
    
    return len(errors) == 0, errors
