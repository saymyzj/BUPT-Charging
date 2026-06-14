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
export const updateProfileBatteryCapacity = (data) => request({ url: '/api/auth/profile/battery-capacity', method: 'put', data })

// 提交充电请求
export const createChargeRequest = (data) => request({ url: '/api/request/create', method: 'post', data })

// 查询请求状态（轮询）
export const getRequestStatus = (requestId) => request({ url: `/api/request/status/${requestId}`, method: 'get' })
export const getActiveRequest = () => request({ url: '/api/request/active', method: 'get' })

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
export const getRequestDetails = () => request({ url: '/api/request/details', method: 'get' })
export const payRequestDetail = (requestId) => request({ url: `/api/request/detail/${requestId}/pay`, method: 'post' })

// ======================
// 7.2 管理端接口
// ======================

// 系统配置
export const getSystemConfig = () => request({ url: '/api/admin/system/config', method: 'get' })
export const setDispatchMode = (data) => request({ url: '/api/admin/system/dispatch-mode', method: 'put', data })
export const setFaultDispatchMode = (data) => request({ url: '/api/admin/system/fault-dispatch-mode', method: 'put', data })

// 充电桩管理
export const getStations = () => request({ url: '/api/admin/stations', method: 'get' })
export const getStationsOverview = () => request({ url: '/api/stations/overview', method: 'get' })
export const getStationQueue = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/queue`, method: 'get' })
export const getWaitingArea = () => request({ url: '/api/admin/waiting-area', method: 'get' })
export const startStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/start`, method: 'post' })
export const shutdownStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/shutdown`, method: 'post' })
export const faultStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/fault`, method: 'post' })
export const recoverStation = (stationCode) => request({ url: `/api/admin/stations/${stationCode}/recover`, method: 'post' })

// 用户管理
export const getUsers = (params) => request({ url: '/api/admin/users', method: 'get', params })
export const getUserDetail = (userId) => request({ url: `/api/admin/users/${userId}`, method: 'get' })
export const updateBatteryCapacity = (userId, data) => request({ url: `/api/admin/users/${userId}/battery-capacity`, method: 'put', data })
export const exportAllUserDetailsXlsxUrl = '/api/admin/users/details/export.xlsx'
export const exportAllUserDetailsXlsx = () => request({
  url: exportAllUserDetailsXlsxUrl,
  method: 'get',
  responseType: 'blob',
})
export const exportAllUserBillsXlsxUrl = '/api/admin/users/bills/export.xlsx'
export const exportAllUserBillsXlsx = () => request({
  url: exportAllUserBillsXlsxUrl,
  method: 'get',
  responseType: 'blob',
})

// 报表统计
export const getReports = (granularity) => request({ url: '/api/admin/reports', method: 'get', params: { granularity } })

// 验收控制台
export const getAcceptanceState = () => request({ url: '/api/acceptance/state', method: 'get' })
export const initializeAcceptanceDatabase = (data) => request({ url: '/api/acceptance/initialize', method: 'post', data })
export const resetAcceptance = (data) => request({ url: '/api/acceptance/reset', method: 'post', data })
export const enableAcceptance = (data) => request({ url: '/api/acceptance/enable', method: 'post', data })
export const disableAcceptance = () => request({ url: '/api/acceptance/disable', method: 'post' })
export const setAcceptanceTime = (data) => request({ url: '/api/acceptance/time', method: 'put', data })
export const setAcceptanceStatus = (data) => request({ url: '/api/acceptance/status', method: 'put', data })
export const parseAcceptanceXlsx = (file) => {
  const data = new FormData()
  data.append('file', file)
  return request({ url: '/api/acceptance/xlsx/parse', method: 'post', data })
}
export const getAcceptanceEvents = () => request({ url: '/api/acceptance/events', method: 'get' })
export const saveAcceptanceEvents = (data) => request({ url: '/api/acceptance/events', method: 'put', data })
export const addAcceptanceEvent = (data) => request({ url: '/api/acceptance/events', method: 'post', data })
export const executeAcceptanceEvent = (eventId) => request({ url: `/api/acceptance/events/${eventId}/execute`, method: 'post' })
export const executeAcceptanceCurrent = () => request({ url: '/api/acceptance/execute-current', method: 'post' })
export const executeAcceptanceUntil = (data) => request({ url: '/api/acceptance/execute-until', method: 'post', data })
export const executeAcceptanceAll = () => request({ url: '/api/acceptance/execute-all', method: 'post' })
export const getAcceptanceSnapshot = (params) => request({ url: '/api/acceptance/snapshot', method: 'get', params })
export const getAcceptanceSnapshots = () => request({ url: '/api/acceptance/snapshots', method: 'get' })
export const exportAcceptanceXlsxUrl = '/api/acceptance/export.xlsx'
