<template>
  <div class="user-workspace-wrapper">
    <!-- Top Nav -->
    <nav class="top-nav">
      <div class="nav-brand">⚡ 智能充电桩调度计费系统</div>
      <div class="nav-center">
        <router-link to="/user/workspace" class="nav-tab active">工作台</router-link>
        <router-link to="/user/task" class="nav-tab">当前任务</router-link>
        <router-link to="/user/account" class="nav-tab">账户中心</router-link>
      </div>
      <div class="nav-right">
        <span>🔔 通知(3)</span>
        <span>用户: 张三</span>
        <span class="logout">退出</span>
        <span>{{ clock }}</span>
      </div>
    </nav>

    <div class="main-wrap">
      <!-- Left -->
      <div class="left-area">
        <div class="inner-tabs">
          <button class="inner-tab" :class="{active: tab==='overview'}" @click="tab='overview'">充电桩总览</button>
          <button class="inner-tab" :class="{active: tab==='submit'}" @click="tab='submit'">提交请求</button>
        </div>

        <!-- Tab 1: Overview -->
        <div class="tab-content" :class="{active: tab==='overview'}">
          <div class="summary-row">
            <div class="summary-badge"><div class="icon fast">⚡</div><div><div class="val">{{ kpi.fastWait }}</div><div class="lbl">快充平均等待 (分)</div></div></div>
            <div class="summary-badge"><div class="icon slow">🔋</div><div><div class="val">{{ kpi.slowWait }}</div><div class="lbl">慢充平均等待 (分)</div></div></div>
            <div class="summary-badge"><div class="icon queue">👥</div><div><div class="val">{{ kpi.queue }}</div><div class="lbl">当前排队 (人)</div></div></div>
          </div>

          <div class="filter-row">
            <button class="filter-btn" :class="{active: pileFilter==='all'}" @click="pileFilter='all'">全部</button>
            <button class="filter-btn" :class="{active: pileFilter==='charging'}" @click="pileFilter='charging'">充电中</button>
            <button class="filter-btn" :class="{active: pileFilter==='idle'}" @click="pileFilter='idle'">空闲</button>
            <button class="filter-btn" :class="{active: pileFilter==='fault'}" @click="pileFilter='fault'">故障</button>
          </div>

          <div class="pile-grid">
            <div v-for="pile in filteredPiles" :key="pile.code" class="pile-card" :data-status="pile.status">
              <div class="pile-header">
                <span class="pile-code">{{ pile.code }}</span>
                <span class="type-badge" :class="pile.type === '快充' ? 'fast' : 'slow'">{{ pile.type }}</span>
              </div>
              <div class="pile-power">额定功率: {{ pile.power }}kW</div>
              <div class="status-line">
                <span class="status-dot" :class="pile.status"></span>
                <span class="status-text" :class="{fault: pile.status==='fault'}">{{ pile.statusText }}</span>
              </div>
              <template v-if="pile.status==='charging' || pile.status==='waiting'">
                <div class="progress-wrap"><div class="progress-bar" :style="{width: pile.progress+'%'}"></div></div>
                <div class="charge-info">{{ pile.user }} · {{ pile.energy }} · {{ pile.progress }}%</div>
              </template>
            </div>
          </div>
        </div>

        <!-- Tab 2: Submit Request -->
        <div class="tab-content" :class="{active: tab==='submit'}">
          <div class="form-card">
            <h3>提交充电请求</h3>
            <p class="sub">选择充电模式和需求电量，系统将自动为您分配最优充电桩</p>

            <div class="mode-select">
              <div class="mode-card" :class="{selected: mode==='fast'}" @click="selectMode('fast')">
                <div class="mode-icon">⚡</div>
                <div class="mode-title">快充</div>
                <div class="mode-desc">30kW 大功率</div>
                <div class="mode-wait">预计等待 ~8分钟</div>
              </div>
              <div class="mode-card" :class="{selected: mode==='slow'}" @click="selectMode('slow')">
                <div class="mode-icon">🌿</div>
                <div class="mode-title">慢充</div>
                <div class="mode-desc">7kW 节能</div>
                <div class="mode-wait">预计等待 ~15分钟</div>
              </div>
            </div>

            <div class="kwh-section">
              <label>需求电量 (kWh)</label>
              <div class="kwh-presets">
                <button class="kwh-btn" :class="{selected: kwh===10}" @click="selectKwh(10)">10</button>
                <button class="kwh-btn" :class="{selected: kwh===20}" @click="selectKwh(20)">20</button>
                <button class="kwh-btn" :class="{selected: kwh===30}" @click="selectKwh(30)">30</button>
                <button class="kwh-btn" :class="{selected: kwh===50}" @click="selectKwh(50)">50</button>
                <button class="kwh-btn" :class="{selected: kwh===80}" @click="selectKwh(80)">80</button>
              </div>
              <div class="kwh-custom">
                <input type="number" v-model.number="customKwh" placeholder="自定义" min="1" max="100" @input="onCustomKwhInput">
                <span>kWh</span>
              </div>
            </div>

            <div class="info-box">
              <span>预计等待时间: <strong>{{ mode==='fast'?'~8分钟':'~15分钟' }}</strong></span>
              <span>预计完成时间: <strong>{{ mode==='fast'?'~45分钟':'~2小时' }}</strong></span>
            </div>

            <button class="submit-btn" @click="submitRequest">提交充电请求</button>
            <p class="form-note">系统将自动为您分配最优充电桩</p>
          </div>
        </div>
      </div>

      <!-- Right Panel -->
      <div class="right-panel">
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-val">{{ stats.history }}</div><div class="stat-lbl">我的历史充电 (次)</div></div>
          <div class="stat-card"><div class="stat-val gold">{{ stats.totalKwh }}</div><div class="stat-lbl">累计充电量 (kWh)</div></div>
          <div class="stat-card"><div class="stat-val rust">¥{{ stats.totalFee }}.00</div><div class="stat-lbl">累计消费</div></div>
          <div class="stat-card"><div class="stat-val" style="color:var(--primary)">¥{{ stats.balance }}.00</div><div class="stat-lbl">账户余额</div></div>
        </div>
        <div class="divider"></div>
        <div class="notif-title">最近通知</div>
        <div class="notif-list">
          <div class="notif-item" v-for="(n, i) in notifications" :key="i">
            <span class="time">{{ n.time }}</span> {{ n.icon }} <span class="tag" :class="n.tagClass">[{{ n.tag }}]</span> {{ n.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { createChargeRequest } from '@/api/charging'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const clock = ref('')
let clockInterval = null
onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
})
onUnmounted(() => { if(clockInterval) clearInterval(clockInterval) })
function updateClock() {
  clock.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

const tab = ref('overview')
const pileFilter = ref('all')
const mode = ref('fast')
const kwh = ref(30)
const customKwh = ref(null)

const kpi = ref({ fastWait: 8, slowWait: 15, queue: 7 })
const piles = ref([
  { code: 'FAST_01', type: '快充', power: 30, status: 'charging', statusText: '充电中', user: 'user_003', energy: '23.4/30 kWh', progress: 78 },
  { code: 'FAST_02', type: '快充', power: 30, status: 'waiting', statusText: '等待离场', user: 'user_007', energy: '30/30 kWh', progress: 100 },
  { code: 'SLOW_01', type: '慢充', power: 7, status: 'charging', statusText: '充电中', user: 'user_001', energy: '13.5/30 kWh', progress: 45 },
  { code: 'SLOW_02', type: '慢充', power: 7, status: 'idle', statusText: '空闲就绪' },
  { code: 'SLOW_03', type: '慢充', power: 7, status: 'fault', statusText: '设备故障' }
])
const filteredPiles = computed(() => {
  if (pileFilter.value === 'all') return piles.value
  return piles.value.filter(p => p.status === pileFilter.value)
})

function selectMode(m) {
  mode.value = m
}
function selectKwh(val) {
  kwh.value = val
  customKwh.value = null
}
function onCustomKwhInput(e) {
  if (customKwh.value) kwh.value = customKwh.value
}
async function submitRequest() {
  if (!kwh.value || kwh.value <= 0) {
    ElMessage.warning('请输入有效的充电量')
    return
  }
  
  try {
    const payload = {
      // 构造符合冻结接口文档的时间格式 YYYY-MM-DDTHH:mm:ss
      request_time: new Date().toISOString().substring(0, 19), 
      charge_mode: mode.value.toUpperCase(), // 转为 FAST 或 SLOW
      request_energy: Number(kwh.value)
    }
    
    // 调用我们在 charging.js 封装好的接口发起真实请求
    const res = await createChargeRequest(payload)
    
    if (res && res.code === 0) {
      const waitTime = Math.round(res.data.estimated_wait_seconds / 60)
      const waitText = waitTime < 1 ? '不足 1 分钟' : `约 ${waitTime} 分钟`
      await ElMessageBox.alert(
        `
        <div style="text-align: center; padding: 20px 0;">
          <div style="font-size: 15px; color: var(--text2); margin-bottom: 8px;">请求流水号</div>
          <div style="font-family: Georgia, serif; font-size: 36px; font-weight: 700; color: var(--primary); margin-bottom: 24px; letter-spacing: 1px;">${res.data.request_id}</div>
          
          <div style="font-size: 15px; color: var(--text2); margin-bottom: 8px;">预计等待时间</div>
          <div style="font-family: Georgia, serif; font-size: 28px; font-weight: 700; color: var(--accent);">${waitText}</div>
        </div>
        `,
        '🎉 充电请求提交成功',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '立即查看任务',
          customStyle: { borderRadius: '16px' },
          showClose: false,
          center: true,
          confirmButtonClass: 'btn-primary'
        }
      )
      // 保存请求信息到 sessionStorage（会话级，不跨浏览器重开）供任务页面读取
      const simulatedWaitSeconds = 30
      sessionStorage.setItem('currentRequestID', res.data.request_id)
      sessionStorage.setItem(`taskFlow_${res.data.request_id}`, JSON.stringify({
        request_id: res.data.request_id,
        request_energy: Number(kwh.value),
        charge_mode: mode.value.toUpperCase(),
        submit_time: new Date().toISOString(),
        estimated_wait_seconds: simulatedWaitSeconds,
        status: 'WAITING'
      }))
      // 清理旧的持久化缓存，避免“下次打开仍保留记录”
      localStorage.removeItem('currentRequestID')
      
      // 携带状态跳往当前任务页 (Task.vue)
      router.push('/user/task')
    } else {
      ElMessage.error(`提交失败: ${res?.message || '服务器内部错误'}`)
    }
  } catch (err) {
    console.error('Request Error:', err)
    ElMessage.error('接口请求异常，请检查后端是否稳定运行以及网络配置！')
  }
}

