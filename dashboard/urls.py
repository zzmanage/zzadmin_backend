from django.urls import include, path
from rest_framework.routers import DefaultRouter

# 导入系统管理视图
from .views.system import (
    UserProfileViewSet,
    RoleViewSet,
    MenuViewSet,
    DepartmentViewSet,
    PermissionViewSet,
    PostViewSet,
    DictionaryViewSet,
    ButtonViewSet,
    LoginLogViewSet,
    OperationLogViewSet,
    ApiWhiteListViewSet,
    MenuButtonViewSet,
    ApiEndpointViewSet,
    FileViewSet,
    MessageViewSet,
    UserMessageViewSet,
    TaskLogViewSet,
    StatsViewSet,
    AuthViewSet,
    IntervalScheduleViewSet,
    CrontabScheduleViewSet,
    PeriodicTaskViewSet,
    TaskManagementViewSet,
)

# 导入验证码视图
from .views.captcha import CaptchaView

# 导入租户管理视图
from .views.tenant import TenantViewSet, TenantUserViewSet

# 导入工作流管理视图
from .views.workflow import (
    WorkflowDefinitionViewSet,
    WorkflowInstanceViewSet,
    WorkflowTaskViewSet,
    WorkflowTransitionViewSet,
)


app_name = "dashboard"

# 创建路由器
router = DefaultRouter()

# 注册系统管理视图集
router.register(r"buttons", ButtonViewSet, basename="button")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"users", UserProfileViewSet, basename="user")
router.register(r"posts", PostViewSet, basename="post")
router.register(r"menus", MenuViewSet, basename="menu")
router.register(r"dictionaries", DictionaryViewSet, basename="dictionary")

# 注册日志视图集
router.register(r"operation_logs", OperationLogViewSet, basename="operation_log")
router.register(r"login_logs", LoginLogViewSet, basename="login_log")

# 注册API白名单视图集
router.register(r"api_whitelists", ApiWhiteListViewSet, basename="api_whitelist")
router.register(r"menu_buttons", MenuButtonViewSet, basename="menu_button")
router.register(r"api_endpoints", ApiEndpointViewSet, basename="api_endpoint")

# 注册定时任务相关视图集
router.register(r"interval_schedules", IntervalScheduleViewSet, basename="interval_schedule")
router.register(r"crontab_schedules", CrontabScheduleViewSet, basename="crontab_schedule")
router.register(r"periodic_tasks", PeriodicTaskViewSet, basename="periodic_task")
router.register(r"task_management", TaskManagementViewSet, basename="task_management")
router.register(r"task_logs", TaskLogViewSet, basename="task_log")

# 注册消息相关视图集
router.register(r"messages", MessageViewSet)
router.register(r"user_messages", UserMessageViewSet)

# 注册文件管理相关视图集
router.register(r"files", FileViewSet, basename="file")

# 注册验证码视图
router.register(r"captcha", CaptchaView, basename="captcha")

# 注册统计数据视图集（使用新的StatsViewSet替换旧的StatisticsViewSet）
router.register(r"statistics", StatsViewSet, basename="statistics")

# 注册认证视图
router.register(r"auth", AuthViewSet, basename="auth")

# 注册租户管理视图集
router.register(r"tenants", TenantViewSet, basename="tenant")
router.register(r"tenant_users", TenantUserViewSet, basename="tenant_user")

# 注册工作流管理视图集
router.register(r"workflows", WorkflowDefinitionViewSet, basename="workflow")
router.register(r"workflow_instances", WorkflowInstanceViewSet, basename="workflow_instance")
router.register(r"workflow_tasks", WorkflowTaskViewSet, basename="workflow_task")
router.register(r"workflow_transitions", WorkflowTransitionViewSet, basename="workflow_transition")


# API URL模式
urlpatterns = [
    # 包含路由器生成的URL模式
    path("api/", include(router.urls)),
]