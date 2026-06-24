import logging
from rest_framework import permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from typing import List, Dict, Any

from ...models import MenuButton, Menu
from ...serializers import PermissionSerializer
from ...filters import MenuButtonFilter
from ..base import BaseViewSet

import logging

logger = logging.getLogger(__name__)


class PermissionViewSet(BaseViewSet):
    """权限视图集
    
    提供权限的CRUD操作以及权限树相关功能
    """
    
    queryset = MenuButton.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MenuButtonFilter
    search_fields = ['name', 'value', 'api', 'method', 'menu__name']
    ordering_fields = ['menu__sort', 'sort', 'created_at', 'updated_at']
    ordering = ['menu__sort', 'sort']
    
    # 操作模块名称
    operation_module = "权限管理"

    # 权限是系统级数据，不按租户过滤
    enable_tenant_filter = False
    
    @action(detail=False, methods=["get"])
    def tree(self, request):
        """获取完整的权限树（包含菜单和按钮）
        
        优化树构建逻辑，避免重复查询和递归深度过大问题
        
        Returns:
            Response: 权限树数据
        """
        # 权限检查已在中间件中实现
        
        try:
            # 构建缓存键，使用基类的方法
            cache_key = self.get_cache_key('tree')
            
            # 尝试从缓存获取数据
            cached_tree = self._get_cached_data(cache_key)
            if cached_tree:
                return Response(cached_tree)
            
            # 优化查询：使用prefetch_related同时获取菜单和关联的按钮权限
            menus = (
                Menu.objects.filter(is_deleted=False)
                .order_by("sort")
                .select_related('parent')
                .prefetch_related(
                    Prefetch('menuPermission',
                             queryset=MenuButton.objects.only(
                                 'id', 'name', 'value', 'api', 'method', 'sort'
                             ))
                )
                .only(
                    'id', 'name', 'sort', 'parent_id', 'status',
                    'web_path', 'component', 'icon', 'visible'
                )
            )
            
            # 构建权限树
            menu_tree = self._build_permission_tree(menus)
            
            # 缓存权限树，设置过期时间为10分钟
            self._set_cached_data(cache_key, menu_tree, 600)
            
            return Response(menu_tree)
        except Exception as e:
            logger.error(f"获取权限树失败: {str(e)}")
            return Response(
                {"error": "获取权限树失败"},
                status=400,
            )
    
    def _build_permission_tree(self, menus):
        """迭代方式构建权限树，提高性能并避免栈溢出
        
        Args:
            menus: 所有菜单查询集
        
        Returns:
            list: 权限树结构数据
        """
        # 创建节点映射字典，方便快速查找父节点
        node_map = {}
        root_nodes = []
        
        # 1. 先将所有菜单节点放入字典中，并找出根节点
        for menu in menus:
            # 复制菜单数据
            menu_data = {
                "id": menu.id,
                "name": menu.name,
                "web_path": menu.web_path,
                "component": menu.component,
                "icon": menu.icon,
                "visible": menu.visible,
                "sort": menu.sort,
                "children": []  # 初始化子节点列表
            }
            
            node_map[menu.id] = menu_data
            
            # 记录根节点（parent_id为None的节点）
            if menu.parent_id is None:
                root_nodes.append(menu_data)
        
        # 2. 构建父子关系
        for menu in menus:
            if menu.parent_id is not None and menu.parent_id in node_map:
                # 如果当前节点有父节点且父节点存在于映射中
                parent_node = node_map[menu.parent_id]
                current_node = node_map[menu.id]
                parent_node['children'].append(current_node)
        
        # 3. 为每个菜单节点添加按钮权限
        for menu in menus:
            menu_node = node_map[menu.id]
            buttons = []
            
            # 从prefetch_related的结果中获取按钮权限
            for button in menu.menuPermission.all():
                button_data = {
                    "id": button.id,
                    "name": button.name,
                    "value": button.value,
                    "api": button.api,
                    "method": button.method,
                    "method_display": dict(MenuButton.METHOD_CHOICES).get(
                        button.method, ""
                    ),
                    "sort": button.sort,
                }
                buttons.append(button_data)
            
            # 对按钮按sort字段排序
            buttons.sort(key=lambda x: x.get('sort', 0))
            
            # 将按钮添加到菜单节点
            menu_node['buttons'] = buttons
        
        # 4. 对每个节点的子节点按sort字段排序
        for node_id, node in node_map.items():
            node['children'].sort(key=lambda x: x.get('sort', 0))
        
        # 对根节点按sort字段排序
        root_nodes.sort(key=lambda x: x.get('sort', 0))
        
        return root_nodes
    
    def _invalidate_cache_on_update(self):
        """重写缓存失效方法，清除所有与权限相关的缓存
        
        除了调用基类的方法外，还需要清除角色权限树缓存和用户权限缓存
        """
        # 调用基类方法清除默认缓存
        super()._invalidate_cache_on_update()
        
        # 清除角色权限树缓存
        self._clear_pattern_caches('role_permissions_tree_*')
        
        # 清除用户权限缓存
        self._clear_pattern_caches('user_permissions_*')
    
    def create(self, request, *args, **kwargs):
        """重写创建方法，添加缓存清除逻辑"""
        response = super().create(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def update(self, request, *args, **kwargs):
        """重写更新方法，添加缓存清除逻辑"""
        response = super().update(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def destroy(self, request, *args, **kwargs):
        """重写删除方法，添加缓存清除逻辑"""
        response = super().destroy(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response