# 代码规范

## 一、命名规范

### 1.1 基本原则

- **有意义**：名称应该表达意图，避免无意义缩写
- **一致性**：整个项目保持命名风格一致
- **可读性**：易于理解和记忆

### 1.2 命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/包 | 小写下划线 | `user_service.py` |
| 类名 | 大驼峰（PascalCase） | `UserService` |
| 函数/方法 | 小写下划线 | `get_user_by_id` |
| 变量 | 小写下划线 | `user_count` |
| 常量 | 大写下划线 | `MAX_RETRY_COUNT` |
| 私有属性 | 单下划线前缀 | `_internal_cache` |
| 私有方法 | 单下划线前缀 | `_validate_input` |
| 保护属性 | 单下划线前缀 | `_protected_value` |
| 魔术方法 | 双下划线包围 | `__init__` |

### 1.3 命名示例

```python
MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30

class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository
        self._cache = {}
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self._repository.find_by_id(user_id)
    
    def _validate_email(self, email: str) -> bool:
        return "@" in email
```

---

## 二、类型注解

### 2.1 强制使用类型注解

**所有公开函数必须有类型注解**：

```python
from typing import Optional, List, Dict, Any, Union, TypeVar, Generic

def get_user(user_id: int) -> Optional[User]:
    ...

def create_users(users: List[UserCreateDTO]) -> List[User]:
    ...

def process_data(data: Dict[str, Any]) -> Union[Success, Failure]:
    ...

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None
```

### 2.2 类型注解最佳实践

```python
from typing import Optional, List, Callable, Awaitable

async def batch_process(
    items: List[Any],
    processor: Callable[[Any], Awaitable[Any]],
    concurrency: int = 10
) -> List[Any]:
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process_with_limit(item: Any) -> Any:
        async with semaphore:
            return await processor(item)
    
    tasks = [process_with_limit(item) for item in items]
    return await asyncio.gather(*tasks)
```

---

## 三、文档字符串

### 3.1 Google风格文档字符串

```python
def calculate_order_total(
    items: List[OrderItem], 
    discount: Optional[float] = None
) -> float:
    """计算订单总金额.
    
    根据订单商品列表计算总金额，支持可选折扣。
    
    Args:
        items: 订单商品列表，每个商品包含价格和数量
        discount: 可选折扣率，范围0-1，默认为None表示无折扣
    
    Returns:
        订单总金额，保留两位小数
    
    Raises:
        ValueError: 当商品列表为空时
        ValueError: 当折扣率不在0-1范围内时
    
    Example:
        >>> items = [OrderItem(price=100, quantity=2)]
        >>> calculate_order_total(items, discount=0.9)
        180.0
    """
    if not items:
        raise ValueError("订单商品列表不能为空")
    
    if discount is not None and not (0 <= discount <= 1):
        raise ValueError("折扣率必须在0-1范围内")
    
    total = sum(item.price * item.quantity for item in items)
    
    if discount is not None:
        total *= (1 - discount)
    
    return round(total, 2)
```

### 3.2 类文档字符串

```python
class UserService:
    """用户服务类.
    
    提供用户相关的业务逻辑处理，包括用户创建、查询、更新和删除。
    
    Attributes:
        repository: 用户数据访问对象
        cache: 缓存服务
    
    Example:
        >>> service = UserService(repository, cache)
        >>> user = await service.get_by_id(1)
        >>> print(user.username)
    """
    
    def __init__(
        self, 
        repository: UserRepository, 
        cache: CacheService
    ) -> None:
        """初始化用户服务.
        
        Args:
            repository: 用户数据访问对象
            cache: 缓存服务
        """
        self._repository = repository
        self._cache = cache
```

---

## 四、代码组织

### 4.1 导入顺序

```python
# 1. 标准库
import os
import sys
from typing import Optional, List
from datetime import datetime

# 2. 第三方库
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel, Field

# 3. 本地模块
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.models.user import User
from app.schemas.user import UserCreateDTO, UserVO
from app.repositories.user_repository import UserRepository
```

### 4.2 类组织顺序

```python
class UserService:
    """用户服务类."""
    
    # 类常量
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 30
    
    # 初始化方法
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository
    
    # 公有方法
    async def create(self, dto: UserCreateDTO) -> User:
        ...
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        ...
    
    # 私有方法
    def _validate_password(self, password: str) -> bool:
        ...
    
    def _hash_password(self, password: str) -> str:
        ...
```

