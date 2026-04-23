# 性能优化

## 一、数据库性能优化

### 1.1 查询优化

**避免N+1查询**：

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload, subqueryload

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

**指定查询字段**：

```python
async def get_user_summaries() -> List[dict]:
    result = await session.execute(
        select(User.id, User.username, User.email)
        .where(User.deleted == False)
    )
    return [
        {"id": row.id, "username": row.username, "email": row.email}
        for row in result.all()
    ]
```

**批量操作**：

```python
async def batch_create_users(users: List[User]) -> List[User]:
    session.add_all(users)
    await session.commit()
    for user in users:
        await session.refresh(user)
    return users

async def batch_update_users(
    user_ids: List[int], 
    update_data: dict
) -> None:
    await session.execute(
        update(User)
        .where(User.id.in_(user_ids))
        .values(**update_data)
    )
    await session.commit()
```

### 1.2 索引优化

```python
from sqlalchemy import Index

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_user_status_created', 'status', 'created_at'),
        Index('idx_user_phone', 'phone'),
    )
```

### 1.3 分页优化

**传统分页**：

```python
async def get_users_page(
    page: int = 1, 
    page_size: int = 20
) -> PageResult[UserVO]:
    offset = (page - 1) * page_size
    
    count_result = await session.execute(
        select(func.count(User.id)).where(User.deleted == False)
    )
    total = count_result.scalar()
    
    result = await session.execute(
        select(User)
        .where(User.deleted == False)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()
    
    return PageResult(
        items=[UserVO.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
```

**游标分页**：

```python
async def get_users_cursor(
    cursor: Optional[int] = None,
    limit: int = 20
) -> CursorResult[UserVO]:
    query = select(User).where(User.deleted == False)
    
    if cursor:
        query = query.where(User.id < cursor)
    
    query = query.order_by(User.id.desc()).limit(limit + 1)
    
    result = await session.execute(query)
    users = result.scalars().all()
    
    has_more = len(users) > limit
    if has_more:
        users = users[:limit]
    
    next_cursor = users[-1].id if users and has_more else None
    
    return CursorResult(
        items=[UserVO.model_validate(u) for u in users],
        next_cursor=next_cursor,
        has_more=has_more
    )
```

---

## 二、缓存策略

### 2.1 Redis缓存

```python
from redis.asyncio import Redis
from typing import TypeVar, Type, Optional, Callable, Awaitable
import json

T = TypeVar('T')

class CacheService:
    """缓存服务."""
    
    def __init__(self, redis: Redis):
        self._redis = redis
    
    async def get(
        self, 
        key: str, 
        model: Type[T]
    ) -> Optional[T]:
        """获取缓存."""
        data = await self._redis.get(key)
        if data is None:
            return None
        return model.model_validate_json(data)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 3600
    ) -> None:
        """设置缓存."""
        await self._redis.setex(
            key, 
            ttl, 
            value.model_dump_json()
        )
    
    async def delete(self, key: str) -> None:
        """删除缓存."""
        await self._redis.delete(key)
    
    async def get_or_set(
        self, 
        key: str, 
        model: Type[T], 
        factory: Callable[[], Awaitable[T]],
        ttl: int = 3600
    ) -> T:
        """获取或设置缓存."""
        cached = await self.get(key, model)
        if cached is not None:
            return cached
        
        value = await factory()
        await self.set(key, value, ttl)
        return value
    
    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存."""
        keys = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            return await self._redis.delete(*keys)
        return 0
```

### 2.2 缓存装饰器

```python
from functools import wraps
from typing import Optional, Callable

def cached(
    key_prefix: str, 
    ttl: int = 3600,
    key_builder: Optional[Callable] = None
):
    """缓存装饰器."""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache: CacheService = kwargs.get('cache') or args[0]._cache
            
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                args_str = ':'.join(str(arg) for arg in args[1:])
                kwargs_str = ':'.join(f"{k}={v}" for k, v in kwargs.items())
                cache_key = f"{key_prefix}:{args_str}:{kwargs_str}"
            
            model = func.__annotations__.get('return')
            
            cached_value = await cache.get(cache_key, model)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

@cached(key_prefix="user", ttl=1800)
async def get_user_by_id(
    user_id: int, 
    cache: CacheService
) -> Optional[User]:
    return await user_repository.find_by_id(user_id)
```

### 2.3 缓存穿透防护

```python
async def get_user_with_cache(
    user_id: int, 
    cache: CacheService
) -> Optional[User]:
    """防止缓存穿透."""
    cache_key = f"user:{user_id}"
    
    cached = await cache.get(cache_key, User)
    if cached is not None:
        return cached
    
    user = await user_repository.find_by_id(user_id)
    
    if user is None:
        await cache._redis.setex(cache_key, 300, "NULL")
        return None
    
    await cache.set(cache_key, user, 1800)
    return user
```

