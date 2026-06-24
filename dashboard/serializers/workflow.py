"""
工作流管理序列化器模块
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowTask,
    WorkflowTransition
)


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    """工作流定义序列化器"""
    
    # 添加格式化字段
    status_text = serializers.SerializerMethodField()
    created_at_str = serializers.SerializerMethodField()
    updated_at_str = serializers.SerializerMethodField()
    
    # 兼容前端传入的 definition 字段
    definition = serializers.JSONField(
        write_only=True,
        required=False,
        help_text="前端传入的流程定义JSON"
    )
    
    def get_status_text(self, obj):
        """获取状态文字"""
        return obj.get_status_display()
    
    def get_created_at_str(self, obj):
        """获取格式化的创建时间"""
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def get_updated_at_str(self, obj):
        """获取格式化的更新时间"""
        if obj.updated_at:
            return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def validate(self, attrs):
        """处理前端传入的 definition 字段"""
        # 如果前端传入 definition，将其映射到 flow_json
        definition = attrs.pop('definition', None)
        if definition:
            attrs['flow_json'] = definition
        return attrs
    
    class Meta:
        model = WorkflowDefinition
        fields = [
            "id",
            "name",
            "code",
            "description",
            "flow_json",
            "definition",
            "status",
            "status_text",
            "created_at",
            "created_at_str",
            "updated_at",
            "updated_at_str",
            "tenant",
            "created_by",
        ]
        read_only_fields = ["created_at", "updated_at"]


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    """工作流实例序列化器"""
    
    # 添加格式化字段
    status_text = serializers.SerializerMethodField()
    workflow_name = serializers.CharField(source='definition.name', read_only=True)
    definition_name = serializers.CharField(source='definition.name', read_only=True)
    creator = serializers.CharField(source='created_by.username', read_only=True)
    created_at_str = serializers.SerializerMethodField()
    started_at_str = serializers.SerializerMethodField()
    completed_at_str = serializers.SerializerMethodField()
    updated_at_str = serializers.SerializerMethodField()
    
    definition = WorkflowDefinitionSerializer(read_only=True)
    definition_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowDefinition.objects.all(), 
        source="definition",
        required=False,
        allow_null=True,
        write_only=True
    )
    
    # 兼容前端传入的 definition 字段
    definition_value = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="前端传入的流程定义ID"
    )
    
    def get_status_text(self, obj):
        """获取状态文字"""
        status_map = {
            0: 'CREATED',
            1: 'RUNNING',
            2: 'COMPLETED',
            3: 'FAILED',
            4: 'SUSPENDED'
        }
        return status_map.get(obj.status, 'UNKNOWN')
    
    def get_created_at_str(self, obj):
        """获取格式化的创建时间"""
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def get_started_at_str(self, obj):
        """获取格式化的启动时间"""
        if obj.started_at:
            return obj.started_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def get_completed_at_str(self, obj):
        """获取格式化的完成时间"""
        if obj.completed_at:
            return obj.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def get_updated_at_str(self, obj):
        """获取格式化的更新时间"""
        # 使用最新的时间作为更新时间
        latest_time = obj.completed_at or obj.started_at or obj.created_at
        if latest_time:
            return latest_time.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def validate(self, attrs):
        """处理 definition 和 definition_value 字段"""
        # 如果前端传入 definition_value（前端使用 definition 作为 prop）
        definition_value = self.initial_data.get('definition')
        if definition_value and 'definition' not in attrs:
            try:
                definition = WorkflowDefinition.objects.get(id=definition_value)
                attrs['definition'] = definition
            except WorkflowDefinition.DoesNotExist:
                raise serializers.ValidationError({'definition': '流程定义不存在'})
        return attrs
    
    class Meta:
        model = WorkflowInstance
        fields = [
            "id",
            "definition",
            "definition_id",
            "definition_name",
            "workflow_name",
            "definition_value",
            "business_key",
            "business_type",
            "status",
            "status_text",
            "data",
            "tenant",
            "created_by",
            "creator",
            "created_at",
            "created_at_str",
            "started_at",
            "started_at_str",
            "completed_at",
            "completed_at_str",
            "updated_at_str",
        ]
        read_only_fields = ["created_at", "started_at", "completed_at"]


class WorkflowTaskSerializer(serializers.ModelSerializer):
    """工作流任务序列化器"""
    
    # 添加格式化字段
    status_text = serializers.SerializerMethodField()
    workflow_name = serializers.CharField(source='instance.definition.name', read_only=True)
    definition_name = serializers.CharField(source='instance.definition.name', read_only=True)
    assignee_name = serializers.CharField(source='assignee.username', read_only=True)
    created_at_str = serializers.SerializerMethodField()
    started_at_str = serializers.SerializerMethodField()
    due_date_str = serializers.SerializerMethodField()
    
    instance = WorkflowInstanceSerializer(read_only=True)
    instance_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowInstance.objects.all(), source="instance"
    )
    
    def get_status_text(self, obj):
        """获取状态文字"""
        return obj.get_status_display()
    
    def get_created_at_str(self, obj):
        """获取格式化的创建时间"""
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def get_started_at_str(self, obj):
        """获取格式化的开始时间"""
        if obj.started_at:
            return obj.started_at.strftime('%Y-%m-%d %H:%M:%S')
        return ''
    
    def get_due_date_str(self, obj):
        """获取格式化的截止时间（预留字段）"""
        return ''
    
    class Meta:
        model = WorkflowTask
        fields = [
            "id",
            "instance",
            "instance_id",
            "workflow_name",
            "definition_name",
            "task_def_key",
            "task_name",
            "candidate_users",
            "candidate_roles",
            "status",
            "status_text",
            "comment",
            "data",
            "tenant",
            "assignee",
            "assignee_name",
            "created_at",
            "created_at_str",
            "started_at",
            "started_at_str",
            "completed_at",
            "due_date_str",
        ]
        read_only_fields = ["created_at", "started_at", "completed_at"]


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    """工作流流转记录序列化器"""
    
    task = WorkflowTaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowTask.objects.all(), source="task"
    )
    
    class Meta:
        model = WorkflowTransition
        fields = [
            "id",
            "task",
            "task_id",
            "from_state",
            "to_state",
            "transition_name",
            "comment",
            "data",
            "tenant",
            "operator",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class WorkflowTaskActionSerializer(serializers.Serializer):
    """工作流任务操作序列化器"""
    
    action = serializers.CharField(required=True, max_length=20)
    comment = serializers.CharField(required=False, max_length=500)
    data = serializers.JSONField(required=False, default=dict)
