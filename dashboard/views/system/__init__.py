"""
系统管理视图模块
按业务功能组织视图
"""

# 用户管理视图
from .users import UserProfileViewSet
from .roles import RoleViewSet
from .menus import MenuViewSet

# 基础数据管理视图
from .departments import DepartmentViewSet
from .permissions import PermissionViewSet
from .posts import PostViewSet
from .dictionaries import DictionaryViewSet
from .buttons import ButtonViewSet

# 日志管理视图
from .login_logs import LoginLogViewSet
from .operation_logs import OperationLogViewSet

# 系统配置视图
from .api_whitelists import ApiWhiteListViewSet
from .menu_buttons import MenuButtonViewSet
from .api_endpoints import ApiEndpointViewSet

# 文件管理视图
from .files import FileViewSet

# 消息管理视图
from .messages import MessageViewSet, UserMessageViewSet

# 任务管理视图
from .tasks import (
    TaskLogViewSet,
    IntervalScheduleViewSet,
    CrontabScheduleViewSet,
    PeriodicTaskViewSet,
    TaskManagementViewSet,
)

# 统计数据视图
from .stats import StatsViewSet

# 认证视图
from .auth import AuthViewSet

__all__ = [
    # 用户管理
    'UserProfileViewSet',
    'RoleViewSet',
    'MenuViewSet',
    
    # 基础数据管理
    'DepartmentViewSet',
    'PermissionViewSet',
    'PostViewSet',
    'DictionaryViewSet',
    'ButtonViewSet',
    
    # 日志管理
    'LoginLogViewSet',
    'OperationLogViewSet',
    
    # 系统配置
    'ApiWhiteListViewSet',
    'MenuButtonViewSet',
    'ApiEndpointViewSet',
    
    # 文件管理
    'FileViewSet',
    
    # 消息管理
    'MessageViewSet',
    'UserMessageViewSet',
    
    # 任务管理
    'TaskLogViewSet',
    'IntervalScheduleViewSet',
    'CrontabScheduleViewSet',
    'PeriodicTaskViewSet',
    'TaskManagementViewSet',
    
    # 统计数据
    'StatsViewSet',
    
    # 认证
    'AuthViewSet',
]