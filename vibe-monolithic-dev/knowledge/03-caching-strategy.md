# 缓存策略

## 一、缓存概述

### 1.1 为什么使用缓存

- 减少数据库访问压力
- 提升系统响应速度
- 提高并发处理能力

### 1.2 缓存层次

| 缓存类型 | 介质 | 响应时间 | 作用域 |
|----------|------|----------|--------|
| 本地缓存 | JVM内存 | <1ms | 单节点 |
| 分布式缓存 | Redis | <10ms | 多节点共享 |

---

## 二、Caffeine本地缓存

### 2.1 配置文件

```yaml
spring:
  cache:
    type: caffeine
    caffeine:
      spec: initialCapacity=50,maximumSize=500,expireAfterWrite=60m
```

### 2.2 使用示例

```java
@Cacheable(value = "user", key = "#userId")
public UserVO getUserById(Long userId) {
    return convertToVO(userMapper.selectById(userId));
}

@CachePut(value = "user", key = "#user.id")
public UserVO updateUser(User user) {
    userMapper.updateById(user);
    return convertToVO(user);
}

@CacheEvict(value = "user", key = "#userId")
public void deleteUser(Long userId) {
    userMapper.deleteById(userId);
}
```

### 2.3 适用场景

- 热点数据（访问频率高）
- 不经常变化的数据（字典、配置）
- 读多写少的数据

---

## 三、Redis分布式缓存

### 3.1 配置

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      database: 0
      timeout: 5000ms
      lettuce:
        pool:
          max-active: 8
          max-idle: 8
          min-idle: 0
```

### 3.2 使用示例

```java
@Service
@RequiredArgsConstructor
public class UserCacheService {
    
    private final RedisTemplate<String, Object> redisTemplate;
    private final UserMapper userMapper;
    
    private static final String USER_KEY = "user:";
    private static final long EXPIRE_TIME = 30;
    
    public User getUserById(Long userId) {
        String key = USER_KEY + userId;
        
        // 查缓存
        User cached = (User) redisTemplate.opsForValue().get(key);
        if (cached != null) {
            return cached;
        }
        
        // 查数据库
        User user = userMapper.selectById(userId);
        if (user != null) {
            redisTemplate.opsForValue().set(key, user, EXPIRE_TIME, TimeUnit.MINUTES);
        }
        return user;
    }
    
    public void deleteUserCache(Long userId) {
        redisTemplate.delete(USER_KEY + userId);
    }
}
```

---

## 四、二级缓存策略

### 4.1 什么是二级缓存

**第一级**：Caffeine（本地缓存）
- 速度快，无网络开销
- 存储热点数据

**第二级**：Redis（分布式缓存）
- 多节点共享
- 存储共享数据

### 4.2 实现方案

```java
@Service
public class CacheService {
    
    @Autowired
    private CacheManager caffeineCacheManager;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    public <T> T get(String key, Class<T> type, Supplier<T> loader) {
        // 1. 查本地缓存
        Cache cache = caffeineCacheManager.getCache("default");
        T result = cache.get(key, type);
        if (result != null) {
            return result;
        }
        
        // 2. 查Redis
        result = (T) redisTemplate.opsForValue().get(key);
        if (result != null) {
            cache.put(key, result);
            return result;
        }
        
        // 3. 查数据库并缓存
        result = loader.get();
        if (result != null) {
            redisTemplate.opsForValue().set(key, result, 30, TimeUnit.MINUTES);
            cache.put(key, result);
        }
        return result;
    }
    
    public void evict(String key) {
        caffeineCacheManager.getCache("default").evict(key);
        redisTemplate.delete(key);
    }
}
```

---

## 五、缓存问题及解决方案

### 5.1 缓存穿透

**问题**：查询不存在的数据，每次都打到数据库

**解决方案**：空值缓存

```java
public User getUserById(Long userId) {
    String key = USER_KEY + userId;
    
    // 查缓存（含空值）
    User cached = (User) redisTemplate.opsForValue().get(key);
    if (cached != null) {
        return cached;
    }
    
    // 查数据库
    User user = userMapper.selectById(userId);
    
    // 空值也缓存（设置较短过期时间）
    if (user == null) {
        redisTemplate.opsForValue().set(key, "", 5, TimeUnit.MINUTES);
    } else {
        redisTemplate.opsForValue().set(key, user, 30, TimeUnit.MINUTES);
    }
    return user;
}
```

### 5.2 缓存击穿

**问题**：热点key失效，大量请求打到数据库

**解决方案**：分布式锁 + 双重检查

```java
public User getUserById(Long userId) {
    String key = USER_KEY + userId;
    
    // 1. 查缓存
    User cached = (User) redisTemplate.opsForValue().get(key);
    if (cached != null) {
        return cached;
    }
    
    // 2. 获取分布式锁
    String lockKey = "lock:" + key;
    Boolean acquired = redisTemplate.opsForValue().setIfAbsent(lockKey, "1", 
        10, TimeUnit.SECONDS);
    
    if (Boolean.TRUE.equals(acquired)) {
        try {
            // 3. 双重检查
            cached = (User) redisTemplate.opsForValue().get(key);
            if (cached != null) {
                return cached;
            }
            
            // 4. 查数据库
            User user = userMapper.selectById(userId);
            if (user != null) {
                redisTemplate.opsForValue().set(key, user, 30, TimeUnit.MINUTES);
            }
            return user;
        } finally {
            redisTemplate.delete(lockKey);
        }
    } else {
        // 等待其他线程加载
        Thread.sleep(100);
        return getUserById(userId);
    }
}
```

### 5.3 缓存雪崩

**问题**：大量缓存同时过期，请求打到数据库

**解决方案**：随机过期时间 + 持久化缓存

```java
// 随机过期时间
private long getExpireTime() {
    return 30 + new Random().nextInt(10);
}

// 使用永久缓存
redisTemplate.opsForValue().set(key, user);
```

---

## 六、缓存使用规范

### 6.1 缓存原则

| 操作 | 缓存策略 |
|------|----------|
| 查询 | 先缓存后数据库 |
| 新增 | 删除缓存 |
| 更新 | 删除缓存 |
| 删除 | 删除缓存 |

### 6.2 过期时间设置

| 数据类型 | 过期时间 | 说明 |
|----------|----------|------|
| 热点数据 | 1小时 | 频繁访问 |
| 普通数据 | 10-30分钟 | 一般访问 |
| 配置数据 | 1小时-1天 | 很少变化 |
| 空值缓存 | 5分钟 | 防止穿透 |

### 6.3 缓存注解

```java
// 查询缓存
@Cacheable(value = "user", key = "#userId")
UserVO getUserById(Long userId);

// 更新后删除缓存
@CacheEvict(value = "user", key = "#user.id")
void updateUser(User user);

// 删除缓存
@CacheEvict(value = "user", key = "#userId")
void deleteUser(Long userId);

// 清空所有缓存
@CacheEvict(value = "user", allEntries = true)
void clearUserCache();
```
