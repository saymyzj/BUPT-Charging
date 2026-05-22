<template>
  <div class="landing">
<!-- NAV -->
<nav class="nav" :class="{ scrolled }">
  <div class="nav-brand"><div class="nav-logo">&#9889;</div>充电调度系统</div>
  <div class="nav-right">
    <a href="#features">功能</a>
    <a href="#how">流程</a>
    <a href="#billing">计费</a>
    <button class="btn-nav btn-nav-outline" @click="openModal('login')">登录</button>
    <button class="btn-nav btn-nav-fill" @click="openModal('register')">免费注册</button>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-left">
    <div class="hero-badge">智能充电桩调度计费系统 · V3.0</div>
    <h1>让每一度电<br>都被<span>智能调度</span></h1>
    <p class="hero-desc">基于最优化算法自动分配快充/慢充桩位，最小化等待时间。峰平谷分时计费引擎自动生成结构化详单，每一笔费用清晰可查。</p>
    <div class="hero-actions">
      <button class="btn-hero btn-hero-primary" @click="openModal('login')">立即开始</button>
      <button class="btn-hero btn-hero-ghost" @click="scrollTo('features')">了解更多</button>
    </div>
    <div class="hero-trust">已用于 <span>课程演示</span> · 支持 <span>10 桩位</span> 并发调度</div>
  </div>
  <div class="hero-right">
    <div class="hero-mockup">
      <div class="mockup-bar"><span class="mockup-dot"></span><span class="mockup-dot"></span><span class="mockup-dot"></span></div>
      <div class="mockup-body">
        <div class="mock-row">
          <div class="mock-card"><div class="mock-card-title">快充在线</div><div class="mock-card-val">5/5</div><div class="mock-card-sub">30kW × 5</div></div>
          <div class="mock-card"><div class="mock-card-title">慢充在线</div><div class="mock-card-val">5/5</div><div class="mock-card-sub">10kW × 5</div></div>
          <div class="mock-card"><div class="mock-card-title">排队中</div><div class="mock-card-val">3</div><div class="mock-card-sub">预估 8min</div></div>
        </div>
        <div class="mock-timeline">
          <div class="mock-timeline-title">当前充电进度 · 桩位 F-03</div>
          <div class="tl-bar"><div class="tl-fill"></div></div>
          <div class="tl-labels"><span>0 kWh</span><span>已充 39 kWh</span><span>目标 60 kWh</span></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- FEATURES -->
<section class="features-section" id="features">
  <div class="section-header"><h2>六大核心能力</h2><p>覆盖用户侧与管理侧的全流程智能服务</p></div>
  <div class="feat-grid">
    <div class="feat-card"><div class="feat-icon green">&#9889;</div><h3>智能调度引擎</h3><p>基于「最短完成时间」策略，自动匹配快充/慢充桩位，支持正常、故障、扩展三种调度模式切换。</p></div>
    <div class="feat-card"><div class="feat-icon blue">&#128202;</div><h3>实时状态监控</h3><p>排队号、前车数量、预估等待时间、当前充电功率全端实时同步，用户信息完全透明。</p></div>
    <div class="feat-card"><div class="feat-icon amber">&#128176;</div><h3>分时计费详单</h3><p>峰/平/谷三段电价 + 服务费自动计算，充电完成即生成精确到分钟的结构化费用明细。</p></div>
    <div class="feat-card"><div class="feat-icon green">&#128274;</div><h3>故障自动恢复</h3><p>充电桩故障时自动触发 PRIORITY / TIME_ORDER 策略，受影响车辆平滑转移至可用桩位。</p></div>
    <div class="feat-card"><div class="feat-icon blue">&#128100;</div><h3>双角色权限体系</h3><p>用户端提交充电请求、查看排队进度；管理员端控制桩位启停、查看运营报表与统计。</p></div>
    <div class="feat-card"><div class="feat-icon amber">&#128203;</div><h3>多维运营报表</h3><p>按日/周/月统计充电量、营收、桩位利用率，支持数据导出，辅助管理决策。</p></div>
  </div>
