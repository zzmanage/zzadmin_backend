"""
基础序列化器模块
提供通用的序列化器基类和工具
"""
from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """基础序列化器"""
    
    class Meta:
        abstract = True


class AuditableSerializer(BaseSerializer):
    """可审计序列化器"""
    
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        abstract = True


class ResponseSerializer(serializers.Serializer):
    """统一响应序列化器"""
    
    code = serializers.IntegerField(default=200)
    message = serializers.CharField(default="success")
    data = serializers.DictField(default=dict)
