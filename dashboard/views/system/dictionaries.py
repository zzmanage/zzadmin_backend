# -*- coding: utf-8 -*-
import logging
from rest_framework import permissions, filters, status, serializers, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError
from django.core.exceptions import MultipleObjectsReturned
from ...models import Dictionary
from ...serializers import DictionarySerializer
from ...filters import DictionaryFilter
from ..base import BaseViewSet

logger = logging.getLogger(__name__)


class DictionaryViewSet(BaseViewSet):
    """字典视图集
    
    提供字典的CRUD操作以及字典项相关功能
    """
    
    queryset = Dictionary.objects.all()
    serializer_class = DictionarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DictionaryFilter
    search_fields = ['label', 'value', 'remark']
    ordering_fields = ['sort', 'created_at', 'updated_at']
    ordering = ['sort']
    
    # 操作模块名称
    operation_module = "字典管理"
    
    @action(detail=False, methods=["post"], url_path="refresh_cache")
    def refresh_cache(self, request):
        """刷新所有字典缓存
        
        Returns:
            Response: 刷新结果信息
        """
        try:
            # 清除所有字典相关缓存
            self._clear_dictionary_caches()
            logger.info("字典缓存已成功刷新")
            return Response(
                {"detail": "字典缓存已成功刷新"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"刷新字典缓存失败: {str(e)}")
            return Response(
                {"error": "刷新字典缓存失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["get"])    
    def items(self, request, pk=None):
        """获取指定字典ID或value的子字典项列表
        
        Args:
            pk: 字典ID或字典value
        
        Returns:
            Response: 子字典项列表数据
        """
        # 权限检查已在中间件中实现
        try:
            # 获取字典对象，优先尝试按ID查找，然后尝试按value查找
            logger.debug(f"从数据库获取字典对象")
            
            # 尝试按ID或value查找字典
            dictionary = None
            try:
                # 首先尝试将pk转换为整数，按ID查找字典
                dict_id = int(pk)
                dictionary = self.get_object()
                logger.debug(f"通过ID找到字典对象: {dictionary.label} ({dictionary.value})")
            except (ValueError, Exception):
                # 如果无法转换为整数或按ID查找失败，尝试按value查找
                logger.debug(f"通过ID查找失败，尝试按value查找")
                try:
                    dictionary = self.get_queryset().get(value=pk)
                    logger.debug(f"通过value找到字典对象: {dictionary.label} ({dictionary.value})")
                except Dictionary.DoesNotExist:
                    logger.error(f"获取字典项列表失败: 字典ID或value {pk} 不存在")
                    return Response({"error": "字典不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            # 如果仍然找不到字典，返回404
            if not dictionary:
                logger.error(f"获取字典项列表失败: 字典ID或value {pk} 不存在")
                return Response({"error": "字典不存在"}, status=status.HTTP_404_NOT_FOUND)

            # 通过related_name 'sublist'获取所有子字典项
            # 筛选出status为True（启用状态）的子字典项，并按sort字段排序
            # 使用only限制查询字段，提高查询效率
            logger.debug(f"查询字典的子字典项")
            query = dictionary.sublist.all()  # 修改为返回所有状态的字典项
            
            # 处理label搜索参数
            label_param = request.GET.get('label')
            if label_param:
                logger.debug(f"应用label搜索过滤: {label_param}")
                query = query.filter(label__icontains=label_param)
            
            sub_items = query.order_by("sort").only(
                'id', 'label', 'value', 'sort', 'status', 'remark'
            )
            logger.debug(f"查询子字典项成功，数量: {sub_items.count()}")

            # 序列化子字典项数据
            logger.debug(f"开始序列化子字典项数据")
            serializer = self.get_serializer(sub_items, many=True)
            serialized_data = serializer.data
            logger.debug(f"序列化成功，数据长度: {len(serialized_data)}")

            logger.debug(f"准备返回字典项列表数据")

            # 返回序列化后的数据
            return Response(serialized_data)
        except Dictionary.DoesNotExist:
            logger.error(f"获取字典项列表失败: 字典ID或value {pk} 不存在")
            return Response({"error": "字典不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"获取字典项列表失败: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return Response(
                {"error": "获取字典项列表失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _clear_dictionary_caches(self, identifier=None):
        """清除字典缓存
        
        Args:
            identifier: 可选，指定要清除的字典ID或字典value。如果未提供，则清除所有字典缓存
        """
        # 利用BaseViewSet提供的缓存机制清除相关缓存
        logger.debug(f"清除字典相关缓存")
        # 由于items方法已移除自定义缓存，此方法不再需要具体实现

    def create(self, request, *args, **kwargs):
        """重写创建方法，添加缓存清除逻辑和验证处理
        
        同时支持创建字典和字典项，字典项创建时通过parent_id指定父节点
        """
        try:
            # 手动执行序列化和验证，避免异常被装饰器捕获
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 验证通过后，执行保存操作
            self.perform_create(serializer)
            
            # 清除缓存
            dictionary = serializer.instance
            if dictionary.parent:
                # 如果是字典项，清除父字典的缓存
                self._clear_dictionary_caches(dictionary.parent.id)
                self._clear_dictionary_caches(dictionary.parent.value)
            else:
                # 如果是顶层字典，清除所有字典缓存
                self._clear_dictionary_caches()
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except serializers.ValidationError as e:
            # 直接返回验证错误，不经过装饰器的异常处理
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 其他异常仍然让装饰器处理
            raise
    
    def update(self, request, *args, **kwargs):
        """重写更新方法，添加缓存清除逻辑
        
        只支持通过ID更新字典和字典项
        """
        try:
            # 先检查对象是否存在
            try:
                dict_id = kwargs.get('pk')
                # 尝试直接查询数据库检查对象是否存在
                dictionary = self.get_queryset().get(pk=dict_id)
            except self.get_queryset().model.DoesNotExist:
                logger.error(f"更新字典失败: 字典ID '{dict_id}' 不存在")
                return Response(
                    {"error": "未找到"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # 执行更新操作
            response = super().update(request, *args, **kwargs)
            
            if response.status_code < 400:
                # 清除相关缓存
                if dictionary.parent:
                    self._clear_dictionary_caches(dictionary.parent.id)
                else:
                    self._clear_dictionary_caches()
            return response
        except Exception as e:
            logger.error(f"更新字典失败: {str(e)}")
            return Response(
                {"error": "更新字典失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """重写删除方法，添加缓存清除逻辑和ProtectedError处理
        
        只支持通过ID删除字典和字典项
        """
        try:
            # 先检查对象是否存在
            try:
                dict_id = kwargs.get('pk')
                # 尝试直接查询数据库检查对象是否存在
                dictionary = self.get_queryset().get(pk=dict_id)
            except self.get_queryset().model.DoesNotExist:
                logger.error(f"删除字典失败: 字典ID '{dict_id}' 不存在")
                return Response(
                    {"error": "未找到"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # 检查是否要删除的是字典项（有父节点）
            if dictionary.parent:
                # 删除字典项，不检查子字典项
                logger.debug(f"删除字典项: ID={dictionary.id}, label={dictionary.label}")
                parent_id = dictionary.parent.id
                
                # 执行删除操作
                self.perform_destroy(dictionary)
                
                # 清除父字典的缓存
                self._clear_dictionary_caches(parent_id)
                
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                # 删除顶层字典，检查是否有子字典项
                if dictionary.sublist.exists():
                    logger.warning(f"删除字典失败: ID为{dictionary.id}的字典 '{dictionary.label}' 有子字典项，无法直接删除")
                    return Response(
                        {"error": "字典存在子字典项，无法直接删除，请先删除子字典项"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 执行删除操作
                self.perform_destroy(dictionary)
                
                # 清除所有字典缓存
                self._clear_dictionary_caches()
                
                return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            logger.error(f"删除字典失败: 存在保护关系，错误信息: {str(e)}")
            return Response(
                {"error": "删除失败，该字典被其他数据引用"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"删除字典失败: {str(e)}")
            return Response(
                {"error": "删除字典失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_queryset(self):
        """获取基础查询集"""
        # 调用父类方法获取基础查询集（包含FilterMixin的过滤和数据权限过滤）
        queryset = super().get_queryset()
        
        # 优化查询，只选择必要的字段
        queryset = queryset.only(
            'id', 'label', 'value', 'sort', 'status', 'parent_id', 'remark'
        )
        
        logger.debug(f"获取查询集: {queryset.count()}个字典对象")
        return queryset
        
    def filter_queryset(self, queryset):
        # 先调用父类方法应用其他过滤器
        filtered_queryset = super().filter_queryset(queryset)
        
        # 对parent参数进行特殊处理
        # 使用request.GET而不是request.query_params以确保兼容性
        parent_param = self.request.GET.get('parent', None)
        if parent_param is not None:
            # 处理空值情况：如果传入null、none、空字符串或空格，返回parent为null的字典
            if parent_param.lower() in ("null", "none") or parent_param.strip() == "":
                filtered_queryset = filtered_queryset.filter(parent__isnull=True)
            else:
                # 尝试将value转换为整数，过滤parent_id等于该值的字典
                try:
                    parent_id = int(parent_param)
                    filtered_queryset = filtered_queryset.filter(parent_id=parent_id)
                except (ValueError, TypeError):
                    # 如果无法转换为整数，返回空查询集
                    filtered_queryset = filtered_queryset.none()
        
        # 保留基本的调试信息
        logger.debug(f"最终过滤后查询集大小: {filtered_queryset.count()}")
        logger.debug(f"最终过滤后的查询集: {[dict(id=obj.id, parent_id=obj.parent_id, label=obj.label) for obj in filtered_queryset[:5]]}")
        
        return filtered_queryset
        
    def list(self, request, *args, **kwargs):
        """获取字典列表"""
        # BaseViewSet基类已实现缓存逻辑，直接调用父类方法
        return super().list(request, *args, **kwargs)