</section>

<!-- HOW IT WORKS -->
<section class="how-section" id="how">
  <div class="section-header"><h2>使用流程</h2><p>从注册到完成充电，仅需四步</p></div>
  <div class="steps">
    <div class="step"><div class="step-num">1</div><h4>注册登录</h4><p>填写用户名、密码与电池容量完成注册</p></div>
    <div class="step"><div class="step-num">2</div><h4>提交请求</h4><p>选择充电模式与目标电量，系统分配排队号</p></div>
    <div class="step"><div class="step-num">3</div><h4>自动调度</h4><p>引擎实时计算最优桩位，叫号后确认上桩</p></div>
    <div class="step"><div class="step-num">4</div><h4>计费结算</h4><p>充电完成自动生成详单，查看并确认离场</p></div>
  </div>
</section>

<!-- BILLING -->
<section class="billing-section" id="billing">
  <div class="section-header"><h2>费率标准</h2><p>峰平谷分时电价 + 统一服务费</p></div>
  <div class="bill-grid">
    <div class="bill-card"><div class="bill-card-label">峰时电价</div><div class="bill-card-val">1.0</div><div class="bill-card-unit">元 / kWh（10:00–15:00, 18:00–21:00）</div></div>
    <div class="bill-card"><div class="bill-card-label">平时电价</div><div class="bill-card-val">0.7</div><div class="bill-card-unit">元 / kWh（07:00–10:00, 15:00–18:00, 21:00–23:00）</div></div>
    <div class="bill-card"><div class="bill-card-label">谷时电价</div><div class="bill-card-val">0.4</div><div class="bill-card-unit">元 / kWh（23:00–07:00）</div></div>
  </div>
</section>

<!-- STATS -->
<section class="stats-section">
  <div class="stat-item"><div class="stat-icon">&#9889;</div><div class="stat-num">10</div><div class="stat-label">充电桩总数</div></div>
  <div class="stat-item"><div class="stat-icon">&#128296;</div><div class="stat-num">30kW</div><div class="stat-label">快充功率</div></div>
  <div class="stat-item"><div class="stat-icon">&#128260;</div><div class="stat-num">3</div><div class="stat-label">调度模式</div></div>
  <div class="stat-item"><div class="stat-icon">&#128337;</div><div class="stat-num">24/7</div><div class="stat-label">不间断服务</div></div>
</section>

<!-- CTA -->
<section class="cta-section">
  <h2>准备好开始了吗？</h2>
  <p>注册账号即可体验完整的智能充电调度与计费流程</p>
  <button class="btn-hero btn-hero-primary" @click="openModal('register')">免费注册</button>
</section>

<!-- FOOTER -->
<footer class="footer">
  <div class="footer-inner">
    <div class="footer-left">&copy; 2026 智能充电桩调度计费系统 · 北京邮电大学 课程项目</div>
    <div class="footer-links"><a href="#features">功能</a><a href="#how">流程</a><a href="#billing">计费</a></div>
  </div>
</footer>