### 2.4 缓存击穿防护

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def cache_lock(redis: Redis, key: str, timeout: int = 10):
    """缓存锁."""
    lock_key = f"lock:{key}"
    acquired = False
    
    try:
        acquired = await redis.set(lock_key, "1", nx=True, ex=timeout)
        if not acquired:
            await asyncio.sleep(0.1)
            acquired = await redis.set(lock_key, "1", nx=True, ex=timeout)
        
        yield acquired
    finally:
        if acquired:
            await redis.delete(lock_key)

async def get_hot_user(
    user_id: int, 
    cache: CacheService
) -> Optional[User]:
    """防止缓存击穿."""
    cache_key = f"user:{user_id}"
    
    cached = await cache.get(cache_key, User)
    if cached is not None:
        return cached
    
    async with cache_lock(cache._redis, cache_key) as acquired:
        if acquired:
            user = await user_repository.find_by_id(user_id)
            if user:
                await cache.set(cache_key, user, 1800)
            return user
        else:
            await asyncio.sleep(0.5)
            return await cache.get(cache_key, User)
```

---

## 三、异步处理

### 3.1 并发控制

```python
import asyncio
from typing import List, Any

async def batch_process(
    items: List[Any], 
    processor: Callable[[Any], Awaitable[Any]],
    concurrency: int = 10
) -> List[Any]:
    """批量并发处理."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process_with_limit(item: Any) -> Any:
        async with semaphore:
            return await processor(item)
    
    tasks = [process_with_limit(item) for item in items]
    return await asyncio.gather(*tasks)

async def parallel_fetch(
    user_ids: List[int], 
    product_ids: List[int]
) -> tuple[List[User], List[Product]]:
    """并行获取多种数据."""
    users_task = get_users(user_ids)
    products_task = get_products(product_ids)
    
    users, products = await asyncio.gather(users_task, products_task)
    return users, products
```

### 3.2 Celery异步任务

```python
from celery import Celery

celery_app = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task(bind=True, max_retries=3)
def send_email_task(
    self, 
    to: str, 
    subject: str, 
    body: str
) -> None:
    """异步发送邮件."""
    try:
        send_email(to, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@celery_app.task
def generate_report_task(user_id: int) -> str:
    """异步生成报告."""
    report = generate_user_report(user_id)
    return save_report(report)

async def create_order(dto: OrderCreateDTO) -> Order:
    order = await order_service.create(dto)
    
    send_email_task.delay(
        to=order.user.email,
        subject="订单创建成功",
        body=f"您的订单 {order.id} 已创建成功"
    )
    
    return order
```

---

## 四、连接池优化

### 4.1 数据库连接池

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
```

### 4.2 Redis连接池

```python
from redis.asyncio import Redis, ConnectionPool

redis_pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=50,
    decode_responses=False
)

async def get_redis() -> Redis:
    return Redis(connection_pool=redis_pool)
```

### 4.3 HTTP连接池

```python
import httpx

async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
    ) as client:
        yield client
```

---

## 五、性能监控

### 5.1 性能指标收集

```python
import time
from functools import wraps
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint']
)

def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            status = 200
            return result
        except HTTPException as e:
            status = e.status_code
            raise
        finally:
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=func.__name__,
                endpoint=func.__qualname__,
                status=status
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=func.__name__,
                endpoint=func.__qualname__
            ).observe(duration)
    
    return wrapper
```

### 5.2 慢查询日志

```python
import time
from sqlalchemy import event

SLOW_QUERY_THRESHOLD = 1.0

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    
    if total_time > SLOW_QUERY_THRESHOLD:
        logger.warning(
            "Slow query detected",
            query=statement,
            parameters=parameters,
            duration=total_time
        )
```

---

## 六、性能优化清单

### 6.1 数据库优化

- [ ] 避免N+1查询
- [ ] 使用索引优化查询
- [ ] 指定查询字段
- [ ] 使用批量操作
- [ ] 合理使用分页
- [ ] 优化连接池配置

### 6.2 缓存优化

- [ ] 热点数据缓存
- [ ] 防止缓存穿透
- [ ] 防止缓存击穿
- [ ] 防止缓存雪崩
- [ ] 设置合理过期时间

### 6.3 异步优化

- [ ] 使用异步IO
- [ ] 并发控制
- [ ] 异步任务处理
- [ ] 连接池复用

### 6.4 代码优化

- [ ] 减少循环嵌套
- [ ] 使用生成器
- [ ] 避免重复计算
- [ ] 使用高效数据结构
