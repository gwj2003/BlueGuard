import { createApp } from 'vue'
import LegacyPage from '@/legacy/LegacyPage.vue'

export function mountLegacyPage(rawHtml) {
    createApp(LegacyPage, { rawHtml }).mount('#app')
}