# 简化中间件堆栈定义
# 导入所有中间件
from .exception_middleware import (
    ExceptionHandlingMiddleware,
    RequestResponseLoggingMiddleware,
)
from .request_preprocessing import RequestPreprocessingMiddleware, APIResponseMiddleware
from .api_permission_middleware import APIPermissionMiddleware
from .whitelist_middleware import ApiWhiteListMiddleware
from .auth_middleware import AuthenticationMiddleware, CORSHeadersMiddleware
from .websocket_middleware import JWTTokenAuthMiddleware


# WebSocket认证中间件堆栈
def JWTAuthMiddlewareStack(inner):
    # 直接返回传入的应用，不做任何中间件处理
    # 实际的WebSocket认证由JWTTokenAuthMiddleware处理
    return inner


# 导出所有中间件类
__all__ = [
    "ExceptionHandlingMiddleware",
    "RequestResponseLoggingMiddleware",
    "RequestPreprocessingMiddleware",
    "APIResponseMiddleware",
    "APIPermissionMiddleware",
    "ApiWhiteListMiddleware",
    "AuthenticationMiddleware",
    "CORSHeadersMiddleware",
    "JWTTokenAuthMiddleware",
    "JWTAuthMiddlewareStack",
]
