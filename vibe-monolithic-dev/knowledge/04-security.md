# 安全认证

## 一、安全架构

### 1.1 安全目标

- **身份认证**：确认用户身份
- **权限授权**：控制用户访问资源
- **数据保护**：保护敏感数据
- **审计追溯**：记录操作日志

### 1.2 安全技术栈

| 技术 | 用途 |
|------|------|
| Spring Security | 安全框架 |
| JWT | 令牌认证 |
| BCrypt | 密码加密 |
| HTTPS | 传输加密 |

---

## 二、认证流程

### 2.1 登录流程

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│  客户端  │───▶│  Controller │───▶│ Service │───▶│  数据库  │
│         │    │            │    │         │    │          │
│         │◀───│  Token    │◀───│ 验证密码 │◀───│ 用户信息  │
└─────────┘    └──────────┘    └─────────┘    └──────────┘
```

### 2.2 认证实现

```java
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {
    
    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider jwtTokenProvider;
    private final UserMapper userMapper;
    
    @Override
    public LoginResult login(LoginDTO dto) {
        // 1. 认证
        Authentication authentication = authenticationManager.authenticate(
            new UsernamePasswordAuthenticationToken(dto.getUsername(), dto.getPassword())
        );
        
        // 2. 生成Token
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        String accessToken = jwtTokenProvider.generateToken(userDetails);
        String refreshToken = jwtTokenProvider.generateRefreshToken(userDetails);
        
        // 3. 返回结果
        return LoginResult.builder()
            .accessToken(accessToken)
            .refreshToken(refreshToken)
            .expiresIn(7200)
            .build();
    }
}
```

---

## 三、JWT令牌

### 3.1 Token结构

```
Header.Payload.Signature
```

**Header**：
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload**：
```json
{
  "sub": "userId",
  "username": "admin",
  "roles": ["ROLE_USER"],
  "iat": 1700000000,
  "exp": 1700007200
}
```

**Signature**：
```
HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)
```

### 3.2 TokenProvider

```java
@Component
public class JwtTokenProvider {
    
    @Value("${jwt.secret}")
    private String secret;
    
    @Value("${jwt.expiration}")
    private long expiration;
    
    public String generateToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", userDetails.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .collect(Collectors.toList()));
        
        return Jwts.builder()
            .setClaims(claims)
            .setSubject(userDetails.getUsername())
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + expiration))
            .signWith(SignatureAlgorithm.HS256, secret)
            .compact();
    }
    
    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(secret).parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
    
    public String getUsernameFromToken(String token) {
        return Jwts.parser()
            .setSigningKey(secret)
            .parseClaimsJws(token)
            .getBody()
            .getSubject();
    }
}
```

### 3.3 配置

```yaml
jwt:
  secret: your-256-bit-secret-key-here
  expiration: 7200000  # 2小时
  refresh-expiration: 604800000  # 7天
```

---

## 四、权限控制

### 4.1 角色权限模型

```
用户 ──▶ 角色 ──▶ 权限
```

### 4.2 权限注解

```java
// 角色控制
@PreAuthorize("hasRole('ADMIN')")
@PostMapping
public Result<Void> create() { }

// 权限控制
@PreAuthorize("hasAuthority('user:create')")
@PostMapping
public Result<Void> create() { }

// 多种权限
@PreAuthorize("hasAnyAuthority('user:create', 'user:update')")
@PutMapping
public Result<Void> update() { }
```

### 4.3 自定义权限校验

```java
@Component("authService")
@RequiredArgsConstructor
public class AuthService {
    
    private final DataScopeService dataScopeService;
    
    public boolean hasPermission(String permission) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .anyMatch(p -> p.equals(permission));
    }
    
    public boolean hasDataScope(Long deptId) {
        return dataScopeService.hasDeptScope(deptId);
    }
}
```

---

## 五、密码安全

### 5.1 密码加密

```java
@Configuration
public class PasswordConfig {
    
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

### 5.2 密码校验

```java
@Service
public class UserServiceImpl implements UserService {
    
    @Autowired
    private PasswordEncoder passwordEncoder;
    
    @Override
    public void createUser(UserCreateDTO dto) {
        // 密码加密存储
        dto.setPassword(passwordEncoder.encode(dto.getPassword()));
        userMapper.insert(convertToEntity(dto));
    }
    
    @Override
    public boolean validatePassword(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }
}
```

---

## 六、接口安全

### 6.1 请求过滤

```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    
    @Autowired
    private JwtTokenProvider jwtTokenProvider;
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
                                    HttpServletResponse response, 
                                    FilterChain filterChain) {
        // 1. 获取Token
        String token = getTokenFromRequest(request);
        
        // 2. 验证Token
        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
            String username = jwtTokenProvider.getUsernameFromToken(token);
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            
            // 3. 设置认证信息
            UsernamePasswordAuthenticationToken authentication = 
                new UsernamePasswordAuthenticationToken(
                    userDetails, null, userDetails.getAuthorities());
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }
        
        filterChain.doFilter(request, response);
    }
}
```

### 6.2 异常处理

```java
@Component
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {
    
    @Override
    public void commence(HttpServletRequest request, 
                         HttpServletResponse response, 
                         AuthenticationException e) {
        response.setContentType("application/json;charset=UTF-8");
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.getWriter().write(Result.fail(401, "未登录或Token已过期").toJson());
    }
}
```

---

## 七、安全配置

### 7.1 Spring Security配置

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {
    
    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;
    
    @Autowired
    private JwtAuthenticationEntryPoint jwtAuthenticationEntryPoint;
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .exceptionHandling()
                .authenticationEntryPoint(jwtAuthenticationEntryPoint)
            .and()
            .authorizeHttpRequests()
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/public/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }
}
```

---

## 八、敏感数据保护

### 8.1 数据脱敏

```java
@Component
public class SensitiveDataUtil {
    
    public static String maskPhone(String phone) {
        if (StringUtils.isEmpty(phone)) {
            return "";
        }
        return phone.substring(0, 3) + "****" + phone.substring(7);
    }
    
    public static String maskIdCard(String idCard) {
        if (StringUtils.isEmpty(idCard)) {
            return "";
        }
        return idCard.substring(0, 6) + "********" + idCard.substring(14);
    }
}
```

### 8.2 日志脱敏

```java
@Component
public class LogMaskUtil {
    
    public static String mask(String content, String type) {
        switch (type) {
            case "phone":
                return maskPhone(content);
            case "idCard":
                return maskIdCard(content);
            default:
                return content;
        }
    }
}
```
