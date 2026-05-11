<template>
  <div class="map-analysis">
    <aside class="sidebar">
      <div class="control-panel">
        <h3>分布识别分析</h3>

        <label class="field-label">选择底图</label>
        <PrettySelect v-model="basemapSelectModel" :options="basemapOptions" placeholder="请选择底图" />

        <label class="field-label">选择图层</label>
        <PrettySelect v-model="layerSelectModel" :options="layerOptions" placeholder="请选择图层" />

        <div v-if="selectedLayer === 'heatmap'" class="layer-settings">
          <div class="settings-title">热力图参数</div>
          <label class="field-label">热力半径：{{ heatmapRadius }} px</label>
          <input
            v-model.number="heatmapRadiusModel"
            type="range"
            min="10"
            max="60"
            step="1"
            class="range-input"
            :style="heatmapRadiusSliderStyle"
          />

          <label class="field-label">透明度：{{ heatmapOpacityDisplay }}</label>
          <input
            v-model.number="heatmapOpacityModel"
            type="range"
            min="0.1"
            max="1"
            step="0.05"
            class="range-input"
            :style="heatmapOpacitySliderStyle"
          />
        </div>

        <div v-else-if="selectedLayer === 'choropleth'" class="layer-settings">
          <div class="settings-title">填色图层级</div>
          <PrettySelect
            v-model="adminLevelSelectModel"
            :options="adminLevelOptions"
            :disabled="isAdminLayerLoading"
            placeholder="请选择层级"
          />
          <div v-if="selectedAdminLevel !== 'province'" class="loading-note"></div>
          <div v-if="isAdminLayerLoading" class="loading-note">正在生成分级填色图，请稍候...</div>
        </div>

        <div v-else-if="selectedLayer === 'buffer'" class="layer-settings">
          <div class="settings-title">缓冲区参数</div>
          <label class="field-label">缓冲半径：{{ bufferRadiusMeters }} 米</label>
          <input
            v-model.number="bufferRadiusMetersModel"
            type="range"
            min="200"
            max="20000"
            step="100"
            class="range-input"
            :style="bufferRadiusSliderStyle"
          />
        </div>

        <label class="field-label">选择物种</label>
        <PrettySelect v-model="speciesSelectModel" :options="speciesOptions" placeholder="-- 请选择物种 --" />

        <div v-if="selectedSpecies" class="time-range-panel">
          <div class="settings-title">选择时间区间</div>
          <div v-if="hasYearRange" class="year-range-wrap">
            <div class="year-range-values">
              <span>{{ yearFromDisplay }}</span>
              <span>{{ yearToDisplay }}</span>
            </div>
            <div class="dual-range">
              <div class="dual-range-track"></div>
              <div class="dual-range-selected" :style="selectedRangeStyle"></div>
              <input type="range" :min="yearMin" :max="yearMax" v-model.number="yearFrom" class="dual-thumb" />
              <input type="range" :min="yearMin" :max="yearMax" v-model.number="yearTo" class="dual-thumb" />
            </div>
            <div class="year-range-hint">全范围：{{ yearMin }} — {{ yearMax }}</div>
          </div>
          <div v-else class="loading-note">无可用年份数据或所有记录均为未知年份。</div>
          <label style="margin-top:8px; display:flex; gap:8px; align-items:center;">
            <input type="checkbox" v-model="includeUnknown" />
            <span class="field-label" style="font-weight:400;">包含未知时间段</span>
          </label>
        </div>

        <div v-if="selectedSpecies" class="stats-card">
          <div class="stats-title">分布统计</div>
          <div class="stats-value">{{ currentLocations.length }} 个记录点</div>
        </div>
      </div>
    </aside>

    <div class="map-stage">
      <div id="map" class="map-container"></div>
      <div v-if="isAdminLayerLoading" class="map-loading-mask">
        <div class="map-loading-card">
          <div class="map-loading-title">正在加载分级填色图</div>
          <div class="map-loading-text">市级和区县级数据量较大，首次生成会稍慢。</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import PrettySelect from '@/shared/components/PrettySelect.vue'

const props = defineProps({
  speciesList: { type: Array, required: true },
  selectedSpecies: { type: String, required: true },
  selectedBasemap: { type: String, required: true },
  selectedLayer: { type: String, required: true },
  heatmapRadius: { type: Number, required: true },
  heatmapMinOpacity: { type: Number, required: true },
  selectedAdminLevel: { type: String, required: true },
  bufferRadiusMeters: { type: Number, required: true },
  isAdminLayerLoading: { type: Boolean, required: true },
  currentLocations: { type: Array, required: true },
  yearFrom: { type: Number, required: false },
  yearTo: { type: Number, required: false },
  includeUnknown: { type: Boolean, required: false },
  yearMin: { type: Number, required: false },
  yearMax: { type: Number, required: false },
  changeBasemap: { type: Function, required: true },
  changeLayer: { type: Function, required: true },
  onSpeciesChange: { type: Function, required: true },
})

