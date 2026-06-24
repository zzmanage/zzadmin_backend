import logging
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
import json
import logging

logger = logging.getLogger(__name__)


class RequestPreprocessingMiddleware:
    """
    请求预处理中间件
    统一处理请求前的通用逻辑，如参数验证、数据预处理等
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 预处理逻辑只应用于API请求
        if request.path.startswith("/api/"):
            # 确保请求体JSON格式正确（如果是JSON请求）
            if (
                request.method in ["POST", "PUT", "PATCH"]
                and request.content_type == "application/json"
                and request.body
            ):
                try:
                    # 尝试解析JSON以验证格式
                    request_json = json.loads(request.body)
                    # 将解析后的JSON保存到request对象上，方便后续使用
                    setattr(request, "json_data", request_json)
                except json.JSONDecodeError:
                    # 如果JSON格式错误，返回400错误
                    logger.warning(f"请求{request.path}包含无效的JSON格式")
                    return JsonResponse(
                        {
                            "code": status.HTTP_400_BAD_REQUEST,
                            "message": "请求数据格式错误，请检查JSON格式",
                            "path": request.path,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        # 继续处理请求
        response = self.get_response(request)
        return response


class APIResponseMiddleware:
    """
    API响应统一处理中间件
    统一API响应格式，确保所有API返回一致的结构
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 只处理API请求的响应
        if (
            request.path.startswith("/api/")
            and hasattr(response, "content_type")
            and response.content_type is not None
            and "application/json" in response.content_type
        ):

            try:
                # 尝试解析响应内容
                response_data = json.loads(response.content)

                # 检查是否已经是统一格式
                if (
                    isinstance(response_data, dict)
                    and "code" in response_data
                    and "message" in response_data
                    and "data" in response_data
                ):
                    return response

                # 检查是否是旧的错误格式
                if isinstance(response_data, dict) and "error" in response_data:
                    wrapped_data = {
                        "code": response.status_code,
                        "message": response_data["error"],
                        "data": {}
                    }
                else:
                    # 统一包装其他响应格式
                    wrapped_data = {
                        "code": response.status_code,
                        "message": (
                            "操作成功" if 200 <= response.status_code < 300 else "操作失败"
                        ),
                        "data": response_data,
                    }

                # 创建新的响应
                return JsonResponse(wrapped_data, status=response.status_code)
            except Exception as e:
                # 如果解析或处理失败，返回统一的错误响应
                logger.warning(f"API响应格式处理失败: {str(e)}")
                # 对于无法解析的响应，返回统一错误格式
                return JsonResponse(
                    {
                        "code": 500,
                        "message": "服务器返回格式错误",
                        "data": {}
                    },
                    status=500
                )

        return response
