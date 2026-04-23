# 测试规范

## 一、测试策略

### 1.1 测试金字塔

```
        ┌───────────┐
        │   E2E     │  少量端到端测试
        ├───────────┤
        │ Integration│  适量集成测试
        ├───────────┤
        │   Unit     │  大量单元测试
        └───────────┘
```

### 1.2 测试覆盖率要求

| 测试类型 | 覆盖率要求 |
|----------|------------|
| 单元测试 | >= 80% |
| 集成测试 | >= 60% |
| 总体覆盖率 | >= 70% |

---

## 二、单元测试

### 2.1 测试结构

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.user_service import UserService
from app.schemas.user import UserCreateDTO

class TestUserService:
    """用户服务测试类."""
    
    @pytest.fixture
    def mock_repository(self):
        """模拟数据访问对象."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_cache(self):
        """模拟缓存服务."""
        return AsyncMock()
    
    @pytest.fixture
    def user_service(self, mock_repository, mock_cache):
        """创建用户服务实例."""
        return UserService(mock_repository, mock_cache)
    
    @pytest.mark.asyncio
    async def test_create_user_success(
        self, 
        user_service, 
        mock_repository
    ):
        """测试创建用户成功."""
        dto = UserCreateDTO(
            username="testuser",
            email="test@example.com",
            password="Test@123456"
        )
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = dto.username
        mock_user.email = dto.email
        
        mock_repository.find_by_username.return_value = None
        mock_repository.find_by_email.return_value = None
        mock_repository.create.return_value = mock_user
        
        result = await user_service.create(dto)
        
        assert result.id == 1
        assert result.username == dto.username
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self, 
        user_service, 
        mock_repository
    ):
        """测试创建用户时用户名重复."""
        dto = UserCreateDTO(
            username="existinguser",
            email="test@example.com",
            password="Test@123456"
        )
        
        existing_user = MagicMock()
        mock_repository.find_by_username.return_value = existing_user
        
        with pytest.raises(BusinessException) as exc_info:
            await user_service.create(dto)
        
        assert "用户名已存在" in str(exc_info.value)
```

### 2.2 测试命名规范

```python
def test_<method>_<scenario>_<expected_result>():
    ...

class TestUserService:
    async def test_create_user_with_valid_data_returns_user():
        ...
    
    async def test_create_user_with_duplicate_username_raises_exception():
        ...
    
    async def test_get_user_by_id_when_not_found_returns_none():
        ...
```

### 2.3 测试数据管理

```python
import pytest
from app.models.user import User, UserStatus

@pytest.fixture
def sample_user():
    """示例用户数据."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        status=UserStatus.ACTIVE
    )

@pytest.fixture
def sample_users():
    """示例用户列表."""
    return [
        User(id=1, username="user1", email="user1@example.com"),
        User(id=2, username="user2", email="user2@example.com"),
        User(id=3, username="user3", email="user3@example.com"),
    ]

class TestUserService:
    @pytest.mark.asyncio
    async def test_get_all_users(
        self, 
        user_service, 
        mock_repository,
        sample_users
    ):
        mock_repository.find_all.return_value = sample_users
        
        result = await user_service.get_all()
        
        assert len(result) == 3
        assert result[0].username == "user1"
```

---

## 三、集成测试

### 3.1 测试客户端配置

```python
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base
from app.api.deps import get_session

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def session(test_engine):
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
async def client(session):
    async def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()
```

### 3.2 API测试

```python
import pytest
from httpx import AsyncClient

