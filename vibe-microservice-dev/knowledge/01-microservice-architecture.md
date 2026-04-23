# 微服务架构设计

## 架构原则

### 1. 领域驱动设计（DDD）

按业务域划分微服务：
- **用户域**: 认证、授权、用户管理
- **订单域**: 订单创建、查询、状态流转
- **商品域**: 商品管理、库存
- **支付域**: 支付、退款

### 2. 服务拆分原则

- 单一职责：每个服务只负责一个明确的业务功能
- 松耦合：服务间通过API通信，避免直接依赖
- 高内聚：相关业务逻辑放在一起
- 独立部署：每个服务可独立开发、测试、部署

### 3. 服务间通信

```
同步调用: OpenFeign + LoadBalancer
异步通知: RocketMQ
```

## 项目结构

```
microservice-demo/
├── microservice-common/                 # 通用模块
│   ├── common-core/                   # 核心通用（Result, Exception, Constants）
│   ├── common-redis/                  # Redis配置
│   ├── common-security/               # 安全通用（JWT, Security）
│   └── common-web/                    # Web通用（GlobalExceptionHandler）
│
├── microservice-gateway/              # 网关服务 (8080)
│   └── src/main/
│
├── microservice-auth/                 # 认证服务 (8081)
│   └── src/main/
│
├── microservice-upms/                 # 用户权限服务 (8082)
│   ├── controller/
│   ├── service/
│   ├── mapper/
│   └── entity/
│
├── microservice-order/                 # 订单服务 (8083)
│
├── microservice-product/              # 商品服务 (8084)
│
└── microservice-pay/                  # 支付服务 (8085)
```

## 服务注册与发现

### Nacos配置

```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: nacos:8848
        namespace: dev
        group: DEFAULT_GROUP
      config:
        server-addr: nacos:8848
        namespace: dev
```

### 服务元数据

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          version: v1
          weight: 1.0
          preserve-header: true
```

## 服务注册流程

```
服务启动 → Nacos Client → 注册到Nacos → 心跳保活 → 服务下线 → Nacos通知Consumer
```

## 负载均衡

### LoadBalancer配置

```yaml
spring:
  cloud:
    loadbalancer:
      ribbon:
        enabled: false  # 禁用Ribbon，使用Spring LoadBalancer
```

### 自定义负载均衡策略

```java
@Configuration
public class LoadBalancerConfig {
    
    @Bean
    public ServiceInstanceListSupplier serviceInstanceListSupplier() {
        return ServiceInstanceListSupplier.builder()
                .withDiscoveryClient()
                .withHealthChecks()
                .build();
    }
}
```

## 服务熔断与降级

### Sentinel vs Hystrix

| 特性 | Sentinel | Hystrix |
|------|----------|---------|
| 熔断策略 | 基于响应时间、异常比例、异常数 | 基于异常比例 |
| 限流策略 | 直接拒绝、预热、排队等待 | 信号量/线程池 |
| 配置方式 | 控制台/注解/配置文件 | 注解/代码 |
| 实时监控 | 支持 | 支持 |

### 降级策略

```java
@FeignClient(name = "product-service", fallback = ProductFeignFallback.class)
public interface ProductFeignClient {
    @GetMapping("/product/{id}")
    Result<ProductVO> getById(@PathVariable("id") Long id);
}

@Component
public class ProductFeignFallback implements ProductFeignClient {
    @Override
    public Result<ProductVO> getById(Long id) {
        // 降级处理
        return Result.success(new ProductVO().setId(id).setName("降级商品"));
    }
}
```

## 分布式事务

### CAP定理

- **C**: Consistency（一致性）
- **A**: Availability（可用性）
- **P**: Partition Tolerance（分区容错性）

CP: Zookeeper, Nacos（配置为CP模式）
AP: Eureka, Nacos（默认AP模式）

### BASE理论

- **Basically Available**: 基本可用
- **Soft State**: 软状态
- **Eventually Consistent**: 最终一致性

## 设计模式

### 1. 聚合根模式

```
Order (聚合根)
  ├── OrderItem[] (实体)
  ├── OrderStatus (值对象)
  └── createOrder() (领域服务)
```

### 2. 领域事件模式

```java
// 订单创建后发布事件
eventPublisher.publishEvent(new OrderCreatedEvent(orderId, userId));

// 库存服务监听并处理
@EventListener
public void handleOrderCreated(OrderCreatedEvent event) {
    // 扣减库存
}
```
