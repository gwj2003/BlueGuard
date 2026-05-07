<script setup>
import { computed } from 'vue'

const isHomePage = computed(() => {
  if (typeof window === 'undefined') {
    return true
  }

  const path = window.location.pathname.toLowerCase()
  return path.endsWith('/index.html') || path.endsWith('/')
})

const homeHref = computed(() => (isHomePage.value ? '#header' : 'index.html'))

function sectionHref(sectionId) {
  return isHomePage.value ? `#${sectionId}` : `index.html#${sectionId}`
}

function sectionClass() {
  return {
    'page-scroll': isHomePage.value,
  }
}
</script>

<template>
  <nav class="navbar navbar-expand-md navbar-dark navbar-custom fixed-top">
    <a class="navbar-brand logo-image" href="index.html"><img src="/images/logo.svg" alt="alternative" /></a>

    <button
      class="navbar-toggler"
      type="button"
      data-toggle="collapse"
      data-target="#navbarsExampleDefault"
      aria-controls="navbarsExampleDefault"
      aria-expanded="false"
      aria-label="切换导航"
    >
      <span class="navbar-toggler-awesome fas fa-bars"></span>
      <span class="navbar-toggler-awesome fas fa-times"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarsExampleDefault">
      <ul class="navbar-nav ml-auto">
        <li class="nav-item">
          <a class="nav-link" :class="sectionClass()" :href="homeHref">首页 <span class="sr-only">(当前)</span></a>
        </li>
        <li class="nav-item">
          <a class="nav-link" :class="sectionClass()" :href="sectionHref('intro')">平台简介</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" :class="sectionClass()" :href="sectionHref('services')">平台特色</a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" :class="sectionClass()" :href="sectionHref('projects')" id="projectsDropdown" role="button" aria-haspopup="true" aria-expanded="false">核心功能</a>
          <div class="dropdown-menu" aria-labelledby="projectsDropdown">
            <a class="dropdown-item" href="basin-monitoring.html"><span class="item-text">流域监测项目</span></a>
            <div class="dropdown-items-divide-hr"></div>
            <a class="dropdown-item" href="knowledge-graph.html"><span class="item-text">知识图谱应用</span></a>
            <div class="dropdown-items-divide-hr"></div>
            <a class="dropdown-item" href="mobile-monitoring.html"><span class="item-text">移动端监测</span></a>
          </div>
        </li>
      </ul>
    </div>
  </nav>
</template>