const emit = defineEmits([
  'update:selectedSpecies',
  'update:selectedBasemap',
  'update:selectedLayer',
  'update:heatmapRadius',
  'update:heatmapMinOpacity',
  'update:selectedAdminLevel',
  'update:bufferRadiusMeters',
  'update:yearFrom',
  'update:yearTo',
  'update:includeUnknown',
])

const basemapOptions = [
  { label: '高德卫星影像', value: 'gaode_satellite' },
  { label: '高德卫星影像（带标注）', value: 'gaode_satellite_annotated' },
]

const layerOptions = [
  { label: '散点图', value: 'points' },
  { label: '空间热力图', value: 'heatmap' },
  { label: '分级填色图', value: 'choropleth' },
  { label: '缓冲区图', value: 'buffer' },
]

const adminLevelOptions = [
  { label: '省级填色图', value: 'province' },
  { label: '市级填色图', value: 'city' },
  { label: '区县级填色图', value: 'district' },
]

const speciesOptions = computed(() => [
  { label: '-- 请选择物种 --', value: '' },
  ...props.speciesList.map((species) => ({ label: species, value: species })),
])

const basemapModelWithChange = computed({
  get: () => props.selectedBasemap,
  set: (value) => {
    emit('update:selectedBasemap', value)
    props.changeBasemap?.(value)
  },
})

const layerModelWithChange = computed({
  get: () => props.selectedLayer,
  set: (value) => {
    emit('update:selectedLayer', value)
  },
})

const heatmapRadiusModel = computed({
  get: () => props.heatmapRadius,
  set: (value) => {
    emit('update:heatmapRadius', Number(value))
  },
})

const heatmapOpacityModel = computed({
  get: () => props.heatmapMinOpacity,
  set: (value) => {
    emit('update:heatmapMinOpacity', Number(value))
  },
})

const adminLevelSelectModel = computed({
  get: () => props.selectedAdminLevel,
  set: (value) => {
    emit('update:selectedAdminLevel', value)
  },
})

const bufferRadiusMetersModel = computed({
  get: () => props.bufferRadiusMeters,
  set: (value) => {
    emit('update:bufferRadiusMeters', Number(value))
  },
})

const speciesModelWithChange = computed({
  get: () => props.selectedSpecies,
  set: (value) => {
    emit('update:selectedSpecies', value)
    props.onSpeciesChange?.(value)
  },
})

const yearFromModel = computed({
  get: () => props.yearFrom ?? null,
  set: (value) => {
    if (value === null || value === '') {
      emit('update:yearFrom', null)
      return
    }
    const raw = Number(value)
    const min = props.yearMin ?? raw
    const max = props.yearMax ?? raw
    const upper = props.yearTo ?? max
    const normalized = Math.min(Math.max(raw, min), Math.min(upper, max))
    emit('update:yearFrom', normalized)
  },
})

const yearToModel = computed({
  get: () => props.yearTo ?? null,
  set: (value) => {
    if (value === null || value === '') {
      emit('update:yearTo', null)
      return
    }
    const raw = Number(value)
    const min = props.yearMin ?? raw
    const max = props.yearMax ?? raw
    const lower = props.yearFrom ?? min
    const normalized = Math.max(Math.min(raw, max), Math.max(lower, min))
    emit('update:yearTo', normalized)
  },
})

const includeUnknownModel = computed({
  get: () => (props.includeUnknown === undefined ? true : props.includeUnknown),
  set: (value) => emit('update:includeUnknown', Boolean(value)),
})

const basemapSelectModel = basemapModelWithChange
const layerSelectModel = layerModelWithChange
const speciesSelectModel = speciesModelWithChange
const heatmapRadius = computed(() => props.heatmapRadius)
const bufferRadiusMeters = computed(() => props.bufferRadiusMeters)
const heatmapOpacityDisplay = computed(() => props.heatmapMinOpacity.toFixed(2))

const buildSingleSliderStyle = (value, min, max) => {
  const span = Math.max(1e-9, max - min)
  const ratio = (Number(value) - min) / span
  const progress = Math.max(0, Math.min(100, ratio * 100))
  return { '--range-progress': `${progress}%` }
}

