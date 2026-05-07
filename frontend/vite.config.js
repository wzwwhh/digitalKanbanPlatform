import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  // ✅ 核心修改：这里设置部署的公共基础路径
  // 如果你想在 /kanban/ 下访问，这里必须写 '/kanban/'
  base: '/kanban/',

  server: {
    port: 5175,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 如果后端不需要 /api 前缀，可能需要 rewrite，视后端情况而定
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})