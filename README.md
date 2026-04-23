# Trae AI Skills Collection

Trae AI 技能集合，为AI驱动的软件开发提供全面的技术规范和最佳实践。

## 📚 Skills 概览

本仓库包含5个核心开发技能，涵盖前端、后端、移动开发和架构设计等多个领域。

| Skill | 描述 | 适用场景 |
|-------|------|----------|
| `frontend-ui-design` | 前端UI设计规范 | Web应用界面开发、组件设计、样式规范 |
| `mobile-app-dev` | Uni-app移动开发 | 跨平台移动应用（iOS/Android/小程序） |
| `vibe-microservice-dev` | Spring Cloud微服务 | 大规模分布式系统、企业级应用 |
| `vibe-monolithic-dev` | Spring Boot单体 | 中小型项目、快速迭代、内部系统 |
| `vibe-python-dev` | Python后端开发 | Web API、数据处理、微服务 |

---

## 🚀 快速开始

### 1. Frontend UI Design - 前端UI设计规范

**技术栈**: Vue.js / React / Tailwind CSS / shadcn/ui

**核心能力**:
- 完整的设计系统（颜色、间距、字体、圆角、阴影）
- 现代化UI组件规范（按钮、表单、卡片、表格）
- 响应式布局与暗色模式支持
- 需求清单对接流程

**触发场景**:
- 创建新的前端页面或组件
- 开发表单、表格、列表、详情等业务页面
- 优化页面布局和视觉层次
- 前端代码审查和UI规范检查

**文件结构**:
```
frontend-ui-design/
└── SKILL.md  # 完整的设计规范文档
```

---

### 2. Mobile App Dev - Uni-app移动开发

**技术栈**: Uni-app / Vue.js / Vuex / SCSS

**核心能力**:
- 一套代码多端发布（iOS/Android/H5/小程序）
- 原生API调用（相机、定位、支付、推送）
- 移动端UI组件和手势交互
- 应用打包和发布上架

**触发场景**:
- 创建新的 Uni-app 移动应用项目
- 开发 App 页面或组件
- 对接移动端原生 API
- 应用签名打包和商店上架

**文件结构**:
```
mobile-app-dev/
└── SKILL.md  # 完整的移动开发规范文档
```

---

### 3. Microservice Dev - Spring Cloud微服务

**技术栈**: Spring Boot 3.2 / Spring Cloud Alibaba / Nacos / Seata / Sentinel / RocketMQ

**核心能力**:
- 微服务架构设计与服务治理
- 分布式事务处理（Seata AT模式）
- 服务注册发现与配置管理（Nacos）
- API网关路由与熔断限流（Sentinel）
- 完整十步开发流程

**触发场景**:
- 构建分布式微服务系统
- 应对高并发、高可用需求
- 多团队协作的大型项目
- 微服务代码优化和检查

**文件结构**:
```
vibe-microservice-dev/
├── SKILL.md                           # 主技能文档
└── knowledge/                          # 知识库
    ├── 01-microservice-architecture.md # 微服务架构设计
    ├── 02-nacos-config.md             # Nacos服务注册与配置
    ├── 03-gateway.md                  # 网关设计
    ├── 04-feign-sentinel.md            # 服务调用与熔断
    ├── 04-jetcache.md                 # JetCache三级缓存
    ├── 05-seata.md                    # 分布式事务
    ├── 06-mq.md                       # 消息队列
    ├── 07-tracing.md                  # 链路追踪
    └── 08-security.md                 # 微服务安全
```

---

### 4. Monolithic Dev - Spring Boot单体

**技术栈**: Spring Boot 3.2 / MyBatis-Plus / JetCache / Spring Security / JWT

**核心能力**:
- 模块化单体架构（空壳Server + 业务模块）
- 本地事务管理与缓存策略
- 限流与分布式锁
- Spring Security + JWT认证
- 十步开发流程

**触发场景**:
- 中小型项目（团队<10人）
- 快速迭代的创业项目
- 不需要微服务复杂度的业务系统
- 需要分布式部署的企业内部系统

