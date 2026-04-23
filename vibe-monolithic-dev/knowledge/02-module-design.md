# 模块化设计

## 一、模块化原则

### 1.1 高内聚低耦合

- **高内聚**：模块内的代码应该共同完成一个明确的职责
- **低耦合**：模块间应该通过接口通信，减少直接依赖

### 1.2 单一职责

每个模块应该有且只有一个改变的理由：
- 系统模块：处理用户、角色、权限
- 订单模块：处理订单相关业务
- 商品模块：处理商品相关业务

### 1.3 依赖规则

- 公共模块不能依赖业务模块
- 业务模块之间不能循环依赖
- 依赖方向应该指向更稳定的模块

---

## 二、模块结构

### 2.1 目录结构

```
module-xxx/
├── src/main/java/com/xxx/xxx/
│   ├── controller/
│   ├── service/
│   │   └── impl/
│   ├── repository/
│   │   └── entity/
│   ├── dto/
│   ├── vo/
│   ├── enums/
│   └── convert/
└── src/main/resources/
    ├── mapper/
    └── module-xxx.sql
```

### 2.2 包命名规范

| 包名 | 职责 | 示例 |
|------|------|------|
| controller | HTTP接口 | UserController |
| service | 业务逻辑 | UserService |
| repository | 数据访问 | UserMapper |
| dto | 数据传输 | UserCreateDTO |
| vo | 视图对象 | UserVO |
| enums | 枚举定义 | UserStatus |
| convert | 对象转换 | UserConvert |

---

## 三、模块间通信

### 3.1 直接依赖

同一项目内，模块间可以直接注入调用：

```java
@Service
@RequiredArgsConstructor
public class OrderServiceImpl implements OrderService {
    
    private final ProductService productService;
    
    @Override
    public void createOrder(OrderCreateDTO dto) {
        // 直接调用ProductService
        productService.checkStock(dto.getProductId(), dto.getQuantity());
    }
}
```

### 3.2 事件通信

跨模块通信使用事件机制：

```java
// Order模块发布事件
eventPublisher.publishEvent(new OrderCreatedEvent(order));

// Product模块监听并处理
@Async
@EventListener
public void handleOrderCreated(OrderCreatedEvent event) {
    productService.reduceStock(event.getProductId(), event.getQuantity());
}
```

---

## 四、模块划分示例

### 4.1 基础模块

**module-system（系统模块）**：
- 用户管理
- 角色管理
- 菜单管理
- 部门管理
- 岗位管理
- 日志管理

**module-infra（基础设施模块）**：
- 文件管理
- 配置管理
- 字典管理
- 定时任务

### 4.2 业务模块

**module-order（订单模块）**：
- 订单创建
- 订单支付
- 订单取消
- 订单查询

**module-product（商品模块）**：
- 商品管理
- 库存管理
- 分类管理
- 品牌管理

**module-member（会员模块）**：
- 注册登录
- 会员等级
- 积分管理
- 收货地址

---

## 五、模块配置

### 5.1 Server pom.xml

```xml
<dependencies>
    <!-- 公共模块 -->
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>common-core</artifactId>
    </dependency>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>common-redis</artifactId>
    </dependency>
    
    <!-- 业务模块 -->
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>module-system</artifactId>
    </dependency>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>module-order</artifactId>
    </dependency>
</dependencies>
```

### 5.2 模块配置

```yaml
# application.yml
spring:
  profiles:
    active: dev
  
# 模块开关
module:
  system:
    enabled: true
  order:
    enabled: true
  product:
    enabled: true
```

---

## 六、模块隔离

### 6.1 数据库隔离

- 每个模块使用独立的表前缀
- 避免跨模块直接操作对方表
- 通过API接口访问

### 6.2 事务隔离

- 单模块事务使用 `@Transactional`
- 跨模块使用消息最终一致性
- 避免长事务

---

## 七、模块开发规范

### 7.1 接口定义

```java
@RestController
@RequestMapping("/api/v1/orders")
public interface OrderController {
    
    @PostMapping
    Result<Long> create(@Validated @RequestBody OrderCreateDTO dto);
    
    @GetMapping("/{orderId}")
    Result<OrderVO> getById(@PathVariable Long orderId);
    
    @GetMapping("/page")
    Result<PageResult<OrderVO>> getPage(@Validated OrderPageQuery query);
}
```

### 7.2 Service定义

```java
public interface OrderService {
    
    Long create(OrderCreateDTO dto);
    
    OrderVO getById(Long orderId);
    
    PageResult<OrderVO> getPage(OrderPageQuery query);
    
    void cancel(Long orderId);
}
```

### 7.3 DTO定义

```java
@Data
public class OrderCreateDTO {
    
    @NotNull(message = "商品ID不能为空")
    private Long productId;
    
    @NotNull(message = "数量不能为空")
    @Min(value = 1, message = "数量最小为1")
    private Integer quantity;
    
    @NotBlank(message = "收货地址不能为空")
    private String address;
}
```
