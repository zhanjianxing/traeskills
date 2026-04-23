# 微服务缓存策略

## 技术选型

- **JetCache**: 阿里开源缓存框架
- **本地缓存**: Caffeine
- **分布式缓存**: Redis

## 微服务缓存架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gateway                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
      ┌──────────────────────┼──────────────────────┐
      ▼                      ▼                      ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Order      │      │  Product    │      │  Account    │
│  Service    │      │  Service    │      │  Service    │
│  ┌────────┐ │      │  ┌────────┐ │      │  ┌────────┐ │
│  │L1本地  │ │      │  │L1本地  │ │      │  │L1本地  │ │
│  │缓存    │ │      │  │缓存    │ │      │  │缓存    │ │
│  └────┬───┘ │      │  └────┬───┘ │      │  └────┬───┘ │
│       │     │      │       │     │      │       │     │
│  ┌────┴───┐ │      │  ┌────┴───┐ │      │  ┌────┴───┐ │
│  │L2 Redis│ │      │  │L2 Redis│ │      │  │L2 Redis│ │
│  │缓存    │ │      │  │缓存    │ │      │  │缓存    │ │
│  └────┬───┘ │      │  └────┬───┘ │      │  └────┬───┘ │
│       │     │      │       │     │      │       │     │
│       └─────┼──────┴───────┼─────┴───────┼──────┘     │
│             │              │              │              │
│             └──────────────┴──────────────┘             │
│                            │                            │
│                      ┌─────▼─────┐                      │
│                      │   MySQL   │                      │
│                      └───────────┘                      │
└─────────────────────────────────────────────────────────┘
```

## JetCache配置

### 依赖

```xml
<dependency>
    <groupId>com.alicp.jetcache</groupId>
    <artifactId>jetcache-starter-redis</artifactId>
    <version>2.7.7</version>
</dependency>
<dependency>
    <groupId>com.alicp.jetcache</groupId>
    <artifactId>jetcache-starter-caffeine</artifactId>
    <version>2.7.7</version>
</dependency>
```

### application.yml

```yaml
jetcache:
  statIntervalMinutes: 15
  areaInCacheName: false
  local:
    default:
      type: caffeine
      keyConvertor: fastjson
      limit: 500
      expire: 5000  # 本地缓存5秒
  remote:
    default:
      type: redis
      keyConvertor: fastjson
      host: ${redis.host:localhost}
      port: ${redis.port:6379}
      password: ${redis.password:}
      database: 0
      poolConfig:
        minIdle: 2
        maxIdle: 10
        maxTotal: 20
      expire: 180000  # 远程缓存3分钟
```

## 开启JetCache

```java
@SpringBootApplication
@EnableMethodCache(basePackages = "com.example.service")
@EnableCreateCacheAnnotation
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}
```

## 服务内缓存使用

### @Cached 注解

```java
@Service
public class ProductService {
    
    @Cached(name = "product:", key = "#productId", expire = 1800, cacheType = CacheType.BOTH)
    public ProductVO getProductById(Long productId) {
        return convertToVO(productMapper.selectById(productId));
    }
    
    @CacheInvalidate(name = "product:", key = "#productId")
    public void updateProduct(ProductUpdateDTO dto) {
        productMapper.updateById(convertToEntity(dto));
    }
}
```

### 缓存更新

```java
@Service
public class ProductService {
    
    @CacheUpdate(name = "product:", key = "#dto.id", value = "#result")
    public ProductVO updateProduct(ProductUpdateDTO dto) {
        Product product = convertToEntity(dto);
        productMapper.updateById(product);
        return convertToVO(product);
    }
}
```

## 跨服务缓存策略

### 缓存穿透防护

当一个服务更新数据后，需要通知其他服务清除缓存。

### 方案1：Redis发布订阅

```java
@Service
public class CacheInvalidationService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    public void invalidateProductCache(Long productId) {
        // 删除本服务缓存
        redisTemplate.delete("product:" + productId);
        
        // 发布缓存失效消息
        redisTemplate.convertAndSend("cache:invalidate:product", productId);
    }
}

@Component
public class CacheInvalidationListener {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @PostConstruct
    public void init() {
        redisTemplate.listenTo(new PatternTopic("cache:invalidate:*")).addListener((message, pattern) -> {
            String channel = message.getChannel();
            Object body = message.getBody();
            
            if (channel.contains("product")) {
                redisTemplate.delete("product:" + body);
            }
        });
    }
}
```

### 方案2：RocketMQ消息

```java
@Service
public class ProductService {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    @Transactional(rollbackFor = Exception.class)
    public ProductVO updateProduct(ProductUpdateDTO dto) {
        productMapper.updateById(convertToEntity(dto));
        
        // 发送缓存失效消息
        Message message = MessageBuilder.withPayload(dto.getId())
                .setHeader("cacheKey", "product:" + dto.getId())
                .build();
        rocketMQTemplate.asyncSend("cache-invalidate-topic", message, null);
        
        return getProductById(dto.getId());
    }
}

