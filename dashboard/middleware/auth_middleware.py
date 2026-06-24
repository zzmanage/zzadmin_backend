from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.contrib.auth import get_user_model
from ..models import UserProfile

User = get_user_model()


class AuthenticationMiddleware(MiddlewareMixin):
    """认证中间件

    处理用户认证相关的逻辑，特别是验证令牌是否与last_token匹配
    """

    def process_request(self, request):
        """处理请求，进行认证处理

        Args:
            request: HTTP请求对象
        """
        # 跳过OPTIONS请求
        if request.method == "OPTIONS":
            return

        # 跳过不需要认证的路径（例如登录、注册、重置密码等）
        if (
            request.path.startswith("/api/auth/login")
            or request.path.startswith("/api/auth/register")
            or "reset_password" in request.path
            or request.path.startswith("/api/captcha/")
        ):
            return

        # 获取Authorization头
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if auth_header.startswith("Bearer "):
            # 提取token
            token = auth_header.split(" ")[1]

            # 使用JWTAuthentication验证token
            jwt_auth = JWTAuthentication()

            try:
                # 获取用户信息
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)

                # 检查用户是否存在对应的UserProfile
                try:
                    user_profile = UserProfile.objects.get(user=user)

                    # 验证token是否与last_token匹配
                    if user_profile.last_token != token:
                        # 如果不匹配，则抛出认证失败异常
                        raise AuthenticationFailed("Token已失效，请重新登录")
                except UserProfile.DoesNotExist:
                    # 如果没有UserProfile，说明用户可能是新创建的
                    # 创建UserProfile并设置last_token
                    UserProfile.objects.create(user=user, last_token=token)
            except (InvalidToken, AuthenticationFailed, User.DoesNotExist):
                # 不做处理，让DRF的认证机制来处理认证失败
                pass


class CORSHeadersMiddleware(MiddlewareMixin):
    """CORS跨域请求中间件

    处理跨域资源共享相关的逻辑
    """

    def process_response(self, request, response):
        """处理响应，添加CORS相关的响应头

        Args:
            request: HTTP请求对象
            response: HTTP响应对象

        Returns:
            response: 添加了CORS头的响应对象
        """
        # 这些配置通常由django-cors-headers包处理
        # 这里保留这个中间件作为示例，实际使用时可以根据需要调整
        return response