class TestUserAPI:
    """用户API集成测试."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient):
        """测试创建用户API."""
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
        assert data["data"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self, 
        client: AsyncClient
    ):
        """测试创建重复用户名."""
        user_data = {
            "username": "duplicateuser",
            "email": "test1@example.com",
            "password": "Test@123456"
        }
        
        await client.post("/api/v1/users", json=user_data)
        
        user_data["email"] = "test2@example.com"
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_get_user(self, client: AsyncClient):
        """测试获取用户API."""
        create_response = await client.post(
            "/api/v1/users",
            json={
                "username": "gettest",
                "email": "gettest@example.com",
                "password": "Test@123456"
            }
        )
        user_id = create_response.json()["data"]["id"]
        
        response = await client.get(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == user_id
        assert data["data"]["username"] == "gettest"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient):
        """测试获取不存在的用户."""
        response = await client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_users(self, client: AsyncClient):
        """测试获取用户列表."""
        for i in range(5):
            await client.post(
                "/api/v1/users",
                json={
                    "username": f"listuser{i}",
                    "email": f"listuser{i}@example.com",
                    "password": "Test@123456"
                }
            )
        
        response = await client.get("/api/v1/users?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 5
        assert len(data["data"]["items"]) >= 5
```

### 3.3 认证测试

```python
import pytest
from httpx import AsyncClient
from app.core.security import AuthService

class TestAuthentication:
    """认证测试."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """测试登录成功."""
        await client.post(
            "/api/v1/users",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "Test@123456"
            }
        )
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "Test@123456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient):
        """测试登录密码错误."""
        await client.post(
            "/api/v1/users",
            json={
                "username": "wrongpass",
                "email": "wrongpass@example.com",
                "password": "Test@123456"
            }
        )
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "wrongpass",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(
        self, 
        client: AsyncClient
    ):
        """测试带Token访问受保护接口."""
        await client.post(
            "/api/v1/users",
            json={
                "username": "protected",
                "email": "protected@example.com",
                "password": "Test@123456"
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "protected",
                "password": "Test@123456"
            }
        )
        token = login_response.json()["data"]["access_token"]
        
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["username"] == "protected"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(
        self, 
        client: AsyncClient
    ):
        """测试无Token访问受保护接口."""
        response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 401
```

---

## 四、测试工具

### 4.1 pytest配置

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    asyncio: mark test as async
    unit: mark test as unit test
    integration: mark test as integration test
    slow: mark test as slow running
```

### 4.2 conftest.py

```python
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.core.database import async_session
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers():
    def _auth_headers(user_id: int) -> dict:
        token = AuthService.create_access_token({"sub": user_id})
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers
```

### 4.3 Mock工具

```python
from unittest.mock import AsyncMock, MagicMock, patch

def create_mock_user(**kwargs):
    """创建模拟用户对象."""
    defaults = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "status": "active"
    }
    defaults.update(kwargs)
    return MagicMock(**defaults)

def create_mock_repository():
    """创建模拟数据访问对象."""
    repo = AsyncMock()
    repo.find_by_id.return_value = None
    repo.find_all.return_value = []
    repo.create.return_value = None
    repo.update.return_value = None
    repo.delete.return_value = None
    return repo

@pytest.fixture
def mock_user_repository():
    with patch("app.repositories.user_repository.UserRepository") as mock:
        yield mock
```

---

## 五、测试覆盖率

### 5.1 覆盖率配置

```toml
[tool.coverage.run]
source = ["app"]
branch = true
omit = [
    "app/tests/*",
    "app/core/config.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 70
```

### 5.2 运行测试

```bash
pytest --cov=app --cov-report=html --cov-report=term

pytest -m unit
pytest -m integration
pytest -m "not slow"
```

---

## 六、测试最佳实践

### 6.1 测试原则

- **独立性**：每个测试应该独立运行
- **可重复性**：多次运行结果一致
- **快速性**：单元测试应该快速执行
- **可读性**：测试代码应该清晰易懂

### 6.2 测试清单

- [ ] 每个公开方法都有测试
- [ ] 测试正常情况
- [ ] 测试边界条件
- [ ] 测试异常情况
- [ ] 测试覆盖率达标
- [ ] 测试命名清晰
- [ ] 测试数据隔离

### 6.3 常见测试模式

```python
class TestUserService:
    """测试模式示例."""
    
    @pytest.mark.asyncio
    async def test_happy_path(self, user_service, mock_repository):
        """正常流程测试."""
        ...
    
    @pytest.mark.asyncio
    async def test_edge_case(self, user_service, mock_repository):
        """边界条件测试."""
        ...
    
    @pytest.mark.asyncio
    async def test_error_case(self, user_service, mock_repository):
        """异常情况测试."""
        ...
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("input,expected", [
        ("valid@email.com", True),
        ("invalid-email", False),
        ("", False),
    ])
    async def test_email_validation(
        self, 
        user_service, 
        input, 
        expected
    ):
        """参数化测试."""
        result = user_service._validate_email(input)
        assert result == expected
```
