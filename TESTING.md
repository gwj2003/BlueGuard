# 测试指南

本文档提供了完整的测试步骤，确保应用正常工作。

## 前置条件

- Python 3.8 或更高版本
- Node.js 20 或更高版本
- npm 或 yarn

## 快速验证清单

### 1. 后端验证

```bash
cd backend
pip install -r requirements.txt

# 验证能否导入关键模块
python -c "from fastapi import FastAPI; print('FastAPI OK')"
python -c "from langchain_openai import ChatOpenAI; print('LangChain OK')"
python -c "import pandas; print('Pandas OK')"

# 启动后端
uvicorn main:app --reload --port 8000
```

预期输出：
```
Uvicorn running on http://0.0.0.0:8000
```

访问 http://localhost:8000/ 应显示：
```json
{"message": "后端服务已启动！可以开始查询水生外来入侵物种了！"}
```

### 2. 前端验证

```bash
cd frontend
npm install
npm run dev
```

预期输出：
```
  ➜  Local:   http://localhost:5173/
```

在浏览器打开 http://localhost:5173/

### 3. API 端点测试

#### 测试物种列表
```bash
curl http://localhost:8000/api/species
```

#### 测试知识问答
```bash
curl -X POST http://localhost:8000/api/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "福寿螺有什么危害？"}'
```

#### 测试数据上报
```bash
curl -X POST http://localhost:8000/api/record/location \
  -H "Content-Type: application/json" \
  -d '{
    "species": "福寿螺",
    "latitude": 30.5,
    "longitude": 114.1,
    "location_name": "武汉市",
    "date": "2024-04-01"
  }'
```

### 4. 前端功能测试

#### Tab 1: 分布识别分析
- [ ] 能否加载物种列表
- [ ] 选择物种后地图是否显示标记点
- [ ] 能否看到点位数统计

#### Tab 2: 知识问答
- [ ] 能否看到问答面板
- [ ] 能否选择物种
- [ ] 能否提交问题并收到回答
- [ ] 能否清空对话

#### Tab 3: 数据上报
- [ ] 能否填写表单
- [ ] 能否保存记录
- [ ] 能否看见已保存的记录列表

## 故障排查

### 后端问题

**问题：ModuleNotFoundError: No module named 'fastapi'**
```bash
解决：pip install -r requirements.txt
```

**问题：Connection refused on port 8000**
```bash
解决：
1. 检查是否有其他进程占用 8000 端口
2. 尝试使用其他端口：uvicorn main:app --port 8001
```

**问题：Neo4j connection failed**
```bash
解决：
- 如果不需要 Neo4j，可以忽略此错误
- 应用会自动切换到 LLM 离线模式
```

### 前端问题

**问题：npm install 失败**
```bash
解决：
rm -rf node_modules package-lock.json
npm install
```

**问题：Cannot find module 'leaflet'**
```bash
解决：npm install leaflet
```

**问题：API 连接失败**
```bash
解决：
1. 确保后端在 http://localhost:8000 运行
2. 检查浏览器控制台的错误信息
3. 检查 CORS 配置
```

## 性能优化建议

### 对于大量物种数据
- 使用数据库分页
- 在地图上限制显示的标记数量

### 对于知识问答
- 响应缓存
- 使用异步处理

## 开发工作流

### 热重载开发
```bash
# 终端 1: 后端
cd backend
uvicorn main:app --reload

# 终端 2: 前端
cd frontend
npm run dev
```

### 生产部署
```bash
# 后端
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端
npm run build
# 部署 dist/ 目录到静态服务器
```

## 数据维护

### 定期备份
```bash
# 备份数据库
cp backend/data/species.db backup/species_$(date +%Y%m%d).db
```

### 清理旧数据
```bash
# 删除指定日期之前的上报记录（谨慎操作）
sqlite3 backend/data/species.db "DELETE FROM location_records WHERE date < '2025-01-01';"
```

## 常见问题 (FAQ)

**Q: 如何绑定自己的 API Key？**
A: 修改 `backend/graph_chain.py` 中的 OPENAI_API_KEY

**Q: 如何添加新物种？**
A: 将 CSV 文件放入 `backend/data/gbif_results/` 目录，文件名为物种名.csv

**Q: 如何修改地图初始位置？**
A: 修改 HomeView.vue 中的 `map.setView([35, 105], 4)`

**Q: 能否离线运行？**
A: 可以，只要 Neo4j 和 API key 可选。应用会使用 LLM 离线回答。

---

如有问题，请提交 Issue 或查阅项目 README.md
