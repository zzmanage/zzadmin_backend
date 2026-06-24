import logging
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
import traceback

logger = logging.getLogger(__name__)


class ExceptionHandlingMiddleware:
    """
    异常处理中间件
    统一捕获和处理应用程序中发生的异常，返回标准化的错误响应
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # 处理请求
            response = self.get_response(request)
            return response
        except Exception as e:
            # 记录异常详情
            logger.error(f"请求 {request.path} 发生异常: {str(e)}")
            logger.error(traceback.format_exc())

            # 对API请求返回JSON格式的错误响应
            if request.path.startswith('/api/'):
                # 根据异常类型返回不同的错误信息
                if isinstance(e, PermissionError):
                    return JsonResponse(
                        {
                            'code': status.HTTP_403_FORBIDDEN,
                            'message': '权限不足',
                            'path': request.path,
                            'error': str(e),
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
                elif isinstance(e, ValueError):
                    return JsonResponse(
                        {
                            'code': status.HTTP_400_BAD_REQUEST,
                            'message': '请求参数错误',
                            'data': {
                                'path': request.path,
                                'error': str(e)
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    # 其他异常返回500错误
                    return JsonResponse(
                        {
                            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                            'message': '服务器内部错误',
                            'data': {
                                'path': request.path,
                                'error': str(e) if settings.DEBUG else 'Internal Server Error'
                            }
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                # 非API请求直接抛出异常，由Django默认处理
                raise


class RequestResponseLoggingMiddleware:
    """
    请求响应日志中间件
    记录请求和响应的详细信息，用于调试和监控
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 记录请求信息（不记录敏感信息）
        if request.path.startswith('/api/'):
            # 记录请求方法、路径、客户端IP等基本信息
            logger.info(
                f"请求: {request.method} {request.path} "
                f"来源IP: {self.get_client_ip(request)} "
                f"用户代理: {request.META.get('HTTP_USER_AGENT', '')[:200]}"
            )

            # 记录请求体（对于非敏感的请求）
            if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
                # 避免记录过大的请求体
                if len(request.body) < 1024 * 10:
                    try:
                        # 尝试解析请求体以检查是否包含敏感信息
                        if request.content_type == 'application/json':
                            request_data = request.body.decode('utf-8')
                            # 这里可以添加逻辑来过滤敏感信息
                            logger.debug(f"请求体: {request_data}")
                    except:
                        logger.debug(f"请求体: 二进制数据，长度: {len(request.body)} bytes")

        # 处理请求
        response = self.get_response(request)

        # 记录响应信息
        if request.path.startswith('/api/'):
            logger.info(
                f"响应: {request.method} {request.path} "
                f"状态码: {response.status_code} "
                f"内容类型: {response.get('Content-Type', '')}"
            )

            # 记录响应体（对于JSON响应且内容不太大的情况）
            if response.get('Content-Type', '').startswith('application/json'):
                try:
                    content = response.content
                    if len(content) < 1024 * 10:
                        # 这里可以添加逻辑来过滤响应中的敏感信息
                        logger.debug(f"响应体: {content.decode('utf-8')}")
                except:
                    logger.debug(f"响应体: 无法解析的内容，长度: {len(response.content)} bytes")

        return response

    def get_client_ip(self, request):
        """\获取客户端真实IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip