import { createApp } from 'vue'
import HomePage from '@/pages/HomePage.vue'

export function mountHomePage() {
    createApp(HomePage).mount('#app')
}
