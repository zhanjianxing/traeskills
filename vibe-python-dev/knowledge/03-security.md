# 安全规范

## 一、认证与授权

### 1.1 JWT认证

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """认证服务."""
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 2
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(
        plain_password: str, 
        hashed_password: str
    ) -> bool:
        """密码验证."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @classmethod
    def create_access_token(
        cls, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=cls.ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({
            "exp": expire, 
            "type": "access",
            "iat": datetime.utcnow()
        })
        
        return jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=cls.ALGORITHM
        )
    
    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        """创建刷新令牌."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire, 
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        
        return jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=cls.ALGORITHM
        )
    
    @classmethod
    def decode_token(cls, token: str) -> Optional[dict]:
        """解码令牌."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[cls.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
```

### 1.2 依赖注入认证

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import AuthService
from app.models.user import User, UserStatus

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """获取当前登录用户."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthService.decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    user_repository = UserRepository(session)
    user = await user_repository.find_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user
```

### 1.3 权限控制

```python
from functools import wraps
from typing import List, Callable
from fastapi import HTTPException, status

def require_permissions(permissions: List[str]):
    """权限装饰器."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未登录"
                )
            
            user_permissions = set(current_user.permissions)
            required_permissions = set(permissions)
            
            if not required_permissions.issubset(user_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@router.delete("/users/{user_id}")
@require_permissions(["user:delete"])
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    ...
```

---

## 二、SQL注入防护

### 2.1 使用ORM参数化查询

```python
from sqlalchemy import select, text

class UserRepository:
    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def search_by_username(self, keyword: str) -> List[User]:
        result = await self._session.execute(
            select(User).where(User.username.ilike(f"%{keyword}%"))
        )
        return result.scalars().all()
```

### 2.2 禁止字符串拼接SQL

```python
async def bad_example(user_input: str) -> List[User]:
    result = await self._session.execute(
        text(f"SELECT * FROM users WHERE username = '{user_input}'")
    )
    return result.scalars().all()

async def good_example(user_input: str) -> List[User]:
    result = await self._session.execute(
        text("SELECT * FROM users WHERE username = :username"),
        {"username": user_input}
    )
    return result.scalars().all()
```

---

## 三、XSS防护

### 3.1 输入过滤

```python
from html import escape
from bleach import clean

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'img']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt']
}

def sanitize_html(content: str) -> str:
    """清理HTML内容，防止XSS攻击."""
    return clean(
        content, 
        tags=ALLOWED_TAGS, 
        attributes=ALLOWED_ATTRIBUTES, 
        strip=True
    )

def escape_html(content: str) -> str:
    """转义HTML特殊字符."""
    return escape(content)
```

### 3.2 输出编码

```python
from fastapi.responses import JSONResponse
import json

def safe_json_response(data: dict) -> JSONResponse:
    """安全的JSON响应."""
    return JSONResponse(
        content=json.loads(json.dumps(data, ensure_ascii=False))
    )
```

---

## 四、敏感数据处理

### 4.1 密码安全

```python
from passlib.context import CryptContext
import secrets
import hashlib

pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    """密码加密."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_secure_token(length: int = 32) -> str:
    """生成安全随机令牌."""
    return secrets.token_hex(length)

def hash_sensitive_data(data: str, salt: str) -> str:
    """敏感数据哈希."""
    return hashlib.sha256(f"{data}{salt}".encode()).hexdigest()
```

### 4.2 数据脱敏

```python
def mask_phone(phone: str) -> str:
    """手机号脱敏."""
    if len(phone) != 11:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"

def mask_email(email: str) -> str:
    """邮箱脱敏."""
    if "@" not in email:
        return email
    username, domain = email.split("@")
    if len(username) <= 2:
        return f"{username[0]}***@{domain}"
    return f"{username[:2]}***@{domain}"

def mask_id_card(id_card: str) -> str:
    """身份证号脱敏."""
    if len(id_card) != 18:
        return id_card
    return f"{id_card[:6]}********{id_card[-4:]}"

def mask_bank_card(card_number: str) -> str:
    """银行卡号脱敏."""
    if len(card_number) < 8:
        return card_number
    return f"{card_number[:4]}****{card_number[-4:]}"

class UserVO(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None
    id_card: Optional[str] = None
    
    @field_serializer('phone')
    def serialize_phone(self, value: Optional[str]) -> Optional[str]:
        return mask_phone(value) if value else None
    
    @field_serializer('email')
    def serialize_email(self, value: Optional[str]) -> Optional[str]:
        return mask_email(value) if value else None
```

### 4.3 日志安全

```python
import structlog

logger = structlog.get_logger()

SENSITIVE_FIELDS = ['password', 'token', 'secret', 'key', 'card']

def sanitize_log_data(data: dict) -> dict:
    """清理日志中的敏感数据."""
    sanitized = {}
    for key, value in data.items():
        if any(field in key.lower() for field in SENSITIVE_FIELDS):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
    return sanitized

def safe_log(level: str, message: str, **kwargs):
    """安全日志记录."""
    sanitized_kwargs = sanitize_log_data(kwargs)
    getattr(logger, level)(message, **sanitized_kwargs)
```

---

## 五、API安全

### 5.1 请求限流

```python
from fastapi import Request, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    redis = Redis.from_url(settings.REDIS_URL)
    await FastAPILimiter.init(redis)

@router.get("/users")
@RateLimiter(times=100, seconds=60)
async def list_users(request: Request):
    ...
```

### 5.2 CORS配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)
```

### 5.3 安全头

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

## 六、文件上传安全

### 6.1 文件类型校验

```python
import magic
from pathlib import Path

ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> None:
    """校验上传文件."""
    if file.size > MAX_FILE_SIZE:
        raise ValidationException(f"文件大小不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB")
    
    content = file.file.read(2048)
    file.file.seek(0)
    
    mime_type = magic.from_buffer(content, mime=True)
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationException(f"不支持的文件类型: {mime_type}")

def generate_safe_filename(original_filename: str) -> str:
    """生成安全的文件名."""
    ext = Path(original_filename).suffix.lower()
    safe_name = secrets.token_hex(16)
    return f"{safe_name}{ext}"
```

### 6.2 文件存储安全

```python
import aiofiles
from pathlib import Path

UPLOAD_DIR = Path("uploads")

async def save_upload_file(
    file: UploadFile, 
    user_id: int
) -> str:
    """安全保存上传文件."""
    validate_file(file)
    
    safe_filename = generate_safe_filename(file.filename)
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = user_dir / safe_filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return str(file_path)
```

---

## 七、安全检查清单

### 7.1 认证安全

- [ ] 使用强密码哈希算法（bcrypt）
- [ ] JWT令牌设置合理过期时间
- [ ] 实现刷新令牌机制
- [ ] 登出时使令牌失效
- [ ] 实现登录失败锁定机制

### 7.2 授权安全

- [ ] 所有接口都有权限校验
- [ ] 数据权限校验（数据归属）
- [ ] 操作权限校验（角色权限）
- [ ] 避免越权访问

### 7.3 数据安全

- [ ] 敏感数据加密存储
- [ ] 敏感数据脱敏显示
- [ ] 日志不输出敏感信息
- [ ] 传输使用HTTPS

### 7.4 输入安全

- [ ] 所有输入进行校验
- [ ] 防止SQL注入
- [ ] 防止XSS攻击
- [ ] 防止CSRF攻击

### 7.5 接口安全

- [ ] 实现请求限流
- [ ] 配置安全响应头
- [ ] 正确配置CORS
- [ ] 文件上传安全校验
