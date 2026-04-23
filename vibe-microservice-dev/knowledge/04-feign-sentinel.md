# 服务调用与熔断

## OpenFeign

### 基础使用

```java
@FeignClient(name = "microservice-product")
public interface ProductFeignClient {
    
    @GetMapping("/product/{id}")
    Result<ProductVO> getById(@PathVariable("id") Long id);
    
    @PostMapping("/product/reduce-stock")
    Result<Void> reduceStock(@RequestBody ReduceStockDTO dto);
}
```

### 开启Feign

```java
@SpringBootApplication
@EnableFeignClients
@EnableDiscoveryClient
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}
```

### 超时配置

```yaml
feign:
  client:
    config:
      default:
        connect-timeout: 5000
        read-timeout: 10000
      microservice-product:
        connect-timeout: 3000
        read-timeout: 5000
```

### 日志配置

```yaml
logging:
  level:
    com.example: DEBUG
```

```java
@Bean
public Logger.Level feignLoggerLevel() {
    return Logger.Level.FULL;
}
```

## Sentinel集成

### 开启Sentinel

```yaml
feign:
  sentinel:
    enabled: true
```

### 降级处理

```java
@Component
public class ProductFeignFallback implements ProductFeignClient {
    
    @Override
    public Result<ProductVO> getById(Long id) {
        return Result.error(500, "服务降级，商品服务暂时不可用");
    }
    
    @Override
    public Result<Void> reduceStock(ReduceStockDTO dto) {
        return Result.error(500, "服务降级，库存服务暂时不可用");
    }
}
```

```java
@FeignClient(name = "microservice-product", fallback = ProductFeignFallback.class)
public interface ProductFeignClient {
    // ...
}
```

### 熔断规则

```java
@Component
public class SentinelConfig {
    
    @PostConstruct
    public void init() {
        // 慢调用比例
        FlowRule rule = new FlowRule("getProduct")
                .setGrade(RuleConstant.FLOW_GRADE_QPS)
                .setCount(100)
                .setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_DEFAULT)
                .setMaxQueueingTimeMs(500)
                .setResource("getProduct");
        
        // 异常比例
        DegradeRule degradeRule = new DegradeRule("getProduct")
                .setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType())
                .setCount(0.5)
                .setMinRequestAmount(10)
                .setStatIntervalMs(10000)
                .setTimeWindow(10);
        
        DegradeRuleManager.loadRules(Arrays.asList(degradeRule));
    }
}
```

### 热点参数限流

```java
@GetMapping("/product/{id}")
@SentinelResource(value = "getProduct", blockHandler = "handleBlock", 
    paramIndex = 0,
    argsConverter = LongConverter.class)
public Result<ProductVO> getById(@PathVariable Long id) {
    return Result.success(productService.getById(id));
}

public Result<ProductVO> handleBlock(Long id, BlockException e) {
    return Result.error(429, "热点商品访问过于频繁");
}
```

## 服务调用链

```
Gateway → Auth → UPMS → Order → Product
                         ↓
                       Account
```

## 请求重试

### Feign重试

```yaml
feign:
  client:
    config:
      default:
        retryer: Retryer.Default
```

### 自定义重试

```java
@Bean
public Retryer retryer() {
    return new Retryer.Default(100, 1000, 3);
}
```

## 最佳实践

### 1. 接口设计

```java
// 使用统一的响应格式
public interface ProductFeignClient {
    @GetMapping("/product/{id}")
    Result<ProductVO> getById(@PathVariable("id") Long id);
}
```

### 2. 超时设置

```yaml
feign:
  client:
    config:
      default:
        connect-timeout: 3000
        read-timeout: 5000
        logger-level: basic
```

### 3. 熔断降级

```java
// 始终提供降级方案
@FeignClient(name = "product-service", fallback = ProductFeignFallback.class)
public interface ProductFeignClient {
    // ...
}
```

### 4. 日志记录

```yaml
# 开启日志
feign:
  logging-level: basic
```
