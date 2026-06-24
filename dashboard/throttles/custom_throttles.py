import logging
import time

from django.conf import settings
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle, SimpleRateThrottle

logger = logging.getLogger(__name__)


class IPThrottle(SimpleRateThrottle):
    """
    基于IP的访问频率限制
    限制来自同一IP的请求频率
    """

    scope = "ip"

    def get_cache_key(self, request, view):
        # 使用客户端IP作为缓存键
        ip = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ip}


class UserThrottle(SimpleRateThrottle):
    """
    基于用户的访问频率限制
    限制已登录用户的请求频率
    """

    scope = "user"

    def get_cache_key(self, request, view):
        # 对于已认证的用户，使用用户ID作为缓存键
        if request.user and request.user.is_authenticated:
            return self.cache_format % {"scope": self.scope, "ident": request.user.pk}
        # 对于未认证的用户，回退到基于IP的限制
        ip = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ip}


class DynamicRateThrottle(BaseThrottle):
    """
    动态速率限制
    根据不同的视图和用户类型设置不同的限制速率
    """

    def __init__(self):
        self.rate = None
        self.num_requests = None
        self.duration = None
        self.key = None
        self.history = None
        self.now = None

    def allow_request(self, request, view):
        # 获取动态配置的速率限制
        self.rate = getattr(view, "throttle_rate", None) or settings.REST_FRAMEWORK.get(
            "DEFAULT_THROTTLE_RATES", {}
        ).get("dynamic", "100/hour")
        self.num_requests, self.duration = self.parse_rate(self.rate)

        # 构建缓存键
        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        # 获取请求历史记录
        self.history = cache.get(self.key, [])
        self.now = time.time()

        # 移除过期的请求记录
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        # 检查是否超过限制
        if len(self.history) >= self.num_requests:
            # 记录超过限制的请求
            logger.warning(
                f"Rate limit exceeded for {self.key}, limit: {self.num_requests}/{self.duration}s"
            )
            return False

        # 添加当前请求到历史记录
        self.history.insert(0, self.now)
        cache.set(self.key, self.history, self.duration)
        return True

    def wait(self):
        """计算还需要等待多长时间才能继续请求"""
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return remaining_duration
        return None

    def get_cache_key(self, request, view):
        """生成缓存键"""
        # 为不同视图生成不同的缓存键前缀
        view_name = view.__class__.__name__

        if request.user and request.user.is_authenticated:
            # 对于已认证用户，结合用户ID和视图名
            return f"throttle:dynamic:{view_name}:user:{request.user.pk}"
        else:
            # 对于未认证用户，结合IP和视图名
            ip = self.get_ident(request)
            return f"throttle:dynamic:{view_name}:ip:{ip}"

    def get_ident(self, request):
        """获取客户端标识符（IP地址）"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def parse_rate(self, rate):
        """解析速率字符串（如'100/hour'或'5/10m'）为请求数和持续时间"""
        if rate is None:
            return (None, None)
        num, period = rate.split("/")
        num_requests = int(num)
        # 提取period中的字母部分（忽略数字）
        period_char = "".join([c for c in period if c.isalpha()]) or period[0]
        # 使用字母的第一个字符作为键
        duration_key = period_char[0].lower() if period_char else "h"  # 默认使用小时
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(
            duration_key, 3600
        )  # 默认3600秒（1小时）
        return (num_requests, duration)


class LoginRateThrottle(BaseThrottle):
    """
    登录尝试频率限制
    专门用于限制登录接口的访问频率，防止暴力破解
    """

    def __init__(self):
        self.rate = "5/10m"  # 10分钟内最多5次尝试
        self.num_requests, self.duration = self.parse_rate(self.rate)
        self.cache_prefix = "throttle:login:"

    def allow_request(self, request, view):
        # 只对登录请求进行限制
        if request.path not in ["/api/auth/login/", "/api/auth/login"]:
            return True

        # 获取用户名和IP
        username = request.data.get("username", "unknown")
        ip = self.get_ident(request)

        # 创建两个缓存键：一个基于用户名，一个基于IP
        user_key = f"{self.cache_prefix}user:{username}"
        ip_key = f"{self.cache_prefix}ip:{ip}"

        # 获取历史记录
        user_history = cache.get(user_key, [])
        ip_history = cache.get(ip_key, [])
        now = time.time()

        # 清理过期记录
        user_history = [t for t in user_history if t > now - self.duration]
        ip_history = [t for t in ip_history if t > now - self.duration]

        # 检查是否超过限制
        if (
            len(user_history) >= self.num_requests
            or len(ip_history) >= self.num_requests
        ):
            logger.warning(
                f"Login attempt limit exceeded for username:{username} or IP:{ip}"
            )
            return False

        # 记录当前尝试
        user_history.append(now)
        ip_history.append(now)

        # 更新缓存
        cache.set(user_key, user_history, self.duration)
        cache.set(ip_key, ip_history, self.duration)

        return True

    def wait(self):
        # 简单返回等待时间，实际使用时可能需要更精确的计算
        return self.duration

    def get_ident(self, request):
        # 同DynamicRateThrottle中的实现
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def parse_rate(self, rate):
        # 同DynamicRateThrottle中的实现
        num, period = rate.split("/")
        num_requests = int(num)
        # 提取period中的字母部分（忽略数字）
        period_char = "".join([c for c in period if c.isalpha()]) or period[0]
        # 使用字母的第一个字符作为键
        duration_key = period_char[0].lower() if period_char else "h"  # 默认使用小时
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(
            duration_key, 3600
        )  # 默认3600秒（1小时）
        return (num_requests, duration)
