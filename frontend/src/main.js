import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// 注册所有插件（主题、组件等）
import './themes/_registry'
import './widgets/_registry'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
