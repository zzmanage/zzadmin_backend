import logging
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response

from dashboard.models import UserProfile

# 配置日志
logger = logging.getLogger(__name__)

# 线程池配置
ASYNC_EXECUTOR = ThreadPoolExecutor(max_workers=getattr(settings, "UTIL_WORKERS", 4))

# 缓存相关配置
PERMISSION_CACHE_PREFIX = "permission_"
PERMISSION_CACHE_TIMEOUT = 60 * 10  # 10分钟
IP_LOCATION_CACHE_TIMEOUT = 60 * 60 * 24  # 24小时
IP_LOCATION_FAILURE_CACHE_TIMEOUT = 60 * 60  # 1小时
USER_AGENT_CACHE_PREFIX = "user_agent_"
USER_AGENT_CACHE_TIMEOUT = 60 * 60  # 1小时


# 统一的异常处理装饰器
def handle_exceptions(default_return=None, log_level='error', include_traceback=False, filter_sensitive=True):
    """统一异常处理装饰器，用于捕获和处理函数执行过程中的异常
    
    Args:
        default_return: 发生异常时的默认返回值，默认为None
        log_level: 日志记录级别，默认为'error'
        include_traceback: 是否在响应中包含堆栈跟踪（仅在DEBUG模式下有效），默认为False
        filter_sensitive: 是否过滤敏感字段，默认为True
    
    Returns:
        function: 装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # 记录函数执行时间（调试模式下）
                if settings.DEBUG:
                    exec_time = (time.time() - start_time) * 1000
                    logger.debug(f"函数 {func.__name__} 执行耗时: {exec_time:.2f}ms")
                return result
            except Exception as e:
                # 收集异常上下文信息
                context_info = _collect_exception_context(args, kwargs, filter_sensitive)
                
                # 记录异常信息
                log_func = getattr(logger, log_level)
                log_func(f"函数 {func.__name__} 执行异常: {str(e)}, 上下文: {context_info}")

                # 记录详细的异常信息（调试模式下）
                if settings.DEBUG:
                    logger.exception(f"函数 {func.__name__} 执行异常详情:")
                
                # 如果default_return是Response对象并且在DEBUG模式下，添加更多错误详情
                if isinstance(default_return, Response) and settings.DEBUG:
                    # 使用辅助函数丰富响应信息
                    debug_response = _enrich_response_with_error_info(
                        default_return, e, context_info, include_traceback
                    )
                    return debug_response

                return default_return if default_return is not None else {}

        return wrapper

    return decorator

def _collect_exception_context(args, kwargs, filter_sensitive=True):
    """收集异常上下文信息
    
    Args:
        args: 函数参数列表
        kwargs: 函数关键字参数字典
        filter_sensitive: 是否过滤敏感字段
    
    Returns:
        dict: 包含用户、路径、方法和数据的上下文信息
    """
    # 初始化上下文信息
    context = {
        'user': 'anonymous',
        'path': 'unknown',
        'method': 'unknown',
        'data_sample': '',
        'query_params': ''
    }
    
    # 尝试从参数中获取请求对象
    if args and hasattr(args[0], 'request'):
        request = args[0].request
        context['user'] = request.user.id if request.user.is_authenticated else 'anonymous'
        context['path'] = request.path
        context['method'] = request.method
        
        # 安全地记录请求参数，避免敏感信息
        try:
            if request.method in ['POST', 'PUT', 'PATCH'] and request.data:
                data_str = str(request.data)[:500]  # 只记录前500个字符
                context['data_sample'] = data_str
            if request.GET:
                context['query_params'] = str(request.GET)[:500]
        except:
            pass
    
    return context

def _enrich_response_with_error_info(response, exception, context_info, include_traceback=False):
    """在响应中添加异常信息
    
    Args:
        response: 原始响应对象
        exception: 异常对象
        context_info: 上下文信息
        include_traceback: 是否包含堆栈跟踪
    
    Returns:
        Response: 添加了异常信息的响应对象
    """
    # 创建一个新的Response对象，而不是尝试深拷贝
    debug_data = response.data
    # 如果响应数据是字典类型，添加调试信息
    if isinstance(debug_data, dict):
        debug_data = debug_data.copy()  # 复制原始数据，避免修改
        debug_info = {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'function': context_info.get('function', 'unknown'),
            **context_info
        }
        
        # 如果需要，添加堆栈跟踪（仅在DEBUG模式下）
        if include_traceback:
            import traceback
            debug_info['traceback'] = traceback.format_exc()
            
        debug_data['debug_info'] = debug_info
    
    # 创建一个新的Response对象
    return Response(
        debug_data,
        status=response.status_code,
        headers=response.headers
    )


@handle_exceptions(default_return=("Unknown Browser", "Unknown OS"))
def parse_user_agent(user_agent):
    """解析User-Agent字符串，提取浏览器和操作系统信息，增加缓存机制

    Args:
        user_agent: 用户代理字符串

    Returns:
        tuple: (browser, os) 浏览器和操作系统信息
    """
    if not user_agent:
        return "Unknown Browser", "Unknown OS"

    # 使用MD5哈希作为缓存键，避免长字符串
    import hashlib

    cache_key = (
        f"{USER_AGENT_CACHE_PREFIX}{hashlib.md5(user_agent.encode()).hexdigest()}"
    )

    # 尝试从缓存获取
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    browser = "Unknown Browser"
    os = "Unknown OS"

    # 使用更精确的正则表达式检测操作系统
    os_patterns = {
        r"Windows": "Windows",
        r"Macintosh|Mac OS X": "Mac OS",
        r"Linux": "Linux",
        r"iPhone": "iOS",
        r"Android": "Android",
        r"iPad": "iOS",
        r"Windows Phone": "Windows Phone",
        r"BlackBerry": "BlackBerry",
        r"PostOffice": "Unknown Device",
    }

    for pattern, os_name in os_patterns.items():
        if re.search(pattern, user_agent, re.IGNORECASE):
            os = os_name
            break

    # 使用更精确的正则表达式检测浏览器
    browser_patterns = {
        r"Chrome": "Chrome",
        r"Firefox": "Firefox",
        r"Safari(?!.*Chrome)": "Safari",
        r"Edge": "Edge",
        r"MSIE|Trident/": "Internet Explorer",
        r"Opera|OPR": "Opera",
        r"Brave": "Brave",
        r"Vivaldi": "Vivaldi",
    }

    for pattern, browser_name in browser_patterns.items():
        if re.search(pattern, user_agent, re.IGNORECASE):
            browser = browser_name
            break

    # 缓存结果
    cache.set(cache_key, (browser, os), USER_AGENT_CACHE_TIMEOUT)

    return browser, os


def get_ip_location(ip_address, async_mode=False):
    """获取IP地址的地理位置信息，支持异步和多源备份

    Args:
        ip_address: IP地址字符串
        async_mode: 是否异步获取

    Returns:
        dict: 包含地理位置信息的字典，如果是异步模式则返回Future对象
    """
    
    # 根据async_mode决定是否异步执行
    if async_mode:
        return ASYNC_EXECUTOR.submit(_get_location_sync, ip_address)
    else:
        return _get_location_sync(ip_address)


def _get_location_sync(ip_address):
    """同步获取IP地址的地理位置信息
    
    Args:
        ip_address: IP地址字符串
        
    Returns:
        dict: 包含地理位置信息的字典
    """
    # 缓存键
    cache_key = f"ip_location_{ip_address}"
    
    # 尝试从缓存获取
    cached_result = _get_location_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # 如果是本地IP，返回默认值
    if ip_address in ["127.0.0.1", "localhost"]:
        result = _get_default_location_for_local_ip()
        _cache_location_result(cache_key, result, IP_LOCATION_CACHE_TIMEOUT)
        return result
    
    # 从多个服务获取位置信息
    result = _get_location_from_services(ip_address)
    
    # 确定缓存超时时间
    cache_timeout = IP_LOCATION_FAILURE_CACHE_TIMEOUT if not result else IP_LOCATION_CACHE_TIMEOUT
    _cache_location_result(cache_key, result, cache_timeout)
    
    return result


def _get_location_from_cache(cache_key):
    """从缓存获取地理位置信息
    
    Args:
        cache_key: 缓存键
        
    Returns:
        dict or None: 缓存的地理位置信息，或None如果缓存未命中
    """
    return cache.get(cache_key)


def _get_default_location_for_local_ip():
    """获取本地IP的默认地理位置信息
    
    Returns:
        dict: 默认的地理位置信息
    """
    return {
        "continent": "亚洲",
        "country": "中国",
        "province": "北京",
        "city": "北京",
        "district": "海淀区",
        "isp": "本地网络",
        "area_code": "CN",
        "country_english": "China",
        "country_code": "CN",
        "longitude": "116.397232",
        "latitude": "39.907501",
    }


def _get_location_from_services(ip_address):
    """从多个IP地理位置服务获取信息
    
    Args:
        ip_address: IP地址字符串
        
    Returns:
        dict: 获取到的地理位置信息，如果所有服务都失败则返回默认值
    """
    # 定义多个IP地理位置服务作为备份
    services = [
        {
            "url": f"http://ip-api.com/json/{ip_address}?lang=zh-CN",
            "headers": {"User-Agent": "Backend Management System"},
            "parser": _parse_ip_api_response,
        },
        {
            "url": f"https://ipinfo.io/{ip_address}/json",
            "headers": {"User-Agent": "Backend Management System"},
            "parser": _parse_ipinfo_response,
        },
    ]

    result = None
    for service in services:
        try:
            result = _get_location_from_single_service(service)
            if result:
                break  # 成功获取后退出循环
        except requests.RequestException as e:
            logger.warning(f"使用服务 {service['url']} 获取IP位置信息失败: {e}")

    # 如果所有服务都失败，返回默认值
    if not result:
        result = {
            "continent": "未知",
            "country": "未知",
            "province": "未知",
            "city": "未知",
            "district": "未知",
            "isp": "未知",
            "area_code": "未知",
            "country_english": "Unknown",
            "country_code": "Unknown",
            "longitude": "未知",
            "latitude": "未知",
        }
        
    return result


def _get_location_from_single_service(service):
    """从单个IP地理位置服务获取信息
    
    Args:
        service: 服务配置字典，包含url、headers和parser
        
    Returns:
        dict or None: 获取到的地理位置信息，或None如果失败
    """
    # 设置超时和重试机制
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=1)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    response = session.get(
        service["url"], headers=service["headers"], timeout=3
    )

    if response.status_code == 200:
        data = response.json()
        return service["parser"](data)
    
    return None


def _cache_location_result(cache_key, result, timeout):
    """缓存地理位置信息结果
    
    Args:
        cache_key: 缓存键
        result: 要缓存的地理位置信息
        timeout: 缓存超时时间
    """
    cache.set(cache_key, result, timeout)


def _parse_ip_api_response(data):
    """解析ip-api.com的响应数据"""
    if data.get("status") == "success":
        return {
            "continent": data.get("continent", "未知"),
            "country": data.get("country", "未知"),
            "province": data.get("regionName", "未知"),
            "city": data.get("city", "未知"),
            "district": "未知",  # ip-api不提供区县信息
            "isp": data.get("isp", "未知"),
            "area_code": data.get("zip", "未知"),
            "country_english": data.get("country", "未知"),
            "country_code": data.get("countryCode", "未知"),
            "longitude": str(data.get("lon", "未知")),
            "latitude": str(data.get("lat", "未知")),
        }
    return None


def _parse_ipinfo_response(data):
    """解析ipinfo.io的响应数据"""
    # 简单的国家映射
    country_map = {
        "CN": "中国",
        "US": "美国",
        "JP": "日本",
        "KR": "韩国",
        "SG": "新加坡",
        "HK": "中国香港",
    }

    # 从location中提取经纬度
    loc = data.get("loc", "").split(",")
    longitude = loc[1] if len(loc) > 1 else "未知"
    latitude = loc[0] if len(loc) > 0 else "未知"

    return {
        "continent": "未知",
        "country": country_map.get(
            data.get("country", "未知"), data.get("country", "未知")
        ),
        "province": data.get("region", "未知"),
        "city": data.get("city", "未知"),
        "district": "未知",
        "isp": data.get("org", "未知"),
        "area_code": data.get("postal", "未知"),
        "country_english": data.get("country", "未知"),
        "country_code": data.get("country", "未知"),
        "longitude": longitude,
        "latitude": latitude,
    }


@handle_exceptions()
def get_client_ip(request):
    """获取客户端IP地址，支持代理情况，增加IP格式验证"""
    # 定义IP地址验证正则表达式（支持IPv4和IPv6）
    ipv4_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    ipv6_pattern = (
        r"^([0-9a-fA-F]{0,4}:){2,7}"
        r"([0-9a-fA-F]{0,4}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$"
    )

    # 支持的代理头字段列表
    proxy_headers = [
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_REAL_IP",
        "HTTP_CLIENT_IP",
        "HTTP_X_FORWARDED",
        "HTTP_X_CLUSTER_CLIENT_IP",
        "HTTP_FORWARDED_FOR",
        "HTTP_FORWARDED",
    ]

    # 遍历所有代理头字段
    for header in proxy_headers:
        ip_list = request.META.get(header)
        if ip_list:
            # 可能有多个IP，取第一个
            ip = ip_list.split(",")[0].strip()
            # 验证IP格式是否正确
            if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
                # 过滤掉私有IP地址（可选）
                if not settings.DEBUG or not is_private_ip(ip):
                    return ip

    # 从REMOTE_ADDR获取
    ip = request.META.get("REMOTE_ADDR")
    return ip


def is_private_ip(ip):
    """判断是否为私有IP地址"""
    # IPv4私有地址范围
    private_ranges = [
        re.compile(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
        re.compile(r"^172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}$"),
        re.compile(r"^192\.168\.\d{1,3}\.\d{1,3}$"),
        re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
    ]

    for pattern in private_ranges:
        if pattern.match(ip):
            return True

    return False


def check_user_permission(request, permission_value):
    """检查用户是否有指定的权限，使用更高效的数据库查询

    Args:
        request: HTTP请求对象
        permission_value: 要检查的权限值

    Returns:
        Response or None: 如果没有权限，返回错误响应；如果有权限，返回None
    """
    # 检查用户是否是超级用户，如果是则直接放行
    if request.user.is_superuser:
        return None

    try:
        # 使用子查询方式直接判断用户是否有指定权限，避免加载所有角色和权限
        has_permission = UserProfile.objects.filter(
            user=request.user, roles__permissions__value=permission_value
        ).exists()

        if not has_permission:
            # 如果快速查询没有找到权限，再进行详细查询以确保准确性
            # 同时也兼容更复杂的权限检查场景
            user_profile = (
                UserProfile.objects.select_related("user")
                .prefetch_related("roles__permissions")
                .get(user=request.user)
            )

            has_permission = False
            for role in user_profile.roles.all():
                if role.permissions.filter(value=permission_value).exists():
                    has_permission = True
                    break

            if not has_permission:
                return Response(
                    {"status": "error", "message": f"您没有{permission_value}权限"},
                    status=status.HTTP_403_FORBIDDEN,
                )
    except UserProfile.DoesNotExist:
        return Response(
            {"status": "error", "message": "用户资料不存在"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"权限检查异常: {str(e)}")
        return Response(
            {"status": "error", "message": "权限检查失败"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 有权限，返回None
    return None


def permission_required(permission_value, cache_timeout=None):
    """权限验证装饰器，优化缓存策略和权限检查逻辑

    用于检查用户是否拥有指定权限的装饰器，可直接应用于视图方法

    Args:
        permission_value: 要检查的权限值
        cache_timeout: 缓存超时时间（秒），默认根据请求类型设置

    Returns:
        装饰后的函数
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # 直接使用传入的权限值
            full_permission_value = permission_value

            # 缓存键
            cache_key = (
                f"{PERMISSION_CACHE_PREFIX}{request.user.id}_"
                f"{full_permission_value}_{request.method}"
            )

            # 确定缓存超时时间
            if cache_timeout is None:
                # 根据请求类型设置不同的缓存时间
                if request.method == "GET":
                    current_timeout = PERMISSION_CACHE_TIMEOUT  # 10分钟
                elif request.method in ["POST", "PUT", "DELETE"]:
                    current_timeout = 60  # 1分钟
                else:
                    current_timeout = 5 * 60  # 5分钟
            else:
                current_timeout = cache_timeout

            # 非超级用户使用缓存
            if not request.user.is_superuser:
                # 检查版本标记，决定是否需要重新验证权限
                version_key = f"{PERMISSION_CACHE_PREFIX}version_{request.user.id}"
                global_version_key = f"{PERMISSION_CACHE_PREFIX}global_version"

                user_version = cache.get(version_key, 0)
                global_version = cache.get(global_version_key, 0)

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
                    # 不使用缓存，直接进行权限检查
                    use_cache = False
                else:
                    cached_result = cache.get(cache_key)
                    use_cache = cached_result is not None

                if use_cache:
                    if cached_result is True:
                        # 缓存命中，有权限
                        return view_func(self, request, *args, **kwargs)
                    elif cached_result is False:
                        # 缓存命中，无权限
                        return Response(
                            {
                                "status": "error",
                                "message": f"您没有{full_permission_value}权限",
                            },
                            status=status.HTTP_403_FORBIDDEN,
                        )

            # 权限检查
            permission_response = check_user_permission(request, full_permission_value)

            if permission_response:
                # 缓存无权限结果
                if not request.user.is_superuser:
                    cache.set(cache_key, False, current_timeout)
                    # 保存版本信息
                    cache.set(
                        f"{cache_key}_version",
                        {
                            "user": cache.get(
                                f"{PERMISSION_CACHE_PREFIX}version_{request.user.id}", 0
                            ),
                            "global": cache.get(
                                f"{PERMISSION_CACHE_PREFIX}global_version", 0
                            ),
                        },
                        current_timeout,
                    )
                return permission_response

            # 缓存有权限结果
            if not request.user.is_superuser:
                cache.set(cache_key, True, current_timeout)
                # 保存版本信息
                cache.set(
                    f"{cache_key}_version",
                    {
                        "user": cache.get(
                            f"{PERMISSION_CACHE_PREFIX}version_{request.user.id}", 0
                        ),
                        "global": cache.get(
                            f"{PERMISSION_CACHE_PREFIX}global_version", 0
                        ),
                    },
                    current_timeout,
                )

            # 有权限，继续执行原函数
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


