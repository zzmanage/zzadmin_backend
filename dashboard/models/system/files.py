from django.contrib.auth.models import User
from django.db import models
from .base import BaseModel
from .departments import Department


class File(BaseModel):
    """文件模型"""

    name = models.CharField(
        max_length=255, verbose_name="文件名称", help_text="文件名称"
    )
    file = models.FileField(
        upload_to="files/%Y/%m/%d", verbose_name="文件路径", help_text="文件路径"
    )
    file_type = models.CharField(
        max_length=100,
        verbose_name="文件类型",
        help_text="文件类型",
        null=True,
        blank=True,
    )
    size = models.IntegerField(
        verbose_name="文件大小(字节)", help_text="文件大小(字节)"
    )
    description = models.TextField(
        verbose_name="文件描述", help_text="文件描述", null=True, blank=True
    )
    uploader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="上传用户",
        help_text="上传用户",
    )

    CATEGORY_CHOICES = (
        (0, "文档"),
        (1, "图片"),
        (2, "视频"),
        (3, "音频"),
        (4, "压缩包"),
        (5, "其他"),
    )
    category = models.IntegerField(
        choices=CATEGORY_CHOICES,
        default=5,
        verbose_name="文件分类",
        help_text="文件分类",
    )

    PERMISSION_CHOICES = (
        (0, "私有"),
        (1, "部门可见"),
        (2, "公开"),
    )
    permission = models.IntegerField(
        choices=PERMISSION_CHOICES,
        default=0,
        verbose_name="访问权限",
        help_text="访问权限",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联部门",
        help_text="关联部门",
    )

    download_count = models.IntegerField(
        default=0, verbose_name="下载次数", help_text="下载次数"
    )
    last_download_time = models.DateTimeField(
        null=True, blank=True, verbose_name="最后下载时间", help_text="最后下载时间"
    )

    class Meta:
        verbose_name = "文件"
        verbose_name_plural = "文件管理"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.file and not self.file_type:
            if '.' in self.file.name:
                self.file_type = self.file.name.split(".")[-1].lower()
            else:
                self.file_type = "unknown"

        if self.file and not self.size:
            try:
                self.size = self.file.size
                super().save(*args, **kwargs)
            except (OSError, ValueError):
                if not self.pk:
                    super().save(*args, **kwargs)
                    self.size = self.file.size
                    kwargs.pop('force_insert', None)
                    kwargs.pop('force_update', None)
                    super().save(update_fields=['size'], **kwargs)
                else:
                    super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
