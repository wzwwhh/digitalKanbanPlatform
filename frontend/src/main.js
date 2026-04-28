import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 注册所有插件（主题、组件等）
import './themes/_registry'
import './widgets/_registry'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 初始化主题（必须在 pinia 挂载后）
import { useThemeStore } from './stores/theme'
const themeStore = useThemeStore()
themeStore.initTheme()

app.mount('#app')
