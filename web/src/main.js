import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // 引入样式
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 引入图标
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册所有图标，供侧边栏使用
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia()) // 启用状态管理
app.use(router)        // 启用路由
app.use(ElementPlus)   // 启用UI库

app.mount('#app')