@Component
public class CacheInvalidationConsumer {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @StreamListener("cache-invalidate-input")
    public void handleCacheInvalidate(Message<String> message) {
        String cacheKey = message.getHeaders().get("cacheKey", String.class);
        if (StringUtils.isNotBlank(cacheKey)) {
            redisTemplate.delete(cacheKey);
        }
    }
}
```

## 分布式缓存锁

### 使用@CacheLock

```java
@Service
public class ProductService {
    
    @Cached(name = "product:", key = "#productId", expire = 1800, cacheType = CacheType.BOTH)
    @CacheLock(name = "product:", key = "#productId")
    public ProductVO getProductByIdWithLock(Long productId) {
        return convertToVO(productMapper.selectById(productId));
    }
}
```

### 手动分布式锁

```java
@Service
public class DistributedLockService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    public <T> T executeWithLock(String lockKey, long expireSeconds, Callable<T> callable) {
        String requestId = UUID.randomUUID().toString();
        
        try {
            Boolean acquired = redisTemplate.opsForValue()
                    .setIfAbsent(lockKey, requestId, expireSeconds, TimeUnit.SECONDS);
            
            if (!Boolean.TRUE.equals(acquired)) {
                throw new BusinessException("获取锁失败");
            }
            
            return callable.call();
        } catch (Exception e) {
            throw new RuntimeException(e);
        } finally {
            // 释放锁
            String script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end";
            redisTemplate.execute(new DefaultRedisScript<>(script, Long.class), 
                    Arrays.asList(lockKey), requestId);
        }
    }
}
```

## 缓存与Sentinel结合

### 限流+缓存

```java
@Service
public class ProductService {
    
    @SentinelResource(value = "getProduct", blockHandler = "handleBlock")
    @Cached(name = "product:", key = "#productId", expire = 300, cacheType = CacheType.BOTH)
    public ProductVO getProductById(Long productId) {
        return convertToVO(productMapper.selectById(productId));
    }
    
    public ProductVO handleBlock(Long productId, BlockException e) {
        // 尝试从缓存获取
        ProductVO cached = getProductFromCache(productId);
        if (cached != null) {
            return cached;
        }
        return ProductVO.builder().id(productId).name("限流返回").build();
    }
}
```

## 热点数据缓存

### 预热加载

```java
@Component
public class CacheWarmup {
    
    @Autowired
    private ProductMapper productMapper;
    
    @PostConstruct
    public void warmup() {
        log.info("开始商品缓存预热...");
        
        // 查询热点商品（销量前100）
        List<Product> hotProducts = productMapper.selectList(
            new QueryWrapper<Product>()
                .orderByDesc("sales_count")
                .last("LIMIT 100")
        );
        
        Cache<Long, ProductVO> cache = CacheBuilder.create()
                .cacheNameSpec("product:TTL=3600,LIMIT=500")
                .build();
        
        hotProducts.forEach(p -> 
            cache.put(p.getId(), convertToVO(p))
        );
        
        log.info("商品缓存预热完成，共 {} 条数据", hotProducts.size());
    }
}
```

## 缓存监控

### 配置统计

```yaml
jetcache:
  statIntervalMinutes: 15  # 统计间隔
```

### 查看统计

通过JMX或日志查看缓存命中率：
- `jetcache.stat` 日志
- `jconsole` JMX

## 最佳实践

1. **缓存粒度**: 按业务ID缓存，避免大对象
2. **过期时间**: 本地缓存短(秒级)，远程缓存长(分钟级)
3. **跨服务更新**: 使用MQ通知其他服务清除缓存
4. **热点数据**: 启动时预热
5. **分布式锁**: 高并发更新时使用@CacheLock
6. **限流结合**: Sentinel限流 + 缓存降级

```java
// 推荐配置
@Cached(name = "product:", 
        key = "#productId", 
        expire = 1800,       // Redis缓存30分钟
        cacheType = CacheType.BOTH)
@CacheLock(name = "product:", key = "#productId")
public ProductVO getProductById(Long productId) {
    return convertToVO(productMapper.selectById(productId));
}
```
