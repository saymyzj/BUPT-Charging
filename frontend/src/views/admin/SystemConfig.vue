<template>
  <div class="page">
    <div class="page-head">
      <h1>系统配置</h1>
      <p>查看系统参数，切换调度模式与故障策略</p>
    </div>

    <div v-if="loading && !config" class="loading-text">加载中...</div>

    <template v-if="config">
      <!-- Status Bar -->
      <div class="status-bar">
        <div class="stat-cell">
          <div class="stat-icon tone-green"><span class="material-icons">timeline</span></div>
          <div>
            <div class="stat-label">系统状态</div>
            <div class="stat-val green">正常运行</div>
            <div class="stat-sub">所有服务运行良好</div>
          </div>
        </div>
        <div class="stat-cell">
          <div class="stat-icon tone-blue"><span class="material-icons">dns</span></div>
          <div>
            <div class="stat-label">当前调度模式</div>
            <div class="stat-val-row">
              <span class="stat-val">{{ currentDispatchText }}</span>
              <span class="stat-badge">当前使用</span>
            </div>
            <div class="stat-sub">按最优策略分配资源</div>
          </div>
        </div>
        <div class="stat-cell">
          <div class="stat-icon tone-purple"><span class="material-icons">ev_station</span></div>
          <div class="stat-full">
            <div class="stat-label">充电桩总数</div>
            <div class="stat-val">{{ config.fast_station_count + config.slow_station_count }} <span class="stat-unit">/ {{ config.fast_station_count + config.slow_station_count }}</span></div>
            <div class="stat-bar-wrap">
              <div class="stat-bar"><div class="stat-bar-fill" style="width:100%"></div></div>
              <span class="stat-sub">快充 {{ config.fast_station_count }} 慢充 {{ config.slow_station_count }}</span>
            </div>
          </div>
        </div>
        <div class="stat-cell">
          <div class="stat-icon tone-orange"><span class="material-icons">schedule</span></div>
          <div>
            <div class="stat-label">等候区容量</div>
            <div class="stat-val">{{ config.waiting_area_capacity }} <span class="stat-unit">个</span></div>
            <div class="stat-sub">每桩队列 {{ config.charging_queue_len }} 辆</div>
          </div>
        </div>
        <div class="stat-cell no-border">
          <div class="stat-icon tone-cyan"><span class="material-icons">queue</span></div>
          <div>
            <div class="stat-label">每桩队列长度</div>
            <div class="stat-val">{{ config.charging_queue_len }} <span class="stat-unit">辆</span></div>
            <div class="stat-sub">最大并发充电数</div>
          </div>
        </div>
      </div>

      <!-- Dispatch Mode -->
      <section class="section">
        <div class="section-head">
          <div>
            <h3 class="section-title">调度模式</h3>
            <p class="section-sub">选择系统的调度策略，影响资源分配与充电效率</p>
          </div>
        </div>
        <div class="mode-grid">
          <button
            v-for="m in dispatchModes"
            :key="m.key"
            class="mode-card"
            :class="{ active: config.dispatch_mode === m.key }"
            @click="changeDispatch(m.key)"
          >
            <div v-if="config.dispatch_mode === m.key" class="mode-check-circle">✓</div>
            <div class="mode-head">
              <div class="mode-icon-wrap" :class="m.color"><span class="material-icons">{{ m.icon }}</span></div>
              <div>
                <div class="mode-title-row">
                  <span class="mode-title">{{ m.text }}</span>
                  <span v-if="config.dispatch_mode === m.key" class="mode-badge">当前使用</span>
                </div>
                <p class="mode-desc">{{ m.desc }}</p>
              </div>
            </div>
            <ul class="mode-detail">
              <li v-for="d in m.detail" :key="d">{{ d }}</li>
            </ul>
          </button>
        </div>
      </section>

      <!-- Fault Dispatch Mode -->
      <section class="section">
        <div class="section-head">
          <div>
            <h3 class="section-title">故障恢复策略</h3>
            <p class="section-sub">配置系统在故障情况下的恢复与调度优先级</p>
          </div>
        </div>
        <div class="fault-grid">
          <button
            v-for="m in faultModes"
            :key="m.key"
            class="mode-card"
            :class="{ active: config.fault_dispatch_mode === m.key }"
            @click="changeFault(m.key)"
          >
            <div v-if="config.fault_dispatch_mode === m.key" class="mode-check-circle">✓</div>
            <div class="fault-head">
              <div class="fault-icon-wrap" :class="m.color"><span class="material-icons">{{ m.icon }}</span></div>
              <div>
                <div class="mode-title-row">
                  <span class="mode-title">{{ m.text }}</span>
                  <span v-if="config.fault_dispatch_mode === m.key" class="mode-badge">当前使用</span>
                </div>
                <p class="mode-desc">{{ m.desc }}</p>
                <p class="mode-note" :class="{ active: config.fault_dispatch_mode === m.key }">{{ m.note }}</p>
              </div>
            </div>
          </button>
        </div>
      </section>

      <!-- Readonly Params (bottom) -->
      <section class="params-card">
        <div class="params-head">
          <div>
            <h3 class="section-title">系统参数 <span class="readonly-tag">只读</span></h3>
            <p class="section-sub">以下参数由系统自动维护，展示当前物理设备拓扑</p>
          </div>
          <button class="btn-refresh" :disabled="loading" @click="loadConfig">↺ 刷新</button>
        </div>
        <div class="param-grid">
          <div class="param">
            <span class="p-label">快充桩数量</span>
            <span class="p-val">{{ config.fast_station_count }} <small>台</small></span>
          </div>
          <div class="param">
            <span class="p-label">慢充桩数量</span>
            <span class="p-val">{{ config.slow_station_count }} <small>台</small></span>
          </div>
          <div class="param">
            <span class="p-label">等候区容量</span>
            <span class="p-val">{{ config.waiting_area_capacity }} <small>个</small></span>
          </div>
          <div class="param">
            <span class="p-label">每桩队列长度</span>
            <span class="p-val">{{ config.charging_queue_len }} <small>辆</small></span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSystemConfig, setDispatchMode, setFaultDispatchMode } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { DISPATCH_MODE, DISPATCH_MODE_TEXT, FAULT_DISPATCH_MODE, FAULT_DISPATCH_MODE_TEXT } from '@/constants/enums'

