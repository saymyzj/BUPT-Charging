<template>
  <div class="auth-a-wrapper">
    
<div class="container">
  <!-- LEFT -->
  <div class="left-panel">
    <div class="brand-icon">&#9889;</div>
    <div class="brand-title">智能充电桩调度计费系统</div>
    <div class="brand-tagline">智能调度 &middot; 高效充电 &middot; 透明计费</div>
    <ul class="features">
      <li>
        <div class="feature-icon">&#9889;</div>
        <div class="feature-text">
          <strong>智能调度</strong>
          <span>智能调度算法，最小化等待时间</span>
        </div>
      </li>
      <li>
        <div class="feature-icon">&#128202;</div>
        <div class="feature-text">
          <strong>实时监控</strong>
          <span>实时监控充电状态</span>
        </div>
      </li>
      <li>
        <div class="feature-icon">&#128176;</div>
        <div class="feature-text">
          <strong>透明计费</strong>
          <span>透明计费，自动生成账单</span>
        </div>
      </li>
    </ul>
  </div>

  <!-- RIGHT -->
  <div class="right-panel">
    <div class="auth-card">
      <div class="auth-header">
        <h2>欢迎回来</h2>
        <p>请登录或注册您的账号</p>
      </div>

      <div class="tabs">
        <button class="tab-btn" :class="{ active: activeTab === 'login' }" @click="activeTab = 'login'">登录</button>
        <button class="tab-btn" :class="{ active: activeTab === 'register' }" @click="activeTab = 'register'">注册</button>
        <div class="tab-indicator" :class="{ register: activeTab === 'register' }"></div>
      </div>

      <div class="form-wrapper">
        <!-- LOGIN FORM -->
        <form class="auth-form" :class="{ active: activeTab === 'login' }" @submit.prevent="handleLogin">
          <div class="form-group">
            <label>用户名</label>
            <div class="input-wrap">
              <input type="text" v-model="loginForm.user" placeholder="请输入用户名" autocomplete="username" :class="{ error: loginErrors.user }">
              <span class="error-msg">请输入用户名</span>
            </div>
          </div>
          <div class="form-group">
            <label>密码</label>
            <div class="input-wrap">
              <input :type="loginPwdType" v-model="loginForm.pwd" placeholder="请输入密码" autocomplete="current-password" :class="{ error: loginErrors.pwd }">
              <button type="button" class="toggle-pwd" @click="togglePwd('login')">{{ loginPwdType === 'password' ? '显示' : '隐藏' }}</button>
              <span class="error-msg">请输入密码</span>
            </div>
          </div>
          <div class="form-options">
            <label class="remember-me">
              <input type="checkbox"> 记住我
            </label>
            <a href="#" class="forgot-link">忘记密码?</a>
          </div>
          <button type="submit" class="btn btn-login">登 录</button>
          <div class="switch-text">还没有账号? <a @click="activeTab = 'register'">立即注册</a></div>
        </form>

        <!-- REGISTER FORM -->
        <form class="auth-form" :class="{ active: activeTab === 'register' }" @submit.prevent="handleRegister">
          <div class="form-group">
            <label>用户名</label>
            <div class="input-wrap">
              <input type="text" v-model="regForm.user" placeholder="请输入用户名" autocomplete="username" :class="{ error: regErrors.user }">
              <span class="error-msg">请输入用户名</span>
            </div>
          </div>
          <div class="form-group">
            <label>密码</label>
            <div class="input-wrap">
              <input :type="regPwdType" v-model="regForm.pwd" placeholder="请输入密码" autocomplete="new-password" :class="{ error: regErrors.pwd }">
              <button type="button" class="toggle-pwd" @click="togglePwd('reg')">{{ regPwdType === 'password' ? '显示' : '隐藏' }}</button>
              <span class="error-msg">请输入密码</span>
            </div>
          </div>
          <div class="form-group">
            <label>确认密码</label>
            <div class="input-wrap">
              <input :type="regPwdConfirmType" v-model="regForm.confirm" placeholder="请再次输入密码" autocomplete="new-password" :class="{ error: regErrors.confirm }">
              <button type="button" class="toggle-pwd" @click="togglePwd('confirm')">{{ regPwdConfirmType === 'password' ? '显示' : '隐藏' }}</button>
              <span class="error-msg">{{ regErrors.confirmMsg }}</span>
            </div>
          </div>
          <div class="form-group">
            <label>角色</label>
            <div class="input-wrap select-wrap">
              <select v-model="regForm.role">
                <option value="user">普通用户</option>
                <option value="admin">管理员</option>
              </select>
            </div>
          </div>
          <button type="submit" class="btn btn-register">注 册</button>
          <div class="switch-text">已有账号? <a @click="activeTab = 'login'">返回登录</a></div>
        </form>
      </div>
    </div>
  </div>
