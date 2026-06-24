"""
系统角色管理视图
提供角色管理的CRUD操作
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from ...models import Role
from ...serializers import RoleSerializer
from ..base import BaseViewSet


class RoleViewSet(BaseViewSet):
    """角色视图集"""
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'key', 'description']
    ordering_fields = ['sort', 'created_at', 'updated_at']
    ordering = ['sort']
    
    @action(detail=False, methods=['get'])
    def all_list(self, request):
        """获取所有角色列表（不分页）"""
        queryset = Role.objects.all().order_by('sort')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return Role.objects.all()
        
        # 普通用户只能查看自己拥有的角色
        return Role.objects.filter(userprofile__user=user).distinct()
    
    def create(self, request, *args, **kwargs):
        """创建角色"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权创建角色'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, pk=None):
        """更新角色"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权更新角色'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, pk)
    
    def destroy(self, request, pk=None):
        """删除角色"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权删除角色'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, pk)
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """获取角色权限"""
        role = self.get_object()
        permissions = role.permissions.all()
        from ...serializers import MenuButtonSerializer
        serializer = MenuButtonSerializer(permissions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def permissions(self, request, pk=None):
        """分配角色权限"""
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        role.permissions.set(permission_ids)
        role.save()
        from ...serializers import MenuButtonSerializer
        permissions = role.permissions.all()
        serializer = MenuButtonSerializer(permissions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def permissions_tree(self, request, pk=None):
        """获取角色权限树"""
        role = self.get_object()
        # 返回角色权限的树形结构
        from ...models import Menu
        menus = Menu.objects.all()
        role_permission_ids = set(role.permissions.values_list('id', flat=True))
        
        def build_tree(items, parent_id=None):
            tree = []
            for item in items:
                if item.parent_id == parent_id:
                    children = build_tree(items, item.id)
                    has_permission = False
                    # 检查该菜单的按钮权限
                    buttons = item.menuPermission.all()
                    button_list = []
                    for btn in buttons:
                        checked = btn.id in role_permission_ids
                        has_permission |= checked
                        button_list.append({
                            'id': btn.id,
                            'name': btn.name,
                            'value': btn.value,
                            'checked': checked,
                        })
                    
                    tree.append({
                        'id': item.id,
                        'name': item.name,
                        'is_catalog': item.is_catalog,
                        'checked': has_permission,
                        'children': children,
                        'buttons': button_list,
                    })
            return tree
        
        tree_data = build_tree(list(menus))
        return Response(tree_data)
    
    @action(detail=True, methods=['post'])
    def update_permissions(self, request, pk=None):
        """更新角色权限（支持菜单和按钮）"""
        role = self.get_object()
        menu_ids = request.data.get('menu_ids', [])
        button_ids = request.data.get('button_ids', [])
        
        # 获取所有菜单关联的按钮权限
        from ...models import Menu, MenuButton
        all_permission_ids = set(button_ids)
        
        # 如果选择了菜单，自动选择其所有按钮权限
        for menu_id in menu_ids:
            try:
                menu = Menu.objects.get(id=menu_id)
                menu_button_ids = list(menu.menubutton_set.values_list('id', flat=True))
                all_permission_ids.update(menu_button_ids)
            except Menu.DoesNotExist:
                pass
        
        role.permissions.set(list(all_permission_ids))
        role.save()
        
        return Response({'detail': '权限更新成功', 'permission_count': len(all_permission_ids)})
