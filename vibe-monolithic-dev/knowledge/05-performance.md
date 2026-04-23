# 性能优化

## 一、数据库性能优化

### 1.1 索引优化

**索引设计原则**：
- WHERE条件字段建立索引
- 区分度高的字段优先
- 复合索引遵循最左前缀原则
- 避免在索引列上使用函数

```sql
-- 正确：使用索引
SELECT * FROM user WHERE status = 1 AND create_time > '2024-01-01';

-- 错误：索引失效
SELECT * FROM user WHERE YEAR(create_time) = 2024;
SELECT * FROM user WHERE name LIKE '%test';
```

**索引类型选择**：
| 场景 | 索引类型 |
|------|----------|
| 唯一性查询 | 唯一索引 |
| 范围查询 | BTree索引 |
| 全文检索 | 全文索引 |
| 地理位置 | 空间索引 |

### 1.2 SQL优化

**避免全表扫描**：
```sql
-- 优化前
SELECT * FROM user WHERE name LIKE '%test';

-- 优化后
SELECT id, name, email FROM user WHERE name LIKE 'test%';
```

**分页优化**：
```sql
-- 优化前：OFFSET大时性能差
SELECT * FROM user ORDER BY id LIMIT 100000, 10;

-- 优化后：基于ID分页
SELECT * FROM user WHERE id > 100000 ORDER BY id LIMIT 10;
```

**批量操作**：
```java
// 批量插入
userService.saveBatch(userList);

// 批量更新
userService.updateBatchById(userList);
```

### 1.3 分库分表

**分表策略**：
- 按时间分表：适合日志、订单
- 按地区分表：适合区域性业务
- 按用户ID哈希分表：适合用户相关数据

---

## 二、缓存性能优化

### 2.1 缓存策略

| 数据类型 | 缓存策略 | 过期时间 |
|----------|----------|----------|
| 热点数据 | Caffeine + Redis | 1小时 |
| 配置数据 | Redis | 1天 |
| 会话数据 | Redis | 2小时 |

### 2.2 缓存优化

**预热**：
```java
@PostConstruct
public void cacheWarmUp() {
    // 预热热点数据
    List<Dict> dictList = dictMapper.selectList(null);
    dictList.forEach(dict -> {
        redisTemplate.opsForValue().set("dict:" + dict.getCode(), dict);
    });
}
```

**异步更新**：
```java
@Async
public void asyncUpdateCache() {
    // 异步更新缓存，不阻塞主流程
}
```

---

## 三、并发性能优化

### 3.1 乐观锁

```java
@Data
@TableName("product")
public class Product {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String name;
    
    private Integer stock;
    
    @Version
    private Integer version;
}
```

```java
@Service
public class ProductService {
    
    public void reduceStock(Long productId, Integer quantity) {
        // 乐观锁更新
        int rows = productMapper.updateStock(productId, quantity);
        if (rows == 0) {
            throw new BusinessException("库存不足或数据已被修改");
        }
    }
}

<!-- ProductMapper.xml -->
<update id="updateStock">
    UPDATE product 
    SET stock = stock - #{quantity}, version = version + 1 
    WHERE id = #{id} AND stock >= #{quantity} AND version = #{version}
</update>
```

### 3.2 分布式锁

```java
@Service
public class SeckillService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    public void seckill(Long productId, Long userId) {
        String lockKey = "lock:seckill:" + productId;
        
        // 获取分布式锁
        Boolean acquired = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, userId.toString(), 10, TimeUnit.SECONDS);
        
        if (Boolean.TRUE.equals(acquired)) {
            try {
                // 执行业务逻辑
                doSeckill(productId, userId);
            } finally {
                redisTemplate.delete(lockKey);
            }
        } else {
            throw new BusinessException("系统繁忙，请稍后重试");
        }
    }
}
```

### 3.3 异步处理

```java
@Service
public class OrderService {
    
    @Async
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 异步发送通知
        notificationService.sendOrderNotification(event.getOrderId());
    }
    
    @Async("taskExecutor")
    public CompletableFuture<Void> processAsync(Task task) {
        return CompletableFuture.runAsync(() -> {
            // 耗时操作
        });
    }
}
```

---

## 四、JVM性能优化

### 4.1 内存模型

```
┌─────────────────────────────────────────┐
│                  Heap                   │
│  ┌─────────────┐    ┌───────────────┐  │
│  │   Young     │    │     Old       │  │
│  │  Eden S0 S1 │    │               │  │
│  └─────────────┘    └───────────────┘  │
├─────────────────────────────────────────┤
│                Metaspace                │
├─────────────────────────────────────────┤
│              Native Memory              │
└─────────────────────────────────────────┘
```

### 4.2 参数调优

```bash
# 生产环境JVM参数
-Xms2g -Xmx2g                    # 堆大小
-XX:NewRatio=2                   # 新生代/老年代比例
-XX:+UseG1GC                     # 使用G1垃圾收集器
-XX:MaxGCPauseMillis=200         # 最大GC停顿时间
-XX:+HeapDumpOnOutOfMemoryError # OOM时导出堆栈
-XX:HeapDumpPath=/tmp/          # 堆栈导出路径
```

### 4.3 GC选择

| 收集器 | 适用场景 |
|--------|----------|
| Serial | 小数据量、单核 |
| Parallel | 大数据量、吞吐量优先 |
| CMS | 停顿时间敏感 |
| G1 | 大堆、平衡停顿和吞吐量 |

---

## 五、网络性能优化

### 5.1 HTTP连接池

```yaml
spring:
  http:
    client:
      pool:
        max-connections: 200
        max-per-route: 20
        connect-timeout: 5000
        socket-timeout: 10000
```

### 5.2 数据库连接池

```yaml
spring:
  datasource:
    hikari:
      minimum-idle: 5
      maximum-pool-size: 20
      idle-timeout: 300000
      connection-timeout: 30000
      max-lifetime: 1800000
```

---

## 六、应用性能优化

### 6.1 接口优化

**批量接口**：
```java
// 优化前：N次查询
for (Long userId : userIds) {
    User user = userService.getById(userId);
}

// 优化后：批量查询
List<User> users = userService.listByIds(userIds);
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, Function.identity()));
```

**预计算**：
```java
// 缓存聚合结果
@Cacheable(value = "statistics", key = "'user:count'")
public Long getUserCount() {
    return userMapper.selectCount(null);
}
```

### 6.2 序列化优化

```java
@Configuration
public class JacksonConfig {
    
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        // 忽略空值
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
        // 使用JSR310日期API
        mapper.registerModule(new JavaTimeModule());
        return mapper;
    }
}
```

---

## 七、监控与诊断

### 7.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| QPS | >1000 | 每秒请求数 |
| RT | <200ms | 平均响应时间 |
| Error Rate | <0.1% | 错误率 |
| CPU | <70% | CPU使用率 |

### 7.2 监控工具

- **APM**: SkyWalking、Pinpoint
- **Metrics**: Micrometer + Prometheus
- **Logging**: ELK Stack

### 7.3 诊断命令

```bash
# 查看GC日志
jstat -gcutil <pid> 1000

# 线程堆栈
jstack <pid>

# 堆内存Dump
jmap -dump:format=b,file=heap.hprof <pid>

# 查看TCP连接
netstat -an | grep TIME_WAIT
```