**文件结构**:
```
vibe-monolithic-dev/
├── SKILL.md                           # 主技能文档
└── knowledge/                          # 知识库
    ├── 01-monolithic-architecture.md  # 单体架构设计
    ├── 02-module-design.md            # 模块化设计
    ├── 03-caching-strategy.md         # 缓存策略
    ├── 04-security.md                 # 安全认证
    └── 05-performance.md              # 性能优化
```

---

### 5. Python Dev - Python后端开发

**技术栈**: Python 3.11+ / FastAPI / SQLAlchemy / Redis / Celery

**核心能力**:
- 分层架构与领域驱动设计
- 异步API开发与性能优化
- Pydantic数据验证
- Repository模式与事务管理
- 八步开发流程

**触发场景**:
- Web API服务开发（FastAPI/Flask）
- 数据处理与分析系统
- 微服务架构项目
- Python代码优化和检查

**文件结构**:
```
vibe-python-dev/
├── SKILL.md                           # 主技能文档
└── knowledge/                          # 知识库
    ├── 01-project-architecture.md    # 项目架构设计
    ├── 02-code-standards.md          # 代码规范
    ├── 03-security.md               # 安全规范
    ├── 04-performance.md             # 性能优化
    └── 05-testing.md                 # 测试规范
```

---

## 📖 使用指南

### 在Trae AI中使用

当您与Trae AI对话时，根据您的开发任务，AI会自动选择合适的技能：

1. **明确指定**: 直接说明您需要的技能，如"使用vibe-microservice-dev开发用户服务"
2. **场景识别**: AI会根据您的需求描述自动匹配相关技能
3. **多技能组合**: 复杂项目可能需要多个技能配合使用

### 需求清单对接

所有技能都强调**需求清单对接**流程：

```
docs/工作空间/01-项目管理/[项目名]/01-需求/需求清单.md
```

关键步骤：
1. 读取并理解需求清单
2. 提取功能列表和API接口信息
3. 按照技能规范实现功能
4. 验证功能完整性

---

## 🏗️ 架构原则

### 单体 vs 微服务选择

| 因素 | 单体架构 | 微服务架构 |
|------|---------|-----------|
| 团队规模 | < 10人 | > 10人 |
| 项目复杂度 | 中低 | 高 |
| 迭代速度 | 快速 | 中等 |
| 扩展需求 | 垂直扩展 | 水平扩展 |
| 部署方式 | 单点部署 | 分布式部署 |

### 技术栈选择

| 需求 | 推荐技术 |
|------|---------|
| Web前端 | Vue.js + Tailwind CSS |
| 移动应用 | Uni-app (跨平台) |
| Java后端(大型) | Spring Cloud Alibaba |
| Java后端(中小型) | Spring Boot 模块化 |
| Python后端 | FastAPI / Flask |

---

## 📋 开发流程

### 十步法（Java生态）

```
Step 0: 读取需求清单
Step 1: 参数校验（JSR-303）
Step 2: 幂等校验 + 业务校验
Step 3: 数据操作（MyBatis-Plus）
Step 4: 缓存策略（JetCache）
Step 5: 服务调用（Feign）
Step 6: 限流熔断（Sentinel）
Step 7: 分布式事务（Seata）
Step 8: 消息队列/事件发布
Step 9: 结果封装
```

### 八步法（Python生态）

```
Step 0: 读取需求清单
Step 1: 参数校验（Pydantic）
Step 2: 业务规则校验
Step 3: 数据读写（Repository）
Step 4: 缓存策略
Step 5: 事务管理
Step 6: 事件发布
Step 7: 结果封装
Step 8: 异常处理
```

---

## 🔐 安全规范

所有技能都遵循统一的安全规范：

- **认证**: JWT Token / Spring Security
- **密码**: BCrypt加密存储
- **SQL注入**: 参数化查询
- **敏感数据**: 脱敏处理
- **传输**: HTTPS加密

---

## 📊 性能规范

- **数据库**: 分页查询、索引优化、禁止N+1、禁止SELECT *
- **缓存**: 热点数据缓存、防穿透、防击穿、防雪崩
- **并发**: 乐观锁、分布式锁、异步处理

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这些技能文档。

---

## 📄 License

MIT License - 自由使用、修改和分发
