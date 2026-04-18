<script setup>
import { computed, nextTick, onMounted } from 'vue'

const props = defineProps({
  rawHtml: {
    type: String,
    required: true,
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

function normalizeScriptSrc(src) {
  if (!src) {
    return ''
  }

  if (/^https?:\/\//i.test(src)) {
    return src
  }

  if (src.startsWith('/')) {
    return src
  }

  return `/${src.replace(/^\.\//, '')}`
}

const parsedPage = computed(() => {
  const parser = new DOMParser()
  const doc = parser.parseFromString(props.rawHtml, 'text/html')

  const scriptElements = Array.from(doc.querySelectorAll('script[src]'))
  const extractedScriptSources = scriptElements
    .map((script) => normalizeScriptSrc(script.getAttribute('src') || ''))
    .filter(Boolean)

  // v-html 不会执行 script，因此这里移除模板脚本，改为手动按顺序加载
  scriptElements.forEach((script) => script.remove())

  const bodyAttributes = {}
  for (const attr of Array.from(doc.body.attributes)) {
    bodyAttributes[attr.name] = attr.value
  }

  return {
    title: doc.title || '',
    bodyHtml: doc.body.innerHTML,
    bodyAttributes,
    scriptSources: extractedScriptSources.length > 0 ? extractedScriptSources : fallbackScriptSources,
  }
})

const bodyHtml = computed(() => parsedPage.value.bodyHtml)

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
  for (const src of parsedPage.value.scriptSources) {
    await loadScript(src)
  }
}

onMounted(async () => {
  const { title, bodyAttributes } = parsedPage.value

  if (title) {
    document.title = title
  }

  document.body.removeAttribute('data-spy')
  document.body.removeAttribute('data-target')
  for (const [key, value] of Object.entries(bodyAttributes)) {
    document.body.setAttribute(key, value)
  }

  await nextTick()
  await loadLegacyScripts()

  const spinner = document.querySelector('.spinner-wrapper')
  if (spinner) {
    setTimeout(() => {
      spinner.style.display = 'none'
    }, 700)
  }
})
</script>

<template>
  <div v-html="bodyHtml"></div>
</template>

<style>
html,
body,
#app {
  width: 100%;
}
</style>