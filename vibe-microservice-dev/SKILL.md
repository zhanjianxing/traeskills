---
name: "vibe-microservice-dev"
description: "专业微服务后端开发。用于创建Spring Cloud Alibaba微服务架构项目，微服务后端功能完善、代码优化、代码检查也使用此技能。包含服务注册发现、配置中心、网关、熔断限流、分布式事务、链路追踪等完整微服务治理能力。Invoke when user wants to build a microservice architecture project, improve existing microservices, or perform code review."
---

# 专业微服务后端开发

基于Spring Cloud Alibaba的微服务架构，适用于大规模企业级分布式系统。

## 适用场景

- 构建分布式微服务系统
- 应对高并发、高可用需求
- 多团队协作的大型项目
- 需要服务治理的复杂业务
- **微服务后端功能完善**
- **微服务代码优化重构**
- **微服务代码质量检查**

## 使用场景说明

### 场景1：新项目开发
当用户需要创建一个新的Spring Cloud Alibaba微服务项目时使用。

### 场景2：功能完善
当用户需要为现有微服务添加新功能、修复Bug、完善业务逻辑时使用。遵循十步开发流程，确保代码质量。

### 场景3：代码优化
当用户需要对现有微服务进行性能优化、代码重构、规范整改时使用。检查并应用性能规范和安全规范。

### 场景4：代码检查
当用户需要对微服务代码进行质量检查、漏洞扫描、规范验证时使用。对照开发规范进行检查并给出改进建议。

# 微服务开发规范

## 一、技术栈

- **Spring Boot**: 3.2.x
- **Spring Cloud**: 2023.0.x (Northfields)
- **Spring Cloud Alibaba**: 2023.0.x
- **Java**: 17+
- **Nacos 2.x
- **OpenFeign + LoadBalancer
- **Sentinel 1.8.x
- **Seata 1.7.x
- **Spring Cloud Gateway
- **MySQL 8.0 + MyBatis-Plus 3.5.x
- **JetCache 2.7.x (阿里开源) + Redis 7.x
- **RocketMQ 5.x
- **OpenTelemetry + Grafana Stack
- **Spring Security 6.x + JWT
- **MapStruct 或 Hutool

---

## 二、框架约束必须遵守

### 缓存
使用 JetCache 注解 `@Cached`、`@CacheInvalidate`、`@CacheLock`

### 限流
使用 Sentinel 注解或配置

### 分布式锁
使用 JetCache `@CacheLock`

### 服务调用
使用 OpenFeign，Feign接口必须定义在 common-feign 公共模块中

### 分布式事务
使用 Seata AT 模式

### 对象转换
使用 MapStruct 或 Hutool

### ORM
使用 MyBatis-Plus

### 认证
使用 Spring Security + JWT

---

## 三、十步开发流程（核心约束），必须强制实现！！！

### Step0: 读取需求清单（Requirement Analysis）- **必须执行**

#### 0.1 需求清单路径
```
docs/工作空间/01-项目管理/[项目名]/01-需求/需求清单.md
```

#### 0.2 读取步骤
1. **定位项目根目录**：从当前工作目录向上查找 `docs/工作空间/01-项目管理/`
2. **查找需求清单**：在 `[项目名]/01-需求/` 目录下找到 `需求清单.md`
3. **解析需求清单内容**：
   - 提取功能列表（按模块/子模块）
   - 提取API接口信息（路径、方法、参数、响应）
   - 提取非功能需求（性能、安全要求）

#### 0.3 从需求清单提取的关键信息

| 信息类型 | 提取内容 | 用途 |
|----------|----------|------|
| 功能ID | 如 U001、P001 | Controller/Service 命名参考 |
| 功能名称 | 如 用户登录、商品列表 | 方法名、注释 |
| 功能描述 | 详细业务描述 | 理解业务逻辑 |
| API接口 | /api/v1/xxx | @RequestMapping 路径 |
| HTTP方法 | GET/POST/PUT/DELETE | @GetMapping 等注解 |
| 优先级 | 核心/重要/辅助 | 决定开发顺序 |
| 非功能需求 | 性能/安全/兼容性要求 | 技术选型和优化 |

#### 0.4 API接口实现约束

- **URL必须与需求清单一致**：`url严格按照需求清单中的API设计进行实现`
- **HTTP方法必须与需求清单一致**：GET查询、POST创建、PUT更新、DELETE删除
- **请求参数必须与需求清单一致**：DTO字段与需求清单匹配
- **响应结构必须与需求清单一致**：VO字段与需求清单匹配

#### 0.5 开发前检查清单

- [ ] 已读取并理解当前项目的需求清单
- [ ] 所有API接口均按照需求清单中的路径实现
- [ ] HTTP方法与需求清单一致
- [ ] 请求参数DTO与需求清单中的API定义匹配
- [ ] 响应VO与需求清单中的接口规范一致
- [ ] 功能完整覆盖需求清单中的核心功能
- [ ] 功能完整覆盖需求清单中的重要功能

