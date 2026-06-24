from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.stats_views import (
    SystemMonitorViewSet,
    RedisMonitorViewSet,
    DatabaseMonitorViewSet,
    ServiceMonitorViewSet
)

app_name = "monitor"

# 创建路由器
router = DefaultRouter()

# 注册系统监控相关视图集
router.register(r"system", SystemMonitorViewSet, basename="system_monitor")
router.register(r"redis", RedisMonitorViewSet, basename="redis_monitor")
router.register(r"database", DatabaseMonitorViewSet, basename="database_monitor")
router.register(r"service", ServiceMonitorViewSet, basename="service_monitor")

# API URL模式
urlpatterns = [
    path("api/", include(router.urls)),
]