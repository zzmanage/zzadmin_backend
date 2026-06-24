import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from ..models import UserProfile

# 获取logger
logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_by_token(token):
    """通过JWT token获取用户信息，并验证token是否与last_token匹配

    Args:
        token: JWT token字符串

    Returns:
        User: 用户实例，如果token无效或不匹配则返回None
    """
    try:
        # 验证token
        access_token = AccessToken(token)
        user_id = access_token["user_id"]

        # 获取用户
        User = get_user_model()
        user = User.objects.get(id=user_id)

        # 确保用户是活跃的
        if not user.is_active:
            logger.warning(f"用户已禁用: {user_id}")
            return None
        
        # 检查用户是否存在对应的UserProfile
        try:
            user_profile = UserProfile.objects.get(user=user)
            
            # 验证token是否与last_token匹配
            if user_profile.last_token != token:
                logger.warning(f"Token不匹配，用户: {user.username}")
                return None
        except UserProfile.DoesNotExist:
            # 如果没有UserProfile，说明用户可能是新创建的
            # 创建UserProfile并设置last_token
            UserProfile.objects.create(user=user, last_token=token)
            logger.debug(f"为用户 {user.username} 创建UserProfile并设置last_token")
        
        return user

    except (InvalidToken, TokenError, User.DoesNotExist) as e:
        logger.warning(f"Token验证失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return None


class JWTTokenAuthMiddleware(BaseMiddleware):
    """WebSocket JWT Token认证中间件

    从WebSocket连接的URL参数中提取JWT token并进行认证
    """

    async def __call__(self, scope, receive, send):
        # 创建scope的副本以避免修改原始scope
        scope = dict(scope)

        # 尝试从URL参数中提取token
        token = None
        try:
            # 解析查询字符串
            query_string = scope.get("query_string", b"").decode()
            query_params = parse_qs(query_string)

            # 检查是否有token参数
            if "token" in query_params:
                token = query_params["token"][0]
                logger.debug(f"从URL参数中提取到token: {token[:20]}...")
        except Exception as e:
            logger.error(f"解析URL参数时发生错误: {str(e)}")

        # 如果找到token，尝试认证用户
        if token:
            user = await get_user_by_token(token)
            if user:
                scope["user"] = user
                logger.debug(f"用户认证成功: {user.username}")
            else:
                # 认证失败，设置为匿名用户
                from django.contrib.auth.models import AnonymousUser

                scope["user"] = AnonymousUser()
                logger.warning("Token认证失败，设置为匿名用户")
        else:
            # 没有提供token，设置为匿名用户
            from django.contrib.auth.models import AnonymousUser

            scope["user"] = AnonymousUser()
            logger.warning("未提供token，设置为匿名用户")

        # 继续处理请求
        return await super().__call__(scope, receive, send)