const heatmapRadiusSliderStyle = computed(() => buildSingleSliderStyle(props.heatmapRadius, 10, 60))
const heatmapOpacitySliderStyle = computed(() => buildSingleSliderStyle(props.heatmapMinOpacity, 0.1, 1))
const bufferRadiusSliderStyle = computed(() => buildSingleSliderStyle(props.bufferRadiusMeters, 200, 20000))
const hasYearRange = computed(
  () => Number.isFinite(props.yearMin) && Number.isFinite(props.yearMax) && props.yearMax >= props.yearMin
)
const yearSpan = computed(() => {
  if (!hasYearRange.value) return 1
  return Math.max(1, Number(props.yearMax) - Number(props.yearMin))
})
const yearFromDisplay = computed(() => (props.yearFrom ?? props.yearMin ?? '-'))
const yearToDisplay = computed(() => (props.yearTo ?? props.yearMax ?? '-'))
const selectedRangeStyle = computed(() => {
  if (!hasYearRange.value) return { left: '0%', width: '100%' }
  const min = Number(props.yearMin)
  const fromValue = Number(props.yearFrom ?? props.yearMin)
  const toValue = Number(props.yearTo ?? props.yearMax)
  const left = ((fromValue - min) / yearSpan.value) * 100
  const right = ((toValue - min) / yearSpan.value) * 100
  return {
    left: `${Math.max(0, Math.min(100, left))}%`,
    width: `${Math.max(0, Math.min(100, right - left))}%`,
  }
})

// expose for template
const yearFrom = yearFromModel
const yearTo = yearToModel
const includeUnknown = includeUnknownModel
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

.layer-settings {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 0.25rem;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid #d8e4ef;
}

.settings-title {
  font-size: 0.92rem;
  font-weight: 700;
  color: #23313f;
}

.range-input {
  --range-progress: 0%;
  width: 100%;
  height: 28px;
  margin: 0;
  appearance: none;
  background: transparent;
}

.range-input::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, #14bf98 var(--range-progress), #d6e3ef var(--range-progress));
}

.range-input::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
  background: #0ea47f;
  box-shadow: 0 1px 4px rgba(20, 55, 79, 0.3);
  margin-top: -5px;
}

.range-input::-moz-range-track {
  height: 6px;
  border-radius: 999px;
  background: #d6e3ef;
}

.range-input::-moz-range-progress {
  height: 6px;
  border-radius: 999px;
  background: #14bf98;
}

.range-input::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
  background: #0ea47f;
  box-shadow: 0 1px 4px rgba(20, 55, 79, 0.3);
}

.year-range-wrap {
  display: grid;
  gap: 10px;
}

.year-range-values {
  display: flex;
  justify-content: space-between;
  font-size: 0.92rem;
  color: #324252;
}

.year-range-hint {
  font-size: 0.86rem;
  color: #5d7083;
}

.dual-range {
  position: relative;
  height: 28px;
}

.dual-range-track,
.dual-range-selected {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: 6px;
  border-radius: 999px;
}

.dual-range-track {
  left: 0;
  right: 0;
  background: #d6e3ef;
}

.dual-range-selected {
  background: linear-gradient(90deg, #14bf98, #16a085);
}

.dual-thumb {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 28px;
  margin: 0;
  pointer-events: none;
  appearance: none;
  background: transparent;
}

.dual-thumb::-webkit-slider-runnable-track {
  height: 6px;
  background: transparent;
}

.dual-thumb::-webkit-slider-thumb {
  pointer-events: auto;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
  background: #0ea47f;
  box-shadow: 0 1px 4px rgba(20, 55, 79, 0.3);
  margin-top: -5px;
}

.dual-thumb::-moz-range-track {
  height: 6px;
  background: transparent;
}

.dual-thumb::-moz-range-thumb {
  pointer-events: auto;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
  background: #0ea47f;
  box-shadow: 0 1px 4px rgba(20, 55, 79, 0.3);
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
  border-radius: 0.25rem;
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

.map-stage {
  position: relative;
}

.map-loading-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(246, 250, 252, 0.55);
  backdrop-filter: blur(2px);
  z-index: 10;
  pointer-events: none;
}

.map-loading-card {
  min-width: 240px;
  padding: 16px 20px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #d8e4ef;
  box-shadow: 0 14px 34px rgba(15, 35, 52, 0.12);
  text-align: center;
}

.map-loading-title {
  font-size: 1rem;
  font-weight: 700;
  color: #23313f;
}

.map-loading-text,
.loading-note {
  margin-top: 6px;
  font-size: 0.92rem;
  color: #5d7083;
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
