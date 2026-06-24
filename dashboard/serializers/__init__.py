"""
序列化器模块
按业务模块组织序列化器
"""

# 基础序列化器
from .base import BaseSerializer, AuditableSerializer, ResponseSerializer

# 租户管理序列化器
from .tenant import (
    TenantSerializer,
    TenantUserSerializer,
    TenantSettingSerializer,
)

# 工作流管理序列化器
from .workflow import (
    WorkflowDefinitionSerializer,
    WorkflowInstanceSerializer,
    WorkflowTaskSerializer,
    WorkflowTransitionSerializer,
    WorkflowTaskActionSerializer,
)

# 系统管理序列化器
from .system import (
    UserSerializer,
    UserProfileSerializer,
    RoleSerializer,
    MenuSerializer,
    MenuButtonSerializer,
    DepartmentSerializer,
    DictionarySerializer,
    PostSerializer,
    OperationLogSerializer,
    LoginLogSerializer,
    ApiWhiteListSerializer,
    PermissionSerializer,
    MessageSerializer,
    UserMessageSerializer,
    UserMessageSettingsSerializer,
    FileSerializer,
    ButtonSerializer,
    TaskLogSerializer,
    IntervalScheduleSerializer,
    CrontabScheduleSerializer,
    PeriodicTaskSerializer,
    TaskInfoSerializer,
    TaskExecuteSerializer,
    TaskResultSerializer,
)

__all__ = [
    # 基础序列化器
    'BaseSerializer',
    'AuditableSerializer',
    'ResponseSerializer',
    # 租户管理
    'TenantSerializer',
    'TenantUserSerializer',
    'TenantSettingSerializer',
    # 工作流管理
    'WorkflowDefinitionSerializer',
    'WorkflowInstanceSerializer',
    'WorkflowTaskSerializer',
    'WorkflowTransitionSerializer',
    'WorkflowTaskActionSerializer',
    # 系统管理
    'UserSerializer',
    'UserProfileSerializer',
    'RoleSerializer',
    'MenuSerializer',
    'MenuButtonSerializer',
    'DepartmentSerializer',
    'DictionarySerializer',
    'PostSerializer',
    'OperationLogSerializer',
    'LoginLogSerializer',
    'ApiWhiteListSerializer',
    'PermissionSerializer',
    'MessageSerializer',
    'UserMessageSerializer',
    'UserMessageSettingsSerializer',
    'FileSerializer',
    'ButtonSerializer',
    'TaskLogSerializer',
    'IntervalScheduleSerializer',
    'CrontabScheduleSerializer',
    'PeriodicTaskSerializer',
    'TaskInfoSerializer',
    'TaskExecuteSerializer',
    'TaskResultSerializer',
]
