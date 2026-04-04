# 水生入侵生物综合平台

## 项目结构

- `backend/` - Python FastAPI 后端服务
- `frontend/` - Vue 3 前端应用

## 快速启动

### 1. 后端启动

```bash
cd backend

# 创建虚拟环境（可选）
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements-app.txt.txt

# 启动服务
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

后端将在 `http://localhost:8000` 运行

### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发服务
npm run dev
```

前端将在 `http://localhost:5173` 运行

## 功能说明

### 🌍 分布识别分析 (Tab 1)
- 选择物种查看分布地点
- 地图展示物种的各个出现位置
- 显示记录数统计

### 🤖 智能知识问答 (Tab 2)
- 与 AI 助手对话，了解物种信息
- 快速建议问题
- 实时聊天交互

### 📝 数据上报与更新 (Tab 3)
- 新增物种分布记录
- 表单填写坐标和位置信息
- 查看已收集的所有数据

## API 端点

- `GET /api/species` - 获取物种列表
- `GET /api/locations/{species}` - 获取物种分布位置
- `POST /api/qa` - 提交知识问答
- `POST /api/record/location` - 上报新记录
- `GET /api/records` - 获取所有记录

## 环境配置

### 必需（可选）
- Neo4j 数据库：用于知识图谱（可选，不连接时自动使用 LLM 离线回答）
- DeepSeek API Key：用于 LLM 模型（默认已配置示例 key）

### API 密钥配置

在 `backend/graph_chain.py` 中修改：
- `OPENAI_API_KEY`: DeepSeek API 密钥
- `OPENAI_API_BASE`: DeepSeek API 地址

## 数据文件格式

### GBIF 结果 (gbif_results/*.csv)
要求字段：`decimalLatitude`, `decimalLongitude`, `locality`

### 上报记录 (data/locations_record.csv)
自动生成，包含：`species`, `latitude`, `longitude`, `location_name`, `date`

## 故障排除

1. **后端连接失败**
   - 检查后端是否在 8000 端口运行
   - 确认 CORS 配置正确（已允许 localhost:5173）

2. **物种列表为空**
   - 检查 `backend/data/gbif_results/` 目录是否有 CSV 文件

3. **知识问答无法连接**
   - 检查 Neo4j 是否运行（如果需要）
   - 检查 API 密钥配置

## 技术栈

### 后端
- FastAPI
- Uvicorn
- LangChain
- Neo4j (可选)
- Pandas

### 前端
- Vue 3
- Vue Router
- Leaflet (地图)
- Vite

## 许可证

此项目为学术研究项目
