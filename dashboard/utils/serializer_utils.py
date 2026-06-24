from rest_framework import serializers
from django.utils import timezone


class FormattedDateTimeField(serializers.DateTimeField):
    """格式化的日期时间字段，统一处理日期时间格式

    提供统一的日期时间格式化方式，避免在多个序列化器中重复相同的格式化逻辑
    默认格式为 '%Y-%m-%d %H:%M:%S'
    """
    
    def __init__(self, format='%Y-%m-%d %H:%M:%S', **kwargs):
        super().__init__(format=format, **kwargs)


class CommonSerializerMixin:
    """通用序列化器混入类

    提供序列化器中常用的方法和字段定义，减少重复代码
    """
    
    def get_created_at_display(self, obj):
        """获取格式化的创建时间"""
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''

    def get_updated_at_display(self, obj):
        """获取格式化的更新时间"""
        if obj.updated_at:
            return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''


class AuditableModelSerializer(serializers.ModelSerializer):
    """带审计字段的模型序列化器基类

    自动处理创建时间和更新时间的格式化显示
    """
    
    # 使用统一的格式化日期时间字段
    created_at = FormattedDateTimeField(read_only=True)
    updated_at = FormattedDateTimeField(read_only=True)
    
    class Meta:
        # 需要被子类覆盖
        model = None
        fields = []
        read_only_fields = ['created_at', 'updated_at']


class ParentChildSerializerMixin:
    """父子关系序列化器混入类

    提供处理父子关系的常用字段和方法
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 自动添加parent_id字段
        if hasattr(self.Meta, 'model') and hasattr(self.Meta.model, 'parent'):
            self.fields['parent_id'] = serializers.PrimaryKeyRelatedField(
                write_only=True,
                queryset=self.Meta.model.objects.all(),
                source='parent',
                allow_null=True,
                required=False,
            )