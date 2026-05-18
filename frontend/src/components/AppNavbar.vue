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
    <a class="navbar-brand logo-image" href="index.html"><img src="/images/new.svg" alt="alternative" style="height: 44px; width: auto" /></a>

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
            <a class="dropdown-item" href="basin-monitoring.html"><span class="item-text">时空分布态势</span></a>
            <div class="dropdown-items-divide-hr"></div>
            <a class="dropdown-item" href="knowledge-graph.html"><span class="item-text">图谱智能问答</span></a>
            <div class="dropdown-items-divide-hr"></div>
            <a class="dropdown-item" href="mobile-monitoring.html"><span class="item-text">众包灾情上报</span></a>
          </div>
        </li>
      </ul>
    </div>
  </nav>
</template>