import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone

from ...models import UserProfile, Role, Menu, OperationLog, LoginLog, Department, Message, Post

logger = logging.getLogger(__name__)


class StatsViewSet(ViewSet):
    """统计数据视图集
    
    提供系统概览统计数据，包括用户统计、角色统计、菜单统计等
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """获取系统概览统计数据
        
        Returns:
            Response: 系统概览统计数据（格式匹配前端Dashboard期望）
        """
        # 构建缓存键，包含用户ID
        cache_key = f'stats_overview_{request.user.id}'
        
        # 尝试从缓存获取数据
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        try:
            # 用户统计
            total_users = UserProfile.objects.count()
            active_users = UserProfile.objects.filter(user__is_active=True).count()
            
            # 角色统计
            total_roles = Role.objects.count()
            
            # 权限统计（从角色权限关联表统计）
            total_permissions = 0
            for role in Role.objects.all():
                total_permissions += role.permissions.count()
            
            # 部门统计
            total_departments = Department.objects.count()
            
            # 岗位统计
            total_positions = Post.objects.count()
            
            # 操作日志统计（总数）
            total_operation_logs = OperationLog.objects.count()
            
            # 登录日志统计（总数）
            total_login_logs = LoginLog.objects.count()
            
            # 构建统计数据（格式匹配前端期望）
            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'total_roles': total_roles,
                'total_permissions': total_permissions,
                'total_departments': total_departments,
                'total_positions': total_positions,
                'total_operation_logs': total_operation_logs,
                'total_login_logs': total_login_logs,
            }
            
            # 缓存结果5分钟
            cache.set(cache_key, stats, 300)
            
            return Response(stats)
        except Exception as e:
            logger.error(f"获取系统概览统计数据失败: {str(e)}")
            return Response({"error": "获取统计数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def user_stats(self, request):
        """获取用户统计数据
        
        Returns:
            Response: 用户统计数据
        """
        # 构建缓存键，包含用户ID
        cache_key = f'stats_user_{request.user.id}'
        
        # 尝试从缓存获取数据
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        try:
            # 按部门统计用户数量
            department_stats = (
                Department.objects.annotate(user_count=Count('userprofile'))
                .values('id', 'name', 'user_count')
            )
            
            # 按角色统计用户数量
            role_stats = (
                Role.objects.annotate(user_count=Count('userprofile'))
                .values('id', 'name', 'user_count')
            )
            
            # 构建统计数据
            stats = {
                'department_stats': list(department_stats),
                'role_stats': list(role_stats),
            }
            
            # 缓存结果5分钟
            cache.set(cache_key, stats, 300)
            
            return Response(stats)
        except Exception as e:
            logger.error(f"获取用户统计数据失败: {str(e)}")
            return Response({"error": "获取用户统计数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def operation_stats(self, request):
        """获取操作日志统计数据
        
        Returns:
            Response: 操作日志统计数据
        """
        # 构建缓存键，包含用户ID
        cache_key = f'stats_operation_{request.user.id}'
        
        # 尝试从缓存获取数据
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        try:
            # 按操作类型统计
            action_stats = (
                OperationLog.objects.values('action')
                .annotate(count=Count('action'))
            )
            
            # 获取最近7天的操作统计
            days = []
            for i in range(6, -1, -1):
                date = timezone.now() - timezone.timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                count = OperationLog.objects.filter(
                    created_at__gte=date_start,
                    created_at__lte=date_end
                ).count()
                days.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count,
                })
            
            # 构建统计数据
            stats = {
                'action_stats': list(action_stats),
                'daily_stats': days,
            }
            
            # 缓存结果5分钟
            cache.set(cache_key, stats, 300)
            
            return Response(stats)
        except Exception as e:
            logger.error(f"获取操作日志统计数据失败: {str(e)}")
            return Response({"error": "获取操作日志统计数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='login-log')
    def login_log(self, request):
        """获取登录日志统计数据（支持日期范围筛选）
        
        Query Params:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            Response: 登录日志统计数据（格式匹配前端Dashboard期望）
        """
        try:
            # 获取日期参数
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # 构建查询
            queryset = LoginLog.objects.all()
            
            # 根据日期范围筛选
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)
            
            # 按登录类型统计
            login_type_distribution = (
                queryset.values('login_type')
                .annotate(count=Count('login_type'))
                .order_by('-count')
            )
            
            # 转换登录类型为中文名称（login_type是整数类型）
            type_mapping = {
                1: '普通登录',
                2: '普通扫码登录',
                3: '微信扫码登录',
                4: '飞书扫码登录',
                5: '钉钉扫码登录',
                6: '短信登录',
            }
            formatted_login_types = []
            for item in login_type_distribution:
                login_type = item['login_type']
                formatted_login_types.append({
                    'name': type_mapping.get(login_type, str(login_type)),
                    'count': item['count'],
                })
            
            # 按区域统计（模拟数据，实际需要IP解析）
            region_distribution = [
                {'name': '北京', 'count': 800},
                {'name': '上海', 'count': 600},
                {'name': '广州', 'count': 500},
                {'name': '深圳', 'count': 450},
                {'name': '杭州', 'count': 350},
                {'name': '其他', 'count': 510},
            ]
            
            # 按日期统计（最近7天）
            daily_logins = []
            for i in range(6, -1, -1):
                date = timezone.now() - timezone.timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                login_count = LoginLog.objects.filter(
                    created_at__gte=date_start,
                    created_at__lte=date_end
                ).count()
                daily_logins.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'login_count': login_count,
                    'active_user_count': int(login_count * 0.7),  # 模拟活跃用户数
                })
            
            # 构建响应数据（格式匹配前端期望）
            stats = {
                'login_type_distribution': formatted_login_types,
                'region_distribution': region_distribution,
                'daily_logins': daily_logins,
            }
            
            return Response(stats)
        except Exception as e:
            logger.error(f"获取登录日志统计数据失败: {str(e)}")
            return Response({"error": "获取登录日志统计数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def user(self, request):
        """获取用户统计数据（支持日期范围筛选）
        
        Query Params:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            Response: 用户统计数据（格式匹配前端Dashboard期望）
        """
        try:
            # 获取日期参数
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # 构建查询
            queryset = UserProfile.objects.all()
            
            # 根据日期范围筛选（按创建时间）
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)
            
            # 获取统计数据
            total_users = queryset.count()
            active_users = queryset.filter(user__is_active=True).count()
            
            # 按创建日期统计（获取最近7天数据）
            daily_growth = []
            for i in range(6, -1, -1):
                date = timezone.now() - timezone.timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                count = UserProfile.objects.filter(
                    created_at__gte=date_start,
                    created_at__lte=date_end
                ).count()
                daily_growth.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count,
                })
            
            # 构建响应数据（格式匹配前端期望）
            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'labels': [item['date'] for item in daily_growth],
                'data': [item['count'] for item in daily_growth],
            }
            
            return Response(stats)
        except Exception as e:
            logger.error(f"获取用户统计数据失败: {str(e)}")
            return Response({"error": "获取用户统计数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)