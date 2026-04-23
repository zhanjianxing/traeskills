# 网关设计

## 网关职责

- **路由转发**: 将请求路由到对应的微服务
- **身份认证**: 验证JWT Token
- **限流熔断**: 保护后端服务
- **日志记录**: 记录访问日志
- **协议转换**: HTTP → Dubbo/gRPC

## Spring Cloud Gateway

### 基础配置

```yaml
server:
  port: 8080

spring:
  application:
    name: microservice-gateway
  cloud:
    nacos:
      discovery:
        server-addr: nacos:8848
    gateway:
      discovery:
        locator:
          enabled: true
          lower-case-service-id: true
      routes:
        - id: auth-service
          uri: lb://microservice-auth
          predicates:
            - Path=/auth/**
          filters:
            - StripPrefix=1
        - id: order-service
          uri: lb://microservice-order
          predicates:
            - Path=/order/**
          filters:
            - StripPrefix=1
        - id: upms-service
          uri: lb://microservice-upms
          predicates:
            - Path=/upms/**
          filters:
            - StripPrefix=1
```

## 网关过滤器

### 全局过滤器

```java
@Component
@Slf4j
public class GlobalAuthFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();
        
        // 跳过不需要认证的路径
        if (isSkipPath(path)) {
            return chain.filter(exchange);
        }
        
        String token = getToken(request);
        if (StringUtils.isBlank(token)) {
            return unauthorized(exchange);
        }
        
        try {
            // 验证Token
            Claims claims = jwtService.parseToken(token);
            String userId = claims.getSubject();
            
            // 将用户信息传递给下游服务
            ServerHttpRequest mutatedRequest = request.mutate()
                    .header("X-User-Id", userId)
                    .header("X-Username", claims.get("username", String.class))
                    .build();
            
            return chain.filter(exchange.mutate().request(mutatedRequest).build());
        } catch (Exception e) {
            log.warn("Token验证失败: {}", e.getMessage());
            return unauthorized(exchange);
        }
    }
    
    @Override
    public int getOrder() {
        return -100;
    }
}
```

### 路由过滤器

```java
@Component
@Slf4j
public class RequestLogFilter extends GatewayFilterFactory<RequestLogFilter.Config> {
    
    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            long startTime = System.currentTimeMillis();
            ServerHttpRequest request = exchange.getRequest();
            
            return chain.filter(exchange).then(Mono.fromRunnable(() -> {
                long cost = System.currentTimeMillis() - startTime;
                log.info("{} {} - {} - {}ms", 
                    request.getMethod(), 
                    request.getPath(), 
                    exchange.getResponse().getStatusCode().value(),
                    cost);
            }));
        };
    }
    
    public static class Config {}
}
```

## 限流

### 基于Sentinel的限流

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: lb://microservice-order
          predicates:
            - Path=/order/**
          filters:
            - name: RequestRateLimiter
              args:
                key-resolver: "#{@pathKeyResolver}"
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
```

### 自定义限流Key

```java
@Component
public class PathKeyResolver implements KeyResolver {
    
    @Override
    public Mono<String> resolve(ServerWebExchange exchange) {
        String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
        return Mono.just(userId != null ? userId : "anonymous");
    }
}
```

## 跨域配置

```java
@Configuration
public class CorsConfig {
    
    @Bean
    public CorsWebFilter corsWebFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.addAllowedOriginPattern("*");
        config.addAllowedMethod("*");
        config.addAllowedHeader("*");
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource(new PathPatternParser());
        source.registerCorsConfiguration("/**", config);
        
        return new CorsWebFilter(source);
    }
}
```

## 动态路由

### 基于Nacos的配置

```yaml
spring:
  cloud:
    gateway:
      config:
        routes-source: nacos
        data-id: gateway-routes
        group: DEFAULT_GROUP
        refresh-enabled: true
```
