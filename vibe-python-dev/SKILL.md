---
name: "vibe-python-dev"
description: "Python后端开发。用于创建企业级Python项目，功能完善、代码优化、代码检查也使用此技能。FastAPI/Flask框架，领域驱动设计，支持分布式部署。Invoke when user wants to build a Python project, improve existing codebase, or perform code review."
---

# Python企业级后端开发

基于Python的企业级后端开发规范，适用于Web API服务、数据处理系统、微服务架构。

## 适用场景

- Web API服务开发（FastAPI/Flask）
- 数据处理与分析系统
- 微服务架构项目
- 企业内部系统开发
- **后端功能完善**
- **代码优化重构**
- **代码质量检查**

## 使用场景说明

### 场景1：新项目开发
当用户需要创建一个新的Python项目时使用。

### 场景2：功能完善
当用户需要为现有项目添加新功能、修复Bug、完善业务逻辑时使用。遵循八步开发流程，确保代码质量。

### 场景3：代码优化
当用户需要对现有项目进行性能优化、代码重构、规范整改时使用。检查并应用性能规范和安全规范。

### 场景4：代码检查
当用户需要对代码进行质量检查、漏洞扫描、规范验证时使用。对照开发规范进行检查并给出改进建议。

---

## 一、技术栈

Python 3.11+ | FastAPI 0.109+ / Flask 3.0+ | SQLAlchemy 2.0+ / Tortoise-ORM | Pydantic v2 | Redis | Celery | Prometheus + Grafana

---

## 二、架构核心理念：分层架构 + 领域驱动

### 分层架构
```
Controller层（接口层） -> Service层（业务层） -> Repository层（数据层） -> Entity层（实体层）
```

### 领域驱动设计原则
按业务领域划分模块 | 聚合根管理领域对象 | 值对象不可变 | 领域事件驱动

---

## 三、框架约束

| 类型 | 推荐方案 |
|------|----------|
| Web框架 | FastAPI（推荐）/ Flask |
| ORM | SQLAlchemy 2.0 / Tortoise-ORM |
| 数据验证 | Pydantic v2 |
| 缓存 | Redis + aioredis |
| 任务队列 | Celery + Redis/RabbitMQ |
| 认证 | JWT + OAuth2 |
| 日志 | structlog |
| 配置 | pydantic-settings |

---

## 四、开发流程（八步法，核心约束，强制执行）

### Step 0: 读取需求清单（Requirement Analysis）- **必须执行**

#### 0.1 需求清单路径
```
docs/工作空间/01-项目管理/[项目名]/01-需求/需求清单.md
```

#### 0.2 读取步骤
1. **定位项目根目录**：从当前工作目录向上查找 `docs/工作空间/01-项目管理/`
2. **查找需求清单**：在 `[项目名]/01-需求/` 目录下找到 `需求清单.md`
3. **解析需求清单内容**：
   - 提取功能列表（按模块/子模块）
   - 提取API接口信息（路径、方法、参数、响应）
   - 提取非功能需求（性能、安全要求）

#### 0.3 API接口实现约束

- **URL必须与需求清单一致**：严格按照需求清单中的API设计实现
- **HTTP方法必须一致**：GET查询、POST创建、PUT更新、DELETE删除
- **请求参数必须一致**：Pydantic模型字段与需求清单匹配
- **响应结构必须一致**：响应模型字段与需求清单匹配

### Step 1: 参数校验（Validation）