const stats = ref({ history: 12, totalKwh: 356, totalFee: 534, balance: 166 })
const notifications = ref([
  { time: '14:23', icon: '🔔', tag: '叫号提醒', tagClass: 'call', text: '您的充电请求已被叫号，请在3分钟内确认到场' },
  { time: '14:21', icon: '✅', tag: '充电完成', tagClass: 'done', text: 'FAST_01充电完成，请尽快移车' },
  { time: '14:18', icon: '⚠️', tag: '故障通知', tagClass: 'warn', text: 'SLOW_03发生故障，受影响用户已重新排队' },
  { time: '14:15', icon: '🔔', tag: '排队更新', tagClass: 'queue', text: '您的预计等待时间已更新为8分钟' },
  { time: '13:50', icon: '✅', tag: '支付成功', tagClass: 'pay', text: '订单REQ-0023支付成功，¥45.00' },
  { time: '13:30', icon: '📋', tag: '新请求', tagClass: 'new', text: '充电请求已提交，进入等待队列' }
])
</script>

<style scoped>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
:global(body) {
  --bg:#faf8f5;--card:#ffffff;--primary:#2d6a4f;--secondary:#c45d3e;
  --accent:#d4a853;--text:#2c2c2c;--text2:#7a7a7a;
  --shadow:0 4px 12px rgba(120,80,40,0.08);--radius:10px;
  --nav-bg:#f5f0e8;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}
.user-workspace-wrapper {
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  width: 100vw;
  width: 100%;
  display: flex;
  flex-direction: column;
}
h1,h2,h3,h4,h5,h6{font-family:Georgia,serif;}

/* Top Nav */
.top-nav{background:var(--nav-bg);border-bottom:3px solid var(--accent);display:flex;align-items:center;justify-content:space-between;padding:0 32px;height:56px;position:sticky;top:0;z-index:100;}
.nav-brand{font-family:Georgia,serif;font-weight:bold;font-size:18px;color:var(--primary);white-space:nowrap;}
.nav-center{display:flex;gap:4px;}
.nav-tab{padding:8px 22px;border-radius:8px;cursor:pointer;font-size:15px;color:var(--text2);transition:all .2s;text-decoration:none;border:none;background:none;}
.nav-tab:hover{color:var(--text);background:rgba(45,106,79,.06);}
.nav-tab.active{color:var(--primary);font-weight:600;background:rgba(45,106,79,.1);}
.nav-right{display:flex;align-items:center;gap:18px;font-size:14px;color:var(--text2);}
.nav-right span{cursor:pointer;transition:color .2s;}.nav-right span:hover{color:var(--text);}
.nav-right .logout{color:var(--secondary);}
#liveClock{font-variant-numeric:tabular-nums;font-weight:500;color:var(--text);}

/* Layout */
.main-wrap{display:flex;gap:24px;padding:24px 32px;width:100%;max-width:none;margin:0;min-height:calc(100vh - 56px);flex:1;}
.left-area{flex:7;min-width:0;}
.right-panel{flex:3;min-width:320px;max-width:420px;}

/* Inner Tabs */
.inner-tabs{display:flex;gap:2px;margin-bottom:20px;border-bottom:2px solid #ebe6de;}
.inner-tab{padding:10px 28px;cursor:pointer;font-size:15px;color:var(--text2);border-bottom:3px solid transparent;margin-bottom:-2px;transition:all .2s;background:none;border-top:none;border-left:none;border-right:none;}
.inner-tab:hover{color:var(--text);}
.inner-tab.active{color:var(--primary);font-weight:600;border-bottom-color:var(--primary);}

/* Tab Content */
.tab-content{display:none;animation:fadeSlide .3s ease;}
.tab-content.active{display:block;}
@keyframes fadeSlide{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}

/* Summary Badges */
.summary-row{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;}
.summary-badge{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:14px 24px;display:flex;align-items:center;gap:10px;flex:1;min-width:200px;}
.summary-badge .icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;}
.summary-badge .icon.fast{background:rgba(212,168,83,.15);color:var(--accent);}
.summary-badge .icon.slow{background:rgba(45,106,79,.1);color:var(--primary);}
.summary-badge .icon.queue{background:rgba(196,93,62,.1);color:var(--secondary);}
.summary-badge .val{font-size:22px;font-weight:700;font-family:Georgia,serif;color:var(--text);}
.summary-badge .lbl{font-size:13px;color:var(--text2);}

/* Filters */
.filter-row{display:flex;gap:8px;margin-bottom:20px;}
.filter-btn{padding:7px 20px;border-radius:20px;border:1.5px solid #ddd;background:var(--card);cursor:pointer;font-size:14px;color:var(--text2);transition:all .2s;}
.filter-btn:hover{border-color:var(--primary);color:var(--primary);}
.filter-btn.active{background:var(--primary);color:#fff;border-color:var(--primary);}

/* Pile Grid */
.pile-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
.pile-card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:20px;transition:transform .25s,box-shadow .25s;cursor:default;}
.pile-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(120,80,40,.13);}
.pile-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.pile-code{font-family:Georgia,serif;font-weight:700;font-size:17px;}
.type-badge{padding:3px 12px;border-radius:12px;font-size:12px;font-weight:600;}
.type-badge.fast{background:rgba(212,168,83,.15);color:#b8922e;}
.type-badge.slow{border:1.5px solid var(--primary);color:var(--primary);background:transparent;}
.pile-power{font-size:13px;color:var(--text2);margin-bottom:10px;}
.status-line{display:flex;align-items:center;gap:8px;margin-bottom:10px;}
.status-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}
.status-dot.charging{background:var(--primary);}
.status-dot.waiting{background:var(--accent);}
.status-dot.idle{background:#bbb;}
.status-dot.fault{background:#d32f2f;}
.status-text{font-size:14px;font-weight:500;}
.status-text.fault{color:#d32f2f;}
.progress-wrap{background:#eee;border-radius:6px;height:8px;margin:8px 0;overflow:hidden;}
.progress-bar{height:100%;border-radius:6px;background:var(--primary);transition:width 1.2s ease;}
.charge-info{font-size:13px;color:var(--text2);}

/* Submit Form Tab */
.form-card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:36px 40px;max-width:720px;margin:0 auto;}
.form-card h3{font-size:22px;margin-bottom:8px;color:var(--text);}
.form-card .sub{color:var(--text2);font-size:14px;margin-bottom:28px;}
.mode-select{display:flex;gap:20px;margin-bottom:28px;}
.mode-card{flex:1;border:2px solid #e8e3da;border-radius:var(--radius);padding:28px 20px;text-align:center;cursor:pointer;transition:all .25s;}
.mode-card:hover{border-color:var(--accent);background:rgba(212,168,83,.03);}
.mode-card.selected{border-color:var(--accent);box-shadow:0 0 0 3px rgba(212,168,83,.2);background:rgba(212,168,83,.04);}
.mode-icon{font-size:36px;margin-bottom:10px;}
.mode-title{font-family:Georgia,serif;font-weight:700;font-size:18px;margin-bottom:6px;}
.mode-desc{font-size:13px;color:var(--text2);margin-bottom:4px;}
.mode-wait{font-size:12px;color:var(--accent);font-weight:500;}

.kwh-section{margin-bottom:28px;}
.kwh-section label{display:block;font-weight:600;margin-bottom:10px;font-size:15px;}
.kwh-presets{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;}
.kwh-btn{width:60px;height:40px;border-radius:8px;border:1.5px solid #ddd;background:var(--card);cursor:pointer;font-size:15px;font-weight:600;color:var(--text2);transition:all .2s;}
.kwh-btn:hover{border-color:var(--primary);color:var(--primary);}
.kwh-btn.selected{background:var(--primary);color:#fff;border-color:var(--primary);}
.kwh-custom{display:flex;align-items:center;gap:10px;}
.kwh-custom input{width:120px;height:40px;border:1.5px solid #ddd;border-radius:8px;padding:0 14px;font-size:15px;outline:none;transition:border .2s;}
.kwh-custom input:focus{border-color:var(--primary);}
.kwh-custom span{color:var(--text2);font-size:14px;}

.info-box{background:#f9f5ee;border-radius:8px;padding:14px 20px;margin-bottom:28px;display:flex;gap:24px;font-size:14px;color:var(--text2);}
.info-box strong{color:var(--text);}

.submit-btn{width:100%;padding:15px;border:none;border-radius:var(--radius);background:var(--primary);color:#fff;font-size:17px;font-weight:600;cursor:pointer;transition:background .2s;margin-bottom:12px;}
.submit-btn:hover{background:#245a42;}
.form-note{text-align:center;font-size:13px;color:var(--text2);}

/* Right Panel */
.right-panel .stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px;}
.stat-card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:18px;text-align:center;}
.stat-val{font-family:Georgia,serif;font-size:24px;font-weight:700;color:var(--primary);margin-bottom:4px;}
.stat-val.gold{color:var(--accent);}
.stat-val.rust{color:var(--secondary);}
.stat-lbl{font-size:13px;color:var(--text2);}
.divider{height:1px;background:#ebe6de;margin:20px 0;}
.notif-title{font-family:Georgia,serif;font-size:16px;font-weight:700;margin-bottom:14px;}
.notif-list{max-height:420px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;padding-right:4px;}
.notif-list::-webkit-scrollbar{width:5px;}.notif-list::-webkit-scrollbar-thumb{background:#ddd;border-radius:4px;}
.notif-item{background:var(--card);border-radius:8px;box-shadow:var(--shadow);padding:12px 16px;font-size:13px;line-height:1.6;animation:fadeIn .4s ease;}
.notif-item .time{color:var(--text2);font-size:12px;margin-right:6px;}
.notif-item .tag{font-weight:600;font-size:12px;}
.notif-item .tag.call{color:var(--accent);}
.notif-item .tag.done{color:var(--primary);}
.notif-item .tag.warn{color:var(--secondary);}
.notif-item .tag.pay{color:var(--primary);}
.notif-item .tag.queue{color:var(--accent);}
.notif-item .tag.new{color:var(--text2);}
@keyframes fadeIn{from{opacity:0;transform:translateX(10px);}to{opacity:1;transform:translateX(0);}}

/* Count-up animation */
.count-up{transition:none;}
</style>
