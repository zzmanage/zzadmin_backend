"""
系统用户管理视图
提供用户管理的CRUD操作
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from ...models import UserProfile
from ...serializers import UserProfileSerializer
from ..base import BaseViewSet


class UserProfileViewSet(BaseViewSet):
    """用户资料视图集"""
    
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return UserProfile.objects.all()
        
        # 普通用户只能查看自己的资料
        return UserProfile.objects.filter(user=user)
    
    def retrieve(self, request, pk=None):
        """获取用户资料"""
        # 超级管理员可以查看所有用户，普通用户只能查看自己
        user = request.user
        
        if not user.is_superuser and str(pk) != str(user.id):
            return Response({'detail': '无权访问'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().retrieve(request, pk)
    
    def update(self, request, *args, **kwargs):
        """更新用户资料"""
        user = request.user
        pk = kwargs.get('pk')
        
        if not user.is_superuser and str(pk) != str(user.id):
            return Response({'detail': '无权修改'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, pk=None):
        """部分更新用户资料"""
        user = request.user
        
        if not user.is_superuser and str(pk) != str(user.id):
            return Response({'detail': '无权修改'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().partial_update(request, pk)
    
    def destroy(self, request, pk=None):
        """删除用户"""
        user = request.user
        
        if not user.is_superuser:
            return Response({'detail': '无权删除'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, pk)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        user = request.user
        profile = UserProfile.objects.get(user=user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """获取当前登录用户信息"""
        user = request.user
        profile = UserProfile.objects.get(user=user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """获取用户角色"""
        profile = self.get_object()
        roles = profile.roles.all()
        from ...serializers import RoleSerializer
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['put'])
    def roles(self, request, pk=None):
        """更新用户角色"""
        profile = self.get_object()
        role_ids = request.data.get('role_ids', [])
        profile.roles.set(role_ids)
        profile.save()
        from ...serializers import RoleSerializer
        roles = profile.roles.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['put'])
    def change_password(self, request, pk=None):
        """修改用户密码"""
        profile = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not profile.user.check_password(old_password):
            return Response({'detail': '旧密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.user.set_password(new_password)
        profile.user.save()
        return Response({'detail': '密码修改成功'})
    
    @action(detail=True, methods=['put'])
    def reset_password(self, request, pk=None):
        """重置用户密码（管理员操作）"""
        if not request.user.is_superuser:
            return Response({'detail': '无权操作'}, status=status.HTTP_403_FORBIDDEN)
        
        profile = self.get_object()
        # 重置为默认密码
        default_password = '123456'
        profile.user.set_password(default_password)
        profile.user.save()
        return Response({'detail': '密码已重置为默认密码'})
