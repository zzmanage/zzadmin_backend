import logging
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class MonitorBaseViewSet(viewsets.ViewSet):
    """系统监控基础视图集
    
    提供系统监控功能中所有视图集的公共基类，包含身份验证、权限控制、日志记录等通用功能
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.operation_module = "系统监控"
        self.permission_value = "monitor_view"
    
    def handle_monitor_exception(self, exc, default_message="操作失败", fallback_data=None):
        """统一的异常处理方法，支持默认消息和fallback数据
        
        Args:
            exc: 异常对象
            default_message: 默认错误消息
            fallback_data: 发生异常时返回的备用数据
            
        Returns:
            Response: 统一格式的错误响应
        """
        logger.error(f"监控功能异常: {str(exc)}")
        
        # 尝试获取异常的消息
        error_message = str(exc) if str(exc) else default_message
        
        # 如果提供了fallback_data，返回包含该数据的成功响应
        if fallback_data is not None:
            return self.success_response(data=fallback_data, message=error_message)
        
        # 否则返回错误响应
        return self.error_response(message=error_message)
    
    def handle_exception(self, exc):
        """处理异常并记录日志"""
        logger.error(f"监控功能异常: {str(exc)}")
        return super().handle_exception(exc)
    
    def success_response(self, data=None, message="操作成功"):
        """统一的成功响应格式"""
        return Response({
            "code": 200,
            "message": message,
            "data": data or {}
        }, status=status.HTTP_200_OK)
    
    def error_response(self, message="操作失败", code=400):
        """统一的错误响应格式"""
        return Response({
            "code": code,
            "message": message,
            "data": {}
        }, status=status.HTTP_400_BAD_REQUEST)