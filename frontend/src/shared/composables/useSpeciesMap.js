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

    const getColor = (d) => {
        return d > 50 ? '#800026' :
            d > 20 ? '#BD0026' :
                d > 10 ? '#E31A1C' :
                    d > 5 ? '#FC4E2A' :
                        d > 2 ? '#FD8D3C' :
                            '#FEB24C'
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
            provinceLayer = L.geoJSON(data.geojson, {
                renderer: adminGeoJsonRenderer,
                smoothFactor: 1.0,
                style: (feature) => {
                    const count = feature.properties.count
                    return {
                        fillColor: count > 0 ? getColor(count) : '#f4f4f4',
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