</div>

<div class="footer">&copy; 2026 G7 Group</div>



  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const activeTab = ref('login');
const loginPwdType = ref('password');
const regPwdType = ref('password');
const regPwdConfirmType = ref('password');

const loginForm = ref({ user: '', pwd: '' });
const regForm = ref({ user: '', pwd: '', confirm: '', role: 'user' });

const loginErrors = ref({ user: false, pwd: false });
const regErrors = ref({ user: false, pwd: false, confirm: false, confirmMsg: '请确认密码' });

function togglePwd(type) {
  if (type === 'login') loginPwdType.value = loginPwdType.value === 'password' ? 'text' : 'password';
  if (type === 'reg') regPwdType.value = regPwdType.value === 'password' ? 'text' : 'password';
  if (type === 'confirm') regPwdConfirmType.value = regPwdConfirmType.value === 'password' ? 'text' : 'password';
}

function handleLogin() {
  loginErrors.value.user = !loginForm.value.user.trim();
  loginErrors.value.pwd = !loginForm.value.pwd.trim();
  if (!loginErrors.value.user && !loginErrors.value.pwd) {
    if (loginForm.value.user === 'admin') {
      router.push('/admin/overview');
    } else {
      router.push('/user/workspace');
    }
  }
}

function handleRegister() {
  regErrors.value.user = !regForm.value.user.trim();
  regErrors.value.pwd = !regForm.value.pwd.trim();
  regErrors.value.confirm = !regForm.value.confirm.trim();
  
  if (regErrors.value.user || regErrors.value.pwd || regErrors.value.confirm) return;

  if (regForm.value.pwd !== regForm.value.confirm) {
    regErrors.value.confirm = true;
    regErrors.value.confirmMsg = '两次密码不一致';
    return;
  }
  
  alert('注册成功!');
}
</script>

<style scoped>

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

.auth-a-wrapper {
  --bg: #faf8f5;
  --card: #ffffff;
  --card-shadow: 0 4px 12px rgba(120,80,40,0.08);
  --primary: #2d6a4f;
  --secondary: #c45d3e;
  --accent: #d4a853;
  --text: #2c2c2c;
  --text-secondary: #7a7a7a;
  --error: #c0392b;
}

html, .auth-a-wrapper { 
  width: 100%; height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--text);
  overflow: hidden;
 }

h1, h2, h3, h4, h5, h6 { font-family: Georgia, serif; }

.container {
  display: flex;
  width: 100%; height: 100vh;
}

/* ===== LEFT PANEL ===== */
.left-panel {
  width: 50%; height: 100%;
  background: var(--primary);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px 60px;
  position: relative;
  overflow: hidden;
  transform: translateX(-100%);
  animation: slideInLeft 0.8s ease forwards;
}

@keyframes slideInLeft {
  to { transform: translateX(0); }
}

.left-panel::before {
  content: '';
  position: absolute;
  top: -100px; right: -100px;
  width: 300px; height: 300px;
  border: 2px solid rgba(255,255,255,0.06);
  border-radius: 50%;
}

.left-panel::after {
  content: '';
  position: absolute;
  bottom: -60px; left: -60px;
  width: 200px; height: 200px;
  border: 2px solid rgba(255,255,255,0.06);
  border-radius: 50%;
}

.brand-icon {
  width: 64px; height: 64px;
  background: var(--accent);
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px;
  margin-bottom: 32px;
}

.brand-title {
  font-family: Georgia, serif;
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 2px;
}

.brand-tagline {
  font-size: 16px;
  opacity: 0.8;
  margin-bottom: 56px;
  letter-spacing: 4px;
}

.features { list-style: none; }

.features li {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 28px;
  font-size: 15px;
  line-height: 1.6;
  opacity: 0;
  animation: fadeUp 0.6s ease forwards;
}

