import logging
import re
import time

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from dashboard.models import ApiWhiteList

# 获取logger
export_logger = logging.getLogger("export")


class ApiWhiteListMiddleware(MiddlewareMixin):
    """API白名单中间件

    检查请求的URL和方法是否在API白名单中，如果是，则跳过认证
    使用缓存机制优化性能，减少数据库查询
    """
    # 缓存键和过期时间
    CACHE_KEY = "api_whitelist_rules"
    CACHE_TIMEOUT = 300  # 5分钟

    def process_request(self, request):
        """处理请求，检查是否在白名单中

        Args:
            request: HTTP请求对象

        Returns:
            None: 如果在白名单中，继续处理请求
            Response: 如果不在白名单中且认证失败，返回认证失败响应
        """
        # 获取当前请求的URL和方法
        path = request.path
        method = request.method

        # 添加调试日志
        export_logger.debug(
            "处理请求: %s %s" % (method, path)
        )

        # 快速路径：常见的静态资源和文档路径直接放行
        if (path.startswith('/static/')
            or path.startswith('/swagger/')
                or path.startswith('/redoc/')):
            return None

        # 将方法转换为数字（与ApiWhiteList模型中的method字段对应）
        method_map = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3}
        method_number = method_map.get(method, 0)

        # 检查是否在白名单中
        is_whitelisted, matched_rule = self._is_in_whitelist(path, method_number)

        if is_whitelisted:
            method_display = dict(matched_rule.METHOD_CHOICES).get(
                matched_rule.method, "ALL"
            )
            export_logger.debug(
                "请求匹配白名单规则: URL=%s, 方法=%s" % (matched_rule.url, method_display)
            )
            return None

        export_logger.debug("请求不在白名单中，需要进行认证")
        # 如果不在白名单中，检查认证
        # 检查是否有JWT令牌
        auth_header = request.headers.get("Authorization")
        export_logger.debug("Authorization头部: %s" % auth_header)

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            jwt_auth = JWTAuthentication()
            try:
                # 验证令牌
                export_logger.debug("开始验证JWT令牌")
                validated_token = jwt_auth.get_validated_token(token)
                # 获取用户
                user = jwt_auth.get_user(validated_token)
                # 设置请求的用户
                request.user = user
                export_logger.debug("JWT令牌验证成功，用户: %s" % user.username)
            except InvalidToken as e:
                # 令牌无效，记录详细错误信息
                export_logger.warning("JWT令牌无效: %s, 请求路径: %s" % (str(e), path))
                # 令牌无效，返回401
                return JsonResponse(
                    {
                        "error": "Invalid or expired token",
                        "detail": str(e),
                    },  # 添加更详细的错误信息
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except TokenError as e:
                # 令牌错误，记录详细错误信息
                export_logger.warning("JWT令牌错误: %s, 请求路径: %s" % (str(e), path))
                # 令牌错误，返回401
                return JsonResponse(
                    {
                        "error": "Token error",
                        "detail": str(e),
                    },  # 添加更详细的错误信息
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            except Exception as e:
                # 其他认证错误
                export_logger.error(
                    "JWT认证过程中发生意外错误: %s, 请求路径: %s" % (str(e), path)
                )
                return JsonResponse(
                    {"error": "Authentication error", "detail": str(e)},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        else:
            export_logger.debug("请求没有Authorization头部或头部格式不正确")
            # 如果是其他需要认证的请求，暂时不做处理，由Django REST Framework的认证类处理
            # 或者如果需要更严格的控制，可以在这里返回401
            pass

    def _is_in_whitelist(self, path, method_number):
        """检查路径和方法是否在白名单中，使用缓存优化性能"""
        # 尝试从缓存获取规则
        start_time = time.time()
        whitelist_rules = cache.get(self.CACHE_KEY)
        cache_hit = whitelist_rules is not None

        if not whitelist_rules:
            try:
                # 查询所有启用的白名单规则
                whitelist_rules = list(ApiWhiteList.objects.filter(is_deleted=False))
                # 按URL复杂度排序，精确匹配的URL优先
                whitelist_rules.sort(
                    key=lambda rule: 0 if '*' not in rule.url else 1
                )
                # 缓存结果
                export_logger.debug("缓存白名单规则，数量: %d" % len(whitelist_rules))
                cache.set(self.CACHE_KEY, whitelist_rules, self.CACHE_TIMEOUT)
            except Exception as e:
                # 如果查询出错，默认不跳过认证
                export_logger.error("查询白名单时发生错误: %s" % str(e))
                return False, None

        # 记录缓存性能
        export_logger.debug(
            "白名单检查耗时: %.2fms, 缓存命中: %s" %
            ((time.time() - start_time) * 1000, cache_hit)
        )

        # 预过滤：只检查相关方法的规则
        filtered_rules = [rule for rule in whitelist_rules if rule.method == method_number]

        # 先检查精确匹配的URL
        for rule in [r for r in filtered_rules if '*' not in r.url]:
            if rule.url == path:
                return True, rule

        # 再检查通配符匹配的URL
        for rule in [r for r in filtered_rules if '*' in r.url]:
            # 转换为正则表达式
            regex_pattern = rule.url.replace(".", "\\.").replace("*", ".*")
            if re.match(f"^{regex_pattern}$", path):
                return True, rule

        return False, None