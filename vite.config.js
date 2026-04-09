import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget =
    env.VITE_DEV_PROXY_TARGET || env.VITE_DEV_API_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    server: {
      proxy: {
        // Local FastAPI: npm run dev:api (see package.json)
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
        '/wait-times': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
        '/virus-trends': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
