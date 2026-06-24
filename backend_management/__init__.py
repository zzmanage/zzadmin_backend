# 确保在Django启动时初始化Celery应用
from .celery import app as celery_app

__all__ = ("celery_app",)