# 清除用户权限缓存的工具函数
def clear_user_permission_cache(user_id):
    """清除指定用户的所有权限缓存"""
    try:
        # 对于不支持keys方法的缓存后端，我们使用一个更安全的方法：
        # 1. 如果缓存后端支持keys方法，尝试精确清除
        # 2. 如果不支持，我们使用一个特殊的缓存键来标记缓存需要刷新
        cache_pattern = f"{PERMISSION_CACHE_PREFIX}{user_id}_*"

        try:
            # 尝试使用keys方法（某些缓存后端如Redis支持）
            if hasattr(cache, "keys"):
                cache_keys = [f for f in cache.keys(cache_pattern)]
                if cache_keys:
                    cache.delete_many(cache_keys)
                    logger.info(
                        f"已清除用户 {user_id} 的权限缓存，共 {len(cache_keys)} 条"
                    )
        except Exception as keys_error:
            logger.warning(f"尝试使用keys方法清除缓存时出错: {str(keys_error)}")

        # 无论如何，设置一个版本标记，确保下次请求重新加载权限
        version_key = f"{PERMISSION_CACHE_PREFIX}version_{user_id}"
        current_version = cache.get(version_key, 0)
        cache.set(version_key, current_version + 1, timeout=PERMISSION_CACHE_TIMEOUT)
        logger.debug(f"已更新用户 {user_id} 的权限缓存版本")

        return True
    except Exception as e:
        logger.error(f"清除用户 {user_id} 的权限缓存失败: {str(e)}")
        return False


