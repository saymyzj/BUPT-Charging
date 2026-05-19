import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'
import { DEV_RESET_STAMP } from './dev-reset-signal'
import { clearAuthSession } from './utils/authSession'

if (DEV_RESET_STAMP) {
  const stamp = String(DEV_RESET_STAMP)
  if (localStorage.getItem('dev_reset_stamp') !== stamp) {
    clearAuthSession()
    localStorage.setItem('dev_reset_stamp', stamp)
  }
}

const app = createApp(App)
app.use(router)
app.mount('#app')
