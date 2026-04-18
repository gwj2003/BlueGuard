<template>
  <div class="map-analysis">
    <aside class="sidebar">
      <div class="control-panel">
        <h3>分布识别分析</h3>

        <label class="field-label">选择底图</label>
        <select v-model="basemapModel" @change="changeBasemap" class="control-input">
          <option value="gaode_satellite">高德卫星影像</option>
          <option value="gaode_satellite_annotated">高德卫星影像（带标注）</option>
        </select>

        <label class="field-label">选择图层</label>
        <select v-model="layerModel" @change="changeLayer" class="control-input">
          <option value="points">散点图</option>
          <option value="heatmap">空间热力图</option>
          <option value="province">省级填色图</option>
          <option value="maxent">MaxEnt 适生区预测</option>
        </select>

        <label class="field-label">选择物种</label>
        <select v-model="speciesModel" @change="onSpeciesChange" class="control-input">
          <option value="">-- 请选择物种 --</option>
          <option v-for="species in speciesList" :key="species" :value="species">{{ species }}</option>
        </select>

        <div v-if="selectedSpecies" class="stats-card">
          <div class="stats-title">分布统计</div>
          <div class="stats-value">{{ currentLocations.length }} 个记录点</div>
        </div>
      </div>
    </aside>

    <div id="map" class="map-container"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  speciesList: { type: Array, required: true },
  selectedSpecies: { type: String, required: true },
  selectedBasemap: { type: String, required: true },
  selectedLayer: { type: String, required: true },
  currentLocations: { type: Array, required: true },
  changeBasemap: { type: Function, required: true },
  changeLayer: { type: Function, required: true },
  onSpeciesChange: { type: Function, required: true },
})

const emit = defineEmits(['update:selectedSpecies', 'update:selectedBasemap', 'update:selectedLayer'])

const speciesModel = computed({
  get: () => props.selectedSpecies,
  set: (value) => emit('update:selectedSpecies', value),
})

const basemapModel = computed({
  get: () => props.selectedBasemap,
  set: (value) => emit('update:selectedBasemap', value),
})

const layerModel = computed({
  get: () => props.selectedLayer,
  set: (value) => emit('update:selectedLayer', value),
})
</script>

<style scoped>
.map-analysis {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 680px;
}

.sidebar {
  border-right: 1px solid #e6edf5;
  background: linear-gradient(180deg, #f8fbff 0%, #eef5fb 100%);
}

.control-panel {
  display: grid;
  gap: 14px;
  padding: 24px 20px;
}

.control-panel h3 {
  margin: 0 0 6px;
  font-size: 1.15rem;
}

.field-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #324252;
}

.control-input {
  width: 100%;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  padding-left: 1rem;
  padding-right: 2rem;
  height: 3rem;
  border: 1px solid #dadada;
  border-radius: 0.25rem;
  background-color: #fff;
  color: #787976;
  font: 400 0.875rem/1.375rem 'Open Sans', sans-serif;
  transition: all 0.2s;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url('/images/down-arrow.png');
  background-position: 96% 50%;
  background-repeat: no-repeat;
}

.control-input:focus {
  border: 1px solid #a1a1a1;
  outline: none;
}

.control-input:hover {
  border-color: #bfc4ca;
}

.stats-card {
  margin-top: 10px;
  padding: 16px;
  border-radius: 0.5rem;
  background: #fff;
  border: 1px solid #d8e4ef;
  box-shadow: 0 8px 20px rgba(17, 52, 72, 0.08);
}

.stats-title {
  font-size: 0.9rem;
  color: #5d7083;
}

.stats-value {
  margin-top: 8px;
  font-size: 1.4rem;
  font-weight: 700;
  color: #14bf98;
}

.map-container {
  min-height: 680px;
}

@media (max-width: 980px) {
  .map-analysis {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: 0;
    border-bottom: 1px solid #e6edf5;
  }
}
</style>
