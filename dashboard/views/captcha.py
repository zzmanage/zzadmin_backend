import base64
from io import BytesIO
from typing import Dict, Optional

from captcha.models import CaptchaStore
from captcha.views import captcha_image
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action


class CaptchaView(viewsets.GenericViewSet):
    """
    验证码视图集 - 用于生成和提供图片验证码
    使用 django-simple-captcha 库实现验证码功能
    """

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="获取成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "key": openapi.Schema(
                            type=openapi.TYPE_STRING, description="验证码ID"
                        ),
                        "image_base": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Base64编码的验证码图片",
                        ),
                    },
                ),
            )
        },
        security=[],
        operation_id="captcha-get",
        operation_description="获取图片验证码用于身份验证",
    )
    @action(detail=False, methods=['get'])
    def get_captcha(self, request) -> Response:
        """处理GET请求，生成并返回图片验证码

        Returns:
            Response: 包含验证码ID和Base64编码图片的响应
        """
        try:
            # 生成验证码
            captcha_id = CaptchaStore.generate_key()

            # 获取验证码图片
            image_data = captcha_image(request, captcha_id)

            # 确保返回的是BytesIO对象
            if isinstance(image_data, bytes):
                image_data = BytesIO(image_data)

            # 将图片转换为base64
            image_base = base64.b64encode(image_data.getvalue())

            json_data = {
                "key": captcha_id,
                "image_base": "data:image/png;base64," + image_base.decode("utf-8"),
            }

            return Response(json_data)
        except Exception as e:
            # 发生异常时返回错误信息
            return Response(
                {"error": f"生成验证码失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# 从工具模块导入verify_captcha函数，保持向后兼容性
from dashboard.utils.captcha_utils import verify_captcha  # noqa: F401
