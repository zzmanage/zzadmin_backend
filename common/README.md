# Common 模块

通用工具和基础组件库，提供统一响应、异常处理、视图基类、工具函数等。

## 目录结构

```
common/
├── __init__.py      # 统一导出
├── exceptions.py    # 异常类
├── response.py       # 统一响应
├── pagination.py    # 分页器
├── views.py         # 视图基类
├── handlers.py      # 异常处理器
├── utils/           # 工具函数
│   ├── cache.py
│   ├── date.py
│   └── string.py
└── README.md
```

## 快速使用

### 1. 统一响应

```python
from common import APIResponse

# 成功响应
return APIResponse.success(data={"id": 1}, message="创建成功")

# 错误响应
return APIResponse.error(message="参数错误", code=400)

# 分页响应
return APIResponse.paginated(data=results, total=100)
```

### 2. 异常处理

```python
from common import NotFoundError, ValidationError

raise NotFoundError("用户不存在")
raise ValidationError("用户名不能为空")
```

### 3. 视图基类

```python
from common import BaseViewSet
from .models import User
from .serializers import UserSerializer

class UserViewSet(BaseViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

### 4. 分页器

```python
from common import CustomPageNumberPagination

class UserViewSet(BaseViewSet):
    pagination_class = CustomPageNumberPagination
```

### 5. 工具函数

```python
from common import format_datetime, mask_phone, cache_decorator

# 日期格式化
format_datetime(now(), "%Y-%m-%d")

# 脱敏手机号
mask_phone("13812345678")  # "138****5678"

# 缓存装饰器
@cache_decorator(timeout=3600)
def get_data():
    return expensive_operation()
```

## 响应格式

**成功：**
```json
{"code": 200, "message": "操作成功", "data": {...}, "success": true}
```

**失败：**
```json
{"code": 400, "message": "操作失败", "data": null, "success": false}
```

**分页：**
```json
{
    "code": 200,
    "data": [...], 
    "success": true,
    "pagination": {
        "total": 100,
        "page": 1,
        "page_size": 10,
        "total_pages": 10
    }
}
```

## 异常类型

| 异常 | 状态码 | 说明 |
|------|--------|------|
| ValidationError | 400 | 验证失败 |
| AuthenticationError | 401 | 认证失败 |
| PermissionDenied | 403 | 权限不足 |
| NotFoundError | 404 | 资源不存在 |
| ConflictError | 409 | 资源冲突 |
| ServerError | 500 | 服务器错误 |
