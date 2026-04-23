---
name: "devops-deploy"
description: "DevOps deployment skill for all projects. Invoke when deploying to server, updating code, or managing production environment. Git-based deployment: commit → push → auto deploy."
---

# DevOps 部署技能

统一的运维部署管理技能，支持 Git 自动化部署，适用于所有项目的部署、更新、回滚操作。

## 核心原则

### 1. Git 优先原则

**所有部署操作必须通过 Git 进行：**

```
本地代码 → Git 提交 → Git 推送 → 服务器自动拉取 → 构建 → 部署
```

**禁止直接上传文件到服务器！**

### 2. 脚本优先原则

操作服务器前，必须先检查本地是否有对应的部署脚本：
- 检查目录：`deploy/scripts/`
- 优先使用现有脚本
- 如无脚本，先创建脚本再执行

### 3. 可回滚原则

每次部署前必须：
- 备份当前版本
- 记录版本号
- 确保可以快速回滚

---

## Git 自动部署流程

### 架构图

```
┌─────────────┐     Git Push      ┌─────────────┐
│   本地开发   │ ───────────────→ │  Git 仓库   │
└─────────────┘                   └──────┬──────┘
                                         │
                                         │ Webhook / CI
                                         ▼
┌─────────────┐     拉取代码      ┌─────────────┐
│  生产环境   │ ←─────────────── │  服务器     │
└─────────────┘                   └──────┬──────┘
                                         │
                                         │ 构建
                                         ▼
                                  ┌─────────────┐
                                  │  部署验证   │
                                  └─────────────┘
```

### 部署命令

**Windows (PowerShell):**
```powershell
cd deploy/scripts

# 完整部署
.\git-deploy.ps1 all "提交信息"

# 仅部署前端
.\git-deploy.ps1 frontend "更新首页"

# 仅部署管理平台
.\git-deploy.ps1 admin "修复登录"

# 仅部署后端
.\git-deploy.ps1 backend "新增API"

# 查看状态
.\git-deploy.ps1 status

# 查看日志
.\git-deploy.ps1 logs

# 回滚
.\git-deploy.ps1 rollback 20260308
```

**Linux/Mac (Bash):**
```bash
cd deploy/scripts

# 完整部署
./git-deploy.sh all "提交信息"

# 仅部署前端
./git-deploy.sh frontend "更新首页"

# 查看状态
./git-deploy.sh status

# 回滚
./git-deploy.sh rollback 20260308
```

---

## 部署流程详解

### Phase 1: 本地 Git 操作

```bash
# 1. 检查 Git 状态
git status

# 2. 提交更改
git add -A
git commit -m "feat: 新功能描述"

# 3. 推送到远程
git push origin main
```

### Phase 2: 服务器自动部署

```bash
# 服务器自动执行：
# 1. 备份当前版本
# 2. 拉取最新代码
# 3. 构建前端 (npm run build)
# 4. 构建管理平台 (npx vite build)
# 5. 构建后端 (mvn package)
# 6. 部署到生产目录
# 7. 重启服务
# 8. 健康检查
```

### Phase 3: 验证

```bash
# 1. 检查官网
curl -s https://wubianj.com/

# 2. 检查管理平台
curl -s https://wubianj.com/admin/

# 3. 检查 API
curl -s https://wubianj.com/api/health
```

---

## 脚本说明

### 本地脚本

| 脚本 | 用途 |
|------|------|
| `git-deploy.sh` | Git 自动部署（Linux/Mac） |
| `git-deploy.ps1` | Git 自动部署（Windows） |
| `deploy.sh` | 传统部署（本地构建→上传） |
| `rollback.sh` | 回滚脚本 |

### 服务器脚本

| 脚本 | 用途 |
|------|------|
| `server-deploy.sh` | 服务器端部署脚本 |

---

## GitHub Actions CI/CD

### 配置文件

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
      - master
  workflow_dispatch:
    inputs:
      deploy_type:
        type: choice
        options:
          - all
          - frontend
          - admin
          - backend

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/enterprise-repo
            git pull
            ./deploy/scripts/server-deploy.sh all
```

### Secrets 配置

在 GitHub 仓库设置中添加：

| Secret | 说明 |
|--------|------|
| `SERVER_HOST` | 服务器地址 |
| `SERVER_PORT` | SSH 端口 |
| `SERVER_USER` | SSH 用户名 |
| `SSH_PRIVATE_KEY` | SSH 私钥 |

---

## 服务器初始化

### 1. 克隆代码仓库

```bash
# 在服务器上执行
cd /opt
git clone <git-repo-url> enterprise-repo
```

### 2. 创建生产目录

```bash
mkdir -p /opt/enterprise/{frontend/dist,admin/dist,backend,nginx,ssl,backup}
```

### 3. 配置 Docker

```bash
cd /opt/enterprise
docker compose up -d
```

---

## 部署检查清单

### 部署前检查

- [ ] 本地代码已提交到 Git
- [ ] 本地测试通过
- [ ] 部署脚本存在
- [ ] Git 远程仓库可访问
- [ ] 服务器连接正常

### 部署后检查

- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 日志无错误
- [ ] 核心功能可用

---

## 回滚操作

### 查看可用备份

```bash
./git-deploy.ps1 rollback
```

### 回滚到指定版本

```bash
./git-deploy.ps1 rollback 20260308120000
```

---

## 常见问题

### 1. Git 推送失败

```bash
# 检查远程仓库配置
git remote -v

# 重新设置远程仓库
git remote set-url origin <git-repo-url>
```

### 2. 服务器拉取失败

```bash
# 检查服务器 Git 配置
ssh user@server "cd /opt/enterprise-repo && git status"

# 手动拉取
ssh user@server "cd /opt/enterprise-repo && git pull origin main"
```

### 3. 构建失败

```bash
# 检查服务器日志
./git-deploy.ps1 logs

# 手动构建
ssh user@server "cd /opt/enterprise-repo && ./deploy/scripts/server-deploy.sh build"
```

---

## 项目目录结构

```
project/
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions CI/CD
├── deploy/
│   ├── scripts/
│   │   ├── git-deploy.sh    # Git 自动部署
│   │   ├── git-deploy.ps1   # Git 自动部署
│   │   ├── server-deploy.sh # 服务器部署
│   │   ├── deploy.sh        # 传统部署
│   │   └── rollback.sh      # 回滚
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── enterprise.conf
│   └── docker-compose.yml
├── frontend/                # 前端代码
├── admin/                   # 管理平台代码
├── backend/                 # 后端代码
└── .gitignore
```

---

## 注意事项

1. **所有代码变更必须通过 Git 提交**
2. **禁止直接上传文件到服务器**
3. **每次部署前自动备份**
4. **保留最近 10 个备份版本**
5. **敏感信息使用环境变量或 .env 文件**
6. **SSL 证书不要提交到 Git**
