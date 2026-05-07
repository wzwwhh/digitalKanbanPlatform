# 🚀 快速部署指南（最终版）

## ✅ 已完成的功能

1. **后端添加 /kanban 前缀** - 后端 API 路径为 `/kanban/api/*`
2. **数据存储到数据库** - 使用 SQLite 存储项目/看板/数据源
3. **MySQL 表探测修复** - 支持自定义数据库连接

## 📦 部署步骤

### 方法一：使用打包脚本（推荐）

**Windows 本地：**
```powershell
.\build-and-pack.ps1
```

这会生成 `kanban-deploy.tar.gz` 文件。

**上传到服务器：**
```bash
scp kanban-deploy.tar.gz user@10.156.195.35:/data/run/
```

**服务器部署：**
```bash
ssh user@10.156.195.35
cd /data/run
tar -xzf kanban-deploy.tar.gz
chmod +x deploy-simple.sh stop-service.sh
./deploy-simple.sh
```

### 方法二：手动部署

**1. 本地构建前端：**
```bash
cd frontend
npm install
npm run build
```

**2. 打包上传：**
```bash
# 打包整个项目
tar -czf kanban.tar.gz backend/ frontend/dist/ deploy-simple.sh stop-service.sh nginx.conf.example

# 上传
scp kanban.tar.gz user@10.156.195.35:/data/run/digitalKanbanPlatform/
```

**3. 服务器启动：**
```bash
cd /data/run/digitalKanbanPlatform
tar -xzf kanban.tar.gz

# 启动后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

## 🔧 Nginx 配置

编辑 nginx 配置文件，添加：

```nginx
server {
    listen 5175;
    server_name localhost;

    # 前端静态文件
    location /kanban/ {
        alias /data/run/digitalKanbanPlatform/frontend/dist/;
        try_files $uri $uri/ /kanban/index.html;
    }

    # 后端 API（注意：后端现在有 /kanban 前缀）
    location /kanban/api/ {
        proxy_pass http://127.0.0.1:8000/kanban/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

重启 nginx：
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## ✅ 验证部署

```bash
# 1. 测试后端
curl http://localhost:8000/kanban/api/health
# 应返回: {"status":"ok","version":"0.1.0"}

# 2. 测试项目 API
curl http://localhost:8000/kanban/api/projects/
# 应返回: []

# 3. 访问前端
# 浏览器打开: http://10.156.195.35:5175/kanban/
```

## 🎯 测试功能

### 1. MySQL 表探测
1. 进入"数据源管理"
2. 点击"数据库"标签
3. 选择"MySQL"
4. 填写连接信息：
   - 主机：10.156.195.35
   - 端口：3306
   - 用户名：root
   - 密码：你的密码
   - 数据库：kanban_test
5. 点击"测试连接" ✅
6. 选择表 `sales_copy1`
7. 点击"探测" ✅

### 2. 数据持久化
- 创建的项目会保存到 `backend/projects.db`
- 不再依赖浏览器 localStorage
- 多用户可以共享数据

## 📝 重要说明

### 后端配置
- 后端默认使用 `/kanban` 前缀
- 如需修改，设置环境变量：`export API_PREFIX=/your-prefix`

### 前端配置
- 生产环境自动使用 API 模式（数据存数据库）
- 开发环境使用 localStorage 模式

### 数据库
- 项目数据存储在：`backend/projects.db`
- 定期备份此文件

## 🛠️ 管理命令

```bash
# 查看后端日志
tail -f data/backend.log

# 停止服务
./stop-service.sh

# 重启服务
./stop-service.sh && ./deploy-simple.sh

# 查看后端进程
ps aux | grep uvicorn

# 查看数据库
sqlite3 backend/projects.db "SELECT * FROM projects;"
```

## ❓ 常见问题

### API 返回 HTML？
- 检查后端是否启动：`curl http://localhost:8000/kanban/api/health`
- 检查 nginx 配置：`proxy_pass http://127.0.0.1:8000/kanban/api/`

### MySQL 探测失败？
- 检查数据库连接信息
- 确保表名正确
- 查看后端日志：`tail -f data/backend.log`

### 前端 404？
- 检查 nginx 配置中的 `try_files`
- 确认前端文件路径正确

## 🎉 完成！

现在你的系统：
- ✅ 后端有 `/kanban` 前缀
- ✅ 数据存储到数据库
- ✅ MySQL 表探测正常工作
- ✅ API 探测正常工作