使用Pydantic进行数据验证：

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class UserCreateDTO(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.lower()
```

### Step 2: 业务规则校验（Business Rules）

进行状态校验、权限校验、业务约束校验：

```python
from app.core.exceptions import BusinessException

async def validate_order_creation(dto: OrderCreateDTO, user: User) -> None:
    if user.status != UserStatus.ACTIVE:
        raise BusinessException("用户状态异常，无法下单")
    
    product = await product_repository.get_by_id(dto.product_id)
    if product.stock < dto.quantity:
        raise BusinessException("商品库存不足")
    
    if product.status != ProductStatus.ON_SALE:
        raise BusinessException("商品已下架")
```

### Step 3: 数据读写操作（Data Operations）

使用Repository模式进行数据操作：

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.deleted == False)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user
```

### Step 4: 缓存策略（Cache Strategy）

使用Redis进行缓存管理：

```python
import json
from typing import Optional, TypeVar, Type
from redis.asyncio import Redis
from app.core.config import settings

T = TypeVar('T')

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get(self, key: str, model: Type[T]) -> Optional[T]:
        data = await self.redis.get(key)
        if data is None:
            return None
        return model.model_validate_json(data)
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self.redis.setex(key, ttl, value.model_dump_json())
    
    async def delete(self, key: str) -> None:
        await self.redis.delete(key)
    
    async def get_or_set(
        self, 
        key: str, 
        model: Type[T], 
        factory: Callable[[], Awaitable[T]],
        ttl: int = 3600
    ) -> T:
        cached = await self.get(key, model)
        if cached is not None:
            return cached
        
        value = await factory()
        await self.set(key, value, ttl)
        return value
```

### Step 5: 事务管理（Transaction Management）

使用上下文管理器管理事务：

```python
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

@asynccontextmanager
async def transaction(session: AsyncSession):
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e

async def create_order(dto: OrderCreateDTO, session: AsyncSession) -> Order:
    async with transaction(session):
        order = Order(
            user_id=dto.user_id,
            product_id=dto.product_id,
            quantity=dto.quantity,
            total_price=dto.quantity * product.price
        )
        session.add(order)
        
        await product_repository.decrease_stock(
            session, dto.product_id, dto.quantity
        )
        
        return order
```

### Step 6: 事件发布（Event Publishing）

使用领域事件驱动：

```python
from dataclasses import dataclass
from typing import Callable, List, Dict, Any
from app.core.events import event_bus

@dataclass
class OrderCreatedEvent:
    order_id: int
    user_id: int
    product_id: int
    quantity: int
    total_price: float

async def create_order(dto: OrderCreateDTO) -> Order:
    order = await order_service.create(dto)
    
    await event_bus.publish(OrderCreatedEvent(
        order_id=order.id,
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_price=order.total_price
    ))
    
    return order

@event_bus.subscribe(OrderCreatedEvent)
async def handle_order_created(event: OrderCreatedEvent):
    await notification_service.send_order_confirmation(event.user_id, event.order_id)
    await statistics_service.update_daily_sales(event.total_price)
```

### Step 7: 结果封装（Result Wrapping）

统一响应格式：

```python
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    
    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "Result[T]":
        return cls(code=0, message=message, data=data)
    
    @classmethod
    def error(cls, code: int = 1, message: str = "error") -> "Result[T]":
        return cls(code=code, message=message, data=None)

class PageResult(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

from fastapi import APIRouter, Depends
from app.core.response import Result, PageResult

router = APIRouter()

@router.post("/users", response_model=Result[UserVO])
async def create_user(
    dto: UserCreateDTO,
    service: UserService = Depends()
) -> Result[UserVO]:
    user = await service.create(dto)
    return Result.success(UserVO.model_validate(user))

@router.get("/users/{user_id}", response_model=Result[UserVO])
async def get_user(
    user_id: int,
    service: UserService = Depends()
) -> Result[UserVO]:
    user = await service.get_by_id(user_id)
    return Result.success(UserVO.model_validate(user))
```

### Step 8: 异常处理（Exception Handling）

统一异常处理：

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    BusinessException, 
    ValidationException,
    NotFoundException,
    PermissionDeniedException
)

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None
        }
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "code": 404,
            "message": exc.message,
            "data": None
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal Server Error",
            "data": None
        }
    )
```

---

## 五、项目结构

### FastAPI项目结构

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
│   │   └── events.py              # 事件总线
│   ├── api/                       # API接口
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
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
│   │   ├── user.py
│   │   ├── order.py
│   │   └── product.py
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
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
│   │   └── email_tasks.py
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── cache.py
│       └── logger.py
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_users.py
│   └── test_orders.py
├── alembic/                       # 数据库迁移
│   ├── versions/
│   └── env.py
├── scripts/                       # 脚本
│   └── init_db.py
├── .env.example
├── .env
├── pyproject.toml                 # 项目配置
├── poetry.lock
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 六、代码规范

### 6.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写下划线 | `user_service.py` |
| 类名 | 大驼峰 | `UserService` |
| 函数/方法 | 小写下划线 | `get_user_by_id` |
| 常量 | 大写下划线 | `MAX_RETRY_COUNT` |
| 变量 | 小写下划线 | `user_count` |
| 私有属性 | 单下划线前缀 | `_internal_cache` |

### 6.2 类型注解

**强制使用类型注解**：

```python
from typing import Optional, List, Dict, Any, Union

def get_user(user_id: int) -> Optional[User]:
    ...

def create_users(users: List[UserCreateDTO]) -> List[User]:
    ...

def process_data(data: Dict[str, Any]) -> Union[Success, Failure]:
    ...
```

### 6.3 文档字符串

使用Google风格文档字符串：

```python
def calculate_order_total(
    items: List[OrderItem], 
    discount: Optional[float] = None
) -> float:
    """计算订单总金额.
    
    Args:
        items: 订单商品列表
        discount: 可选折扣率，范围0-1
    
    Returns:
        订单总金额
    
    Raises:
        ValueError: 当商品列表为空时
    
    Example:
        >>> items = [OrderItem(price=100, quantity=2)]
        >>> calculate_order_total(items, discount=0.9)
        180.0
    """
    if not items:
        raise ValueError("订单商品列表不能为空")
    
    total = sum(item.price * item.quantity for item in items)
    
    if discount is not None:
        total *= (1 - discount)
    
    return total
