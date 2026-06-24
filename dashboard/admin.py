from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Department, MenuButton, OperationLog, Permission, Role, UserProfile

# Register your models here.


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("parent",)
    ordering = ("id",)
    raw_id_fields = ("parent",)


class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("id",)


class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "parent", "created_at", "updated_at")
    search_fields = ("name", "code")
    list_filter = ("parent",)
    ordering = ("id",)
    raw_id_fields = ("parent",)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "用户扩展信息"
    fk_name = "user"  # 指定使用user字段作为外键


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
    )


class OperationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "operation", "module", "ip_address", "created_at")
    search_fields = ("user__username", "operation", "module", "ip_address")
    list_filter = ("module", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("user", "operation", "module", "ip_address", "created_at")

    # 禁止删除操作日志
    def has_delete_permission(self, request, obj=None):
        return False


class MenuButtonAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "menu",
        "value",
        "api",
        "get_method_display",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "value", "api")
    list_filter = ("menu", "method")
    ordering = ("-created_at",)
    raw_id_fields = ("menu",)

    def get_method_display(self, obj):
        if obj.method is not None:
            return dict(MenuButton.METHOD_CHOICES).get(obj.method, "")
        return ""

    get_method_display.short_description = "请求方法"


# 注册模型
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(MenuButton, MenuButtonAdmin)
admin.site.register(OperationLog, OperationLogAdmin)

# 先取消注册默认的User模型，然后用我们自定义的UserAdmin注册
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
