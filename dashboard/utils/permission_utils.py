"""
权限工具模块
提供权限检查和验证功能
"""
from django.contrib.auth.models import Permission


class PermissionChecker:
    """权限检查器"""

    @staticmethod
    def has_permission(user, permission_codename):
        """
        检查用户是否具有指定权限
        :param user: 用户对象
        :param permission_codename: 权限代码名称
        :return: 是否具有权限
        """
        if user.is_superuser:
            return True

        # 检查用户直接拥有的权限
        if user.user_permissions.filter(codename=permission_codename).exists():
            return True

        # 检查用户角色拥有的权限
        for role in user.profile.roles.all():
            if role.permissions.filter(codename=permission_codename).exists():
                return True

        return False

    @staticmethod
    def has_permissions(user, permission_codenames):
        """
        检查用户是否具有多个权限中的任意一个
        :param user: 用户对象
        :param permission_codenames: 权限代码名称列表
        :return: 是否具有任一权限
        """
        if user.is_superuser:
            return True

        for codename in permission_codenames:
            if PermissionChecker.has_permission(user, codename):
                return True

        return False

    @staticmethod
    def has_all_permissions(user, permission_codenames):
        """
        检查用户是否具有所有指定权限
        :param user: 用户对象
        :param permission_codenames: 权限代码名称列表
        :return: 是否具有所有权限
        """
        if user.is_superuser:
            return True

        for codename in permission_codenames:
            if not PermissionChecker.has_permission(user, codename):
                return False

        return True

    @staticmethod
    def get_user_permissions(user):
        """
        获取用户的所有权限
        :param user: 用户对象
        :return: 权限列表
        """
        permissions = set()

        if user.is_superuser:
            # 超级用户拥有所有权限
            return list(Permission.objects.all())

        # 获取用户直接拥有的权限
        for perm in user.user_permissions.all():
            permissions.add(perm)

        # 获取用户角色拥有的权限
        for role in user.profile.roles.all():
            for perm in role.permissions.all():
                permissions.add(perm)

        return list(permissions)

    @staticmethod
    def get_user_permission_codenames(user):
        """
        获取用户的所有权限代码名称
        :param user: 用户对象
        :return: 权限代码名称列表
        """
        permissions = PermissionChecker.get_user_permissions(user)
        return [f"{perm.content_type.app_label}.{perm.codename}" for perm in permissions]