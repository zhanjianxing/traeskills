# Nacos服务注册与配置

## Nacos架构

```
┌─────────────┐
│   Nacos     │
│  Server     │
│  (8848)     │
└──────┬──────┘
       │
       ├──────────┬──────────┐
       │          │          │
       ▼          ▼          ▼
  Service-A  Service-B  Service-C
```

## 服务注册

### 服务提供者

```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: nacos:8848
        namespace: dev
        group: DEFAULT_GROUP
        metadata:
          version: v1
```

### 服务消费者

服务消费者通过OpenFeign自动发现服务，无需额外配置。

## 配置管理

### 配置结构

```
Namespace (命名空间)
 └── Group (分组)
      └── Data ID (配置文件)
           └── 配置内容
```

### 配置文件命名规则

```
${spring.application.name}-${spring.profiles.active}.${spring.cloud.nacos.config.file-extension}
```

例如: `microservice-order-dev.yml`

### 配置示例

```yaml
# microservice-order-dev.yml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://mysql:3306/order_db
    username: root
    password: root

server:
  port: 8083

mybatis-plus:
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
```

### 共享配置

```yaml
spring:
  cloud:
    nacos:
      config:
        shared-configs:
          - data-id: common.yml
            group: DEFAULT_GROUP
            refresh: true
          - data-id: datasource.yml
            group: DEFAULT_GROUP
            refresh: true
```

## 配置动态刷新

### @RefreshScope

```java
@RestController
@RefreshScope
public class ConfigController {
    
    @Value("${custom.config}")
    private String config;
    
    @GetMapping("/config")
    public String getConfig() {
        return config;
    }
}
```

### 配置监听

```java
@Component
public class NacosConfigListener {
    
    @NacosConfigurationProperties(dataId = "microservice-order-dev.yml", autoRefreshed = true)
    @Data
    public static class OrderConfig {
        private Integer maxOrderAmount;
        private Integer orderTimeout;
    }
}
```

## Nacos集群

### 集群部署架构

```
┌─────────────┐
│   Nacos-1   │
│   (8848)    │
└──────┬──────┘
       │
┌──────┴──────┐
│  Nacos-2    │
│  (8848)    │
└──────┬──────┘
       │
┌──────┴──────┐
│  Nacos-3    │
│  (8848)    │
└─────────────┘
       │
       ▼
   MySQL/derby
```

### 高可用配置

```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: nacos1:8848,nacos2:8848,nacos3:8848
      config:
        server-addr: nacos1:8848,nacos2:8848,nacos3:8848
```

## 服务元数据

### 元数据类型

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          version: v1.0
          weight: 1.0
          group: DEFAULT_GROUP
          management:
            port: 8083
            context-path: /actuator
```

### 权重配置

```java
@Service
public class NacosWeightService {
    
    @Autowired
    private NacosService nacosService;
    
    public void setInstanceWeight(String serviceName, String ip, int port, double weight) {
        Instance instance = new Instance();
        instance.setIp(ip);
        instance.setPort(port);
        instance.setWeight(weight);
        
        nacosService.registerInstance(serviceName, instance);
    }
}
```

## 服务健康检查

### 心跳机制

```yaml
spring:
  cloud:
    nacos:
      discovery:
        heart-beat-interval: 5000   # 心跳间隔
        heart-beat-timeout: 15000   # 心跳超时
        ip-delete-timeout: 30000   # IP删除超时
```

### 临时实例 vs 永久实例

```yaml
spring:
  cloud:
    nacos:
      discovery:
        ephemeral: false  # 永久实例
```
