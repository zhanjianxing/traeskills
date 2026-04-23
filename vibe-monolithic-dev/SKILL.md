---
name: "vibe-monolithic-dev"
description: "后端开发。用于创建Spring Boot模块化单体架构项目，后端功能完善、代码优化、代码检查也使用此技能。空壳Server+业务模块化设计，支持分布式部署。Invoke when user wants to build a Spring Boot  project, improve existing  codebase, or perform code review."
---

# 单体架构后端开发

基于Spring Boot的模块化单体架构，适用于中小型项目、内部系统、SaaS平台。

## 适用场景

- 中小型项目（团队<10人）
- 快速迭代的创业项目
- 不需要微服务复杂度的业务系统
- 初期业务不确定，后期可能拆分为微服务的项目
- 需要分布式部署的企业内部系统
- **后端功能完善**
- **代码优化重构**
- **代码质量检查**

## 使用场景说明

### 场景1：新项目开发
当用户需要创建一个新的Spring Boot项目时使用。

### 场景2：功能完善
当用户需要为现有项目添加新功能、修复Bug、完善业务逻辑时使用。遵循十步开发流程，确保代码质量。

### 场景3：代码优化
当用户需要对现有项目进行性能优化、代码重构、规范整改时使用。检查并应用性能规范和安全规范。

### 场景4：代码检查
当用户需要对代码进行质量检查、漏洞扫描、规范验证时使用。对照开发规范进行检查并给出改进建议。

---

## 一、技术栈

Spring Boot 3.2.x | Java 17+ | MyBatis-Plus 3.5.x | JetCache 2.7.x | Spring Security 6.x + JWT | Bucket4j/RateLimiter | Lombok | MapStruct/Hutool | OpenTelemetry + Grafana Stack

---

## 二、架构核心理念：空壳Server + 业务模块化

### 空壳Server
负责应用启动、配置管理、模块装配，不包含具体业务逻辑，是唯一的部署单元。

### 业务模块
按业务领域划分（如 system, order, product），封装具体的业务能力，以依赖方式存在。

### 模块化设计原则
领域驱动边界划分 | 强制隔离依赖规则 | 单向依赖禁止循环 | 单一部署打包JAR

---

## 三、框架约束

缓存：JetCache @Cached/@CacheInvalidate/@CacheLock | 限流：Bucket4j/RateLimiter | 分布式锁：JetCache @CacheLock | ORM：MyBatis-Plus | 认证：Spring Security + JWT | 事件驱动：ApplicationEventPublisher

---

## 四、开发流程（十步法，核心约束，强制执行）

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

### Step 1: 参数校验
JSR-303注解，分组Create/Update，校验失败抛ValidationException

### Step 2: 幂等校验+业务校验
查询是否存在重复提交，基于唯一标识（如业务ID+用户ID）判断，存在则抛BusinessException
状态校验、权限校验、业务约束校验，失败抛出BusinessException

### Step 3: 数据操作
BaseMapper CRUD，禁SELECT *，禁N+1查询，批量操作用saveBatch/updateBatch，指定查询字段

### Step 4: 缓存策略
查询前@Cached缓存，写入后@CacheInvalidate删除，热数据缓存，防穿透空值缓存，防击穿@CacheLock锁

### Step 5: 事务管理
@Transactional指定传播行为和超时范围，仅包含必要的数据操作，缓存和事件发布在事务外

### Step 6: 消息队列（RocketMQ）或 事件发布（ApplicationEventPublisher）
二选一使用：

- 消息队列（RocketMQ）：跨系统/跨服务异步通信，rocketMQTemplate.asyncSend生产，@RocketMQMessageListener消费，幂等用Redis setIfAbsent

- 事件发布（ApplicationEventPublisher）：单体/模块内事件驱动，@Async异步处理，事件在事务提交后执行

### Step 7: 结果封装
Service层返回VO/DTO，Controller层包装Result<T>，记录操作日志

### Step 8: 异常处理
业务异常抛BusinessException，校验异常抛ValidationException，其他异常统一处理

### Step 9: 索引检查    
确认查询条件有对应索引，确认关联查询使用索引，避免全表扫描

---

## 五、与微服务区别

### 调用方式
单体：同一JVM内方法调用（本地事务） | 微服务：HTTP/RPC跨进程调用（分布式事务）

### 事务范围
单体：本地事务，一个数据库连接 | 微服务：分布式事务，跨服务/跨数据库

### 为什么单体不需要分布式事务
每个实例独立处理请求，所有数据库操作在同一个数据库连接中，@Transactional即可保证原子性

