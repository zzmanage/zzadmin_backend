"""
过滤器模块，包含所有API视图的过滤器定义
"""

import django_filters

from .models import (
    ApiWhiteList,
    Button,
    Department,
    Dictionary,
    LoginLog,
    Menu,
    MenuButton,
    OperationLog,
    Permission,
    Post,
    Role,
    TaskLog,
    UserMessage,
    UserProfile,
)


class UserProfileFilter(django_filters.FilterSet):
    """用户资料过滤器

    提供用户资料的高级过滤功能
    """

    # 精确过滤
    department_id = django_filters.NumberFilter(field_name="department__id")
    role_id = django_filters.NumberFilter(field_name="roles__id")
    is_active = django_filters.BooleanFilter(field_name="user__is_active")
    employee_no = django_filters.CharFilter(
        field_name="employee_no", lookup_expr="exact"
    )

    # 模糊过滤
    username = django_filters.CharFilter(
        field_name="user__username", lookup_expr="icontains"
    )
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    mobile = django_filters.CharFilter(field_name="mobile", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="user__email", lookup_expr="icontains")

    # 日期过滤
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    # 排序
    class Meta:
        model = UserProfile
        fields = [
            "department_id",
            "role_id",
            "is_active",
            "employee_no",
            "username",
            "name",
            "mobile",
            "email",
            "created_at__gte",
            "created_at__lte",
        ]


class DepartmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="部门名称")
    description = django_filters.CharFilter(lookup_expr="icontains", label="部门描述")
    status = django_filters.CharFilter(method="filter_status", label="部门状态")
    parent_id = django_filters.NumberFilter(label="上级部门ID")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    def filter_status(self, queryset, name, value):
        # 处理字符串形式的布尔值
        if isinstance(value, str):
            value = value.lower()
            if value in ["0", "false"]:
                return queryset.filter(status=False)
            elif value in ["1", "true"]:
                return queryset.filter(status=True)
        # 对于其他情况，保持原始行为
        return queryset

    class Meta:
        model = Department
        fields = [
            "name",
            "description",
            "status",
            "parent_id",
            "created_at__gte",
            "created_at__lte",
        ]


class RoleFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="角色名称")
    key = django_filters.CharFilter(lookup_expr="icontains", label="权限字符")
    status = django_filters.BooleanFilter(label="角色状态")
    data_range = django_filters.NumberFilter(label="数据权限范围")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = Role
        fields = [
            "name",
            "key",
            "status",
            "data_range",
            "created_at__gte",
            "created_at__lte",
        ]


class PermissionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="权限名称")
    code = django_filters.CharFilter(lookup_expr="icontains", label="权限编码")
    description = django_filters.CharFilter(lookup_expr="icontains", label="权限描述")
    parent_id = django_filters.NumberFilter(label="上级权限ID")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = Permission
        fields = [
            "name",
            "code",
            "description",
            "parent_id",
            "created_at__gte",
            "created_at__lte",
        ]


class MenuButtonFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="名称")
    value = django_filters.CharFilter(lookup_expr="icontains", label="权限值")
    api = django_filters.CharFilter(lookup_expr="icontains", label="接口地址")
    menu_id = django_filters.NumberFilter(label="关联菜单ID")
    method = django_filters.ChoiceFilter(
        choices=[(0, "GET"), (1, "POST"), (2, "PUT"), (3, "DELETE")], label="请求方法"
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = MenuButton
        fields = [
            "name",
            "value",
            "api",
            "menu_id",
            "method",
            "created_at__gte",
            "created_at__lte",
        ]


class PostFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="岗位名称")
    code = django_filters.CharFilter(lookup_expr="icontains", label="岗位编码")
    status = django_filters.NumberFilter(label="岗位状态")
    sort = django_filters.NumberFilter(label="岗位顺序")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = Post
        fields = [
            "name",
            "code",
            "status",
            "sort",
            "created_at__gte",
            "created_at__lte",
        ]


class MenuFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="菜单名称")
    parent_id = django_filters.NumberFilter(label="上级菜单ID")
    visible = django_filters.BooleanFilter(label="是否显示")
    status = django_filters.BooleanFilter(label="菜单状态")
    web_path = django_filters.CharFilter(lookup_expr="exact", label="路由地址")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    # 自定义父菜单过滤器，支持id和null值
    parent = django_filters.CharFilter(method="filter_parent", label="父菜单ID")

    class Meta:
        model = Menu
        fields = [
            "name",
            "parent_id",
            "parent",
            "visible",
            "status",
            "web_path",
            "created_at__gte",
            "created_at__lte",
        ]