<!-- AUTH MODAL -->
<div class="modal-overlay" :class="{ active: showModal }" @click.self="closeModal">
  <div class="modal-card">
    <button class="modal-close" @click="closeModal">&times;</button>
    <div class="modal-header"><h2>欢迎使用</h2><p>请登录或注册您的账号</p></div>
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'login' }" @click="activeTab = 'login'">登录</button>
      <button class="tab-btn" :class="{ active: activeTab === 'register' }" @click="activeTab = 'register'">注册</button>
      <div class="tab-ind" :class="{ reg: activeTab === 'register' }"></div>
    </div>
    <div class="form-wrap">
      <!-- LOGIN -->
      <form class="auth-form" :class="{ active: activeTab === 'login' }" @submit.prevent="handleLogin">
        <div class="fg"><label>用户名</label><input type="text" v-model="loginForm.username" placeholder="请输入用户名" :class="{ err: loginErr.username }"><span class="err-msg" v-if="loginErr.username">请输入用户名</span></div>
        <div class="fg"><label>密码</label><input type="password" v-model="loginForm.password" placeholder="请输入密码" :class="{ err: loginErr.password }"><span class="err-msg" v-if="loginErr.password">请输入密码</span></div>
        <button type="submit" class="btn-submit login" :disabled="loading">{{ loading ? '登录中...' : '登 录' }}</button>
        <div class="switch-text">没有账号？<a @click="activeTab = 'register'">立即注册</a></div>
      </form>
      <!-- REGISTER -->
      <form class="auth-form" :class="{ active: activeTab === 'register' }" @submit.prevent="handleRegister">
        <div class="fg"><label>用户名</label><input type="text" v-model="regForm.username" placeholder="请输入用户名" :class="{ err: regErr.username }"><span class="err-msg" v-if="regErr.username">请输入用户名</span></div>
        <div class="fg"><label>密码</label><input type="password" v-model="regForm.password" placeholder="请输入密码" :class="{ err: regErr.password }"><span class="err-msg" v-if="regErr.password">请输入密码</span></div>
        <div class="fg"><label>确认密码</label><input type="password" v-model="regForm.password2" placeholder="再次输入密码" :class="{ err: regErr.password2 }"><span class="err-msg" v-if="regErr.password2">{{ regErr.password2Msg }}</span></div>
        <div class="fg"><label>电池容量 (kWh)</label><input type="number" v-model.number="regForm.battery_capacity" placeholder="例如 60" min="1" step="0.1" :class="{ err: regErr.battery }"><span class="err-msg" v-if="regErr.battery">请输入电池容量</span><div class="hint">系统据此计算预估充电时间</div></div>
        <button type="submit" class="btn-submit register" :disabled="loading">{{ loading ? '注册中...' : '注 册' }}</button>
        <div class="switch-text">已有账号？<a @click="activeTab = 'login'">返回登录</a></div>
      </form>
    </div>
    <div class="api-msg" v-if="apiMsg" :class="{ 'api-err': apiIsErr }">{{ apiMsg }}</div>
  </div>
</div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '@/api/charging'
import { unwrapResponseData } from '@/api/request'
import { setAuthSession } from '@/utils/authSession'

const router = useRouter()
const scrolled = ref(false)
const showModal = ref(false)
const activeTab = ref('login')
const loading = ref(false)
const apiMsg = ref('')
const apiIsErr = ref(false)

const loginForm = ref({ username: '', password: '' })
const loginErr = ref({ username: false, password: false })

const regForm = ref({ username: '', password: '', password2: '', battery_capacity: null })
const regErr = ref({ username: false, password: false, password2: false, password2Msg: '两次密码不一致', battery: false })

function onScroll() { scrolled.value = window.scrollY > 10 }
onMounted(() => window.addEventListener('scroll', onScroll))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

function openModal(tab) { showModal.value = true; if (tab) activeTab.value = tab; document.body.style.overflow = 'hidden' }
function closeModal() { showModal.value = false; document.body.style.overflow = '' }
function scrollTo(id) { document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }) }

function showMsgFn(msg, isError = true) { apiMsg.value = msg; apiIsErr.value = isError; setTimeout(() => { apiMsg.value = '' }, 4000) }

async function handleLogin() {
  loginErr.value.username = !loginForm.value.username.trim()
  loginErr.value.password = !loginForm.value.password.trim()
  if (loginErr.value.username || loginErr.value.password) return
  loading.value = true
  try {
    const res = await login({ username: loginForm.value.username.trim(), password: loginForm.value.password })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { showMsgFn(data.message || '登录失败'); return }
    setAuthSession({
      token: data.token
    })
    closeModal()
    router.push(data.role === 'ADMIN' ? '/admin/overview' : '/user/workspace')
  } catch (e) {
    showMsgFn(e?.response?.data?.message || e?.message || '登录失败，请检查用户名和密码')
  } finally { loading.value = false }
}

