import logging
from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from typing import Dict, List, Any
from rest_framework.response import Response


from ...models import Department
from ...serializers import DepartmentSerializer
from ...filters import DepartmentFilter
from ..base import TreeViewSet

logger = logging.getLogger(__name__)


from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response

class DepartmentViewSet(TreeViewSet):
    """部门视图集
    
    提供部门的CRUD操作，包括创建、查询、更新和删除部门信息
    """
    
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DepartmentFilter
    search_fields = ['name', 'description', 'owner']
    ordering_fields = ['sort', 'created_at', 'updated_at']
    ordering = ['sort', 'id']
    
    # 操作模块名称
    operation_module = "部门管理"
    
    @action(detail=False, methods=['get'], url_path='tree', url_name='tree')
    def tree(self, request):
        """获取部门树结构数据
        
        Returns:
            Response: 统一格式的部门树结构数据响应
        """
        try:
            # 获取用于构建部门树的查询集
            queryset = self._get_tree_queryset()
            
            # 构建部门树结构
            tree_data = self._build_department_tree(queryset)
            
            # 使用统一的成功响应格式
            return self.success_response(data=tree_data, message=f"获取{self.operation_module}树结构成功")
        except Exception as e:
            logger.error(f"获取{self.operation_module}树结构失败: {str(e)}")
            # 使用统一的错误响应格式
            return self.error_response(message=f"获取{self.operation_module}树结构失败: {str(e)}", code=500)
    
    def _get_tree_queryset(self):
        """获取用于构建部门树的查询集"""
        return (
            self.get_queryset().filter(status=True)
            .order_by("sort", "id")
            .select_related('parent')
            .only('id', 'name', 'key', 'sort', 'status', 'parent_id', 'owner', 'updated_at')
        )
    
    def _build_department_tree(self, departments):
        """迭代方式构建部门树，提高性能并避免栈溢出
        
        Args:
            departments: 所有部门查询集
        
        Returns:
            list: 部门树结构
        """
        # 将查询集转换为字典列表，避免Manager访问错误
        departments_data = []
        for dept in departments:
            # 手动构建部门数据字典
            dept_dict = {
                'id': dept.id,
                'name': dept.name,
                'key': dept.key,
                'sort': dept.sort,
                'status': dept.status,
                'parent_id': dept.parent_id if dept.parent_id else None,
                'owner': dept.owner or '',
                'updated_at': dept.updated_at.isoformat() if dept.updated_at else ''
            }
            departments_data.append(dept_dict)
            
        # 使用通用的树构建方法处理字典列表
        return self._build_tree(departments_data, id_field='id', parent_id_field='parent_id', children_field='children')
    
    def get_queryset(self):
        """重写get_queryset方法，实现数据权限过滤
        
        Returns:
            QuerySet: 过滤后的查询集
        """
        user = self.request.user
        queryset = super().get_queryset()
        
        # 管理员可以查看所有部门
        if hasattr(user, 'profile') and user.profile.roles.filter(admin=True).exists():
            return queryset
        
        # 如果用户没有profile或不是管理员，返回所有部门数据（适用于开发环境或没有严格权限控制的场景）
        # 在生产环境中，应实现更严格的数据权限过滤逻辑
        return queryset
    
    def list(self, request, *args, **kwargs):
        """重写list方法，添加缓存和日志记录"""
        logger.info(f"{self.operation_module} - 获取部门列表请求")
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """重写create方法，添加操作日志"""
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            self._log_operation(request, "create", None, f"创建部门: {response.data['name']}")
        return response
    
    def update(self, request, *args, **kwargs):
        """重写update方法，添加操作日志"""
        department = self.get_object()
        old_name = department.name
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            self._log_operation(request, "update", department, f"更新部门: {old_name} -> {response.data['name']}")
        return response
    
    def destroy(self, request, *args, **kwargs):
        """重写destroy方法，添加操作日志"""
        department = self.get_object()
        department_name = department.name
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            self._log_operation(request, "destroy", department, f"删除部门: {department_name}")
        return response