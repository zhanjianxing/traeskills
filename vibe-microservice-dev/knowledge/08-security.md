# 微服务安全

## 安全架构

```
┌─────────────┐
│   Gateway   │  身份认证
└──────┬──────┘
       │
       ├──────────┬──────────┐
       ▼          ▼          ▼
   Order      Product      Account
   Service    Service      Service
```

## JWT认证流程

```
1. 用户 → /auth/login → Auth Service
2. Auth Service → 验证密码 → 返回JWT
3. 用户 → 请求 + JWT → Gateway
4. Gateway → 验证JWT → 转发到后端服务
5. 后端服务 → 解析JWT → 获取用户信息
```

## 网关统一认证

### JWT验证过滤器

```java
@Component
@Slf4j
public class JwtAuthFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String token = getToken(exchange.getRequest());
        
        if (StringUtils.isBlank(token)) {
            return unauthorized(exchange);
        }
        
        try {
            Claims claims = jwtService.parseToken(token);
            String userId = claims.getSubject();
            
            // 传递给下游服务
            ServerHttpRequest request = exchange.getRequest().mutate()
                    .header("X-User-Id", userId)
                    .header("X-Username", claims.get("username", String.class))
                    .header("X-Token", token)
                    .build();
            
            return chain.filter(exchange.mutate().request(request).build());
        } catch (Exception e) {
            return unauthorized(exchange);
        }
    }
}
```

## 权限控制

### 基于注解的权限

```java
@RestController
@RequestMapping("/api/order")
public class OrderController {
    
    @PreAuthorize("@ss.hasPermission('order:create')")
    @PostMapping
    public Result<Void> create(@Valid @RequestBody OrderCreateDTO dto) {
        return Result.success(orderService.create(dto));
    }
    
    @PreAuthorize("@ss.hasRole('ADMIN')")
    @GetMapping("/list")
    public Result<PageResult<OrderVO>> list(OrderQuery query) {
        return Result.success(orderService.list(query));
    }
}
```

### 权限服务

```java
@Service("ss")
public class SecurityService {
    
    public boolean hasPermission(String permission) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(p -> p.equals(permission));
    }
    
    public boolean hasRole(String role) {
        return hasPermission("ROLE_" + role);
    }
}
```

## 认证服务

### 登录接口

```java
@Service
@Slf4j
public class AuthServiceImpl implements AuthService {
    
    @Autowired
    private PasswordEncoder passwordEncoder;
    
    @Autowired
    private JwtService jwtService;
    
    @Autowired
    private UserMapper userMapper;
    
    @Override
    public LoginVO login(LoginDTO dto) {
        User user = userMapper.selectByUsername(dto.getUsername());
        
        if (user == null || !passwordEncoder.matches(dto.getPassword(), user.getPassword())) {
            throw new BusinessException("用户名或密码错误");
        }
        
        if (user.getStatus() != 1) {
            throw new BusinessException("账户已被禁用");
        }
        
        String token = jwtService.generateToken(user.getId(), user.getUsername());
        
        // 保存Token到Redis
        redisTemplate.opsForValue().set(
            RedisConstants.TOKEN + user.getId(),
            token,
            7,
            TimeUnit.DAYS
        );
        
        return LoginVO.builder()
                .token(token)
                .userId(user.getId())
                .username(user.getUsername())
                .build();
    }
}
```

## Token管理

### 刷新Token

```java
public LoginVO refreshToken(String oldToken) {
    Claims claims = jwtService.parseToken(oldToken);
    Long userId = Long.parseLong(claims.getSubject());
    
    // 检查是否在黑名单
    if (Boolean.TRUE.equals(redisTemplate.hasKey(RedisConstants.TOKEN_BLACKLIST + oldToken))) {
        throw new BusinessException("Token已失效");
    }
    
    // 生成新Token
    User user = userMapper.selectById(userId);
    String newToken = jwtService.generateToken(user.getId(), user.getUsername());
    
    // 将旧Token加入黑名单
    redisTemplate.opsForValue().set(
        RedisConstants.TOKEN_BLACKLIST + oldToken,
        "1",
        7,
        TimeUnit.DAYS
    );
    
    return LoginVO.builder()
            .token(newToken)
            .userId(user.getId())
            .build();
}
```

### 登出

```java
public void logout(String token) {
    Claims claims = jwtService.parseToken(token);
    Long userId = Long.parseLong(claims.getSubject());
    
    // 删除Redis中的Token
    redisTemplate.delete(RedisConstants.TOKEN + userId);
    
    // 加入黑名单
    redisTemplate.opsForValue().set(
        RedisConstants.TOKEN_BLACKLIST + token,
        "1",
        7,
        TimeUnit.DAYS
    );
}
```

## 敏感数据

### 密码加密

```java
// 使用BCrypt加密
String encoded = passwordEncoder.encode(rawPassword);
boolean matches = passwordEncoder.matches(rawPassword, encoded);
```

### 数据脱敏

```java
// 手机号脱敏
public String maskPhone(String phone) {
    return phone.replaceAll("(\\d{3})\\d{4}(\\d{4})", "$1****$2");
}

// 身份证脱敏
public String maskIdCard(String idCard) {
    return idCard.replaceAll("(\\d{4})\\d{10}(\\d{4})", "$1**********$2");
}
```

## 接口限流

### 基于Sentinel

```java
@GetMapping("/test")
@SentinelResource(value = "test", blockHandler = "handleBlock")
public Result<String> test() {
    return Result.success("OK");
}

public Result<String> handleBlock(BlockException e) {
    return Result.error(429, "请求过于频繁");
}
```

## 安全最佳实践

1. **HTTPS传输**: 所有接口使用HTTPS
2. **Token过期**: 设置合理的过期时间（2小时）
3. **密码加密**: 使用BCrypt加密
4. **敏感数据**: 脱敏处理
5. **日志审计**: 记录关键操作
6. **接口限流**: 防止恶意请求
