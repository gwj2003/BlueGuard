# 水生入侵生物综合平台

本项目是前后端分离的多页面应用。

- 后端：FastAPI + SQLite（可选 Neo4j）
- 前端：Vue 3 + Vite（MPA 入口）
- 目标：支撑物种查询、问答、上报与地理展示等能力

## 维护者视角

这个仓库最重要的不是页面本身，而是三条链路：

1. 启动链路：`scripts/` 下的批处理和 shell 脚本负责本地启动、Neo4j 拉起和 ngrok 暴露。
2. 后端链路：`backend/` 负责 API、服务层、仓储层、模型和模式定义。
3. 前端链路：`frontend/` 负责多页面入口、旧模板壳、共享模块和案例页功能组件。

## 仓库结构

```text
./
├── backend/                # 后端服务、数据迁移、图谱与问答逻辑
├── frontend/               # 前端多页面应用与静态资源
├── scripts/                # 本地启动、Neo4j、ngrok 相关脚本
├── environment.yml         # Python/Conda 环境定义
├── SETUP_GUIDE.md          # 安装与启动指南
└── README.md               # 当前文件
```

## 后端目录说明

```text
backend/
├── main.py                 # FastAPI 入口，负责创建应用并挂载路由
├── config.py               # 管理数据库、Neo4j、API Key 等配置
├── database.py             # 负责数据库连接、会话和初始化相关逻辑
├── api/
│   ├── router.py           # 汇总并注册所有业务路由
│   ├── errors.py           # 统一 API 异常与错误响应
│   └── routes/             # 各业务接口：管理、统计、地理、问答、记录、物种、系统
├── services/               # 业务逻辑层，承接路由与数据访问之间的处理
├── repositories/           # 数据访问层，封装 SQL 或查询逻辑
├── models/                 # SQLAlchemy ORM 模型定义
├── schemas/                # 请求/响应模式定义
├── domain/                 # 领域逻辑（问答、地理、物种数据）
│   ├── graph_chain.py      # 图谱问答/推理链路相关逻辑
│   ├── qa_cache.py         # 问答缓存，减少重复计算
│   ├── geo_data.py         # 地理或行政区划数据处理
│   └── species_data.py     # 物种数据整理、读取或映射
├── tools/                  # 数据迁移与导入脚本
│   ├── migrate_csv_to_db.py# 将 CSV 数据导入 SQLite
│   └── import_to_neo4j.py  # 将数据导入 Neo4j 图数据库
├── data/                   # 数据文件目录
├── runtime/                # 运行时产物目录
├── requirements.txt
└── .env.example
```

## 前端目录说明

```text
frontend/
├── index.html              # 首页 HTML 入口
├── basin-monitoring.html   # 流域监测项目页入口
├── knowledge-graph.html    # 知识图谱应用页入口
├── mobile-monitoring.html  # 移动端监测页入口
├── vite.config.js          # Vite 构建、入口页、别名和代理配置
├── package.json            # 前端依赖、脚本和项目元数据
├── public/                 # 静态资源（含 legacy 依赖脚本）
└── src/
	├── entries/            # 各 HTML 入口的挂载脚本
	├── legacy/             # 旧模板兼容壳组件
	├── features/           # 案例页功能组件
	├── shared/             # 共享模块（api/panel/composables/utils）
	├── api/                # 兼容层导出
	└── utils/              # 兼容层导出
```

当前 `entries` 与页面入口对应关系：

- `index.html` -> `src/entries/index.js`
- `basin-monitoring.html` -> `src/entries/basin-monitoring.js`
- `knowledge-graph.html` -> `src/entries/knowledge-graph.js`
- `mobile-monitoring.html` -> `src/entries/mobile-monitoring.js`

## 前端分层

- `frontend/src/entries/`：每个 HTML 页面对应一个入口脚本。
- `frontend/src/legacy/`：保留首页、隐私页、条款页这类旧模板壳，以及模板加载逻辑。
- `frontend/src/features/`：流域监测、知识图谱、移动端监测三个案例页的功能包装。
- `frontend/src/shared/`：真正可复用的模块，包含请求封装、地图工具、问答/上报/物种面板和 composables。
- `frontend/src/api/`、`frontend/src/utils/`：兼容旧导入路径的转发层，后续可逐步收敛。

## 后端分层

- `backend/api/`：路由汇总、错误处理、按业务拆分的端点。
- `backend/services/`：业务逻辑与跨仓储编排。
- `backend/repositories/`：数据库访问封装。
- `backend/models/`：SQLAlchemy 基类与 ORM 定义。
- `backend/schemas/`：Pydantic 请求/响应模式。


## scripts 目录说明

- `scripts/run_backend.*`：仅启动后端
- `scripts/run_frontend.*`：仅启动前端
- `scripts/start-neo4j.*`：启动 Neo4j
- `scripts/start.*`：常规一键启动
- `scripts/start-with-ngrok.*`：一键启动并建立 ngrok 隧道

- Windows 启动后端使用*.bat
- Linux/macOS 启动后端使用*.sh

## 维护常用命令

```bash
# Windows 一键启动
scripts\start.bat

# Windows 启动后端
scripts\run_backend.bat

# Windows 启动前端
scripts\run_frontend.bat

# Windows ngrok 启动
scripts\start-with-ngrok.bat
```

启动后常用地址：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 数据与初始化

- 主运行库：`backend/data/species.db`
- 原始导入数据：`backend/data/gbif_results/*.csv`
- 地理数据：`backend/data/geo/china_100000_full.json`
- 运行时说明：`backend/runtime/README.md`

从 CSV 重建本地数据时：

```bash
cd backend
python tools/migrate_csv_to_db.py
```

## 依赖与规范

- Python 环境以 `environment.yml` 为准，仓库内的 `requirements.txt` 主要用于后端 Python 依赖列举。
- 前端依赖以 `frontend/package.json` 为准。
- 推荐使用 `pre-commit` 保持 Python 和前端基础格式一致。

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 维护注意事项

- `frontend/public/js/*.js` 仍被 legacy 页面依赖，删除前请先确认引用。
- `backend/runtime/species.db` 属于本地运行时数据，不应手工编辑。
- 前端命令需在 `frontend/` 目录执行，例如 `npm run dev` 与 `npm run build`。
- 变更入口或构建配置后，至少执行一次前端构建验证：

## 验证标准

维护侧最基本的验证是：

1. 后端能启动并访问 `/docs`。
2. 前端能在 `5173` 正常打开。
3. `npm run build` 成功。
4. 需要公网时，`scripts\start-with-ngrok.bat` 能正常拉起前端隧道。

## 说明

- Neo4j 和部分 API Key 是可选能力，不可用时系统会降级。
- 这是研究和演示用途项目，不建议直接对外暴露生产入口。