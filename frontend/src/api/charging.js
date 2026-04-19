import request from './request';

// ==========================================
// 健康检查与服务探测
// ==========================================
export const checkHealth = () => {
  return request({
    url: '/health',
    method: 'get'
  });
};

// ==========================================
// 充电请求与调度相关 (用户端核心流程)
// 对应7个已冻结接口
// ==========================================

/**
 * 1. 提交充电请求
 * @param {Object} data 
 * @param {string} data.request_time - ISO 8601 时间字符串
 * @param {string} data.charge_mode - 'FAST' | 'SLOW'
 * @param {number} data.request_energy - 请求电量(kWh)
 */
export const createChargeRequest = (data) => {
  return request({
    url: '/api/request/create',
    method: 'post',
    data
  });
};

/**
 * 2. 查询请求状态 (用于轮询)
 * @param {string} requestId 
 */
export const getRequestStatus = (requestId) => {
  return request({
    url: `/api/request/status/${requestId}`,
    method: 'get'
  });
};

/**
 * 3. 取消排队
 * @param {Object} data 
 * @param {string} data.request_id 
 * @param {string} data.cancel_time 
 */
export const cancelQueue = (data) => {
  return request({
    url: '/api/request/cancel_queue',
    method: 'post',
    data
  });
};

/**
 * 4. 确认到场 (叫号后)
 * @param {Object} data
 * @param {string} data.request_id
 * @param {string} data.confirm_time
 */
export const confirmArrival = (data) => {
  return request({
    url: '/api/request/confirm_arrival',
    method: 'post',
    data
  });
};

/**
 * 5. 中断充电
 * @param {Object} data
 * @param {string} data.request_id
 * @param {string} data.interrupt_time 
 */
export const interruptCharge = (data) => {
  return request({
    url: '/api/request/interrupt_charge',
    method: 'post',
    data
  });
};

/**
 * 6. 确认挪车 (充电或中断后)
 * @param {Object} data
 * @param {string} data.request_id
 * @param {string} data.leave_time
 */
export const confirmLeave = (data) => {
  return request({
    url: '/api/request/confirm_leave',
    method: 'post',
    data
  });
};

// ==========================================
// 待解冻/待实施接口预留 (包含鉴权/登录)
// ==========================================

export const login = (data) => {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data
  });
};

export const register = (data) => {
  return request({
    url: '/api/auth/register',
    method: 'post',
    data
  });
};

export const getResult = (requestId) => {
  return request({
    url: `/api/request/result/${requestId}`,
    method: 'get'
  });
};

export const payRequest = (data) => {
  return request({
    url: '/api/request/pay',
    method: 'post',
    data
  });
};