### Step1: 参数校验（Validation）
JSR-303 注解验证，分组校验 Create/Update 组，校验失败抛 ValidationException

### Step2: 幂等校验+业务校验（Business Rules）
查询是否存在重复提交，基于唯一标识（如业务ID+用户ID）判断
校验业务状态、业务权限、业务约束，失败抛出 BusinessException

### Step3: 数据操作（Data Operations）
MyBatis-Plus BaseMapper 执行 CRUD，查询必须指定字段，**禁止 SELECT ***，**禁止 N+1 查询**，批量操作用 saveBatch/updateBatch

### Step4: 缓存策略（JetCache）
- 查询前：@Cached 注解缓存
- 写入后：@CacheInvalidate 删除缓存
- 分布式锁：@CacheLock
- 防穿透：空值缓存
- 防击穿：@CacheLock 分布式锁
- 短效数据：Redis SET 并设置过期时间

### Step5: 服务调用（OpenFeign）
- 调用方：注入 Feign 接口（接口定义在 common-feign 模块）
- 被调方：无需额外开发，自动暴露 REST API

### Step6: 限流熔断（Sentinel）
- 核心接口：@SentinelResource 注解
- 配置 blockHandler、fallback 方法

### Step7: 分布式事务（Seata）
- 跨服务事务：@GlobalTransactional 注解
- 指定超时时间和事务名

### Step8: 消息队列（RocketMQ）或 事件发布（ApplicationEventPublisher）
二选一使用：

- 消息队列（RocketMQ）：跨系统/跨服务异步通信，rocketMQTemplate.asyncSend生产，@RocketMQMessageListener消费，幂等用Redis setIfAbsent

- 事件发布（ApplicationEventPublisher）：单体/模块内事件驱动，@Async异步处理，事件在事务提交后执行

### Step9: 结果封装
- Service 层：返回业务对象（VO/DTO）
- Controller 层：Result<T> 包装
- 记录操作日志


---

> **无侵入补充**：Nacos（注册/配置）、Gateway（路由）、OpenTelemetry（埋点）后期配置即可

---

## 四、代码规范

### Controller 层
- 返回类型必须是 Result<T>
- 入参必须是 DTO 对象
- 分页使用 PageQuery 子类和 PageResult

### 实体类
- 继承 BaseEntity
- 使用 @TableLogic 逻辑删除
- 使用 @Version 乐观锁

---

## 五、安全规范

### 密码存储
使用 BCrypt 加密

### 认证机制
JWT 令牌，2小时过期，支持双 Token

### 敏感数据
手机号、身份证号脱敏处理

### SQL 注入
使用 #{} 参数化查询

### 传输安全
生产环境使用 HTTPS

---

## 六、性能规范

### 数据库
- 列表查询必须分页
- 查询条件必须有索引
- 禁止 N+1 查询
- 禁止 SELECT *

### 缓存
- 热点数据**必须**缓存
- 防止缓存穿透：空值缓存
- 防止缓存击穿：分布式锁
- 设置合理过期时间

### 并发
- 乐观锁处理并发更新
- 分布式锁处理跨服务并发

---

## 七、微服务规范

### Feign 调用
使用 @FeignClient 声明服务调用，所有 Feign 接口必须定义在 `common-feign` 公共模块中

### Sentinel 熔断
使用 @SentinelResource 注解

### Seata 事务
使用 @GlobalTransactional 注解

### Gateway 路由
使用 lb:// 服务名进行负载均衡

---

## 八、全局异常

- BusinessException：业务异常
- MethodArgumentNotValidException：参数校验失败
- Exception：未知异常返回 500

---

## 九、枚举规范

禁止魔法数字，枚举必须包含 code 和 desc

---

## 十、消息队列

### 生产
使用 rocketMQTemplate.asyncSend

### 消费
使用 @RocketMQMessageListener 注解

### 幂等
使用 Redis 保证幂等

---

## 十一、项目结构

```
project/
├── pom.xml
├── common/
│   ├── common-core
│   ├── common-redis
│   ├── common-security
│   ├── common-web
│   └── common-feign/Feign 公共模块
├── gateway/网关服务，负责路由、限流、认证、负载均衡
├── auth/认证服务，负责用户登录、JWT 令牌颁发与验证
├── admin/
└── xxx-service/
```


## 知识库

- [01-microservice-architecture.md](knowledge/01-microservice-architecture.md) - 微服务架构设计
- [02-nacos-config.md](knowledge/02-nacos-config.md) - Nacos服务注册与配置
- [03-gateway.md](knowledge/03-gateway.md) - 网关设计
- [04-jetcache.md](knowledge/04-jetcache.md) - JetCache三级缓存（推荐）
- [04-feign-sentinel.md](knowledge/04-feign-sentinel.md) - 服务调用与熔断
- [05-seata.md](knowledge/05-seata.md) - 分布式事务
- [06-mq.md](knowledge/06-mq.md) - 消息队列
- [07-tracing.md](knowledge/07-tracing.md) - 链路追踪
- [08-security.md](knowledge/08-security.md) - 微服务安全