---

## 五、代码复杂度

### 5.1 复杂度限制

- **方法长度**：不超过50行
- **圈复杂度**：不超过10
- **嵌套层级**：不超过3层
- **参数数量**：不超过5个

### 5.2 降低复杂度技巧

**使用早返回**：

```python
async def process_order(order_id: int) -> Order:
    order = await order_repository.get_by_id(order_id)
    
    if order is None:
        raise NotFoundException("订单不存在")
    
    if order.status != OrderStatus.PENDING:
        raise BusinessException("订单状态不正确")
    
    if order.expired:
        raise BusinessException("订单已过期")
    
    return await process_valid_order(order)
```

**提取方法**：

```python
async def create_order(dto: OrderCreateDTO) -> Order:
    await self._validate_order_creation(dto)
    order = await self._create_order_entity(dto)
    await self._update_inventory(dto)
    await self._publish_order_event(order)
    return order

async def _validate_order_creation(self, dto: OrderCreateDTO) -> None:
    ...

async def _create_order_entity(self, dto: OrderCreateDTO) -> Order:
    ...

async def _update_inventory(self, dto: OrderCreateDTO) -> None:
    ...

async def _publish_order_event(self, order: Order) -> None:
    ...
```

---

## 六、异常处理

### 6.1 自定义异常

```python
from typing import Optional

class AppException(Exception):
    """应用基础异常."""
    
    def __init__(
        self, 
        message: str, 
        code: int = 1,
        details: Optional[dict] = None
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class BusinessException(AppException):
    """业务异常."""
    pass

class ValidationException(AppException):
    """校验异常."""
    
    def __init__(self, message: str, field: str = "") -> None:
        super().__init__(message, code=400)
        self.field = field

class NotFoundException(AppException):
    """资源不存在异常."""
    
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, code=404)

class PermissionDeniedException(AppException):
    """权限拒绝异常."""
    
    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(message, code=403)
```

### 6.2 异常处理最佳实践

```python
async def get_user(user_id: int) -> User:
    try:
        user = await user_repository.get_by_id(user_id)
        
        if user is None:
            raise NotFoundException(f"用户 {user_id} 不存在")
        
        return user
    
    except NotFoundException:
        raise
    
    except DatabaseError as e:
        logger.error(f"数据库错误: {e}", user_id=user_id)
        raise AppException("系统繁忙，请稍后重试")
    
    except Exception as e:
        logger.exception(f"未知错误: {e}", user_id=user_id)
        raise AppException("系统错误")
```

---

## 七、代码复用

### 7.1 基础Repository

```python
from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """基础数据访问类."""
    
    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self._session = session
        self._model = model
    
    async def find_by_id(self, id: int) -> Optional[T]:
        result = await self._session.execute(
            select(self._model).where(
                self._model.id == id,
                self._model.deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def find_all(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[T]:
        result = await self._session.execute(
            select(self._model)
            .where(self._model.deleted == False)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
    
    async def update(self, entity: T) -> T:
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
    
    async def delete(self, entity: T) -> None:
        entity.deleted = True
        await self._session.commit()
```

### 7.2 具体Repository

```python
class UserRepository(BaseRepository[User]):
    """用户数据访问类."""
    
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)
    
    async def find_by_username(self, username: str) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(
                User.username == username,
                User.deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(
                User.email == email,
                User.deleted == False
            )
        )
        return result.scalar_one_or_none()
```

---

## 八、代码格式化工具

### 8.1 Black配置

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

### 8.2 Ruff配置

```toml
[tool.ruff]
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.isort]
known-first-party = ["app"]
```

### 8.3 MyPy配置

```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
```

---

## 九、代码审查清单

### 9.1 功能正确性

- [ ] 代码是否实现了需求功能
- [ ] 边界条件是否处理正确
- [ ] 错误处理是否完善
- [ ] 日志是否充分

### 9.2 代码质量

- [ ] 命名是否清晰有意义
- [ ] 是否有类型注解
- [ ] 是否有文档字符串
- [ ] 代码是否简洁易读

### 9.3 性能考虑

- [ ] 是否有N+1查询问题
- [ ] 是否使用了缓存
- [ ] 是否有性能瓶颈
- [ ] 数据库查询是否优化

### 9.4 安全考虑

- [ ] 是否有SQL注入风险
- [ ] 是否有XSS风险
- [ ] 敏感数据是否加密
- [ ] 权限校验是否完善
