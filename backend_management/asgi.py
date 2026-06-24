"""
ASGI config for backend_management project.

It exposes the ASGI callable as a module-level variable named ``application``.

重要说明：此配置同时支持处理HTTP请求和WebSocket请求，可以在生产环境中使用单一的Daphne服务运行整个应用。

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# 设置Django设置模块环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_management.settings")

# 初始化Django ASGI应用 - 用于处理HTTP请求
django_asgi_app = get_asgi_application()

# 在Django应用初始化后再导入WebSocket路由配置
from dashboard.routing import websocket_urlpatterns

# 完整的ASGI应用，同时处理HTTP请求和WebSocket请求
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # WebSocket支持已启用，配置了认证中间件和URL路由
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
