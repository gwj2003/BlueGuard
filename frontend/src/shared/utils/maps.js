import L from 'leaflet'

export const BASEMAP_MIN_ZOOM = 4
export const BASEMAP_MAX_ZOOM = 18

export const getBasemapLayers = (basemap) => {
    const layers = []

    switch (basemap) {
        case 'gaode_satellite':
            layers.push(L.tileLayer('https://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', {
                attribution: 'Tiles © AMap',
                minZoom: BASEMAP_MIN_ZOOM,
                maxZoom: BASEMAP_MAX_ZOOM
            }))
            break
        case 'gaode_satellite_annotated':
            layers.push(L.tileLayer('https://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', {
                attribution: 'Tiles © AMap',
                minZoom: BASEMAP_MIN_ZOOM,
                maxZoom: BASEMAP_MAX_ZOOM
            }))
            layers.push(L.tileLayer('https://webst02.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}', {
                minZoom: BASEMAP_MIN_ZOOM,
                maxZoom: BASEMAP_MAX_ZOOM
            }))
            break
    }

    return layers
}

export const applyBasemap = (map, layerGroup, basemap) => {
    if (!map) return null

    if (layerGroup) {
        map.removeLayer(layerGroup)
    }

    const nextGroup = L.layerGroup().addTo(map)
    getBasemapLayers(basemap).forEach((layer) => layer.addTo(nextGroup))
    return nextGroup
}
