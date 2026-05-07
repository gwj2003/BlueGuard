<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Morphext rotating text initialization
  if (window.$) {
    // Will be initialized by scripts.js after component mount
  }
})
</script>

<template>
  <header id="header" class="header">
    <div class="header-content">
      <div class="container">
        <div class="row">
          <div class="col-lg-12">
            <div class="text-container">
              <h1>
                中国水生动物 <span id="js-rotating">入侵检测, 智能化监测, 科学防控</span>
              </h1>
              <p class="p-heading p-large">
                构建全国领先的水生入侵动物智能化监测、分析与防控一体化平台
              </p>
              <a class="btn-solid-lg page-scroll" href="#intro">了解平台</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
header {
  width: 100%;
}
</style>
