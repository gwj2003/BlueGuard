import L from 'leaflet'

export const getBasemapLayers = (basemap) => {
  const layers = []

  switch (basemap) {
    case 'osm':
      layers.push(L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
      }))
      break
    case 'esri':
      layers.push(L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri',
        maxZoom: 18
      }))
      break
    case 'gaode_satellite':
      layers.push(L.tileLayer('https://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', {
        attribution: 'Tiles © AMap',
        maxZoom: 18
      }))
      break
    case 'gaode_satellite_annotated':
      layers.push(L.tileLayer('https://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', {
        attribution: 'Tiles © AMap',
        maxZoom: 18
      }))
      layers.push(L.tileLayer('https://webst02.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}', {
        maxZoom: 18
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
