# 后端异常处理机制说明

## 1. 当前实现

系统采用**全局中间件 + DRF默认机制**的异常处理方案，简洁高效。

### 1.1 全局异常中间件

**文件**: `dashboard/middleware/exception_middleware.py`

```python
class ExceptionHandlingMiddleware:
    """异常处理中间件 - 统一处理API请求中的异常"""

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # 记录异常详情
            logger.error(f"请求 {request.path} 发生异常: {str(e)}")
            logger.error(traceback.format_exc())

            # 对API请求返回JSON格式的错误响应
            if request.path.startswith('/api/'):
                if isinstance(e, PermissionError):
                    return JsonResponse({
                        'code': status.HTTP_403_FORBIDDEN,
                        'message': '权限不足',
                        'path': request.path,
                        'error': str(e),
                    }, status=status.HTTP_403_FORBIDDEN)
                elif isinstance(e, ValueError):
                    return JsonResponse({
                        'code': status.HTTP_400_BAD_REQUEST,
                        'message': '请求参数错误',
                        'data': {'path': request.path, 'error': str(e)}
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return JsonResponse({
                        'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                        'message': '服务器内部错误',
                        'data': {'path': request.path, 'error': str(e) if settings.DEBUG else 'Internal Server Error'}
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                raise
```

### 1.2 异常响应格式

| 异常类型 | HTTP状态码 | 响应格式 |
|----------|------------|----------|
| PermissionError | 403 | `{"code": 403, "message": "权限不足", "path": "...", "error": "..."}` |
| ValueError | 400 | `{"code": 400, "message": "请求参数错误", "data": {...}}` |
| 其他异常 | 500 | `{"code": 500, "message": "服务器内部错误", "data": {...}}` |

## 2. 中间件注册

中间件注册在 `backend_management/settings.py` 的 `MIDDLEWARE` 中：

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'dashboard.middleware.tenant_middleware.TenantMiddleware',
    'dashboard.middleware.auth_middleware.AuthMiddleware',
    'dashboard.middleware.exception_middleware.ExceptionHandlingMiddleware',
    'dashboard.middleware.exception_middleware.RequestResponseLoggingMiddleware',
    'dashboard.middleware.request_preprocessing.RequestPreprocessingMiddleware',
    'dashboard.middleware.whitelist_middleware.WhiteListMiddleware',
    # ...
]
```

## 3. 请求日志中间件

**文件**: `dashboard/middleware/exception_middleware.py`

```python
class RequestResponseLoggingMiddleware:
    """请求响应日志中间件 - 记录请求和响应的详细信息"""

    def __call__(self, request):
        # 记录请求开始
        logger.info(f"请求开始: {request.method} {request.path}")
        # 处理请求...
        # 记录响应
        logger.info(f"请求完成: {request.method} {request.path} - {response.status_code}")
```

## 4. DRF 默认异常处理

Django REST Framework 自带异常处理机制，处理以下异常：
- `ValidationError` - 400
- `NotFound` - 404
- `PermissionDenied` - 403
- `AuthenticationFailed` - 401

## 5. 设计原则

1. **单一职责**: 异常处理统一由中间件负责
2. **统一格式**: 所有API错误返回一致的JSON格式
3. **安全第一**: 生产环境不暴露内部错误详情
4. **分级处理**: 根据异常类型返回适当的HTTP状态码

## 6. 注意事项

- 中间件只处理 `/api/` 路径的请求
- 非API请求的异常由Django默认处理
- `settings.DEBUG=False` 时不返回详细错误信息
