import os

from celery import Celery
from django.conf import settings

# 设置默认的Django设置模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_management.settings")

# 创建Celery应用实例
app = Celery("backend_management")

# 使用Django的设置来配置Celery
# namespace='CELERY'意味着所有与Celery相关的配置项都应该以CELERY_前缀开始
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有Django应用中的任务模块
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    """用于调试的示例任务"""
    print(f"Request: {self.request!r}")
