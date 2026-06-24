"""
WebSocket路由配置
"""

from django.urls import path


def get_websocket_urlpatterns():
    """
    延迟加载WebSocket路由，避免在Django应用初始化前导入模型导致的错误
    """
    # 在函数内部导入，确保Django应用已完全初始化
    from .consumers import NotificationConsumer
    return [
        path("ws/notifications/", NotificationConsumer.as_asgi()),
    ]

# 立即执行函数以保持原有接口兼容性
websocket_urlpatterns = get_websocket_urlpatterns()
