# NgRok 快速启动指南

## 3 个关键步骤：

### 1️⃣ 安装 ngrok
```bash
# 从官网下载：https://ngrok.com/download
# 或使用 npm
npm install -g ngrok

# 首次使用需要登录，访问 https://dashboard.ngrok.com 获取 token
ngrok authtoken <你的-token>
```

### 2️⃣ 启动服务（需要 4 个终端）

**方式 A：使用一键启动脚本** ⭐ 推荐
```bash
# 项目根目录
start-with-ngrok.bat
```
此脚本会自动在 4 个终端中启动：后端、ngrok、前端、信息窗口

**方式 B：手动启动**
```bash
# 终端 1：后端
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# 终端 2：ngrok 隧道（暴露前端 5173 端口）
ngrok http 5173

# 终端 3：前端
cd frontend
npm run dev
```

### 3️⃣ 获取公网 URL
查看 ngrok 终端窗口的输出，会显示：
```
Forwarding   https://xxxx-xxxx-xxxx.ngrok-free.dev → http://localhost:5173
```
**这个 URL 就是其他电脑看到你网页的地址** — 在浏览器中打开即可看到前端界面

---

## 📋 检查清单

在启动前确保：
- [ ] **Neo4j 正在运行**（运行 `start-neo4j.bat` 或手动启动 Neo4j）
- [ ] **已安装 ngrok**（运行 `ngrok --version` 检查）
- [ ] **已登录 ngrok**（运行过 `ngrok authtoken <token>`）
- [ ] **已有前端依赖**（运行过 `cd frontend && npm install`）
- [ ] **`.env` 文件已创建**（项目根目录应该有 `.env` 文件）
- [ ] **Vite 已配置 allowedHosts**（`frontend/vite.config.js` 已包含 ngrok 域名）✅

---

## 🌐 访问方式

| 用途 | 地址 |
|-----|------|
| **本地访问** | `http://localhost:5173` |
| **公网访问** | `https://xxxx-xxxx-xxxx.ngrok.io`（来自 ngrok 输出） |
| **后端 API** | ngrok URL 会自动转发到 `http://localhost:8000` |

---

## ⚠️ 常见问题

### 😕 "ngrok: command not found"
**解决方案：**
- 确保已从 https://ngrok.com/download 下载并安装 ngrok
- Windows 用户：将 ngrok 添加到 PATH 环境变量
- 重启终端或 VS Code

### 😕 "Error: invalid authtoken"  
**解决方案：**
- 访问 https://dashboard.ngrok.com 登录你的账户
- 复制 auth token
- 运行 `ngrok authtoken <你的-token>`

### 😕 "Port 8000 already in use"
**解决方案：**
```bash
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000
# 关闭该进程（将 PID 替换为实际的进程号）
taskkill /PID <PID> /F
```

### 😕 "Blocked request. This host is not allowed"
**解决方案：**
- 这是 Vite 的安全限制
- ✅ 已自动修复：`frontend/vite.config.js` 已配置 `allowedHosts: ['.ngrok-free.dev', '.ngrok.io']`
- 重启前端服务（Ctrl+C 后重新 `npm run dev`）
- 清除浏览器缓存，刷新页面

### 😕 其他电脑无法访问
**检查项：**
- ✅ 后端确实在 8000 端口运行（访问 `http://localhost:8000/` 应该看到响应）
- ✅ ngrok 正在运行且显示了公网 URL
- ✅ 使用正确的 ngrok URL，不是 localhost 地址
- ✅ 网络不被防火墙或代理阻止

---

## 🎯 工作原理

```
┌───────────────────────────────────────┐
│    其他电脑通过浏览器访问网页          │
│  https://xxxx-xxxx-xxxx.ngrok-free.dev│
└────────────────┬──────────────────────┘
                 │ 公网 HTTPS
        ┌────────▼──────────┐
        │   ngrok 隧道      │
        │  (公网 ↔ 本地)    │
        └────────┬──────────┘
                 │ localhost:5173
        ┌────────▼─────────────────┐
        │     你的电脑              │
        │  ┌─────────────────────┐  │
        │  │ 🌐 前端 :5173      │◄─┼─ 其他电脑看到这个网页
        │  │     ↓ /api调用     │  │
        │  │ 🔌 后端 :8000      │  │
        │  │     ↓ 数据库查询    │  │
        │  │ 📊 Neo4j :7687     │  │
        │  └─────────────────────┘  │
        └──────────────────────────┘
```

**流程：**
1. 其他电脑访问 ngrok URL → 看到你的前端网页
2. 前端页面加载 → JavaScript代码运行
3. 前端调用 `/api` → Vite 开发服务器代理到 `:8000`
4. 后端返回数据 → 前端显示结果

---

## 💡 高级技巧

### 保持 ngrok URL 不变（付费功能）
1. 升级到 ngrok 付费账户
2. 在 Dashboard 中创建 Reserved Domain（例如 `my-app.ngrok.io`）
3. 启动时指定：`ngrok http 8000 --domain my-app.ngrok.io`
4. `.env` 中配置 URL：`ALLOW_ORIGINS=["http://localhost:5173", "https://my-app.ngrok.io"]`

### 监控 ngrok 流量
访问 ngrok 的本地监控界面：`http://127.0.0.1:4040`

### 调试后端 CORS
在浏览器开发者工具中，查看：
1. Network 标签 → 请求头中的 Origin
2. 响应头中的 Access-Control-Allow-Origin
3. 确保两者匹配

---

## 📞 需要帮助？

- 官方文档：https://ngrok.com/docs/getting-started/
- FastAPI CORS：https://fastapi.tiangolo.com/tutorial/cors/
- VS Code 终端：查看 Project 文件夹中各个终端窗口的输出
