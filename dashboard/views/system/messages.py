import logging
from rest_framework import permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Max
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from ...models import Message, UserMessage
from ...serializers import MessageSerializer, UserMessageSerializer
from ...filters import UserMessageFilter
from ..base import BaseViewSet

logger = logging.getLogger(__name__)


class MessageViewSet(BaseViewSet):
    """消息视图集
    
    提供系统消息的管理功能，包括创建、查看、更新和删除系统消息
    """
    
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'message_type', 'priority', 'sender__username']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    # 操作模块名称
    operation_module = "消息管理"
    
    def create(self, request, *args, **kwargs):
        """创建消息并发送给指定的用户或部门
        
        Returns:
            Response: 创建结果响应
        """
        # 权限检查已在中间件中实现
        
        try:
            # 使用事务确保数据一致性
            with transaction.atomic():
                data = request.data.copy()
                # 设置发送者为当前用户
                data['sender'] = request.user.id
                
                # 获取接收类型和目标 - 根据新模型定义: 0-全部, 1-部门, 2-角色, 3-指定用户
                receive_type = int(data.get('receive_type', 0))
                
                # 处理接收目标，确保是数组格式
                receive_target = data.get('receive_target')
                if receive_target is None:
                    receive_target = []
                elif isinstance(receive_target, int) or isinstance(receive_target, str):
                    # 单个ID转换为数组
                    receive_target = [int(receive_target)]
                else:
                    # 确保所有元素都是整数
                    receive_target = [int(target) for target in receive_target]
                
                # 验证接收目标
                if receive_type in [1, 2, 3] and not receive_target:
                    return Response({"error": "请选择接收对象"}, status=status.HTTP_400_BAD_REQUEST)
                
                # 序列化并创建消息
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                message = serializer.save()
                
                # 获取所有接收用户
                recipients = []
                from ...models import UserProfile, Department, Role
                
                if receive_type == 0:
                    # 发送给全部用户
                    recipients = UserProfile.objects.all()
                elif receive_type == 1:
                    # 发送给部门
                    departments = Department.objects.filter(id__in=receive_target)
                    # 优化: 使用in查询一次性获取所有部门用户
                    dept_ids = [dept.id for dept in departments]
                    recipients = UserProfile.objects.filter(department_id__in=dept_ids)
                elif receive_type == 2:
                    # 发送给角色
                    roles = Role.objects.filter(id__in=receive_target)
                    # 获取拥有这些角色的所有用户
                    recipients = UserProfile.objects.filter(roles__in=roles).distinct()
                elif receive_type == 3:
                    # 发送给指定用户
                    recipients = UserProfile.objects.filter(id__in=receive_target)
                
                # 优化1: 使用bulk_create批量创建用户消息记录
                user_messages = []
                for recipient in recipients:
                    # recipient是UserProfile对象，需要获取关联的User实例
                    user_messages.append(UserMessage(message=message, recipient=recipient.user))
                
                # 批量创建用户消息记录
                UserMessage.objects.bulk_create(user_messages)
                
                # 优化2: 使用线程池异步处理WebSocket通知，避免阻塞
                try:
                    from ...consumers import send_notification_to_user
                    import threading
                    
                    for recipient in recipients:
                        # 创建一个线程用于异步发送WebSocket消息
                        thread = threading.Thread(
                            target=send_notification_to_user,
                            args=(recipient.id, {"message_id": message.id, "title": message.title}),
                        )
                        thread.daemon = True
                        thread.start()
                except Exception as e:
                    logger.warning(f"WebSocket通知失败: {str(e)}")
                    # WebSocket通知失败不应影响API响应
                
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # 详细日志记录将由全局中间件处理
            logger.error(f"消息创建失败: {str(e)}")
            # 抛出异常让全局中间件处理，确保响应格式统一
            raise


