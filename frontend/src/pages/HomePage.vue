<script setup>
import { nextTick, onMounted, ref } from 'vue'
import AppFooter from '@/components/AppFooter.vue'
import AppNavbar from '@/components/AppNavbar.vue'
import HomeHero from './home/HomeHero.vue'
import HomeIntro from './home/HomeIntro.vue'
import HomeCards from './home/HomeCards.vue'
import HomeServices from './home/HomeServices.vue'
import HomeAccordion from './home/HomeAccordion.vue'
import HomeTabs from './home/HomeTabs.vue'

const isLoading = ref(true)
const isFadingOut = ref(false)
const PRELOADER_DELAY_MS = 500
const PRELOADER_FADE_OUT_MS = 500

// 加载所有必需的 legacy 脚本以完全复现原有功能
const scriptSources = [
  '/js/jquery.min.js',
  '/js/popper.min.js',
  '/js/bootstrap.min.js',
  '/js/jquery.easing.min.js',
  '/js/swiper.min.js',
  '/js/jquery.magnific-popup.js',
  '/js/morphext.min.js',
  '/js/isotope.pkgd.min.js',
  '/js/validator.min.js',
  '/js/scripts.js',
]

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function runLegacyLikePreloaderHide() {
  setTimeout(() => {
    isFadingOut.value = true
    setTimeout(() => {
      isLoading.value = false
    }, PRELOADER_FADE_OUT_MS)
  }, PRELOADER_DELAY_MS)
}

function hasScript(src) {
  const absSrc = new URL(src, window.location.origin).href
  return Array.from(document.scripts).some((script) => script.src === absSrc)
}

function loadScript(src) {
  if (hasScript(src)) {
    return Promise.resolve()
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = src
    script.async = false
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`))
    document.body.appendChild(script)
  })
}

async function loadLegacyScripts() {
  for (const src of scriptSources) {
    await loadScript(src)
  }
}

onMounted(async () => {
  document.title = '中国水生动物入侵智能化平台'
  document.body.setAttribute('data-spy', 'scroll')
  document.body.setAttribute('data-target', '.fixed-top')

  try {
    await nextTick()
    await loadLegacyScripts()
  } catch (error) {
    console.error('Failed to initialize home page scripts:', error)
  } finally {
    // 匹配 legacy 预加载器行为：等待 500ms，然后在 500ms 内褪色
    runLegacyLikePreloaderHide()
    await sleep(PRELOADER_DELAY_MS + PRELOADER_FADE_OUT_MS)
  }
})
</script>

<template>
  <AppNavbar />

  <div v-if="isLoading" class="spinner-wrapper" :class="{ 'is-fading-out': isFadingOut }">
    <div class="spinner">
      <div class="bounce1"></div>
      <div class="bounce2"></div>
      <div class="bounce3"></div>
    </div>
  </div>

  <main>
    <HomeHero />
    <HomeIntro />
    <HomeCards />
    <HomeServices />
    <HomeAccordion />
    <HomeTabs />
  </main>

  <AppFooter />
</template>

<style>
html,
body,
#app {
  width: 100%;
}

.spinner-wrapper {
  opacity: 1;
}

.spinner-wrapper.is-fading-out {
  opacity: 0;
  transition: opacity 500ms ease;
}
</style>