class DictionaryFilter(django_filters.FilterSet):
    """字典过滤类"""

    label = django_filters.CharFilter(lookup_expr="icontains", label="字典名称")
    value = django_filters.CharFilter(lookup_expr="icontains", label="字典编号")
    type = django_filters.NumberFilter(label="数据值类型")
    status = django_filters.BooleanFilter(label="状态")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    # 自定义父级过滤器，支持id和null值
    parent = django_filters.CharFilter(method="filter_parent", label="父级ID")

    def filter_parent(self, queryset, name, value):
        """过滤父级字典，支持空值查询"""
        # 处理None情况：不传入参数时返回所有字典
        if value is None:
            return queryset
        
        # 如果传入null或none（字符串），返回parent为null的字典（顶级字典）
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ("null", "none"):
                return queryset.filter(parent__isnull=True)
            # 如果是空字符串或纯空格，返回所有字典（不过滤）
            if value.strip() == "":
                return queryset

        # 尝试将value转换为整数，过滤parent_id等于该值的字典
        try:
            parent_id = int(value)
            return queryset.filter(parent_id=parent_id)
        except (ValueError, TypeError):
            # 如果无法转换为整数，返回空查询集
            return queryset.none()

    class Meta:
        model = Dictionary
        fields = [
            "label",
            "value",
            "parent",
            "type",
            "status",
            "created_at__gte",
            "created_at__lte",
        ]


class ApiWhiteListFilter(django_filters.FilterSet):
    url = django_filters.CharFilter(lookup_expr="icontains", label="URL地址")
    method = django_filters.NumberFilter(label="请求方法")
    enable_datasource = django_filters.BooleanFilter(label="激活数据权限")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = ApiWhiteList
        fields = [
            "url",
            "method",
            "enable_datasource",
            "created_at__gte",
            "created_at__lte",
        ]


class OperationLogFilter(django_filters.FilterSet):
    user_id = django_filters.NumberFilter(label="操作用户ID")
    action = django_filters.CharFilter(lookup_expr="icontains", label="操作类型")
    model = django_filters.CharFilter(lookup_expr="icontains", label="操作模型")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="操作时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="操作时间小于等于"
    )
    ip_address = django_filters.CharFilter(lookup_expr="icontains", label="IP地址")

    class Meta:
        model = OperationLog
        fields = [
            "user_id",
            "action",
            "model",
            "created_at__gte",
            "created_at__lte",
            "ip_address",
        ]


class LoginLogFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr="icontains", label="用户名")
    ip = django_filters.CharFilter(lookup_expr="icontains", label="登录IP")
    browser = django_filters.CharFilter(lookup_expr="icontains", label="浏览器")
    os = django_filters.CharFilter(lookup_expr="icontains", label="操作系统")
    country = django_filters.CharFilter(lookup_expr="icontains", label="国家")
    province = django_filters.CharFilter(lookup_expr="icontains", label="省份")
    city = django_filters.CharFilter(lookup_expr="icontains", label="城市")
    start_date = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="登录时间大于等于"
    )
    end_date = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="登录时间小于等于"
    )

    class Meta:
        model = LoginLog
        fields = [
            "username",
            "ip",
            "browser",
            "os",
            "country",
            "province",
            "city",
            "start_date",
            "end_date",
        ]


class UserMessageFilter(django_filters.FilterSet):
    recipient_id = django_filters.NumberFilter(
        field_name="recipient_id", label="接收用户ID"
    )
    is_read = django_filters.BooleanFilter(label="是否已读")
    message_title = django_filters.CharFilter(
        field_name="message__title", lookup_expr="icontains", label="消息标题"
    )
    message_content = django_filters.CharFilter(
        field_name="message__content", lookup_expr="icontains", label="消息内容"
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = UserMessage
        fields = [
            "recipient_id",
            "is_read",
            "message_title",
            "message_content",
            "created_at__gte",
            "created_at__lte",
        ]


class ButtonFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="按钮名称")
    value = django_filters.CharFilter(lookup_expr="icontains", label="按钮值")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="创建时间大于等于"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="创建时间小于等于"
    )

    class Meta:
        model = Button
        fields = [
            "name",
            "value",
            "created_at__gte",
            "created_at__lte",
        ]


class TaskLogFilter(django_filters.FilterSet):
    """任务日志过滤器"""
    # 按时间范围过滤
    start_time__gte = django_filters.DateTimeFilter(
        field_name="start_time", lookup_expr="gte", label="开始时间大于等于"
    )
    start_time__lte = django_filters.DateTimeFilter(
        field_name="start_time", lookup_expr="lte", label="开始时间小于等于"
    )
    # 按状态过滤
    status = django_filters.ChoiceFilter(choices=TaskLog.STATUS_CHOICES, label="任务状态")
    # 按任务名称搜索
    task_name = django_filters.CharFilter(lookup_expr="icontains", label="任务名称")

    class Meta:
        model = TaskLog
        fields = [
            "periodic_task",
            "status",
            "task_name",
            "start_time__gte",
            "start_time__lte",
        ]
