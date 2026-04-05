# 水生入侵生物综合平台

一个前后端分离的水生入侵物种分析系统：
- 后端：FastAPI + SQLite + 地理分析 + 图谱问答
- 前端：Vue 3 + Leaflet 地图可视化

## 目录

- `backend/` 后端服务与数据处理
- `frontend/` 前端界面
- `start.bat` Windows 一键启动

## 快速启动

### 方式一：一键启动（推荐）

Windows:
```bash
start.bat
```

### 方式二：手动启动

后端：
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

前端（新终端）：
```bash
cd frontend
npm install
npm run dev
```

访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- OpenAPI 文档：http://localhost:8000/docs

## 核心功能

- 分布识别分析：地图点位、热力图、省级统计、MaxEnt 图层
- 智能知识问答：图谱问答 + LLM 降级
- 数据上报：前端表单新增记录，落库保存

## 数据与数据库

### 当前存储

- 主数据库：`backend/data/species.db`
- 原始分布数据：`backend/data/gbif_results/*.csv`（用于初始化/迁移）
- 用户上报记录：写入 SQLite 的 `location_records` 表

### 初始化数据库（从 CSV 导入）

```bash
cd backend
python migrate_csv_to_db.py
```

## 数据库 CRUD（增删改查）

这里给你一个可直接照抄的流程。

### 1) 查（Read）

API 查询物种列表：
```bash
curl http://localhost:8000/api/species
```

API 查询某物种位置：
```bash
curl "http://localhost:8000/api/locations/福寿螺"
```

SQL 直接查询：
```sql
SELECT species_label, latitude, longitude
FROM species_distribution
WHERE species_label = '福寿螺'
LIMIT 20;
```

### 2) 增（Create）

通过 API 新增上报记录：
```bash
curl -X POST http://localhost:8000/api/record/location \
  -H "Content-Type: application/json" \
  -d '{
    "species": "福寿螺",
    "latitude": 30.2741,
    "longitude": 120.1551,
    "location_name": "杭州西湖",
    "date": "2026-04-05"
  }'
```

SQL 直接新增（谨慎）：
```sql
INSERT INTO location_records(species, latitude, longitude, location_name, date)
VALUES ('福寿螺', 30.2741, 120.1551, '杭州西湖', '2026-04-05');
```

### 3) 改（Update）

目前后端 API 没有提供更新接口，可直接用 SQL：
```sql
UPDATE location_records
SET location_name = '杭州西湖景区'
WHERE id = 1;
```

如果你希望走 API，我可以帮你加 `PUT /api/record/location/{id}`。

### 4) 删（Delete）

目前后端 API 没有提供删除接口，可直接用 SQL：
```sql
DELETE FROM location_records
WHERE id = 1;
```

如果你希望走 API，我可以帮你加 `DELETE /api/record/location/{id}`。

## 常用 API

- `GET /api/species`
- `GET /api/species/{species}`
- `GET /api/locations/{species}`
- `GET /api/province-data/{species}`
- `GET /api/maxent-image/{species}`
- `POST /api/qa`
- `POST /api/record/location`
- `GET /api/records`
- `GET /api/health`

## 测试

详细测试步骤见 `TESTING.md`。

## 说明

- Neo4j 和 API Key 可选，不可用时系统会降级到普通 LLM 回答。
- 本项目是研究用途示例，不建议直接暴露到公网。
