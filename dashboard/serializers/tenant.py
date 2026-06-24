"""
租户管理序列化器模块
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import Tenant, TenantUser, TenantSetting


class TenantSerializer(serializers.ModelSerializer):
    """租户序列化器"""
    
    created_by = serializers.ReadOnlyField(source='created_by.username')
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='created_by',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "domain",
            "code",
            "status",
            "contact_name",
            "contact_phone",
            "contact_email",
            "max_users",
            "max_storage",
            "created_at",
            "updated_at",
            "expires_at",
            "created_by",
            "created_by_id",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by"]


class TenantUserSerializer(serializers.ModelSerializer):
    """租户用户关联序列化器"""
    
    tenant = TenantSerializer(read_only=True)
    tenant_id = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(), source="tenant", write_only=True, required=True
    )
    # user字段返回完整的用户信息（auth_user）
    user = serializers.SerializerMethodField()
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True, required=True
    )
    
    class Meta:
        model = TenantUser
        fields = [
            "id",
            "tenant",
            "tenant_id",
            "user",
            "user_id",
            "role",
            "joined_at",
            "is_active",
        ]
        read_only_fields = ["joined_at", "tenant"]
    
    def get_user(self, obj):
        """返回用户信息"""
        from .system import UserSerializer
        return UserSerializer(obj.user).data


class TenantSettingSerializer(serializers.ModelSerializer):
    """租户配置序列化器"""
    
    class Meta:
        model = TenantSetting
        fields = [
            "id",
            "tenant",
            "settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
