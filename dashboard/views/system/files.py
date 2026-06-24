import logging
import os
from rest_framework import permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.http import FileResponse

from ...models import File
from ...serializers import FileSerializer

from ..base import BaseViewSet

logger = logging.getLogger(__name__)


# 文件类型映射 - 将扩展名映射到类型分类
FILE_TYPE_MAP = {
    # 文档
    'doc': 'doc',
    'docx': 'doc',
    'txt': 'doc',
    'pdf': 'doc',
    'xls': 'doc',
    'xlsx': 'doc',
    'ppt': 'doc',
    'pptx': 'doc',
    'csv': 'doc',
    'md': 'doc',
    'json': 'doc',
    'xml': 'doc',
    # 图片
    'jpg': 'image',
    'jpeg': 'image',
    'png': 'image',
    'gif': 'image',
    'bmp': 'image',
    'webp': 'image',
    'svg': 'image',
    # 视频
    'mp4': 'video',
    'avi': 'video',
    'mov': 'video',
    'wmv': 'video',
    'flv': 'video',
    'mkv': 'video',
    # 音频
    'mp3': 'audio',
    'wav': 'audio',
    'ogg': 'audio',
    'flac': 'audio',
    'm4a': 'audio',
    # 压缩
    'zip': 'archive',
    'rar': 'archive',
    '7z': 'archive',
    'tar': 'archive',
    'gz': 'archive',
}


def get_file_category(file_name):
    """根据文件名获取文件类型分类"""
    ext = os.path.splitext(file_name)[1].lower().lstrip('.')
    if not ext:
        return 'other'
    return FILE_TYPE_MAP.get(ext, 'other')


class FileViewSet(BaseViewSet):
    """文件视图集
    
    提供文件的CRUD操作，包括文件上传、下载、查看和删除功能
    """
    
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'file_type', 'created_by__username']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    # 操作模块名称
    operation_module = "文件管理"
    
    def perform_create(self, serializer):
        """重写perform_create方法以处理文件上传的特定逻辑"""
        # 验证文件是否存在
        if 'file' not in self.request.FILES:
            raise ValueError("文件不能为空")
        
        file_obj = self.request.FILES['file']
        file_size = file_obj.size
        file_name = file_obj.name
        
        # 验证文件大小
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 默认10MB
        if file_size > max_size:
            raise ValueError(f"文件大小超过限制({max_size}字节)")
        
        # 构建文件路径和保存文件
        current_date = timezone.now()
        year = current_date.year
        month = current_date.month
        day = current_date.day
        
        # 创建目录（如果不存在）
        file_dir = os.path.join('files', str(year), f'{month:02d}', f'{day:02d}')
        os.makedirs(os.path.join(settings.MEDIA_ROOT, file_dir), exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(file_dir, file_name)
        file_full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        with open(file_full_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
        
        # 准备文件数据
        file_data = {
            'name': file_name,
            'file': file_path,
            'size': file_size,
            'file_type': get_file_category(file_name),
            'created_by': self.request.user.id,
            'description': self.request.data.get('description', ''),
        }
        
        # 更新serializer数据
        serializer.validated_data.update(file_data)
        super().perform_create(serializer)
    
    def perform_destroy(self, instance):
        """重写perform_destroy方法以处理文件删除的特定逻辑"""
        # 构建物理文件路径
        file_full_path = os.path.join(settings.MEDIA_ROOT, instance.file.name)
        
        # 先删除数据库记录
        super().perform_destroy(instance)
        
        # 尝试删除物理文件（如果存在）
        if os.path.exists(file_full_path):
            # 使用safe_api_call处理可能的异常
            success, _ = self.safe_api_call(os.remove, file_full_path)
            if not success:
                logger.warning(f"物理文件删除失败")
                # 物理文件删除失败不应影响API响应
    
    def create(self, request, *args, **kwargs):
        """使用BaseViewSet的create方法，同时处理文件上传的特定验证"""
        try:
            return super().create(request, *args, **kwargs)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """使用BaseViewSet的destroy方法"""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'], url_path='download', url_name='download')
    def download(self, request, pk=None):
        """下载文件
        
        Args:
            request: HTTP请求对象
            pk: 文件ID
        
        Returns:
            FileResponse: 文件下载响应
        """
        # 权限检查已在中间件中实现
        
        try:
            # 获取文件对象
            file_obj = self.get_object()
            
            # 构建物理文件路径
            file_full_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)
            
            # 检查文件是否存在
            if not os.path.exists(file_full_path):
                return Response({"error": "文件不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            # 更新下载统计信息
            with transaction.atomic():
                file_obj.download_count += 1
                file_obj.last_download_time = timezone.now()
                file_obj.save(update_fields=['download_count', 'last_download_time'])
            
            # 清除相关缓存
            self._invalidate_cache_on_update()
            
            # 创建文件响应
            response = FileResponse(open(file_full_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Length'] = file_obj.size
            
            return response
        except Exception as e:
            # 详细日志记录将由全局中间件处理
            logger.error(f"文件下载失败: {str(e)}")
            # 抛出异常让全局中间件处理，确保响应格式统一
            raise
    
    def _invalidate_cache_on_update(self):
        """清除文件相关的缓存，重写BaseViewSet的方法以提供特定的缓存清除逻辑"""
        try:
            # 尝试使用delete_pattern方法清除缓存（适用于Redis等缓存后端）
            cache.delete_pattern('file_queryset_*')
            logger.debug("使用delete_pattern方法成功清除文件缓存")
        except AttributeError:
            # 如果当前缓存后端不支持delete_pattern方法（如LocMemCache）
            # 我们需要使用更通用的方法来清除缓存
            logger.debug("当前缓存后端不支持delete_pattern方法，使用备用方案清除缓存")
            
            # 调用父类方法执行通用的缓存清除逻辑
            super()._invalidate_cache_on_update()
            
            # 方案1: 清除所有缓存（适用于开发环境或缓存数据量较小的情况）
            try:
                cache.clear()
                logger.debug("已清除所有缓存")
            except Exception as e:
                logger.error(f"清除缓存失败: {str(e)}")
                
            # 方案2: 为文件管理视图集单独设置版本号，通过版本号机制使缓存失效
            # 这里我们使用方案1，因为它更简单直接
    
    def get_queryset(self):
        """获取文件查询集，优化查询性能
        
        Returns:
            QuerySet: 过滤后的文件查询集
        """
        # 调用父类方法获取基础查询集（包含FilterMixin的过滤和数据权限过滤）
        queryset = super().get_queryset()
        
        # 优化查询，只选择必要的字段
        queryset = queryset.only(
            'id', 'name', 'file', 'size', 'file_type', 
            'created_by__id', 'created_by__username',
            'description', 'created_at'
        )
        
        return queryset