class UserMessageViewSet(BaseViewSet):
    """用户消息视图集
    
    提供用户消息的管理功能，包括查看、标记已读和删除用户消息
    """
    
    queryset = UserMessage.objects.all()
    serializer_class = UserMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserMessageFilter
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    # 操作模块名称
    operation_module = "用户消息管理"
    
    def get_queryset(self):
        """获取当前用户的消息查询集
        
        Returns:
            QuerySet: 过滤后的用户消息查询集
        """
        user = self.request.user
        # 缓存键，包含用户ID和请求参数
        cache_key = f'user_message_queryset_{user.id}_{self.request.GET.urlencode()}'
        # 尝试从缓存获取数据
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            return cached_queryset

        # 限制查询字段，只获取必要的信息
        queryset = super().get_queryset()
        
        # 只返回当前用户的消息
        queryset = queryset.filter(recipient=user).only(
            'id', 'message__id', 'message__title', 'message__content', 
            'message__message_type', 'message__priority', 'is_read', 'created_at'
        )

        # 缓存查询结果1分钟
        cache.set(cache_key, queryset, 60)

        return queryset
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读消息数量
        
        Returns:
            Response: 未读消息数量
        """
        try:
            # 缓存键，基于用户ID
            cache_key = f'user_message_unread_count_{request.user.id}'
            # 尝试从缓存获取数据
            cached_count = cache.get(cache_key)
            if cached_count is not None:
                return Response({'count': cached_count})

            # 查询未读消息数量
            count = UserMessage.objects.filter(recipient=request.user, is_read=False).count()
            
            # 缓存结果1分钟
            cache.set(cache_key, count, 60)
            
            return Response({'count': count})
        except Exception as e:
            logger.error(f"获取未读消息数量失败: {str(e)}")
            return Response({"error": "获取未读消息数量失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记消息为已读
        
        Args:
            pk: 用户消息ID
        
        Returns:
            Response: 标记结果响应
        """
        try:
            # 获取用户消息对象
            user_message = self.get_object()
            # 确保消息属于当前用户
            if user_message.recipient != request.user:
                return Response({"error": "无权操作此消息"}, status=status.HTTP_403_FORBIDDEN)
            
            # 标记为已读
            user_message.is_read = True
            user_message.save()
            
            # 清除相关缓存
            self._clear_user_message_caches()
            
            return Response({"message": "消息已标记为已读"})
        except Exception as e:
            logger.error(f"标记消息已读失败: {str(e)}")
            return Response({"error": "标记消息已读失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有消息为已读
        
        Returns:
            Response: 标记结果响应
        """
        try:
            # 更新当前用户的所有未读消息
            updated_count = UserMessage.objects.filter(
                recipient=request.user, is_read=False
            ).update(is_read=True)
            
            # 清除相关缓存
            self._clear_user_message_caches()
            
            return Response({"message": f"成功标记{updated_count}条消息为已读"})
        except Exception as e:
            logger.error(f"标记所有消息已读失败: {str(e)}")
            return Response({"error": "标记所有消息已读失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        """标记消息为已处理
        
        Args:
            pk: 用户消息ID
        
        Returns:
            Response: 标记结果响应
        """
        try:
            # 获取用户消息对象
            user_message = self.get_object()
            # 确保消息属于当前用户
            if user_message.recipient != request.user:
                return Response({"error": "无权操作此消息"}, status=status.HTTP_403_FORBIDDEN)
            
            # 标记为已处理
            user_message.is_processed = True
            user_message.processed_at = timezone.now()
            user_message.save()
            
            # 清除相关缓存
            self._clear_user_message_caches()
            
            return Response({"message": "消息已标记为已处理"})
        except Exception as e:
            logger.error(f"标记消息已处理失败: {str(e)}")
            return Response({"error": "标记消息已处理失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def mark_all_processed(self, request):
        """标记所有消息为已处理
        
        Returns:
            Response: 标记结果响应
        """
        try:
            # 更新当前用户的所有未处理消息
            updated_count = UserMessage.objects.filter(
                recipient=request.user, is_processed=False
            ).update(is_processed=True, processed_at=timezone.now())
            
            # 清除相关缓存
            self._clear_user_message_caches()
            
            return Response({"message": f"成功标记{updated_count}条消息为已处理"})
        except Exception as e:
            logger.error(f"标记所有消息已处理失败: {str(e)}")
            return Response({"error": "标记所有消息已处理失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _clear_user_message_caches(self):
        """清除用户消息相关的缓存，兼容不同的缓存后端"""
        user_id = self.request.user.id
        # 尝试使用delete_pattern方法清除查询集缓存（某些缓存后端如Redis支持）
        if hasattr(cache, 'delete_pattern'):
            try:
                cache.delete_pattern(f'user_message_queryset_{user_id}_*')
            except Exception:
                # 如果delete_pattern调用失败，记录日志并继续
                logger.debug("尝试清除用户消息查询集缓存时出错，跳过此操作")
        # 直接使用delete方法清除未读消息数量缓存（所有缓存后端都支持）
        cache.delete(f'user_message_unread_count_{user_id}')
    
    def destroy(self, request, *args, **kwargs):
        """删除用户消息
        
        Returns:
            Response: 删除结果响应
        """
        try:
            # 获取用户消息对象
            user_message = self.get_object()
            # 确保消息属于当前用户
            if user_message.recipient != request.user:
                return Response({"error": "无权操作此消息"}, status=status.HTTP_403_FORBIDDEN)
            
            # 删除用户消息
            user_message.delete()
            
            # 清除相关缓存
            self._clear_user_message_caches()
            
            return Response({"message": "消息已删除"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"删除消息失败: {str(e)}")
            return Response({"error": "删除消息失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)