def clear_all_permission_caches():
    """清除所有用户的权限缓存"""
    try:
        # 对于不支持keys方法的缓存后端，我们使用一个更安全的方法：
        # 1. 如果缓存后端支持keys方法，尝试精确清除
        # 2. 如果不支持，我们使用一个全局版本标记
        try:
            # 尝试使用keys方法（某些缓存后端如Redis支持）
            if hasattr(cache, "keys"):
                cache_keys = [f for f in cache.keys(f"{PERMISSION_CACHE_PREFIX}*")]
                if cache_keys:
                    cache.delete_many(cache_keys)
                    logger.info(f"已清除所有用户的权限缓存，共 {len(cache_keys)} 条")
        except Exception as keys_error:
            logger.warning(f"尝试使用keys方法清除缓存时出错: {str(keys_error)}")

        # 无论如何，设置一个全局版本标记，确保所有用户下次请求重新加载权限
        global_version_key = f"{PERMISSION_CACHE_PREFIX}global_version"
        current_global_version = cache.get(global_version_key, 0)
        cache.set(
            global_version_key,
            current_global_version + 1,
            timeout=PERMISSION_CACHE_TIMEOUT,
        )
        logger.debug("已更新全局权限缓存版本")

        return True
    except Exception as e:
        logger.error(f"清除所有用户的权限缓存失败: {str(e)}")
        return False


def get_method_code(method):
    """将HTTP方法转换为对应的代码
    
    Args:
        method: HTTP方法字符串（如GET、POST等）
        
    Returns:
        int: 对应的方法代码
    """
    method_map = {
        'GET': 0,
        'POST': 1,
        'PUT': 2,
        'DELETE': 3
    }
    return method_map.get(method, None)
