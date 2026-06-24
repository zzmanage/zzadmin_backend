import re
import logging
from typing import Tuple, Optional, List

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

from dashboard.models import MenuButton, UserProfile
from dashboard.utils.common_utils import get_method_code

logger = logging.getLogger(__name__)


class APIPermissionMiddleware(MiddlewareMixin):
    """
    API权限验证中间件
    基于用户-角色-菜单-菜单按钮的关系，结合API请求的路径和方法进行权限验证
    支持通过settings中的API_PERMISSION_VALIDATION_ENABLED配置开关控制

    注意：白名单检查已经由ApiWhiteListMiddleware处理（在MIDDLEWARE配置中位于此类之前）
    因此，此类只需专注于核心权限验证功能

    核心功能:
    1. 支持通过settings开关控制权限验证启用状态
    2. 实现基于用户-角色-菜单-菜单按钮的权限验证逻辑
    3. 添加权限缓存，提高性能
    4. 提供缓存管理方法，与系统其他部分保持一致性
    """

    # 缓存相关配置
    CACHE_KEY_PREFIX = "api_permission_"
    CACHE_TIMEOUT = 300  # 5分钟
    CACHE_KEY_VERSION = f"{CACHE_KEY_PREFIX}version"
    CACHE_KEY_GLOBAL_VERSION = f"{CACHE_KEY_PREFIX}global_version"

    def process_request(self, request):
        """
        处理请求，进行API权限验证

        Args:
            request: HTTP请求对象

        Returns:
            None: 如果有权限或权限验证被禁用，继续处理请求
            Response: 如果没有权限，返回403 Forbidden响应
        """
        # 检查权限验证开关是否启用
        if not getattr(settings, "API_PERMISSION_VALIDATION_ENABLED", True):
            logger.debug(
                f"API权限验证已禁用，跳过权限检查: {request.method} {request.path}"
            )
            return None

        # 检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            # 未认证用户，不进行权限验证（认证失败的处理应该在认证中间件中完成）
            return None

        # 超级用户直接通过权限验证
        if request.user.is_superuser:
            logger.debug(
                f"超级用户 {request.user.username} 跳过权限检查: {request.method} {request.path}"
            )
            return None

        # 进行权限验证
        has_permission = self._check_permission(request)
        if not has_permission:
            logger.warning(
                f"用户 {request.user.username} 没有权限访问: {request.method} {request.path}"
            )
            return JsonResponse(
                {
                    "status": "error",
                    "message": "您没有访问该API的权限",
                    "path": request.path,
                    "method": request.method,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # 有权限，继续处理请求
        return None

    def _check_permission(self, request) -> bool:
        """
        检查用户是否有访问指定API的权限，使用缓存优化性能

        Args:
            request: HTTP请求对象

        Returns:
            bool: 如果用户有权限，返回True；否则返回False
        """
        try:
            # 获取请求的路径和方法
            path = request.path
            method = request.method
            user_id = request.user.id

            # 构建缓存键
            cache_key = f"{self.CACHE_KEY_PREFIX}{user_id}_{path}_{method}"

            # 检查版本标记，决定是否需要重新验证权限
            user_version = cache.get(f"{self.CACHE_KEY_VERSION}_{user_id}", 0)
            global_version = cache.get(self.CACHE_KEY_GLOBAL_VERSION, 0)

            # 从缓存键中提取保存的版本信息
            cached_version_info = cache.get(f"{cache_key}_version") or {
                "user": 0,
                "global": 0,
            }

            # 如果版本发生变化，需要重新验证权限
            if (
                user_version > cached_version_info["user"]
                or global_version > cached_version_info["global"]
            ):
                logger.debug("权限缓存版本不匹配，需要重新验证权限")
                cached_result = None
            else:
                cached_result = cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            # 获取方法代码
            method_code = get_method_code(method)

            # 使用高效的数据库查询，检查用户是否有匹配的权限
            # 检查用户-角色-权限关系链
            has_permission = UserProfile.objects.filter(
                user=request.user,
                roles__permissions__api=path,
                roles__permissions__method__in=[None, method_code],
            ).exists()

            # 如果没有找到精确匹配的权限，尝试进行模糊匹配（例如处理带参数的URL）
            if not has_permission:
                has_permission = self._check_fuzzy_permission(request)

            # 缓存结果
            cache.set(cache_key, has_permission, self.CACHE_TIMEOUT)
            # 保存版本信息
            cache.set(
                f"{cache_key}_version",
                {
                    "user": user_version,
                    "global": global_version,
                },
                self.CACHE_TIMEOUT,
            )

            return has_permission

        except Exception as e:
            logger.error(f"权限检查异常: {str(e)}")
            # 发生异常时，默认拒绝访问
            return False

    def _check_fuzzy_permission(self, request) -> bool:
        """
        进行模糊权限匹配，处理带参数的URL

        Args:
            request: HTTP请求对象

        Returns:
            bool: 如果用户有权限，返回True；否则返回False
        """
        try:
            path = request.path
            method = request.method
            method_code = get_method_code(method)

            # 获取用户的所有角色和权限，使用select_related和prefetch_related优化查询
            user_profile = (
                UserProfile.objects.select_related("user")
                .prefetch_related("roles__permissions")
                .get(user=request.user)
            )

            # 遍历用户的所有角色和权限，进行模糊匹配
            for role in user_profile.roles.all():
                for permission in role.permissions.all():
                    # 检查权限是否有API路径
                    if not permission.api:
                        continue

                    # 检查请求方法是否匹配
                    if (
                        permission.method is not None
                        and permission.method != method_code
                    ):
                        continue

                    # 进行模糊URL匹配
                    if self._match_url(path, permission.api):
                        return True

            return False

        except Exception as e:
            logger.error(f"模糊权限匹配异常: {str(e)}")
            return False

    def _match_url(self, request_url: str, permission_url: str) -> bool:
        """
        进行URL匹配，支持简单的参数化URL匹配
        例如: /api/users/123/ 匹配 /api/users/{id}/

        Args:
            request_url: 请求的URL
            permission_url: 权限中定义的URL

        Returns:
            bool: 如果URL匹配，返回True；否则返回False
        """
        # 将权限URL转换为正则表达式
        # 替换 {param} 格式的参数为匹配任意字符的正则表达式
        regex_pattern = permission_url
        if "{" in regex_pattern and "}" in regex_pattern:
            # 简单的参数化URL匹配
            regex_pattern = re.sub(r"\{[^}]+\}", r"[^/]+", regex_pattern)
            regex_pattern = f"^{regex_pattern}$"
            return bool(re.match(regex_pattern, request_url))

        # 精确匹配
        return request_url == permission_url

    @classmethod
    def clear_user_permission_cache(cls, user_id):
        """
        清除指定用户的API权限缓存
        与common_utils中的权限缓存清除保持一致
        """
        try:
            # 设置一个版本标记，确保下次请求重新加载权限
            version_key = f"{cls.CACHE_KEY_VERSION}_{user_id}"
            current_version = cache.get(version_key, 0)
            cache.set(version_key, current_version + 1, timeout=cls.CACHE_TIMEOUT)
            logger.debug(f"已更新用户 {user_id} 的API权限缓存版本")

            return True
        except Exception as e:
            logger.error(f"清除用户 {user_id} 的API权限缓存失败: {str(e)}")
            return False

    @classmethod
    def clear_all_permission_caches(cls):
        """
        清除所有用户的API权限缓存
        与common_utils中的全局权限缓存清除保持一致
        """
        try:
            # 设置一个全局版本标记，确保所有用户下次请求重新加载权限
            current_global_version = cache.get(cls.CACHE_KEY_GLOBAL_VERSION, 0)
            cache.set(
                cls.CACHE_KEY_GLOBAL_VERSION,
                current_global_version + 1,
                timeout=cls.CACHE_TIMEOUT,
            )
            logger.debug("已更新全局API权限缓存版本")

            return True
        except Exception as e:
            logger.error(f"清除所有用户的API权限缓存失败: {str(e)}")
            return False
