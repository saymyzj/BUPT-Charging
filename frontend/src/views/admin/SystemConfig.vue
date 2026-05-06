<template>
  <div class="page">
    <div class="page-head">
      <h1>系统配置</h1>
      <p>查看系统参数，切换调度模式与故障策略</p>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>

    <template v-if="config">
      <!-- Readonly Config -->
      <div class="card">
        <div class="card-head"><h3>系统参数（只读）</h3><button class="btn-refresh" @click="loadConfig">刷新</button></div>
        <div class="card-body">
          <div class="param-grid">
            <div class="param"><span class="p-label">快充桩数量</span><span class="p-val">{{ config.fast_station_count }}</span></div>
            <div class="param"><span class="p-label">慢充桩数量</span><span class="p-val">{{ config.slow_station_count }}</span></div>
            <div class="param"><span class="p-label">等候区容量</span><span class="p-val">{{ config.waiting_area_capacity }}</span></div>
            <div class="param"><span class="p-label">每桩队列长度</span><span class="p-val">{{ config.charging_queue_len }}</span></div>
          </div>
        </div>
      </div>

      <!-- Dispatch Mode -->
      <div class="card">
        <div class="card-head"><h3>调度模式</h3><span class="card-tag">PUT /api/admin/system/dispatch-mode</span></div>
        <div class="card-body">
          <div class="mode-group">
            <button v-for="m in dispatchModes" :key="m.key" class="mode-btn" :class="{ active: config.dispatch_mode === m.key }" @click="changeDispatch(m.key)">
              <div class="mode-title">{{ m.text }}</div>
              <div class="mode-desc">{{ m.desc }}</div>
            </button>
          </div>
        </div>
      </div>

      <!-- Fault Dispatch Mode -->
      <div class="card">
        <div class="card-head"><h3>故障恢复策略</h3><span class="card-tag">PUT /api/admin/system/fault-dispatch-mode</span></div>
        <div class="card-body">
          <div class="mode-group">
            <button v-for="m in faultModes" :key="m.key" class="mode-btn" :class="{ active: config.fault_dispatch_mode === m.key }" @click="changeFault(m.key)">
              <div class="mode-title">{{ m.text }}</div>
              <div class="mode-desc">{{ m.desc }}</div>
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSystemConfig, setDispatchMode, setFaultDispatchMode } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { DISPATCH_MODE, DISPATCH_MODE_TEXT, FAULT_DISPATCH_MODE, FAULT_DISPATCH_MODE_TEXT } from '@/constants/enums'

const config = ref(null)
const loading = ref(false)

const dispatchModes = [
  { key: DISPATCH_MODE.NORMAL, text: DISPATCH_MODE_TEXT.NORMAL, desc: '按最短完成时间策略分配' },
  { key: DISPATCH_MODE.EXT_SINGLE_BATCH, text: DISPATCH_MODE_TEXT.EXT_SINGLE_BATCH, desc: '对当前等候区做一次联合优化' },
  { key: DISPATCH_MODE.EXT_FULL_BATCH, text: DISPATCH_MODE_TEXT.EXT_FULL_BATCH, desc: '对所有待分配请求做批量调度' },
]

const faultModes = [
  { key: FAULT_DISPATCH_MODE.PRIORITY, text: FAULT_DISPATCH_MODE_TEXT.PRIORITY, desc: '故障桩队列车辆优先重排到其他桩' },
  { key: FAULT_DISPATCH_MODE.TIME_ORDER, text: FAULT_DISPATCH_MODE_TEXT.TIME_ORDER, desc: '故障桩队列车辆按提交时间重排' },
]

async function loadConfig() {
  loading.value = true
  try {
    const res = await getSystemConfig()
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { loading.value = false; return }
    config.value = data
  } catch (_) { /* silent */ }
  loading.value = false
}

async function changeDispatch(mode) {
  if (config.value.dispatch_mode === mode) return
  try {
    const res = await setDispatchMode({ dispatch_mode: mode })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '切换失败'); return }
    await loadConfig()
  } catch (e) { alert(e?.response?.data?.message || '切换失败') }
}

async function changeFault(mode) {
  if (config.value.fault_dispatch_mode === mode) return
  try {
    const res = await setFaultDispatchMode({ fault_dispatch_mode: mode })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { alert(data.message || '切换失败'); return }
    await loadConfig()
  } catch (e) { alert(e?.response?.data?.message || '切换失败') }
}

onMounted(loadConfig)
</script>

<style scoped>
.page { max-width: 1280px; margin: 0 auto; padding: 28px 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Microsoft YaHei", sans-serif; }
.page-head { margin-bottom: 24px; }
.page-head h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #111827; }
.page-head p { font-size: 14px; color: #6b7280; margin-top: 4px; }
.loading-text { color: #9ca3af; font-size: 14px; padding: 40px 0; text-align: center; }

.card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; margin-bottom: 16px; }
.card-head { padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e5e7eb; }
.card-head h3 { font-size: 14px; font-weight: 600; color: #111827; }
.card-tag { font-size: 11px; font-family: "SF Mono", monospace; color: #059669; padding: 3px 8px; border-radius: 6px; background: #ecfdf5; border: 1px solid #d1fae5; }
.card-body { padding: 20px; }

.btn-refresh { padding: 5px 12px; border-radius: 6px; border: 1px solid #e5e7eb; background: white; font-size: 11px; font-weight: 600; color: #6b7280; cursor: pointer; transition: 0.12s; }
.btn-refresh:hover { border-color: #10b981; color: #059669; }

.param-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.param { padding: 16px; border-radius: 10px; background: #f8faf9; border: 1px solid #e5e7eb; }
.p-label { display: block; font-size: 11px; color: #9ca3af; font-weight: 500; text-transform: uppercase; letter-spacing: 0.3px; }
.p-val { display: block; font-size: 22px; font-weight: 700; color: #111827; margin-top: 6px; }

.mode-group { display: flex; gap: 12px; flex-wrap: wrap; }
.mode-btn { flex: 1; min-width: 200px; padding: 18px; border-radius: 10px; border: 2px solid #e5e7eb; background: white; cursor: pointer; text-align: left; transition: 0.15s; }
.mode-btn:hover { border-color: #10b981; }
.mode-btn.active { border-color: #10b981; background: #ecfdf5; }
.mode-title { font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.mode-desc { font-size: 12px; color: #6b7280; line-height: 1.5; }
.mode-btn.active .mode-title { color: #059669; }
</style>