```

### 6.4 代码复杂度

- 方法长度不超过50行
- 圈复杂度不超过10
- 嵌套层级不超过3层
- 参数数量不超过5个

---

## 七、安全规范

### 7.1 SQL注入防护

使用ORM参数化查询：

```python
from sqlalchemy import select, text

async def get_user_by_email(email: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

async def search_users(keyword: str) -> List[User]:
    result = await session.execute(
        select(User).where(User.username.ilike(f"%{keyword}%"))
    )
    return result.scalars().all()
```

### 7.2 XSS防护

```python
from html import escape
from bleach import clean

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u']

def sanitize_html(content: str) -> str:
    """清理HTML内容，防止XSS攻击"""
    return clean(content, tags=ALLOWED_TAGS, strip=True)

def escape_output(content: str) -> str:
    """转义输出内容"""
    return escape(content)
```

### 7.3 敏感数据处理

```python
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """密码加密"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证"""
    return pwd_context.verify(plain_password, hashed_password)

def mask_phone(phone: str) -> str:
    """手机号脱敏"""
    if len(phone) != 11:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"

def mask_id_card(id_card: str) -> str:
    """身份证号脱敏"""
    if len(id_card) != 18:
        return id_card
    return f"{id_card[:6]}********{id_card[-4:]}"
```

### 7.4 JWT安全

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=2)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt
```

### 7.5 依赖注入安全

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await user_repository.get_by_id(session, user_id)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user
```

---

## 八、性能规范

### 8.1 数据库性能

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

async def get_orders_with_items(user_id: int) -> List[Order]:
    result = await session.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()

async def get_user_with_orders(user_id: int) -> Optional[User]:
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.orders))
    )
    return result.scalar_one_or_none()
```

### 8.2 缓存策略

```python
from functools import wraps
from typing import TypeVar, Callable
from app.utils.cache import cache_service

T = TypeVar('T')

def cached(
    key_prefix: str, 
    ttl: int = 3600,
    key_builder: Optional[Callable] = None
):
    """缓存装饰器"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}:{':'.join(map(str, args[1:]))}"
            
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

@cached(key_prefix="user", ttl=1800)
async def get_user_by_id(user_id: int) -> Optional[User]:
    return await user_repository.get_by_id(user_id)
```

### 8.3 异步处理

```python
import asyncio
from typing import List

async def batch_process(items: List[Any]) -> List[Any]:
    """批量并发处理"""
    semaphore = asyncio.Semaphore(10)
    
    async def process_with_limit(item: Any) -> Any:
        async with semaphore:
            return await process_item(item)
    
    tasks = [process_with_limit(item) for item in items]
    return await asyncio.gather(*tasks)

async def parallel_fetch(
    user_ids: List[int], 
    product_ids: List[int]
) -> tuple[List[User], List[Product]]:
    """并行获取多种数据"""
    users_task = get_users(user_ids)
    products_task = get_products(product_ids)
    
    users, products = await asyncio.gather(users_task, products_task)
    return users, products
```

### 8.4 连接池配置

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    echo=settings.DEBUG
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
```

---

## 九、日志规范

### 9.1 结构化日志

```python
import structlog
from app.core.config import settings

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if not settings.DEBUG 
            else structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.LOG_LEVEL)
    ),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def create_order(dto: OrderCreateDTO) -> Order:
    logger.info(
        "Creating order", 
        user_id=dto.user_id, 
        product_id=dto.product_id
    )
    
    try:
        order = await order_service.create(dto)
        logger.info(
            "Order created successfully", 
            order_id=order.id
        )
        return order
    except Exception as e:
        logger.error(
            "Failed to create order", 
            error=str(e),
            user_id=dto.user_id
        )
        raise
```

---

## 十、测试规范

### 10.1 单元测试

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.user import UserCreateDTO

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test@123456"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["username"] == "testuser"

@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get("/api/v1/users/99999")
    
    assert response.status_code == 404
```

### 10.2 测试覆盖率

```bash
pytest --cov=app --cov-report=html --cov-fail-under=80
```

---

## 十一、依赖管理

### pyproject.toml

```toml
[tool.poetry]
name = "app"
version = "0.1.0"
description = "Enterprise Python Application"
authors = ["Team <team@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
redis = {extras = ["hiredis"], version = "^5.0.0"}
pydantic = {extras = ["email"], version = "^2.5.0"}
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
structlog = "^24.1.0"
celery = "^5.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
httpx = "^0.26.0"
black = "^24.1.0"
ruff = "^0.1.0"
mypy = "^1.8.0"
pre-commit = "^3.6.0"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

---

## 十二、CI/CD

### Dockerfile

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --group appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 知识库

- 01-project-architecture.md - 项目架构设计
- 02-code-standards.md - 代码规范
- 03-security.md - 安全规范
- 04-performance.md - 性能优化
- 05-testing.md - 测试规范