const config = ref(null)
const loading = ref(false)

const currentDispatchText = computed(() =>
  config.value ? (DISPATCH_MODE_TEXT[config.value.dispatch_mode] ?? config.value.dispatch_mode) : ''
)

const dispatchModes = [
  {
    key: DISPATCH_MODE.NORMAL,
    text: DISPATCH_MODE_TEXT.NORMAL,
    desc: '按最短完成时间策略分配，平衡效率与公平性',
    icon: 'layers',
    color: 'icon-green',
    detail: ['适用于日常运营场景', '系统自动优化分配'],
  },
  {
    key: DISPATCH_MODE.EXT_SINGLE_BATCH,
    text: DISPATCH_MODE_TEXT.EXT_SINGLE_BATCH,
    desc: '对当前等候区做一次联合优化，提升整体效率',
    icon: 'library_books',
    color: 'icon-blue',
    detail: ['适合短时间高峰拥堵', '手动触发执行'],
  },
  {
    key: DISPATCH_MODE.EXT_FULL_BATCH,
    text: DISPATCH_MODE_TEXT.EXT_FULL_BATCH,
    desc: '对所有待分配请求做批量调度，适用于离线计算',
    icon: 'grid_view',
    color: 'icon-purple',
    detail: ['适合大规模集中调度', '执行时间较长'],
  },
]

