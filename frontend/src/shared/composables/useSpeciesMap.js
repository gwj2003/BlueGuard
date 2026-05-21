import { ref, nextTick, watch } from 'vue'
import L from 'leaflet'
import 'leaflet.heat'

import { getJson } from '@/api/client'
import { applyBasemap, BASEMAP_MAX_ZOOM, BASEMAP_MIN_ZOOM } from '@/utils/maps'


export const useSpeciesMap = (activeTab) => {
    const selectedSpecies = ref('')
    const selectedBasemap = ref('gaode_satellite')
    const selectedLayer = ref('points')
    const heatmapRadius = ref(20)
    const heatmapMinOpacity = ref(0.28)
    const selectedAdminLevel = ref('province')
    const bufferRadiusMeters = ref(2000)
    const currentLocations = ref([])
    const isAdminLayerLoading = ref(false)
    const yearFrom = ref(null)
    const yearTo = ref(null)
    const includeUnknown = ref(true)
    const yearMin = ref(null)
    const yearMax = ref(null)
    let lastSpeciesForRange = null

    let map = null
    let markersLayer = null
    let tileLayer = null
    let heatLayer = null
    let provinceLayer = null
    let bufferLayer = null
    let renderToken = 0
    let adminLoadToken = 0
    let locationLoadToken = 0
    let speciesSwitchToken = 0
    let isUpdatingRangeBySpecies = false

    const initMap = () => {
        if (map) return

        map = L.map('map', {
            minZoom: BASEMAP_MIN_ZOOM,
            maxZoom: BASEMAP_MAX_ZOOM,
        }).setView([35, 105], BASEMAP_MIN_ZOOM)
        markersLayer = L.layerGroup().addTo(map)
        changeBasemap()
        changeLayer()
    }

    const changeBasemap = () => {
        tileLayer = applyBasemap(map, tileLayer, selectedBasemap.value)
    }

    const clearDataLayers = () => {
        if (markersLayer && map?.hasLayer(markersLayer)) map.removeLayer(markersLayer)
        if (heatLayer && map?.hasLayer(heatLayer)) map.removeLayer(heatLayer)
        if (provinceLayer && map?.hasLayer(provinceLayer)) map.removeLayer(provinceLayer)
        if (bufferLayer && map?.hasLayer(bufferLayer)) map.removeLayer(bufferLayer)

        markersLayer = null
        heatLayer = null
        provinceLayer = null
        bufferLayer = null
    }

    const CHINA_BOUNDS = L.latLngBounds([
        [18.0, 73.0],
        [54.0, 135.0]
    ])
    const adminGeoJsonRenderer = L.canvas()

    const fitToCurrentSpeciesBounds = () => {
        if (!map) return
        const valid = (currentLocations.value || []).filter(
            (point) => Number.isFinite(point.latitude) && Number.isFinite(point.longitude)
        )
        if (!valid.length) return
        const bounds = L.latLngBounds(valid.map((point) => [point.latitude, point.longitude]))
        if (bounds.isValid()) {
            map.fitBounds(bounds)
        }
    }

    const fitToChinaBounds = () => {
        if (!map) return
        if (!CHINA_BOUNDS.isValid()) return
        map.fitBounds(CHINA_BOUNDS)
    }

    const updatePoints = () => {
        if (!markersLayer) return
        markersLayer.clearLayers()

        currentLocations.value.forEach((loc) => {
            if (Number.isFinite(loc.latitude) && Number.isFinite(loc.longitude)) {
                L.circleMarker([loc.latitude, loc.longitude], {
                    radius: 5,
                    fillColor: '#ff6b6b',
                    color: '#d63031',
                    weight: 2,
                    opacity: 0.7,
                    fillOpacity: 0.6
                })
                    .addTo(markersLayer)
                    .bindPopup(loc.location_name || `${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}`)
            }
        })
    }

    const loadHeatmapData = async (token, speciesValue = selectedSpecies.value) => {
        if (!speciesValue) return
        try {
            const params = {}
            if (yearFrom.value !== null) params.year_from = yearFrom.value
            if (yearTo.value !== null) params.year_to = yearTo.value
            params.include_unknown = includeUnknown.value
            const data = await getJson(`/heatmap/${encodeURIComponent(speciesValue)}`, params)
            if (token !== renderToken || selectedLayer.value !== 'heatmap') return
            const points = data.points || []
            if (points.length === 0) return
            heatLayer = L.heatLayer(points, {
                radius: heatmapRadius.value,
                blur: 15,
                maxZoom: 10,
                max: 1.0,
                minOpacity: heatmapMinOpacity.value,
                gradient: {
                    0.2: '#0000ff',
                    0.4: '#00ffff',
                    0.6: '#00ff00',
                    0.8: '#ffff00',
                    1.0: '#ff0000'
                }
            }).addTo(map)
        } catch (error) {
            console.error('加载热力图数据失败:', error)
        }
    }

    const CHOROPLETH_COLORS = ['#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026']

    const buildNaturalBreaks = (values, maxClasses = CHOROPLETH_COLORS.length) => {
        const sorted = values
            .map((value) => Number(value))
            .filter((value) => Number.isFinite(value) && value > 0)
            .sort((a, b) => a - b)

        if (!sorted.length) return []

        const uniqueValues = [...new Set(sorted)]
        if (uniqueValues.length === 1) {
            return [uniqueValues[0], uniqueValues[0]]
        }

        const classCount = Math.min(maxClasses, uniqueValues.length)
        const lowerClassLimits = Array.from({ length: sorted.length + 1 }, () => Array(classCount + 1).fill(0))
        const varianceCombinations = Array.from({ length: sorted.length + 1 }, () => Array(classCount + 1).fill(Infinity))

        for (let i = 1; i <= classCount; i += 1) {
            lowerClassLimits[1][i] = 1
            varianceCombinations[1][i] = 0
        }

        for (let l = 2; l <= sorted.length; l += 1) {
            let sum = 0
            let sumSquares = 0
            let weight = 0
            let variance = 0

            for (let m = 1; m <= l; m += 1) {
                const lowerClassLimit = l - m + 1
                const value = sorted[lowerClassLimit - 1]
                weight += 1
                sum += value
                sumSquares += value * value
                variance = sumSquares - (sum * sum) / weight

                const previousClassLimit = lowerClassLimit - 1
                if (previousClassLimit === 0) continue

                for (let j = 2; j <= classCount; j += 1) {
                    const nextVariance = variance + varianceCombinations[previousClassLimit][j - 1]
                    if (varianceCombinations[l][j] >= nextVariance) {
                        lowerClassLimits[l][j] = lowerClassLimit
                        varianceCombinations[l][j] = nextVariance
                    }
                }
            }

            lowerClassLimits[l][1] = 1
            varianceCombinations[l][1] = variance
        }

        const breaks = Array(classCount + 1).fill(0)
        breaks[0] = sorted[0]
        breaks[classCount] = sorted[sorted.length - 1]

        let k = sorted.length
        for (let j = classCount; j > 1; j -= 1) {
            const breakIndex = Math.max(0, lowerClassLimits[k][j] - 2)
            breaks[j - 1] = sorted[breakIndex]
            k = lowerClassLimits[k][j] - 1
        }

        return breaks
    }

    const getClassColor = (classIndex, classCount) => {
        if (classCount <= 1) return CHOROPLETH_COLORS[0]
        const paletteIndex = Math.round((classIndex / (classCount - 1)) * (CHOROPLETH_COLORS.length - 1))
        return CHOROPLETH_COLORS[paletteIndex]
    }

    const createNaturalBreaksClassifier = (features = []) => {
        const counts = features.map((feature) => Number(feature?.properties?.count || 0))
        const breaks = buildNaturalBreaks(counts)
        const classCount = Math.max(1, breaks.length - 1)

        return (value) => {
            const count = Number(value || 0)
            if (!Number.isFinite(count) || count <= 0) return '#f4f4f4'
            if (breaks.length <= 2) return getClassColor(0, classCount)

            for (let i = 1; i < breaks.length; i += 1) {
                if (count <= breaks[i]) {
                    return getClassColor(i - 1, classCount)
                }
            }

            return getClassColor(classCount - 1, classCount)
        }
    }

    const loadProvinceData = async (token, speciesValue = selectedSpecies.value) => {
        if (!speciesValue) return
        isAdminLayerLoading.value = true
        adminLoadToken = token
        try {
            const params = { level: selectedAdminLevel.value }
            if (yearFrom.value !== null) params.year_from = yearFrom.value
            if (yearTo.value !== null) params.year_to = yearTo.value
            params.include_unknown = includeUnknown.value
            const data = await getJson(`/province-data/${encodeURIComponent(speciesValue)}`, params)
            if (token !== renderToken || !['level', 'choropleth', 'province'].includes(selectedLayer.value)) return
            const getNaturalBreakColor = createNaturalBreaksClassifier(data.geojson?.features || [])
            provinceLayer = L.geoJSON(data.geojson, {
                renderer: adminGeoJsonRenderer,
                smoothFactor: 1.0,
                style: (feature) => {
                    const count = feature.properties.count
                    return {
                        fillColor: getNaturalBreakColor(count),
                        weight: 1,
                        opacity: 1,
                        color: count > 0 ? 'white' : '#ddd',
                        dashArray: '3',
                        fillOpacity: count > 0 ? 0.8 : 0.3
                    }
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`${feature.properties.name}: ${feature.properties.count} 记录`)
                }
            }).addTo(map)
        } catch (error) {
            console.error('加载省级数据失败:', error)
        } finally {
            if (adminLoadToken === token) {
                isAdminLayerLoading.value = false
            }
        }
    }

    const loadBufferData = async (token, speciesValue = selectedSpecies.value) => {
        if (!speciesValue) return
        try {
            const params = { radius_meters: bufferRadiusMeters.value }
            if (yearFrom.value !== null) params.year_from = yearFrom.value
            if (yearTo.value !== null) params.year_to = yearTo.value
            params.include_unknown = includeUnknown.value
            const data = await getJson(`/buffer-data/${encodeURIComponent(speciesValue)}`, params)
            if (token !== renderToken || selectedLayer.value !== 'buffer') return
            bufferLayer = L.geoJSON(data.geojson, {
                style: () => ({
                    fillColor: '#ff9f43',
                    color: '#d46b08',
                    weight: 2,
                    opacity: 0.9,
                    fillOpacity: 0.25,
                }),
                onEachFeature: (feature, layer) => {
                    const radius = feature?.properties?.radius_meters ?? bufferRadiusMeters.value
                    const count = feature?.properties?.count ?? currentLocations.value.length
                    layer.bindPopup(`
                        <div style="min-width: 180px; line-height: 1.5;">
                          <div><strong>缓冲半径：</strong>${Number(radius).toFixed(0)} 米</div>
                          <div><strong>缓冲点数：</strong>${count}</div>
                        </div>
                    `)
                },
            }).addTo(map)
        } catch (error) {
            console.error('加载缓冲区数据失败:', error)
        }
    }

    const changeLayer = async (options = {}) => {
        if (!map) return
        const { fitBounds = true, species = selectedSpecies.value } = options || {}
        const token = ++renderToken
        clearDataLayers()

        if (selectedLayer.value === 'points') {
            markersLayer = L.layerGroup().addTo(map)
            updatePoints()
            if (fitBounds) fitToCurrentSpeciesBounds()
        } else if (selectedLayer.value === 'heatmap') {
            await loadHeatmapData(token, species)
            if (fitBounds) fitToCurrentSpeciesBounds()
        } else if (['level', 'choropleth', 'province'].includes(selectedLayer.value)) {
            await loadProvinceData(token, species)
            if (fitBounds) fitToChinaBounds()
        } else if (selectedLayer.value === 'buffer') {
            await loadBufferData(token, species)
            if (fitBounds && bufferLayer) {
                const bounds = bufferLayer.getBounds()
                if (bounds.isValid()) {
                    map.fitBounds(bounds, { padding: [20, 20] })
                }
            } else if (fitBounds) {
                fitToCurrentSpeciesBounds()
            }
        }
    }

    const loadFilteredLocations = async (speciesValue = selectedSpecies.value) => {
        if (!speciesValue) return
        const token = ++locationLoadToken
        try {
            const params = {}
            if (yearFrom.value !== null) params.year_from = yearFrom.value
            if (yearTo.value !== null) params.year_to = yearTo.value
            params.include_unknown = includeUnknown.value
            const data = await getJson(`/locations/${encodeURIComponent(speciesValue)}`, params)
            if (token !== locationLoadToken) return
            if (speciesValue !== selectedSpecies.value) return
            currentLocations.value = data.locations || []
            changeLayer({ fitBounds: true, species: speciesValue })
        } catch (error) {
            console.error('加载位置失败:', error)
        }
    }

    const onSpeciesChange = async (speciesValue = selectedSpecies.value) => {
        const nextSpecies = speciesValue || ''
        const switchToken = ++speciesSwitchToken
        if (!nextSpecies) {
            selectedSpecies.value = ''
            currentLocations.value = []
            yearMin.value = null
            yearMax.value = null
            yearFrom.value = null
            yearTo.value = null
            includeUnknown.value = true
            lastSpeciesForRange = null
            changeLayer()
            return
        }

        selectedSpecies.value = nextSpecies
        try {
            // fetch all locations without year filter to compute available range
            const allData = await getJson(`/locations/${encodeURIComponent(nextSpecies)}`)
            if (switchToken !== speciesSwitchToken) return
            const allLocations = allData.locations || []
            const years = allLocations
                .map((r) => (Number.isFinite(r.year) ? Number(r.year) : null))
                .filter((y) => y !== null)

            isUpdatingRangeBySpecies = true
            if (years.length > 0) {
                const minY = Math.min(...years)
                const maxY = Math.max(...years)
                yearMin.value = minY
                yearMax.value = maxY
                // set default sliders to full range when species changed
                yearFrom.value = minY
                yearTo.value = maxY
            } else {
                yearMin.value = null
                yearMax.value = null
                yearFrom.value = null
                yearTo.value = null
            }
            includeUnknown.value = true
            isUpdatingRangeBySpecies = false
            lastSpeciesForRange = nextSpecies

            if (switchToken !== speciesSwitchToken) return
            await loadFilteredLocations(nextSpecies)
        } catch (error) {
            isUpdatingRangeBySpecies = false
            console.error('加载位置或年份范围失败:', error)
        }
    }

    watch(
        () => activeTab.value,
        (newTab) => {
            if (newTab !== 0) return
            nextTick(() => {
                setTimeout(() => {
                    if (activeTab.value !== 0) return
                    if (!map) initMap()
                    else map.invalidateSize(true)
                }, 100)
            })
        },
        { immediate: true }
    )

    watch([heatmapRadius, heatmapMinOpacity], () => {
        if (selectedLayer.value === 'heatmap') {
            changeLayer({ fitBounds: false })
        }
    })

    watch(selectedLayer, (newLayer, oldLayer) => {
        if (!map || newLayer === oldLayer) return
        changeLayer({ fitBounds: true })
    })

    watch(selectedAdminLevel, () => {
        if (['level', 'choropleth', 'province'].includes(selectedLayer.value)) {
            changeLayer({ fitBounds: false })
        }
    })

    watch(bufferRadiusMeters, () => {
        if (selectedLayer.value === 'buffer') {
            changeLayer({ fitBounds: false })
        }
    })

    // when year filters change, enforce bounds and reload filtered locations and layers
    watch([yearFrom, yearTo, includeUnknown], () => {
        if (!selectedSpecies.value) return
        if (isUpdatingRangeBySpecies) return
        // enforce bounds
        if (yearMin.value !== null && yearMax.value !== null) {
            if (yearFrom.value !== null && yearFrom.value < yearMin.value) yearFrom.value = yearMin.value
            if (yearTo.value !== null && yearTo.value > yearMax.value) yearTo.value = yearMax.value
            if (yearFrom.value !== null && yearTo.value !== null && yearFrom.value > yearTo.value) {
                // keep start <= end by adjusting end
                yearTo.value = yearFrom.value
            }
        }
        loadFilteredLocations(selectedSpecies.value)
    })

    return {
        selectedSpecies,
        selectedBasemap,
        selectedLayer,
        heatmapRadius,
        heatmapMinOpacity,
        selectedAdminLevel,
        bufferRadiusMeters,
        isAdminLayerLoading,
        currentLocations,
        yearFrom,
        yearTo,
        includeUnknown,
        yearMin,
        yearMax,
        changeBasemap,
        changeLayer,
        onSpeciesChange,
    }
}
