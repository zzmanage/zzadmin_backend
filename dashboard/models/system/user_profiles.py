from django.contrib.auth.models import User
from django.db import models
from .base import BaseModel
from .departments import Department
from .roles import Role


class UserProfile(BaseModel):
    """用户扩展信息模型"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="用户"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="所属部门",
    )
    roles = models.ManyToManyField(Role, blank=True, verbose_name="角色")
    mobile = models.CharField(
        max_length=11, null=True, blank=True, verbose_name="手机号码"
    )
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="头像"
    )

    employee_no = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        verbose_name="工号",
    )
    name = models.CharField(
        max_length=40, verbose_name="姓名", help_text="姓名", null=True, blank=True
    )

    GENDER_CHOICES = (
        (0, "未知"),
        (1, "男"),
        (2, "女"),
    )
    gender = models.IntegerField(
        choices=GENDER_CHOICES,
        default=0,
        verbose_name="性别",
        null=True,
        blank=True,
        help_text="性别",
    )

    USER_TYPE = (
        (0, "后台用户"),
        (1, "前台用户"),
    )
    user_type = models.IntegerField(
        choices=USER_TYPE,
        default=0,
        verbose_name="用户类型",
        null=True,
        blank=True,
        help_text="用户类型",
    )

    post = models.ForeignKey(
        "Post",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="关联岗位",
        help_text="关联岗位",
    )
    last_token = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="最后一次登录Token"
    )

    class Meta:
        verbose_name = "用户扩展信息"
        verbose_name_plural = "用户扩展信息管理"
        ordering = ["id"]

    def __str__(self):
        return f'{self.user.username} - {self.name or "未设置姓名"}'
