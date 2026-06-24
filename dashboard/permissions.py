from rest_framework import permissions

from .models import MenuButton, Role


class RoleBasedPermission(permissions.BasePermission):
    """基于角色的权限验证
    检查用户是否拥有指定的角色
    """

    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []

    def has_permission(self, request, view):
        # 首先检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False

        # 如果用户是超级用户，直接通过
        if request.user.is_superuser:
            return True

        # 获取用户的所有角色
        user_roles = (
            request.user.profile.roles.all() if hasattr(request.user, "profile") else []
        )

        # 如果需要特定角色
        if self.required_roles:
            # 检查用户是否拥有任意一个所需角色
            for role in user_roles:
                if role.name in self.required_roles or role.key in self.required_roles:
                    return True
            return False

        # 默认允许所有已认证用户
        return True


class PermissionRequired(permissions.BasePermission):
    """基于具体权限的验证
    检查用户是否拥有访问特定API或执行特定操作的权限
    """

    def has_permission(self, request, view):
        # 首先检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False

        # 如果用户是超级用户，直接通过
        if request.user.is_superuser:
            return True

        # 获取用户的所有角色
        try:
            user_roles = (
                request.user.profile.roles.all()
                if hasattr(request.user, "profile")
                else []
            )

            # 检查API路径和请求方法
            for role in user_roles:
                for button in role.permissions.all():
                    if hasattr(button, "api") and button.api == request.path:
                        method_map = {0: "GET", 1: "POST", 2: "PUT", 3: "DELETE"}
                        if (
                            button.method is None
                            or method_map.get(button.method) == request.method
                        ):
                            return True

            # 默认拒绝
            return False
        except Exception:
            return False


class DataScopePermission(permissions.BasePermission):
    """基于数据权限范围的验证
    根据用户角色的数据权限范围限制可访问的数据
    """

    def has_permission(self, request, view):
        # 首先检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False

        # 如果用户是超级用户，直接通过
        if request.user.is_superuser:
            return True

        # 此权限类主要作用于has_object_permission和数据过滤
        # 这里总是返回True，因为实际的数据过滤在视图中实现
        return True

    def has_object_permission(self, request, view, obj):
        # 首先检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False

        # 如果用户是超级用户，直接通过
        if request.user.is_superuser:
            return True

        # 获取用户的所有角色
        user_roles = (
            request.user.profile.roles.all() if hasattr(request.user, "profile") else []
        )

        # 检查是否有角色拥有全部数据权限
        for role in user_roles:
            if role.data_range == 3:  # 全部数据权限
                return True

            # 仅本人数据权限
            if role.data_range == 0:
                # 检查对象是否有created_by字段，并且属于当前用户
                if hasattr(obj, "created_by") and obj.created_by == request.user:
                    return True
                # 检查对象是否属于当前用户（例如User对象）
                if hasattr(obj, "pk") and obj.pk == request.user.pk:
                    return True
                return False

            # 本部门及以下数据权限或本部门数据权限
            if (
                role.data_range in [1, 2]
                and hasattr(request.user, "profile")
                and request.user.profile.department
            ):
                # 检查对象是否有department字段
                if hasattr(obj, "department") and obj.department:
                    # 本部门数据权限
                    if role.data_range == 2:
                        return obj.department == request.user.profile.department
                    # 本部门及以下数据权限需要更复杂的部门树结构检查
                    # 这里简化处理，仅检查是否在同一部门
                    return (
                        obj.department == request.user.profile.department
                        or self._is_sub_department(
                            obj.department, request.user.profile.department
                        )
                    )

        # 默认拒绝
        return False

    def _is_sub_department(self, sub_dept, parent_dept):
        """检查sub_dept是否是parent_dept的子部门
        实际应用中可能需要根据部门表的结构实现
        """
        # 这里简化处理，实际应用中需要根据部门表的层级结构实现
        # 例如通过递归检查部门的父级是否等于parent_dept
        return False


class AdminPermission(RoleBasedPermission):
    """管理员权限验证
    检查用户是否为管理员角色
    """

    def __init__(self):
        super().__init__(["admin"])

    def has_permission(self, request, view):
        # 首先检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False

        # 如果用户是超级用户，直接通过
        if request.user.is_superuser:
            return True

        # 检查用户是否有管理员角色
        try:
            user_roles = (
                request.user.profile.roles.all()
                if hasattr(request.user, "profile")
                else []
            )
            return any(role.admin for role in user_roles)
        except Exception:
            return False


class CustomDjangoModelPermission(permissions.DjangoModelPermissions):
    """自定义的Django模型权限
    扩展默认的Django模型权限，增加对LIST操作的支持
    """

    # 定义权限映射
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class SafeMethodPermission(permissions.BasePermission):
    """安全方法权限
    允许所有用户访问GET、HEAD、OPTIONS请求，其他请求需要认证
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
