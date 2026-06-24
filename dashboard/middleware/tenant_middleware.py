"""
租户上下文中间件
自动从请求中识别租户并设置上下文
支持多种租户识别方式：
1. 请求头 X-Tenant-ID
2. 子域名识别
3. URL路径识别
"""
import re

from django.http import HttpRequest

from dashboard.utils.tenant_utils import set_current_tenant, clear_current_tenant


class TenantMiddleware:
    """租户上下文中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 从请求中获取租户ID
        tenant_id = self._get_tenant_id(request)
        
        # 设置租户上下文
        if tenant_id and request.user.is_authenticated:
            # 验证用户是否属于该租户
            from dashboard.models import TenantUser
            is_member = TenantUser.objects.filter(
                tenant_id=tenant_id,
                user=request.user,
                is_active=True
            ).exists()
            if is_member or request.user.is_superuser:
                set_current_tenant(tenant_id)
        
        try:
            response = self.get_response(request)
        finally:
            # 清理租户上下文
            clear_current_tenant()
        
        return response
    
    def _get_tenant_id(self, request: HttpRequest) -> int | None:
        """从请求中获取租户ID"""
        # 优先从请求头获取
        tenant_id = self._get_from_header(request)
        if tenant_id:
            return tenant_id
        
        # 其次从子域名获取
        tenant_id = self._get_from_domain(request)
        if tenant_id:
            return tenant_id
        
        # 最后从URL路径获取
        tenant_id = self._get_from_path(request)
        if tenant_id:
            return tenant_id
        
        return None
    
    def _get_from_header(self, request: HttpRequest) -> int | None:
        """从请求头 X-Tenant-ID 获取租户ID"""
        header_value = request.headers.get('X-Tenant-ID')
        if header_value:
            try:
                return int(header_value)
            except ValueError:
                return None
        return None
    
    def _get_from_domain(self, request: HttpRequest) -> int | None:
        """从子域名获取租户ID"""
        from dashboard.models import Tenant
        
        hostname = request.get_host().split(':')[0]  # 移除端口
        parts = hostname.split('.')
        
        # 尝试从子域名获取租户code
        if len(parts) >= 3:
            tenant_code = parts[0]
            try:
                tenant = Tenant.objects.get(code=tenant_code, status=1)
                return tenant.id
            except Tenant.DoesNotExist:
                pass
        
        return None
    
    def _get_from_path(self, request: HttpRequest) -> int | None:
        """从URL路径获取租户ID"""
        from dashboard.models import Tenant
        
        path = request.path
        # 匹配 /tenant/{code}/ 格式
        match = re.match(r'^/tenant/([^/]+)/', path)
        if match:
            tenant_code = match.group(1)
            try:
                tenant = Tenant.objects.get(code=tenant_code, status=1)
                return tenant.id
            except Tenant.DoesNotExist:
                pass
        
        return None