.features li:nth-child(1) { animation-delay: 0.9s; }
.features li:nth-child(2) { animation-delay: 1.1s; }
.features li:nth-child(3) { animation-delay: 1.3s; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.feature-icon {
  width: 44px; height: 44px;
  min-width: 44px;
  background: rgba(255,255,255,0.12);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
}

.feature-text strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.feature-text span {
  font-size: 13px;
  opacity: 0.7;
}

/* ===== RIGHT PANEL ===== */
.right-panel {
  width: 50%; height: 100%;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  animation: fadeInRight 0.8s ease 0.3s forwards;
}

@keyframes fadeInRight {
  from { opacity: 0; transform: translateX(40px); }
  to { opacity: 1; transform: translateX(0); }
}

.auth-card {
  width: 420px;
  background: var(--card);
  border-radius: 10px;
  box-shadow: var(--card-shadow);
  padding: 48px 40px 40px;
}

.auth-header {
  text-align: center;
  margin-bottom: 36px;
}

.auth-header h2 {
  font-size: 22px;
  color: var(--text);
  margin-bottom: 8px;
}

.auth-header p {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Tabs */
.tabs {
  display: flex;
  margin-bottom: 32px;
  border-bottom: 2px solid #eee;
  position: relative;
}

.tab-btn {
  flex: 1;
  background: none; border: none;
  padding: 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.3s;
  position: relative;
  font-family: inherit;
}

.tab-btn.active { color: var(--primary); }

.tab-indicator {
  position: absolute;
  bottom: -2px;
  height: 2px;
  width: 50%;
  background: var(--primary);
  transition: left 0.35s ease;
  left: 0;
}

.tab-indicator.register { left: 50%; }

/* Forms */
.form-wrapper {
  position: relative;
  min-height: 300px;
}

.auth-form {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.4s ease, transform 0.4s ease;
  transform: translateY(12px);
}

.auth-form.active {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
  position: relative;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-weight: 500;
}

.input-wrap {
  position: relative;
}

.input-wrap input, .input-wrap select {
  width: 100%;
  padding: 12px 0;
  font-size: 15px;
  border: none;
  border-bottom: 2px solid #e0e0e0;
  background: transparent;
  color: var(--text);
  outline: none;
  transition: border-color 0.3s;
  font-family: inherit;
}

.input-wrap input:focus, .input-wrap select:focus {
  border-bottom-color: var(--primary);
}

.input-wrap input.error {
  border-bottom-color: var(--error);
}

.input-wrap .error-msg {
  display: none;
  font-size: 12px;
  color: var(--error);
  margin-top: 4px;
}

.input-wrap input.error ~ .error-msg {
  display: block;
}

.toggle-pwd {
  position: absolute;
  right: 0; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  padding: 4px 0;
  font-family: inherit;
}

.toggle-pwd:hover { color: var(--primary); }

.input-wrap select {
  cursor: pointer;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  padding-right: 24px;
}

.select-wrap { position: relative; }
.select-wrap::after {
  content: '\25BC';
  position: absolute;
  right: 4px; top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  color: var(--text-secondary);
  pointer-events: none;
}

/* Remember me */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}

.remember-me {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--text-secondary);
  cursor: pointer;
}

.remember-me input[type="checkbox"] {
  width: 16px; height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}

.forgot-link {
  font-size: 13px;
  color: var(--primary);
  text-decoration: none;
}

.forgot-link:hover { text-decoration: underline; }

/* Buttons */
.btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s, transform 0.15s;
  font-family: inherit;
  letter-spacing: 1px;
}

.btn:active { transform: scale(0.98); }

.btn-login {
  background: var(--primary);
  color: #fff;
}

.btn-login:hover { background: #245840; }

.btn-register {
  background: var(--secondary);
  color: #fff;
}

.btn-register:hover { background: #a8492e; }

.switch-text {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.switch-text a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
}

.switch-text a:hover { text-decoration: underline; }

/* Footer */
.footer {
  position: absolute;
  bottom: 20px;
  left: 50%;
  width: 50%;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
}


.auth-a-wrapper {
  min-height: 100vh;
  overflow-x: hidden;
  background: var(--bg, #faf8f5);
}
</style>
