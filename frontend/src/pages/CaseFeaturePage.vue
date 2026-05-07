<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import AppFooter from '@/components/AppFooter.vue'
import AppNavbar from '@/components/AppNavbar.vue'
import CaseQaFeature from '@/features/CaseQaFeature.vue'
import CaseReportFeature from '@/features/CaseReportFeature.vue'
import CaseSpeciesFeature from '@/features/CaseSpeciesFeature.vue'

const props = defineProps({
  pageTitle: {
    type: String,
    required: true,
  },
  pageDescription: {
    type: String,
    default: '',
  },
  featureType: {
    type: String,
    required: true,
    validator: (value) => ['species', 'qa', 'report'].includes(value),
  },
})

const fallbackScriptSources = [
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

const isLoading = ref(true)
const isFadingOut = ref(false)
const PRELOADER_DELAY_MS = 500
const PRELOADER_FADE_OUT_MS = 500

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

const featureComponentMap = {
  species: CaseSpeciesFeature,
  qa: CaseQaFeature,
  report: CaseReportFeature,
}

const currentFeatureComponent = computed(() => featureComponentMap[props.featureType])

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
  for (const src of fallbackScriptSources) {
    await loadScript(src)
  }
}

onMounted(async () => {
  document.title = `${props.pageTitle} - 中国水生动物入侵智能化平台`
  document.body.setAttribute('data-spy', 'scroll')
  document.body.setAttribute('data-target', '.fixed-top')

  try {
    await nextTick()
    await loadLegacyScripts()
  } catch (error) {
    console.error('Failed to initialize case page scripts:', error)
  } finally {
    // Match legacy preloader timing: wait 500ms, then fade out in 500ms.
    runLegacyLikePreloaderHide()
    await sleep(PRELOADER_DELAY_MS + PRELOADER_FADE_OUT_MS)
  }
})
</script>

<template>
  <div v-if="isLoading" class="spinner-wrapper" :class="{ 'is-fading-out': isFadingOut }">
    <div class="spinner">
      <div class="bounce1"></div>
      <div class="bounce2"></div>
      <div class="bounce3"></div>
    </div>
  </div>

  <AppNavbar />

  <header id="header" class="ex-header case-header">
    <div class="container">
      <div class="row">
        <div class="col-md-12">
          <h1>{{ pageTitle }}</h1>
          <p class="p-heading p-large" v-if="pageDescription">{{ pageDescription }}</p>
        </div>
      </div>
    </div>
  </header>

  <div class="ex-basic-1">
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <div class="breadcrumbs">
            <a href="index.html">首页</a><i class="fa fa-angle-double-right"></i>
            <span>{{ pageTitle }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="ex-basic-2 case-content">
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <div class="case-card">
            <component :is="currentFeatureComponent" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="ex-basic-1">
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <div class="breadcrumbs">
            <a href="index.html">首页</a><i class="fa fa-angle-double-right"></i>
            <span>{{ pageTitle }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <AppFooter />
</template>

<style>
html,
body,
#app {
  width: 100%;
}

.case-header {
  background: linear-gradient(135deg, #113448 0%, #0c6f5a 55%, #14bf98 100%);
}

.case-content {
  padding-top: 1.25rem;
  padding-bottom: 0.75rem;
}

.ex-header .p-heading {
  margin-top: 1rem;
  color: #dfe5ec;
}

.case-card {
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 16px 36px rgba(17, 52, 72, 0.12);
  background: #fff;
}

.spinner-wrapper {
  opacity: 1;
}

.spinner-wrapper.is-fading-out {
  opacity: 0;
  transition: opacity 500ms ease;
}
</style>
