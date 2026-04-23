# 项目架构设计

## 一、架构概述

### 1.1 什么是企业级Python架构

企业级Python架构是一种遵循最佳实践、具备高可维护性、高可扩展性的软件架构模式。它强调分层设计、依赖注入、领域驱动等现代软件工程原则。

### 1.2 企业级架构的优势

- **可维护性**：清晰的分层结构，职责分离
- **可测试性**：依赖注入，易于Mock
- **可扩展性**：模块化设计，易于添加新功能
- **团队协作**：统一规范，降低沟通成本

### 1.3 何时选择Python企业级架构

- 团队规模 >= 3人
- 项目周期长，需要长期维护
- 业务复杂度高，需要清晰的架构边界
- 对代码质量和可测试性有要求
- 需要支持高并发、高性能场景

---

## 二、分层架构

### 2.1 核心理念

**四层架构**：
- API层（Controller）：接收请求、参数校验、结果封装
- Service层：业务逻辑、事务管理、事件发布
- Repository层：数据访问、缓存操作
- Model层：数据模型、ORM映射

### 2.2 分层原则

1. **单向依赖**：上层依赖下层，下层不依赖上层
2. **接口隔离**：层与层之间通过接口通信
3. **职责单一**：每层只负责自己的职责
4. **依赖倒置**：高层模块不依赖低层模块，都依赖抽象

### 2.3 各层职责

| 层级 | 职责 | 示例 |
|------|------|------|
| API层 | 接收HTTP请求、参数校验、调用Service、封装响应 | `UserController` |
| Service层 | 业务逻辑处理、事务管理、缓存操作、事件发布 | `UserService` |
| Repository层 | 数据库操作、ORM映射、缓存读写 | `UserRepository` |
| Model层 | 数据模型定义、表映射关系 | `User` |

---

## 三、项目结构设计

### 3.1 标准项目结构

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   ├── core/                      # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理
│   │   ├── security.py            # 安全模块
│   │   ├── exceptions.py          # 异常定义
│   │   ├── events.py              # 事件总线
│   │   └── dependencies.py        # 依赖注入
│   ├── api/                       # API接口
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py
│   │   │   │   ├── orders.py
│   │   │   │   └── products.py
│   │   │   └── router.py
│   │   └── deps.py                # 依赖注入
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py                # 基础模型
│   │   ├── user.py
│   │   ├── order.py
│   │   └── product.py
│   ├── schemas/                   # Pydantic模型
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── order.py
│   │   └── product.py
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_service.py
│   │   ├── order_service.py
│   │   └── product_service.py
│   ├── repositories/              # 数据访问
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_repository.py
│   │   └── order_repository.py
│   ├── tasks/                     # Celery任务
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── email_tasks.py
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── cache.py
│       ├── logger.py
│       └── helpers.py
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_user_service.py
│   │   └── test_order_service.py
│   └── integration/
│       ├── test_users_api.py
│       └── test_orders_api.py
├── alembic/                       # 数据库迁移
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── scripts/                       # 脚本
│   ├── init_db.py
│   └── seed_data.py
├── .env.example
├── .env
├── pyproject.toml
├── poetry.lock
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 3.2 核心模块职责

| 模块 | 职责 |
|------|------|
| core | 配置管理、安全认证、异常定义、事件总线 |
| api | HTTP接口定义、路由配置、依赖注入 |
| models | SQLAlchemy模型定义、表映射 |
| schemas | Pydantic模型定义、数据验证、序列化 |
| services | 业务逻辑实现、事务管理 |
| repositories | 数据库操作、缓存管理 |
| tasks | 异步任务定义、定时任务 |
| utils | 通用工具函数、辅助类 |

---

## 四、依赖注入

### 4.1 FastAPI依赖注入

```python
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_user_repository(
    session: AsyncSession = Depends(get_session)
) -> UserRepository:
    return UserRepository(session)

def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(repository)

@router.post("/users")
async def create_user(
    dto: UserCreateDTO,
    service: UserService = Depends(get_user_service)
):
    return await service.create(dto)
```

### 4.2 依赖注入优势

- **解耦**：组件之间通过接口依赖，降低耦合
- **可测试**：易于Mock依赖进行单元测试
- **可配置**：通过配置切换不同实现
- **生命周期管理**：自动管理资源创建和销毁

---

## 五、配置管理

### 5.1 Pydantic Settings

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Enterprise API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 2
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### 5.2 多环境配置

```python
from app.core.config import Settings

class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

class TestingSettings(Settings):
    DATABASE_URL: str = "postgresql+asyncpg://test:test@localhost/test_db"

def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "development")
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings
    }
    return settings_map[env]()
```

---

## 六、数据库设计

### 6.1 基础模型

```python
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    deleted = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

### 6.2 用户模型示例

```python
from sqlalchemy import Column, String, Enum
from app.models.base import BaseModel
import enum

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    status = Column(
        Enum(UserStatus), 
        default=UserStatus.ACTIVE, 
        nullable=False
    )
    avatar = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
```

---

## 七、API版本管理

### 7.1 版本化路由

```python
from fastapi import APIRouter
from app.api.v1.endpoints import users, orders, products

api_router = APIRouter()

api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["users"]
)
api_router.include_router(
    orders.router, 
    prefix="/orders", 
    tags=["orders"]
)
api_router.include_router(
    products.router, 
    prefix="/products", 
    tags=["products"]
)
```

### 7.2 主应用配置

```python
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")
```

---

## 八、中间件配置

### 8.1 CORS中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.2 请求日志中间件

```python
from fastapi import Request
import time
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time, 2)
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

---

## 九、部署架构

### 9.1 单机部署

适用于开发、测试环境：
- 应用 + PostgreSQL + Redis 部署在同一服务器
- 使用Nginx反向代理

### 9.2 分布式部署

适用于生产环境：
- 应用多实例部署（负载均衡）
- PostgreSQL主从分离
- Redis集群或哨兵模式

### 9.3 部署拓扑

```
                    ┌──────────────┐
                    │    Nginx     │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
      ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
      │ App 1   │    │ App 2   │    │ App 3   │
      └────┬────┘    └────┬────┘    └────┬────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
     │PostgreSQL│    │  Redis  │     │ Celery  │
     │ Master  │     │ Cluster │     │ Workers │
     └─────────┘     └─────────┘     └─────────┘
```

---

## 十、监控与日志

### 10.1 结构化日志

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

logger.info(
    "User created",
    user_id=user.id,
    username=user.username,
    email=user.email
)
```

### 10.2 健康检查

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }

@router.get("/ready")
async def readiness_check(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    try:
        await session.execute(text("SELECT 1"))
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )
```
