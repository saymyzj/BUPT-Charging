import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:5000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // Ensure accessible via both 127.0.0.1 and localhost
    proxy: {
      '/health': {
        target: apiTarget,
        changeOrigin: true
      },
      '/api': {
        target: apiTarget,
        changeOrigin: true
      }
    }
  }
})
