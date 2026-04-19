/**
 * 冻结接口状态枚举字典
 * 基于 docs/冻结接口文档.md
 * 作为成员C，你需要严格使用该字典进行状态判断和展示，绝不可以直接写死硬编码的字符串！
 */

// 1. 充电模式
export const CHARGE_MODE = {
  FAST: 'FAST', // 快充
  SLOW: 'SLOW', // 慢充
};

export const CHARGE_MODE_TEXT = {
  [CHARGE_MODE.FAST]: '快充',
  [CHARGE_MODE.SLOW]: '慢充',
};

// 2. 请求状态
export const REQUEST_STATUS = {
  PENDING: 'PENDING',                 // 已提交
  WAITING: 'WAITING',                 // 等待中
  CALLED: 'CALLED',                   // 已叫号
  CONFIRMED: 'CONFIRMED',             // 已确认到场
  CHARGING: 'CHARGING',               // 充电中
  WAITING_TO_LEAVE: 'WAITING_TO_LEAVE', // 充电结束待挪车
  COMPLETED: 'COMPLETED',             // 已完成
  COMPLETED_EARLY: 'COMPLETED_EARLY', // 提前完成
  CANCELLED: 'CANCELLED',             // 已取消
  NO_SHOW: 'NO_SHOW',                 // 过号
  INTERRUPTED: 'INTERRUPTED',         // 已中断
  FAULT_REQUEUE: 'FAULT_REQUEUE'      // 故障重排
};

export const REQUEST_STATUS_TEXT = {
  [REQUEST_STATUS.PENDING]: '已提交',
  [REQUEST_STATUS.WAITING]: '排队等待中',
  [REQUEST_STATUS.CALLED]: '已叫号，请确认',
  [REQUEST_STATUS.CONFIRMED]: '已确认，等待分配',
  [REQUEST_STATUS.CHARGING]: '充电中',
  [REQUEST_STATUS.WAITING_TO_LEAVE]: '充电结束，请挪车',
  [REQUEST_STATUS.COMPLETED]: '已完成',
  [REQUEST_STATUS.COMPLETED_EARLY]: '提前完成',
  [REQUEST_STATUS.CANCELLED]: '已取消',
  [REQUEST_STATUS.NO_SHOW]: '已过号',
  [REQUEST_STATUS.INTERRUPTED]: '已中断',
  [REQUEST_STATUS.FAULT_REQUEUE]: '故障重新排队'
};

// 3. 充电桩状态
export const STATION_STATUS = {
  IDLE: 'IDLE',                         // 空闲
  RESERVED: 'RESERVED',                 // 已预留
  CHARGING: 'CHARGING',                 // 充电中
  WAITING_TO_LEAVE: 'WAITING_TO_LEAVE', // 待挪车
  FAULT: 'FAULT',                       // 故障
};

export const STATION_STATUS_TEXT = {
  [STATION_STATUS.IDLE]: '空闲',
  [STATION_STATUS.RESERVED]: '等待车辆接入',
  [STATION_STATUS.CHARGING]: '运行中',
  [STATION_STATUS.WAITING_TO_LEAVE]: '等待离场',
  [STATION_STATUS.FAULT]: '设备故障',
};

// 4. 支付状态
export const PAYMENT_STATUS = {
  UNPAID: 'UNPAID',
  PAID: 'PAID',
};

export const PAYMENT_STATUS_TEXT = {
  [PAYMENT_STATUS.UNPAID]: '未支付',
  [PAYMENT_STATUS.PAID]: '已支付',
};
