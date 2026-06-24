"""
视图基类模块
提供统一的视图基类，封装通用逻辑
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.response import APIResponse


class BaseViewSet(viewsets.ModelViewSet):
    """基础视图集"""

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return APIResponse.success(data=serializer.data, message="创建成功", code=201)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return APIResponse.success(data=serializer.data, message="更新成功")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message="删除成功")

    @action(detail=False, methods=['get'])
    def options(self, request):
        """获取选项数据"""
        queryset = self.get_queryset()
        options = [{'id': obj.id, 'name': str(obj)} for obj in queryset]
        return APIResponse.success(data=options)


class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """只读视图集"""

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)


class ActionViewSet(viewsets.ViewSet):
    """动作视图集"""

    def success_response(self, data=None, message="操作成功"):
        return APIResponse.success(data=data, message=message)

    def error_response(self, message="操作失败", code=400):
        return APIResponse.error(message=message, code=code)
