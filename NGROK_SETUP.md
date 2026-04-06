# ngrok 使用指南

## 一、前置准备

### 1. 安装 ngrok
从 https://ngrok.com/download 下载并安装

或使用 npm 安装：
```
npm install -g ngrok
```

### 2. 创建 ngrok 账户并获取 authtoken
1. 访问 https://dashboard.ngrok.com/signup
2. 登录后获取 auth token
3. 运行命令添加 token：
   ```
   ngrok authtoken <你的-token>
   ```

## 二、启动服务

### 方案 A：使用现有的启动脚本（推荐）

**终端 1：启动 Neo4j**
```
.\start-neo4j.bat
```

**终端 2：启动 ngrok 隧道**
```
ngrok http 8000
```
- 记下输出的公网 URL，例如：`https://xxxx-xxxx.ngrok.io`
- 其他电脑通过这个 URL 访问你的应用

**终端 3：启动后端**
```
.\scripts\run_backend.bat
```

**终端 4：启动前端**
```
.\scripts\run_frontend.bat
```

### 方案 B：手动启动

**终端 1：启动后端**
```
cd backend
conda activate blueguard  # 或你的虚拟环境名
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**终端 2：启动 ngrok**
```
ngrok http 8000
```

**终端 3：启动前端**
```
cd frontend
npm install
npm run dev
```

## 三、访问应用

- **本地访问**：http://localhost:5173
- **公网访问**：`https://xxxx-xxxx.ngrok.io`（ngrok 输出的 URL）

## 四、常见问题

### Q1：其他电脑无法访问应用？
- ✓ 确保后端在 8000 端口运行
- ✓ 确保 ngrok 正常工作（显示 URL）
- ✓ 后端已启用 CORS（.env 已配置）
- ✓ 其他电脑使用正确的 ngrok URL

### Q2：前端调用 API 返回 CORS 错误？
- ✓ 检查 `.env` 中 ALLOW_ORIGINS 配置
- ✓ 重启后端服务
- ✓ 确保 ngrok URL 在允许列表中

### Q3：ngrok URL 经常变化？
- ✓ 这是免费版本的限制
- ✓ 升级到付费账户可以获得固定的自定义域名
- ✓ 每次重启 ngrok 时告知其他用户新的 URL

### Q4：如何只在本地测试？
- 不需要 ngrok，直接：
  - 后端：`uvicorn main:app --host 0.0.0.0 --port 8000`
  - 前端：`npm run dev`
  - 访问：http://localhost:5173

## 五、架构示意

```
┌─────────────────────────────────────┐
│    其他电脑（互联网上）              │
│  访问 https://xxxx-xxxx.ngrok.io    │
└────────────────┬────────────────────┘
                 │
                 │ https
        ┌────────▼─────────┐
        │   ngrok 隧道     │
        │（公网 → 本地）   │
        └────────┬─────────┘
                 │
        ┌────────▼─────────────────┐
        │   你的电脑 (localhost)   │
        │  ┌─────────────────────┐ │
        │  │ 前端 :5173         │ │
        │  │ 后端 :8000  ◄──────┼─┼─── API 调用
        │  │ Neo4j :7687        │ │
        │  └─────────────────────┘ │
        └──────────────────────────┘
```

## 六、故障排查

1. **ngrok 显示 "command not found"**
   - 确保已安装并添加到 PATH
   - 重启终端或 VS Code

2. **后端启动时显示 8000 端口已被占用**
   ```
   # Windows：查找占用端口 8000 的进程
   netstat -ano | findstr :8000
   # 然后关闭对应的进程
   taskkill /PID <PID> /F
   ```

3. **前端访问时 API 报错**
   - 查看浏览器控制台错误信息
   - 检查 .env CORS 配置
   - 确保后端确实在运行：http://localhost:8000/
