import request from './request'

// ==========================================
// V3 正式接口 — 基于 成员C页面设计清单 §7
// ==========================================

// ---------- 健康检查 ----------
export const checkHealth = () => request({ url: '/api/health', method: 'get' })

// ======================
// 7.1 用户端接口
// ======================

// 登录 / 注册
export const login = (data) => request({ url: '/api/auth/login', method: 'post', data })
export const register = (data) => request({ url: '/api/auth/register', method: 'post', data })
export const getProfile = () => request({ url: '/api/auth/profile', method: 'get' })

// 提交充电请求
export const createChargeRequest = (data) => request({ url: '/api/request/create', method: 'post', data })

// 查询请求状态（轮询）
export const getRequestStatus = (requestId) => request({ url: `/api/request/status/${requestId}`, method: 'get' })

// 修改充电模式
export const updateChargeMode = (data) => request({ url: '/api/request/mode', method: 'put', data })

// 修改请求电量
export const updateRequestEnergy = (data) => request({ url: '/api/request/energy', method: 'put', data })

// 取消请求（等候区取消）
export const cancelRequest = (data) => request({ url: '/api/request/cancel', method: 'post', data })

// 提前结束（充电区取消 / 提前结束）
export const stopRequest = (data) => request({ url: '/api/request/stop', method: 'post', data })

// 查询详单
export const getRequestDetail = (requestId) => request({ url: `/api/request/detail/${requestId}`, method: 'get' })

// ======================
// 7.2 管理端接口
// ======================

// 系统配置
export const getSystemConfig = () => request({ url: '/api/admin/system/config', method: 'get' })
export const setDispatchMode = (data) => request({ url: '/api/admin/system/dispatch-mode', method: 'put', data })
export const setFaultDispatchMode = (data) => request({ url: '/api/admin/system/fault-dispatch-mode', method: 'put', data })

// 充电桩管理
export const getStations = () => request({ url: '/api/admin/stations', method: 'get' })
export const getStationQueue = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/queue`, method: 'get' })
export const startStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/start`, method: 'post' })
export const shutdownStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/shutdown`, method: 'post' })
export const faultStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/fault`, method: 'post' })
export const recoverStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/recover`, method: 'post' })

// 用户管理
export const getUsers = () => request({ url: '/api/admin/users', method: 'get' })
export const getUserDetail = (userId) => request({ url: `/api/admin/users/${userId}`, method: 'get' })
export const updateBatteryCapacity = (userId, data) => request({ url: `/api/admin/users/${userId}/battery-capacity`, method: 'put', data })

// 报表统计
export const getReports = (granularity) => request({ url: '/api/admin/reports', method: 'get', params: { granularity } })
