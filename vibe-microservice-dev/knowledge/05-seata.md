# 分布式事务

## 分布式事务问题

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Order   │    │ Stock   │    │ Account │
│ Service │    │ Service │    │ Service │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     └──────────────┴──────────────┘
              ↓
        MySQL数据库
```

在分布式系统中，不同服务使用独立的数据库，本地事务无法保证跨服务的数据一致性。

## Seata架构

```
┌─────────────────────────────────────────────┐
│                 TC (Transaction Coordinator) │
│                   (Seata Server)            │
└────────────────────┬────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌────────┐    ┌──────────┐    ┌──────────┐
│ TM-1   │    │ TM-2     │    │ TM-3     │
│(Order) │    │ (Stock)  │    │(Account) │
└────┬───┘    └────┬─────┘    └────┬─────┘
     │              │               │
     └──────────────┴───────────────┘
              ↓
        Application
```

- **TC**: Transaction Coordinator（事务协调器），Seata Server
- **TM**: Transaction Manager（事务管理器），发起方
- **RM**: Resource Manager（资源管理器），参与方

## AT模式（推荐）

### 1. Seata Server配置

```yaml
# seata-server/application.yml
server:
  port: 8091

spring:
  application:
    name: seata-server

seata:
  server:
    service-port: 8091
  store:
    mode: db
    db:
      datasource: druid
      db-type: mysql
      driver-class-name: com.mysql.cj.jdbc.Driver
      url: jdbc:mysql://mysql:3306/seata
      username: root
      password: root
```

### 2. 客户端配置

```yaml
spring:
  cloud:
    alibaba:
      seata:
        tx-service-group: my_test_tx_group

seata:
  application-id: ${spring.application.name}
  tx-service-group: my_test_tx_group
  registry:
    type: nacos
    nacos:
      server-addr: nacos:8848
      namespace: dev
  config:
    type: nacos
    nacos:
      server-addr: nacos:8848
      namespace: dev
```

### 3. 使用@GlobalTransactional

```java
@Service
public class OrderServiceImpl implements OrderService {
    
    @Autowired
    private OrderMapper orderMapper;
    
    @Autowired
    private ProductFeignClient productFeignClient;
    
    @Autowired
    private AccountFeignClient accountFeignClient;
    
    @GlobalTransactional(timeoutMills = 30000, name = "create-order")
    @Override
    public void createOrder(OrderCreateDTO dto) {
        // 1. 创建订单
        Order order = new Order();
        order.setUserId(dto.getUserId());
        order.setProductId(dto.getProductId());
        order.setQuantity(dto.getQuantity());
        order.setTotalAmount(dto.getTotalAmount());
        order.setStatus(OrderStatus.CREATED);
        orderMapper.insert(order);
        
        // 2. 远程调用扣减库存
        productFeignClient.reduceStock(dto.getProductId(), dto.getQuantity());
        
        // 3. 远程调用扣减余额
        accountFeignClient.deductBalance(dto.getUserId(), dto.getTotalAmount());
        
        // 更新订单状态
        order.setStatus(OrderStatus.PAID);
        orderMapper.updateById(order);
    }
}
```

### 4. 开启自动代理

```java
@SpringBootApplication
@EnableDiscoveryClient
@EnableGlobalTransaction
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}
```

## TCC模式

### 1. 定义TCC接口

```java
public interface TccAction {
    
    @TwoPhaseBusinessAction(name = "reduceStock")
    boolean tryReduceStock(
        @BusinessActionContextParameter(paramName = "productId") Long productId,
        @BusinessActionContextParameter(paramName = "quantity") Integer quantity
    );
    
    @Compensable(confirmMethod = "confirmReduceStock", cancelMethod = "cancelReduceStock")
    boolean reduceStock(Long productId, Integer quantity);
    
    boolean confirmReduceStock(BusinessActionContext context);
    
    boolean cancelReduceStock(BusinessActionContext context);
}
```

### 2. 实现TCC接口

```java
@Service
public class TccStockService implements TccAction {
    
    @Override
    public boolean tryReduceStock(Long productId, Integer quantity) {
        // 预留资源
        return stockMapper.reserveStock(productId, quantity) > 0;
    }
    
    @Override
    public boolean reduceStock(Long productId, Integer quantity) {
        // 实际扣减
        return stockMapper.reduceStock(productId, quantity) > 0;
    }
    
    @Override
    public boolean confirmReduceStock(BusinessActionContext context) {
        Long productId = Long.parseLong(context.getActionContext("productId").toString());
        Integer quantity = Integer.parseInt(context.getActionContext("quantity").toString());
        return stockMapper.confirmStock(productId, quantity) > 0;
    }
    
    @Override
    public boolean cancelReduceStock(BusinessActionContext context) {
        Long productId = Long.parseLong(context.getActionContext("productId").toString());
        Integer quantity = Integer.parseInt(context.getActionContext("quantity").toString());
        return stockMapper.cancelStock(productId, quantity) > 0;
    }
}
```

### 3. 使用TCC

```java
@Service
public class OrderService {
    
    @Autowired
    private TccAction tccAction;
    
    @GlobalTransactional
    public void createOrder(OrderDTO dto) {
        tccAction.reduceStock(dto.getProductId(), dto.getQuantity());
        // ...
    }
}
```

## 事务模式选择

| 模式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| AT | 无侵入，自动补偿 | 需要undo_log表 | 大多数场景 |
| TCC | 性能高 | 有侵入 | 性能要求高 |
| Saga | 长流程 | 无回滚 | 流程长 |
| XA | 强一致 | 性能低 | 强一致场景 |

## 最佳实践

### 1. 事务分组

```yaml
seata:
  tx-service-group: order_tx_group
  service:
    vgroup-mapping:
      order_tx_group: default
```

### 2. 超时设置

```java
@GlobalTransactional(timeoutMills = 30000, name = "create-order")
public void createOrder(OrderDTO dto) {
    // 30秒超时
}
```

### 3. 异常处理

```java
@GlobalTransactional(rollbackFor = Exception.class)
public void createOrder(OrderDTO dto) {
    try {
        // 业务逻辑
    } catch (Exception e) {
        throw new RuntimeException("订单创建失败", e);
    }
}
```
