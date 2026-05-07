# Shared Modules

`src/shared/` 是当前前端复用层，存放跨页面可复用的 API、组件、组合式逻辑和工具函数。

## 目录与文件

```text
src/shared/
├── api/
│   ├── client.js           # 通用请求封装
│   └── geocoding.js        # 地理编码相关 API
├── chat/
│   └── ChatPanel.vue       # 问答交互面板
├── report/
│   └── ReportPanel.vue     # 记录上报面板
├── species/
│   └── SpeciesMapPanel.vue # 物种地图展示面板
├── composables/
│   ├── useChatQa.js        # 问答交互逻辑
│   ├── useReportMap.js     # 上报地图交互逻辑
│   └── useSpeciesMap.js    # 物种地图交互逻辑
└── utils/
	└── maps.js             # 地图工具函数
```

## 使用边界

- 可复用的 UI 或逻辑优先放在本目录。
- 页面专用、不可复用逻辑应放在 `src/features/` 或对应页面目录，避免 shared 膨胀。
- 对外提供稳定接口时，优先通过函数参数传入配置，减少硬编码依赖。

## 主要调用方

- `src/features/CaseSpeciesFeature.vue`
- `src/features/CaseQaFeature.vue`
- `src/features/CaseReportFeature.vue`
- `src/legacy/LegacyCaseFeaturePage.vue`