async function handleRegister() {
  regErr.value.username = !regForm.value.username.trim()
  regErr.value.password = !regForm.value.password.trim()
  regErr.value.password2 = !regForm.value.password2.trim()
  regErr.value.battery = !regForm.value.battery_capacity || regForm.value.battery_capacity <= 0
  if (regErr.value.username || regErr.value.password || regErr.value.password2 || regErr.value.battery) return
  if (regForm.value.password !== regForm.value.password2) { regErr.value.password2 = true; regErr.value.password2Msg = '两次密码不一致'; return }
  loading.value = true
  try {
    const res = await register({ username: regForm.value.username.trim(), password: regForm.value.password, battery_capacity: regForm.value.battery_capacity })
    const data = unwrapResponseData(res)
    if (data.code !== undefined && data.code !== 0) { showMsgFn(data.message || '注册失败'); return }
    showMsgFn('注册成功，请登录', false)
    activeTab.value = 'login'
    loginForm.value.username = regForm.value.username.trim()
    regForm.value = { username: '', password: '', password2: '', battery_capacity: null }
  } catch (e) {
    showMsgFn(e?.response?.data?.message || e?.message || '注册失败')
  } finally { loading.value = false }
}
</script>

<style scoped>
.landing { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: #334155; background: #fff; line-height: 1.6; }

/* NAV */
.nav { position: fixed; top: 0; left: 0; right: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 14px 48px; background: rgba(255,255,255,0.92); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid #e2e8f0; transition: box-shadow 0.3s; }
.nav.scrolled { box-shadow: 0 1px 12px rgba(0,0,0,0.04); }
.nav-brand { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 700; color: #0f172a; }
.nav-logo { width: 32px; height: 32px; border-radius: 8px; background: #16a34a; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 16px; }
.nav-right { display: flex; align-items: center; gap: 24px; }
.nav-right a { color: #64748b; text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; }
.nav-right a:hover { color: #0f172a; }
.btn-nav { padding: 9px 20px; border-radius: 8px; border: none; font: inherit; font-size: 14px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.btn-nav-outline { background: none; border: 1px solid #e2e8f0; color: #0f172a; }
.btn-nav-outline:hover { border-color: #0f172a; }
.btn-nav-fill { background: #16a34a; color: #fff; }
.btn-nav-fill:hover { background: #15803d; }

/* HERO */
.hero { padding: 140px 48px 80px; display: flex; align-items: center; justify-content: space-between; gap: 60px; max-width: 1200px; margin: 0 auto; }
.hero-left { max-width: 520px; }
.hero-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 20px; background: #dcfce7; color: #15803d; font-size: 13px; font-weight: 600; margin-bottom: 24px; }
.hero-badge::before { content: ''; width: 6px; height: 6px; background: #16a34a; border-radius: 50%; }
.hero-left h1 { font-size: 46px; font-weight: 800; line-height: 1.18; color: #0f172a; margin-bottom: 20px; letter-spacing: -0.5px; }
.hero-left h1 span { color: #16a34a; }
.hero-desc { font-size: 17px; color: #64748b; margin-bottom: 32px; line-height: 1.7; }
.hero-actions { display: flex; gap: 14px; }
.btn-hero { padding: 14px 30px; border-radius: 10px; border: none; font: inherit; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.btn-hero-primary { background: #16a34a; color: #fff; box-shadow: 0 4px 14px rgba(22,163,74,0.3); }
.btn-hero-primary:hover { background: #15803d; transform: translateY(-1px); }
.btn-hero-ghost { background: #fff; color: #0f172a; border: 1px solid #e2e8f0; }
.btn-hero-ghost:hover { border-color: #0f172a; }
.hero-trust { margin-top: 40px; font-size: 13px; color: #94a3b8; }
.hero-trust span { font-weight: 600; color: #64748b; }
.hero-right { flex: 1; max-width: 560px; }
.hero-mockup { border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 20px 50px rgba(0,0,0,0.07); background: #f8fafb; }
.mockup-bar { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #fff; border-bottom: 1px solid #e2e8f0; }
.mockup-dot { width: 10px; height: 10px; border-radius: 50%; }
.mockup-dot:nth-child(1) { background: #f87171; } .mockup-dot:nth-child(2) { background: #fbbf24; } .mockup-dot:nth-child(3) { background: #34d399; }
.mockup-body { padding: 24px; }
.mock-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.mock-card { padding: 16px; border-radius: 10px; background: #fff; border: 1px solid #e2e8f0; }
.mock-card-title { font-size: 11px; color: #64748b; margin-bottom: 6px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.mock-card-val { font-size: 24px; font-weight: 800; color: #0f172a; }
.mock-card-sub { font-size: 11px; color: #16a34a; margin-top: 4px; font-weight: 600; }
.mock-timeline { background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; padding: 16px; }
.mock-timeline-title { font-size: 11px; color: #64748b; margin-bottom: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.tl-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.tl-fill { height: 100%; width: 65%; background: linear-gradient(90deg, #16a34a, #22c55e); border-radius: 3px; }
.tl-labels { display: flex; justify-content: space-between; margin-top: 6px; font-size: 10px; color: #94a3b8; }

/* SECTION */
.section-header { text-align: center; margin-bottom: 60px; }
.section-header h2 { font-size: 34px; font-weight: 800; color: #0f172a; margin-bottom: 12px; }
.section-header p { font-size: 16px; color: #64748b; max-width: 500px; margin: 0 auto; }

/* FEATURES */
.features-section { padding: 100px 48px; max-width: 1200px; margin: 0 auto; }
.feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.feat-card { padding: 32px 24px; border-radius: 14px; border: 1px solid #e2e8f0; transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s; }
.feat-card:hover { border-color: #16a34a; box-shadow: 0 8px 24px rgba(22,163,74,0.06); transform: translateY(-3px); }
.feat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 18px; }
.feat-icon.green { background: #dcfce7; color: #15803d; }
.feat-icon.blue { background: #dbeafe; color: #3b82f6; }
.feat-icon.amber { background: #fef3c7; color: #b45309; }
.feat-card h3 { font-size: 17px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
.feat-card p { font-size: 14px; color: #64748b; line-height: 1.65; }

/* HOW */
.how-section { padding: 100px 48px; background: #f8fafb; }
.steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; max-width: 1100px; margin: 0 auto; position: relative; }
.steps::before { content: ''; position: absolute; top: 36px; left: 60px; right: 60px; height: 2px; background: #e2e8f0; z-index: 0; }
.step { text-align: center; position: relative; z-index: 1; }
.step-num { width: 48px; height: 48px; border-radius: 50%; background: #16a34a; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; margin: 0 auto 16px; box-shadow: 0 4px 12px rgba(22,163,74,0.25); }
.step h4 { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
.step p { font-size: 13px; color: #64748b; line-height: 1.5; }

/* BILLING */
.billing-section { padding: 80px 48px; background: #0f172a; color: #fff; }
.billing-section .section-header h2 { color: #fff; }
.billing-section .section-header p { color: #94a3b8; }
.bill-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 900px; margin: 0 auto; }
.bill-card { padding: 28px 24px; border-radius: 14px; background: #1e293b; border: 1px solid rgba(255,255,255,0.06); }
.bill-card-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.bill-card-val { font-size: 28px; font-weight: 800; color: #22c55e; margin-bottom: 4px; }
.bill-card-unit { font-size: 13px; color: #94a3b8; }

/* STATS */
.stats-section { padding: 80px 48px; display: flex; justify-content: center; gap: 64px; max-width: 1000px; margin: 0 auto; flex-wrap: wrap; }
.stat-item { text-align: center; min-width: 140px; }
.stat-num { font-size: 42px; font-weight: 800; color: #16a34a; }
.stat-label { font-size: 14px; color: #64748b; margin-top: 4px; }
.stat-icon { font-size: 24px; margin-bottom: 8px; }

/* CTA */
.cta-section { padding: 80px 48px; text-align: center; background: linear-gradient(180deg, #fff 0%, #f0fdf4 100%); }
.cta-section h2 { font-size: 32px; font-weight: 800; color: #0f172a; margin-bottom: 16px; }
.cta-section p { font-size: 16px; color: #64748b; margin-bottom: 32px; }

/* FOOTER */
.footer { padding: 40px 48px; border-top: 1px solid #e2e8f0; }
.footer-inner { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; }
.footer-left { font-size: 13px; color: #64748b; }
.footer-links { display: flex; gap: 24px; }
.footer-links a { font-size: 13px; color: #64748b; text-decoration: none; }
.footer-links a:hover { color: #0f172a; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; z-index: 200; background: rgba(15,23,42,0.5); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity 0.25s; }
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-card { width: 420px; background: #fff; border-radius: 16px; padding: 36px 32px; box-shadow: 0 24px 64px rgba(0,0,0,0.18); transform: translateY(16px); transition: transform 0.3s cubic-bezier(0.2,0.8,0.2,1); position: relative; }
.modal-overlay.active .modal-card { transform: translateY(0); }
.modal-close { position: absolute; top: 16px; right: 16px; width: 32px; height: 32px; border-radius: 8px; background: #f8fafb; border: none; font-size: 18px; color: #64748b; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.modal-close:hover { background: #e2e8f0; }
.modal-header { margin-bottom: 24px; }
.modal-header h2 { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
.modal-header p { font-size: 14px; color: #64748b; }
.tabs { display: flex; padding: 3px; margin-bottom: 24px; background: #f8fafb; border-radius: 10px; position: relative; }
.tab-btn { flex: 1; z-index: 1; padding: 10px 0; border: none; background: none; font: inherit; font-size: 14px; font-weight: 600; color: #64748b; cursor: pointer; transition: color 0.25s; }
.tab-btn.active { color: #0f172a; }
.tab-ind { position: absolute; top: 3px; bottom: 3px; left: 3px; width: calc(50% - 3px); border-radius: 8px; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: left 0.3s cubic-bezier(0.4,0,0.2,1); }
.tab-ind.reg { left: 50%; }
.form-wrap { position: relative; min-height: 260px; }
.auth-form { position: absolute; top: 0; left: 0; width: 100%; opacity: 0; pointer-events: none; transform: translateY(8px); transition: opacity 0.25s, transform 0.25s; }
.auth-form.active { opacity: 1; pointer-events: auto; position: relative; transform: translateY(0); }
.fg { margin-bottom: 16px; }
.fg label { display: block; font-size: 13px; font-weight: 600; color: #0f172a; margin-bottom: 6px; }
.fg input { width: 100%; padding: 11px 14px; border: 1px solid #e2e8f0; border-radius: 8px; font: inherit; font-size: 14px; color: #0f172a; outline: none; transition: border-color 0.2s, box-shadow 0.2s; background: #fff; }
.fg input:focus { border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,0.1); }
.fg input.err { border-color: #dc2626; }
.err-msg { font-size: 12px; color: #dc2626; margin-top: 4px; display: block; }
.hint { font-size: 12px; color: #64748b; margin-top: 4px; }
.btn-submit { width: 100%; padding: 12px; border: none; border-radius: 8px; font: inherit; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; margin-top: 8px; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-submit.login { background: #16a34a; color: #fff; }
.btn-submit.login:hover:not(:disabled) { background: #15803d; }
.btn-submit.register { background: #0f172a; color: #fff; }
.btn-submit.register:hover:not(:disabled) { background: #1e293b; }
.switch-text { text-align: center; margin-top: 16px; font-size: 13px; color: #64748b; }
.switch-text a { color: #16a34a; font-weight: 600; text-decoration: none; cursor: pointer; }

/* API MSG */
.api-msg { margin-top: 16px; padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; text-align: center; background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.api-msg.api-err { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
</style>