const faultModes = [
  {
    key: FAULT_DISPATCH_MODE.PRIORITY,
    text: FAULT_DISPATCH_MODE_TEXT.PRIORITY,
    desc: '故障桩队列车辆优先重新分配到其他桩',
    icon: 'priority_high',
    color: 'icon-green',
    note: '保障故障车主尽快恢复充电',
  },
  {
    key: FAULT_DISPATCH_MODE.TIME_ORDER,
    text: FAULT_DISPATCH_MODE_TEXT.TIME_ORDER,
    desc: '故障桩队列车辆按提交时间重排到全局队列',
    icon: 'update',
    color: 'icon-blue',
    note: '维护全局公平性，避免插队',
  },
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
.page-head h1 { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #0f172a; }
.page-head p { font-size: 13px; color: #6b7280; margin-top: 4px; }
.loading-text { color: #9ca3af; font-size: 14px; padding: 40px 0; text-align: center; }

/* Status Bar */
.status-bar { display: flex; align-items: stretch; background: white; border: 1px solid #e5e7eb; border-radius: 14px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.stat-cell { flex: 1; display: flex; align-items: center; gap: 14px; padding: 18px 20px; border-right: 1px solid #f3f4f6; }
.stat-cell.no-border { border-right: none; }
.stat-icon { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-icon .material-icons { font-size: 22px; }
.tone-green { background: #ecfdf5; color: #059669; }
.tone-blue { background: #eff6ff; color: #2563eb; }
.tone-purple { background: #f5f3ff; color: #7c3aed; }
.tone-orange { background: #fff7ed; color: #f97316; }
.tone-cyan { background: #ecfeff; color: #0891b2; }
.stat-label { font-size: 11px; color: #9ca3af; font-weight: 600; margin-bottom: 4px; }
.stat-val { font-size: 18px; font-weight: 800; color: #111827; }
.stat-val.green { color: #059669; }
.stat-val-row { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
.stat-badge { font-size: 9px; font-weight: 700; color: #059669; background: #ecfdf5; border: 1px solid #d1fae5; padding: 2px 6px; border-radius: 999px; }
.stat-unit { font-size: 12px; font-weight: 600; color: #9ca3af; margin-left: 2px; }
.stat-sub { font-size: 10px; color: #9ca3af; margin-top: 2px; }
.stat-full { flex: 1; min-width: 0; }
.stat-bar-wrap { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.stat-bar { flex: 1; height: 4px; background: #f3f4f6; border-radius: 999px; overflow: hidden; }
.stat-bar-fill { height: 100%; background: #3b82f6; border-radius: 999px; }

/* Section */
.section { margin-bottom: 20px; }
.section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 12px; }
.section-title { font-size: 14px; font-weight: 700; color: #111827; }
.section-sub { font-size: 11px; color: #9ca3af; margin-top: 3px; }

/* API tag */
.api-tag { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-family: "SF Mono", Consolas, monospace; color: #6b7280; padding: 4px 10px; border-radius: 6px; background: #f3f4f6; border: 1px solid #e5e7eb; white-space: nowrap; flex-shrink: 0; }
.api-method { color: #3b82f6; font-weight: 700; }

/* Refresh button */
.btn-refresh { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; border-radius: 8px; border: 1px solid #e5e7eb; background: white; font-size: 12px; font-weight: 600; color: #6b7280; cursor: pointer; transition: 0.12s; flex-shrink: 0; }
.btn-refresh:hover { border-color: #10b981; color: #059669; }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

/* Mode cards - dispatch (3 col) */
.mode-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.fault-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }

.mode-card { position: relative; padding: 20px; border-radius: 14px; border: 2px solid #e5e7eb; background: white; cursor: pointer; text-align: left; transition: border-color 0.15s, box-shadow 0.15s; overflow: hidden; }
.mode-card:hover { border-color: #10b981; box-shadow: 0 4px 12px rgba(16,185,129,0.1); }
.mode-card.active { border-color: #10b981; background: rgba(236,253,245,0.3); box-shadow: 0 0 0 1px #10b981; }

/* Check circle (absolute top-right) */
.mode-check-circle { position: absolute; top: 14px; right: 14px; width: 22px; height: 22px; border-radius: 50%; background: #10b981; color: white; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 900; box-shadow: 0 2px 6px rgba(16,185,129,0.3); }

/* Dispatch card: icon + title in a row, detail below indented */
.mode-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.mode-icon-wrap { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mode-icon-wrap .material-icons { font-size: 20px; }
.mode-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.mode-title { font-size: 14px; font-weight: 700; color: #111827; }
.mode-card.active .mode-title { color: #065f46; }
.mode-badge { font-size: 9px; font-weight: 700; color: #059669; background: #d1fae5; border: 1px solid #a7f3d0; padding: 2px 7px; border-radius: 999px; white-space: nowrap; }
.mode-desc { font-size: 11px; color: #6b7280; line-height: 1.5; }
.mode-card.active .mode-desc { color: rgba(6,95,70,0.8); font-weight: 500; }
.mode-detail { margin: 0; padding: 0 0 0 52px; list-style: none; }
.mode-detail li { font-size: 11px; color: #9ca3af; display: flex; align-items: center; gap: 5px; margin-top: 6px; }
.mode-detail li::before { content: ''; width: 4px; height: 4px; border-radius: 50%; background: #10b981; flex-shrink: 0; }
.mode-card.active .mode-detail li { color: #6b7280; }

/* Icon color variants */
.icon-green { background: #d1fae5; color: #059669; }
.icon-blue { background: #dbeafe; color: #2563eb; }
.icon-purple { background: #ede9fe; color: #7c3aed; }

/* Fault cards: bigger circle icon */
.fault-head { display: flex; align-items: flex-start; gap: 16px; }
.fault-icon-wrap { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
.fault-icon-wrap .material-icons { font-size: 24px; }
.mode-note { font-size: 11px; font-weight: 600; color: #9ca3af; margin-top: 6px; }
.mode-note.active { color: #059669; }

/* Params (bottom card) */
.params-card { background: white; border: 1px solid #e5e7eb; border-radius: 14px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.params-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid #f3f4f6; }
.readonly-tag { font-size: 10px; font-weight: 600; color: #6b7280; background: #f3f4f6; border: 1px solid #e5e7eb; padding: 1px 6px; border-radius: 4px; vertical-align: middle; margin-left: 4px; }
.param-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.param { padding: 18px; border-radius: 10px; background: #f8fafc; border: 1px solid #e5e7eb; }
.p-label { display: block; font-size: 11px; color: #9ca3af; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 8px; }
.p-val { display: block; font-size: 26px; font-weight: 800; color: #111827; font-variant-numeric: tabular-nums; }
.p-val small { font-size: 12px; font-weight: 600; color: #9ca3af; margin-left: 2px; }

@media (max-width: 900px) {
  .page { padding: 20px 18px; }
  .status-bar { flex-wrap: wrap; }
  .stat-cell { flex: 1 1 40%; border-right: none; border-bottom: 1px solid #f3f4f6; }
  .param-grid { grid-template-columns: repeat(2, 1fr); }
  .mode-grid, .fault-grid { grid-template-columns: 1fr; }
}
</style>
