import { createApp } from 'vue'
import CaseFeaturePage from '@/pages/CaseFeaturePage.vue'

export function mountCaseFeaturePage(props) {
    createApp(CaseFeaturePage, props).mount('#app')
}
