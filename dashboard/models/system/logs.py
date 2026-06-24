from django.contrib.auth.models import User
from django.db import models
from .base import BaseModel


class OperationLog(BaseModel):
    """操作日志模型"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="操作用户")
    operation = models.CharField(max_length=200, verbose_name="操作内容")
    module = models.CharField(max_length=100, verbose_name="操作模块")
    ip_address = models.CharField(max_length=50, verbose_name="IP地址")

    action = models.CharField(
        max_length=50, verbose_name="操作类型", null=True, blank=True
    )
    model_name = models.CharField(
        max_length=100, verbose_name="模型名称", null=True, blank=True
    )
    model_id = models.IntegerField(verbose_name="模型ID", null=True, blank=True)
    details = models.TextField(verbose_name="操作详情", null=True, blank=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.operation} - {self.created_at}"


class LoginLog(BaseModel):
    """登录日志模型"""

    LOGIN_TYPE_CHOICES = (
        (1, "普通登录"),
        (2, "普通扫码登录"),
        (3, "微信扫码登录"),
        (4, "飞书扫码登录"),
        (5, "钉钉扫码登录"),
        (6, "短信登录"),
    )
    username = models.CharField(
        max_length=150,
        verbose_name="登录用户名",
        null=True,
        blank=True,
        help_text="登录用户名",
    )
    ip = models.CharField(
        max_length=32, verbose_name="登录ip", null=True, blank=True, help_text="登录ip"
    )
    agent = models.TextField(
        verbose_name="agent信息", null=True, blank=True, help_text="agent信息"
    )
    browser = models.CharField(
        max_length=200,
        verbose_name="浏览器名",
        null=True,
        blank=True,
        help_text="浏览器名",
    )
    os = models.CharField(
        max_length=200,
        verbose_name="操作系统",
        null=True,
        blank=True,
        help_text="操作系统",
    )
    continent = models.CharField(
        max_length=50, verbose_name="州", null=True, blank=True, help_text="州"
    )
    country = models.CharField(
        max_length=50, verbose_name="国家", null=True, blank=True, help_text="国家"
    )
    province = models.CharField(
        max_length=50, verbose_name="省份", null=True, blank=True, help_text="省份"
    )
    city = models.CharField(
        max_length=50, verbose_name="城市", null=True, blank=True, help_text="城市"
    )
    district = models.CharField(
        max_length=50, verbose_name="县区", null=True, blank=True, help_text="县区"
    )
    isp = models.CharField(
        max_length=50, verbose_name="运营商", null=True, blank=True, help_text="运营商"
    )
    area_code = models.CharField(
        max_length=50,
        verbose_name="区域代码",
        null=True,
        blank=True,
        help_text="区域代码",
    )
    country_english = models.CharField(
        max_length=50,
        verbose_name="英文全称",
        null=True,
        blank=True,
        help_text="英文全称",
    )
    country_code = models.CharField(
        max_length=50, verbose_name="简称", null=True, blank=True, help_text="简称"
    )
    longitude = models.CharField(
        max_length=50, verbose_name="经度", null=True, blank=True, help_text="经度"
    )
    latitude = models.CharField(
        max_length=50, verbose_name="纬度", null=True, blank=True, help_text="纬度"
    )
    login_type = models.IntegerField(
        default=1,
        choices=LOGIN_TYPE_CHOICES,
        verbose_name="登录类型",
        help_text="登录类型",
    )

    class Meta:
        verbose_name = "登录日志"
        verbose_name_plural = "登录日志管理"
        ordering = ("-created_at",)

    def __str__(self):
        login_type_display = dict(self.LOGIN_TYPE_CHOICES).get(
            self.login_type, "未知登录类型"
        )
        return f"{self.username} - {login_type_display} - {self.ip} - {self.created_at}"
