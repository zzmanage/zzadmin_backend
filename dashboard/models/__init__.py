"""
模型模块
按业务模块组织模型
"""

# 系统管理模型
from .system import (
    BaseModel,
    Department,
    Permission,
    MenuButton,
    Role,
    UserProfile,
    OperationLog,
    Post,
    Message,
    UserMessage,
    UserMessageSettings,
    Menu,
    Dictionary,
    LoginLog,
    TaskLog,
    ApiWhiteList,
    File,
    Button,
)

# 租户管理模型
from .tenant import (
    Tenant,
    TenantUser,
    TenantSetting,
)

# 工作流管理模型
from .workflow import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowTask,
    WorkflowTransition,
)

__all__ = [
    # 系统管理
    'BaseModel',
    'Department',
    'Permission',
    'MenuButton',
    'Role',
    'UserProfile',
    'OperationLog',
    'Post',
    'Message',
    'UserMessage',
    'UserMessageSettings',
    'Menu',
    'Dictionary',
    'LoginLog',
    'TaskLog',
    'ApiWhiteList',
    'File',
    'Button',
    # 租户管理
    'Tenant',
    'TenantUser',
    'TenantSetting',
    # 工作流管理
    'WorkflowDefinition',
    'WorkflowInstance',
    'WorkflowTask',
    'WorkflowTransition',
]
