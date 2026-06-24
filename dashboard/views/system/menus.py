"""
系统菜单管理视图
提供菜单管理的CRUD操作
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from ...models import Menu
from ...serializers import MenuSerializer
from ..base import BaseViewSet


class MenuViewSet(BaseViewSet):
    """菜单视图集"""
    
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return Menu.objects.all()
        
        # 普通用户只能查看有权限的菜单
        return Menu.objects.filter(
            menubutton__role__userprofile__user=user
        ).distinct()
    
    def create(self, request, *args, **kwargs):
        """创建菜单"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权创建菜单'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, pk=None):
        """更新菜单"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权更新菜单'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, pk)
    
    def destroy(self, request, pk=None):
        """删除菜单"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权删除菜单'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, pk)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取菜单树形结构"""
        user = request.user
        
        if user.is_superuser:
            menus = Menu.objects.all()
        else:
            menus = Menu.objects.filter(
                menubutton__role__userprofile__user=user
            ).distinct()
        
        serializer = self.get_serializer(menus, many=True)
        menu_list = serializer.data
        
        # 构建树形结构
        def build_tree(items, parent_id=None):
            tree = []
            for item in items:
                # 获取父ID：可能是 parent 字段（对象或ID）或 parent_id 字段
                item_parent_id = item.get('parent_id')
                if item_parent_id is None:
                    # 如果没有 parent_id，尝试从 parent 字段获取
                    parent_obj = item.get('parent')
                    if parent_obj is not None:
                        if isinstance(parent_obj, dict):
                            item_parent_id = parent_obj.get('id')
                        else:
                            item_parent_id = parent_obj
                
                if item_parent_id == parent_id:
                    children = build_tree(items, item.get('id'))
                    if children:
                        item['children'] = children
                    else:
                        item['children'] = []
                    tree.append(item)
            return tree
        
        tree_data = build_tree(menu_list)
        return Response(tree_data)
    
    @action(detail=False, methods=['get'])
    def user_menus(self, request):
        """获取当前用户的菜单列表"""
        user = request.user
        
        if user.is_superuser:
            # 超级用户获取所有菜单
            menus = Menu.objects.all()
        else:
            # 普通用户获取有权限的菜单
            menus = Menu.objects.filter(
                menubutton__role__userprofile__user=user
            ).distinct()
        
        serializer = self.get_serializer(menus, many=True)
        return Response(serializer.data)
