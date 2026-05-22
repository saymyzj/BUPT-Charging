import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'

function readEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {}

  const env = {}
  const content = fs.readFileSync(filePath, 'utf8')
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#') || !line.includes('=')) continue

    const splitAt = line.indexOf('=')
    const key = line.slice(0, splitAt).trim()
    const value = line.slice(splitAt + 1).trim().replace(/^['"]|['"]$/g, '')
    if (key) env[key] = value
  }
  return env
}

const frontendDir = path.dirname(fileURLToPath(import.meta.url))
const backendEnv = readEnvFile(path.resolve(frontendDir, '../backend/.env'))
const apiHost = backendEnv.LISTEN_HOST || '127.0.0.1'
const apiPort = backendEnv.LISTEN_PORT || '5000'
const apiTarget = process.env.VITE_API_PROXY_TARGET || `http://${apiHost}:${apiPort}`

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
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
