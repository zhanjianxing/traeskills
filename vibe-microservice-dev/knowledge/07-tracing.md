# 链路追踪

## 分布式追踪系统

### 为什么需要链路追踪

```
用户请求 → Gateway → Auth → Order → Product → Stock → 数据库
              ↓
            某处响应慢，如何定位？
```

微服务架构中，一个请求会经过多个服务，需要追踪完整调用链来定位性能问题。

## SkyWalking

### 架构

```
┌─────────────┐
│   UI        │  可视化界面
└──────┬──────┘
       │
┌──────┴──────┐
│   OAP       │  收集和分析
└──────┬──────┘
       │
┌──────┴──────┐
│   Agent    │  探针
└─────────────┘
```

### Agent配置

```yaml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: sentinel:8080
    skywalking:
      agent:
        service_name: microservice-order
        collector_address: skywalking:11800
```

### SkyWalking依赖

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

## Spring Cloud Sleuth

### 基础配置

```yaml
spring:
  sleuth:
    sampler:
      probability: 1.0  # 采样率
    trace-id128: true
  zipkin:
    base-url: http://zipkin:9411
    sender:
      type: web
```

### 自定义追踪

```java
@Autowired
private Tracer tracer;

public void test() {
    Span span = tracer.nextSpan().name("custom-span").start();
    try (Scope scope = tracer.withScopeInSpan(span)) {
        // 业务逻辑
    } finally {
        span.end();
    }
}
```

### MDC传递

```xml
<!-- logback-spring.xml -->
<pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId:-},%X{spanId:-}] %-5level %logger{50} - %msg%n</pattern>
```

## 监控指标

### 关键指标

- **响应时间**: P50, P90, P99
- **QPS**: 每秒请求数
- **错误率**: 错误请求/总请求
- **链路深度**: 调用层级

### 告警配置

```yaml
spring:
  cloud:
    alibaba:
      sentinel:
        dashboard: sentinel:8080
        filter:
          url-patterns: /**
```

## 最佳实践

### 1. 采样策略

```yaml
spring:
  sleuth:
    sampler:
      probability: 0.1  # 生产环境10%采样
```

### 2. 日志关联

```xml
<!-- 在日志中添加traceId -->
<pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId:-}] %-5level %logger{50} - %msg%n</pattern>
```

### 3. 性能开销

- 链路追踪会带来一定的性能开销
- 生产环境建议采样率10%-50%
- 关键链路可以设置100%采样
