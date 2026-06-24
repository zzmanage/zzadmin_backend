import logging
import traceback
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from ...models import UserProfile, LoginLog
from ...serializers import UserProfileSerializer
from ...utils.cache_utils import CacheManager
from ...utils.permission_utils import PermissionChecker
from ...utils.common_utils import get_ip_location, parse_user_agent

logger = logging.getLogger(__name__)


class AuthViewSet(ViewSet):
    """认证视图集
    
    提供用户登录、登出、令牌刷新和密码重置等认证相关功能
    """
    
    permission_classes = []
    
    def __init__(self, **kwargs):
        """初始化视图集，设置工具类实例"""
        super().__init__(**kwargs)
        self.cache_manager = CacheManager()
        self.permission_checker = PermissionChecker()
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """用户登录接口
        
        Args:
            request: HTTP请求对象，包含用户名和密码
            
        Returns:
            Response: 登录结果响应，包含token和用户信息
        """
        try:
            # 获取请求数据
            username = request.data.get('username')
            password = request.data.get('password')
            
            # 参数验证
            if not username or not password:
                return Response({"error": "用户名和密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 查询用户
            try:
                user_profile = UserProfile.objects.get(user__username=username)
            except ObjectDoesNotExist:
                return Response({"error": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 验证密码
            if not user_profile.user.check_password(password):
                return Response({"error": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 检查用户状态
            if not user_profile.user.is_active:
                return Response({"error": "用户已被禁用"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 使用simplejwt生成标准JWT token
            refresh = RefreshToken.for_user(user_profile.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # 获取客户端IP
            client_ip = request.META.get('REMOTE_ADDR', '')
            
            # 获取User-Agent并解析浏览器和操作系统
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            browser, os = parse_user_agent(user_agent)
            
            # 获取IP地理位置信息
            location_info = get_ip_location(client_ip)
            
            # 记录登录日志（使用事务保证数据一致性）
            with transaction.atomic():
                LoginLog.objects.create(
                    username=user_profile.user.username,
                    ip=client_ip,
                    agent=user_agent,
                    browser=browser,
                    os=os,
                    continent=location_info.get('continent'),
                    country=location_info.get('country'),
                    province=location_info.get('province'),
                    city=location_info.get('city'),
                    district=location_info.get('district'),
                    isp=location_info.get('isp'),
                    area_code=location_info.get('area_code'),
                    country_english=location_info.get('country_english'),
                    country_code=location_info.get('country_code'),
                    longitude=location_info.get('longitude'),
                    latitude=location_info.get('latitude'),
                )
            
            # 更新用户最后登录时间
            user_profile.user.last_login = timezone.now()
            user_profile.user.save(update_fields=['last_login'])
            
            # 获取用户权限（返回可序列化的权限代码名称列表）
            permissions = self.permission_checker.get_user_permission_codenames(user_profile.user)
            
            # 构建响应数据（匹配前端期望的字段名）
            response_data = {
                'access': access_token,
                'refresh': refresh_token,
                'user_id': user_profile.id,
                'username': user_profile.user.username,
                'user': {
                    'id': user_profile.id,
                    'username': user_profile.user.username,
                    'name': user_profile.name,
                    'email': user_profile.user.email,
                    'avatar': str(user_profile.avatar) if user_profile.avatar else None,
                    'roles': [role.name for role in user_profile.roles.all()],
                    'permissions': permissions,
                },
            }
            
            # 清除用户相关缓存
            self.cache_manager.delete_pattern(f'user_permissions_{user_profile.id}_*')
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return Response({"error": "登录失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """用户登出接口
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Response: 登出结果响应
        """
        try:
            # 获取用户信息
            user = request.user
            
            if user.is_authenticated:
                # 清除用户token缓存
                self.cache_manager.delete_pattern(f'token_{user.id}_*')
                
                # 清除用户权限缓存
                self.cache_manager.delete_pattern(f'user_permissions_{user.id}_*')
                
                logger.info(f"用户 {user.username} 已登出")
            
            return Response({"message": "登出成功"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"登出失败: {str(e)}")
            return Response({"error": "登出失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """刷新令牌接口
        
        Args:
            request: HTTP请求对象，包含refresh_token
            
        Returns:
            Response: 刷新结果响应，包含新的token
        """
        try:
            # 获取refresh_token
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return Response({"error": "refresh_token不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用simplejwt验证refresh_token并生成新的access_token
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            # 构建响应数据
            response_data = {
                'access': access_token,
                'refresh': str(refresh),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"刷新令牌失败: {str(e)}")
            return Response({"error": "无效的refresh_token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """重置密码接口
        
        Args:
            request: HTTP请求对象，包含username和new_password
            
        Returns:
            Response: 重置密码结果响应
        """
        try:
            # 获取请求数据
            username = request.data.get('username')
            new_password = request.data.get('new_password')
            
            # 参数验证
            if not username or not new_password:
                return Response({"error": "用户名和新密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 查询用户
            try:
                user = UserProfile.objects.get(username=username)
            except ObjectDoesNotExist:
                return Response({"error": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            # 更新密码
            user.set_password(new_password)
            user.save()
            
            # 清除用户相关缓存
            self.cache_manager.delete_pattern(f'user_permissions_{user.id}_*')
            
            logger.info(f"用户 {user.username} 密码已重置")
            
            return Response({"message": "密码重置成功"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"重置密码失败: {str(e)}")
            return Response({"error": "重置密码失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """验证用户登录状态接口
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Response: 用户信息或未登录状态
        """
        try:
            user = request.user
            
            if not user.is_authenticated:
                return Response({"detail": "未登录"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 获取用户资料
            user_profile = UserProfile.objects.get(user=user)
            permissions = self.permission_checker.get_user_permission_codenames(user)
            
            response_data = {
                'user_id': user_profile.id,
                'username': user.username,
                'name': user_profile.name,
                'email': user.email,
                'roles': [role.name for role in user_profile.roles.all()],
                'permissions': permissions,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"验证登录状态失败: {str(e)}")
            return Response({"detail": "验证失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)