### 什么时候单体也需要分布式事务
多数据源（MySQL+Oracle）、读写分离强制主从库、未来拆分预留Seata接口

---

## 六、代码规范

### Controller层
返回类型必须是Result<T> | 入参必须是DTO对象 | 分页用PageQuery+PageResult | 不包含业务逻辑

### Service层
使用接口+实现类 | 方法以业务命名 | @Transactional事务 | 抛BusinessException

### Repository层
继承BaseMapper<T> | 使用MyBatis-Plus注解 | 禁止直接对外暴露

### 实体类
继承BaseEntity | @TableName/@TableId/@TableField | @TableLogic逻辑删除 | @Version乐观锁

---

## 七、安全规范

### 认证授权
Spring Security + JWT | Token有效期2小时 | 支持刷新Token | @PreAuthorize权限控制

### 敏感数据
密码BCrypt加密 | 手机号身份证脱敏 | 日志禁输出敏感信息

### SQL注入
禁${}拼接SQL | 必须#{}参数化查询

---

## 八、性能规范

### 数据库
列表分页 | 查询索引 | 禁N+1查询 | 禁SELECT * | 批量saveBatch/updateBatch

### 缓存
热点@Cached缓存 | 防穿透空值缓存 | 防击穿@CacheLock锁 | 防雪崩随机过期 | CacheType.BOTH

### 并发
@Version乐观锁 | @CacheLock分布式锁 | @Async异步处理

---

## 九、全局异常

BusinessException：业务异常 | ValidationException：校验失败 | Exception：系统异常返回500

---

## 十、枚举规范

禁止魔法数字，枚举必须包含code和desc

---

## 十一、项目结构

```
project/
├── pom.xml
├── server/                          # 空壳Server（启动入口）
│   ├── src/main/java/...Application.java
│   └── src/main/resources/
│       ├── application.yml
│       └── bootstrap.yml
├── common/                          # 公共模块
│   ├── common-core/                 # 核心公共（常量、异常、工具）
│   ├── common-redis/                # Redis配置
│   ├── common-security/             # 安全模块
│   └── common-web/                  # Web配置（拦截器、参数解析）
└── modules/                         # 业务模块
    ├── module-system/               # 系统模块
    ├── module-admin/                # 后台管理模块
    ├── module-user/                # 用户模块
    └── module-xxx/                  # 其他业务模块
```

### 模块内部结构

```
module-xxx/
├── src/main/java/com/xxx/xxx/
│   ├── controller/
│   │   └── XxxController.java
│   ├── service/
│   │   ├── XxxService.java
│   │   └── impl/
│   │       └── XxxServiceImpl.java
│   ├── repository/
│   │   ├── XxxMapper.java
│   │   └── entity/
│   │       └── Xxx.java
│   ├── dto/
│   │   ├── XxxCreateDTO.java
│   │   ├── XxxUpdateDTO.java
│   │   └── XxxQueryDTO.java
│   ├── vo/
│   │   └── XxxVO.java
│   ├── enums/
│   │   └── XxxStatus.java
│   ├── convert/
│   │   └── XxxConvert.java
│   └── event/
│       └── XxxEvent.java
└── src/main/resources/
    ├── mapper/
    │   └── XxxMapper.xml
    └── module-xxx.sql
```

---

## 十二、模块间通信

禁止直接@Autowired注入其他模块Service | 事件驱动：ApplicationEventPublisher发布+@EventListener监听 | 同步调用：Facade接口

---

## 十三、分布式部署

负载均衡：Nginx/云SLB | Session共享：Redis | 缓存一致性：Redis发布订阅 | 定时任务：XXL-Job分布式任务

---

## 十四、配置管理

多环境：application-{profile}.yml | 优先级：命令行>{profile}>application>默认

---

## 十五、日志监控

OpenTelemetry链路追踪 | Grafana指标可视化 | 告警规则配置 | 日志聚合分析

---

## 十六、测试规范

单元测试：JUnit 5+Mockito，覆盖率>70% | 集成测试：@SpringBootTest+H2数据库

---

## 十七、CI/CD

构建：mvn clean package | 镜像：多阶段构建+非root | 部署：Docker/K8s+健康检查+优雅停机

---

## 知识库

- 01-monolithic-architecture.md - 单体架构设计
- 02-module-design.md - 模块化设计
- 03-caching-strategy.md - 缓存策略
- 04-security.md - 安全认证
- 05-performance.md - 性能优化
