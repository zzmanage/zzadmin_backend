"""
系统管理序列化器模块
包含用户、角色、菜单、部门等系统管理相关序列化器
"""
import json

from django.contrib.auth.models import User
from django_celery_beat.models import CrontabSchedule, IntervalSchedule, PeriodicTask
from rest_framework import serializers

from ..models import (
    UserProfile,
    Role,
    Menu,
    Department,
    Dictionary,
    Post,
    MenuButton,
    OperationLog,
    LoginLog,
    ApiWhiteList,
    Message,
    UserMessage,
    UserMessageSettings,
    File,
    Button,
    TaskLog
)


class UserSerializer(serializers.ModelSerializer):
    """用户模型序列化器"""
    
    def validate_username(self, value):
        if self.instance and value == self.instance.username:
            return value
        
        query = User.objects.filter(username=value)
        if self.instance:
            query = query.exclude(id=self.instance.id)
        
        if query.exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        
        return value
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active"]
        extra_kwargs = {"username": {"validators": []}}


class PostSerializer(serializers.ModelSerializer):
    """岗位序列化器"""
    
    class Meta:
        model = Post
        fields = ["id", "name", "code", "sort", "status"]


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    
    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "created_at",
            "updated_at",
            "key",
            "sort",
            "owner",
            "mobile",
            "email",
            "status",
        ]
        read_only_fields = ["created_at", "updated_at"]


class MenuButtonSerializer(serializers.ModelSerializer):
    """菜单按钮权限序列化器"""
    
    menu_name = serializers.CharField(
        source="menu.name", read_only=True, label="关联菜单名称"
    )
    menu_path = serializers.CharField(
        source="menu.web_path", read_only=True, label="菜单路径"
    )
    method_display = serializers.SerializerMethodField(
        read_only=True, label="请求方法显示"
    )
    
    def get_method_display(self, obj):
        for choice in obj.METHOD_CHOICES:
            if choice[0] == obj.method:
                return choice[1]
        return ""
    
    class Meta:
        model = MenuButton
        fields = [
            "id",
            "menu",
            "menu_name",
            "menu_path",
            "name",
            "value",
            "api",
            "method",
            "method_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "code",
            "description",
            "parent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    permissions = MenuButtonSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=MenuButton.objects.all(),
        source="permissions",
    )
    
    created_at_display = serializers.SerializerMethodField(read_only=True, label="创建时间")
    updated_at_display = serializers.SerializerMethodField(read_only=True, label="更新时间")
    
    def get_created_at_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else ""
    
    def get_updated_at_display(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d %H:%M:%S") if obj.updated_at else ""
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "permission_ids",
            "created_at",
            "updated_at",
            "created_at_display",
            "updated_at_display",
            "key",
            "sort",
            "status",
            "admin",
            "data_range",
        ]
        read_only_fields = ["created_at", "updated_at"]


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    
    parent_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Menu.objects.all(),
        source="parent",
        allow_null=True,
        required=False,
    )
    
    # 只读字段，用于返回父菜单ID
    parent = serializers.PrimaryKeyRelatedField(
        read_only=True,
        allow_null=True,
    )
    
    web_path = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Menu
        fields = [
            "id",
            "parent",
            "parent_id",
            "icon",
            "name",
            "sort",
            "is_link",
            "is_catalog",
            "web_path",
            "component",
            "component_name",
            "status",
            "cache",
            "visible",
        ]


class DictionarySerializer(serializers.ModelSerializer):
    """字典序列化器"""
    
    parent_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Dictionary.objects.all(),
        source="parent",
        allow_null=True,
        required=False,
    )
    
    label = serializers.CharField(required=True, max_length=100)
    value = serializers.CharField(required=True, max_length=200)
    
    def validate(self, data):
        parent = data.get('parent')
        value = data.get('value')
        
        query = Dictionary.objects.filter(parent=parent, value=value)
        
        if self.instance:
            query = query.exclude(id=self.instance.id)
        
        if query.exists():
            if parent:
                raise serializers.ValidationError({
                    'value': f'在父字典 "{parent.label}" 下已存在值为 "{value}" 的字典项'
                })
            else:
                raise serializers.ValidationError({
                    'value': f'已存在值为 "{value}" 的顶级字典项'
                })
        
        return data
    
    class Meta:
        model = Dictionary
        fields = [
            "id",
            "label",
            "value",
            "parent",
            "parent_id",
            "type",
            "color",
            "is_value",
            "status",
            "sort",
            "remark",
        ]
        validators = []


class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    
    user = UserSerializer()
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department"
    )
    roles = RoleSerializer(many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Role.objects.all(), source="roles"
    )
    post = PostSerializer(read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Post.objects.all(),
        source="post",
        allow_null=True,
        required=False,
    )
    
    def __init__(self, *args, **kwargs):
        super(UserProfileSerializer, self).__init__(*args, **kwargs)
        
        if self.instance and hasattr(self.instance, "user"):
            self.fields["user"].instance = self.instance.user
    
    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "department",
            "department_id",
            "roles",
            "role_ids",
            "mobile",
            "avatar",
            "created_at",
            "updated_at",
            "employee_no",
            "name",
            "gender",
            "user_type",
            "post",
            "post_id",
            "last_token",
        ]
        read_only_fields = ["created_at", "updated_at"]
    
    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = User.objects.create_user(
            username=user_data["username"],
            email=user_data.get("email", ""),
            password="123456",
        )
        user.first_name = user_data.get("first_name", "")
        user.last_name = user_data.get("last_name", "")
        user.is_active = user_data.get("is_active", True)
        user.save()
        
        roles = validated_data.pop("roles", None)
        
        user_profile = UserProfile.objects.create(
            user=user,
            **validated_data,
        )
        
        if roles:
            user_profile.roles.add(*roles)
        
        return user_profile
    
    def update(self, instance, validated_data):
        if "user" in validated_data:
            user_data = validated_data.pop("user")
            user = instance.user
            
            original_username = user.username
            new_username = user_data.get("username")
            
            if new_username and new_username != original_username:
                existing_users = User.objects.filter(username=new_username).exclude(
                    id=user.id
                )
                if existing_users.exists():
                    raise serializers.ValidationError(
                        {
                            "user": {
                                "username": [
                                    "A user with that username already exists."
                                ]
                            }
                        }
                    )
            
            for field, value in user_data.items():
                setattr(user, field, value)
            user.save()
        
        for attr, value in validated_data.items():
            if attr not in ["roles"]:
                setattr(instance, attr, value)
        instance.save()
        
        if "roles" in validated_data:
            roles = validated_data["roles"]
            instance.roles.set(roles)
            instance.save()
        
        return instance


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    
    user = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    operation = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        return obj.user.username
    
    def get_operation(self, obj):
        operation_map = {
            "Login": "登录",
            "Logout": "登出",
            "Create": "创建",
            "Update": "更新",
            "Delete": "删除",
            "Query": "查询",
            "Export": "导出",
            "Import": "导入",
            "用户登出": "登出",
        }
        return operation_map.get(obj.operation, obj.operation)
    
    class Meta:
        model = OperationLog
        fields = [
            "id",
            "user",
            "operation",
            "module",
            "ip_address",
            "created_at",
            "action",
            "model_name",
            "model_id",
            "details",
        ]
        read_only_fields = ["created_at"]


class LoginLogSerializer(serializers.ModelSerializer):
    """登录日志序列化器"""
    
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    login_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = LoginLog
        fields = [
            "id",
            "username",
            "ip",
            "agent",
            "browser",
            "os",
            "continent",
            "country",
            "province",
            "city",
            "district",
            "isp",
            "area_code",
            "country_english",
            "country_code",
            "longitude",
            "latitude",
            "login_type",
            "login_type_display",
            "created_at",
        ]
        read_only_fields = ["created_at"]
    
    def get_login_type_display(self, obj):
        LOGIN_TYPE_CHOICES = {
            1: '普通登录',
            2: '普通扫码登录',
            3: '微信扫码登录',
            4: '飞书扫码登录',
            5: '钉钉扫码登录',
            6: '短信登录'
        }
        return LOGIN_TYPE_CHOICES.get(obj.login_type, '未知登录类型')


class ApiWhiteListSerializer(serializers.ModelSerializer):
    """API白名单序列化器"""
    
    class Meta:
        model = ApiWhiteList
        fields = ["id", "url", "method", "enable_datasource", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    """消息元数据序列化器"""
    
    sender = serializers.ReadOnlyField(source="sender.username")
    message_type = serializers.ChoiceField(choices=Message.MESSAGE_TYPE_CHOICES)
    priority = serializers.IntegerField()
    
    class Meta:
        model = Message
        fields = [
            "id",
            "title",
            "content",
            "sender",
            "receive_type",
            "receive_target",
            "message_type",
            "priority",
            "expire_time",
            "status",
            "created_at",
        ]
        read_only_fields = ["sender", "created_at"]


class UserMessageSerializer(serializers.ModelSerializer):
    """用户消息记录序列化器"""
    
    message = MessageSerializer(read_only=True)
    recipient = serializers.ReadOnlyField(source="recipient.username")
    
    class Meta:
        model = UserMessage
        fields = ["id", "message", "recipient", "is_read", "read_at", "is_processed", "processed_at", "created_at"]
        read_only_fields = ["recipient", "created_at"]


class UserMessageSettingsSerializer(serializers.ModelSerializer):
    """用户消息接收设置序列化器"""
    
    user = serializers.ReadOnlyField(source="user.username")
    
    class Meta:
        model = UserMessageSettings
        fields = [
            "id", "user", 
            "enable_system_notify", "system_notify_in_app", "system_notify_email",
            "enable_task_notify", "task_notify_in_app", "task_notify_email",
            "enable_alert_notify", "alert_notify_in_app", "alert_notify_email", "alert_notify_sms",
            "enable_announcement_notify", "announcement_notify_in_app", "announcement_notify_email",
            "email_notify_frequency",
            "created_at", "updated_at"
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class FileSerializer(serializers.ModelSerializer):
    """文件模型序列化器"""
    
    uploader = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("request") and self.context["request"].method == "PATCH":
            self.fields["size"].required = False
            self.fields["file"].required = False
    
    def get_uploader(self, obj):
        return obj.uploader.username if obj.uploader else None
    
    def get_file_size_display(self, obj):
        size = obj.size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_category_name(self, obj):
        category_map = {
            0: "文档",
            1: "图片",
            2: "视频",
            3: "音频",
            4: "压缩包",
            5: "其他",
        }
        return category_map.get(obj.category, "其他")
    
    class Meta:
        model = File
        fields = [
            "id",
            "name",
            "size",
            "file_size_display",
            "file",
            "file_url",
            "file_type",
            "category",
            "category_name",
            "description",
            "uploader",
            "permission",
            "download_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uploader", "created_at", "updated_at", "download_count"]


class ButtonSerializer(serializers.ModelSerializer):
    """按钮序列化器"""
    
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Button
        fields = ["id", "name", "value", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


# ============ 定时任务相关序列化器 ============

class IntervalScheduleSerializer(serializers.ModelSerializer):
    """间隔调度序列化器"""

    class Meta:
        model = IntervalSchedule
        fields = ["id", "every", "period"]
        read_only_fields = ["id"]


class CrontabScheduleSerializer(serializers.ModelSerializer):
    """定时调度序列化器"""

    class Meta:
        model = CrontabSchedule
        fields = [
            "id",
            "minute",
            "hour",
            "day_of_week",
            "day_of_month",
            "month_of_year",
        ]
        read_only_fields = ["id"]


class PeriodicTaskSerializer(serializers.ModelSerializer):
    """周期性任务序列化器"""

    # 嵌套序列化器，用于读取
    interval = IntervalScheduleSerializer(required=False, allow_null=True)
    crontab = CrontabScheduleSerializer(required=False, allow_null=True)
    # 用于写入的ID字段
    interval_id = serializers.PrimaryKeyRelatedField(
        queryset=IntervalSchedule.objects.all(),
        source="interval",
        required=False,
        allow_null=True,
    )
    crontab_id = serializers.PrimaryKeyRelatedField(
        queryset=CrontabSchedule.objects.all(),
        source="crontab",
        required=False,
        allow_null=True,
    )
    # 格式化参数为JSON字符串
    args_display = serializers.SerializerMethodField(read_only=True)
    kwargs_display = serializers.SerializerMethodField(read_only=True)
    # 自定义参数字段，用于写入
    args_json = serializers.CharField(write_only=True, required=False, allow_blank=True)
    kwargs_json = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    # 优化日期显示格式，但不允许前端提交此字段
    date_changed = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = PeriodicTask
        fields = [
            "id",
            "name",
            "task",
            "interval",
            "crontab",
            "interval_id",
            "crontab_id",
            "args",
            "kwargs",
            "args_display",
            "kwargs_display",
            "args_json",
            "kwargs_json",
            "queue",
            "exchange",
            "routing_key",
            "priority",
            "one_off",
            "start_time",
            "expires",
            "enabled",
            "last_run_at",
            "total_run_count",
            "date_changed",
            "description",
        ]
        read_only_fields = ["id", "last_run_at", "total_run_count", "date_changed"]

    def get_args_display(self, obj):
        """格式化args为可读JSON"""
        if obj.args:
            try:
                return json.loads(obj.args)
            except json.JSONDecodeError:
                return obj.args
        return []

    def get_kwargs_display(self, obj):
        """格式化kwargs为可读JSON"""
        if obj.kwargs:
            try:
                return json.loads(obj.kwargs)
            except json.JSONDecodeError:
                return obj.kwargs
        return {}

    def validate(self, data):
        """验证任务配置"""
        # 确保interval和crontab不同时设置或同时不设置
        if data.get("interval") and data.get("crontab"):
            raise serializers.ValidationError("不能同时设置interval和crontab")
        if not data.get("interval") and not data.get("crontab"):
            raise serializers.ValidationError("必须设置interval或crontab")

        # 处理JSON格式的参数
        if "args_json" in data:
            try:
                if data["args_json"]:
                    data["args"] = json.dumps(json.loads(data["args_json"]))
                else:
                    data["args"] = "[]"
            except json.JSONDecodeError:
                raise serializers.ValidationError({"args_json": "无效的JSON格式"})
            del data["args_json"]

        if "kwargs_json" in data:
            try:
                if data["kwargs_json"]:
                    data["kwargs"] = json.dumps(json.loads(data["kwargs_json"]))
                else:
                    data["kwargs"] = "{}"
            except json.JSONDecodeError:
                raise serializers.ValidationError({"kwargs_json": "无效的JSON格式"})
            del data["kwargs_json"]

        return data

    def update(self, instance, validated_data):
        """自定义更新方法，处理嵌套字段"""
        # 处理嵌套的interval字段
        interval_data = validated_data.pop('interval', None)
        if interval_data:
            # 如果是字典类型（新创建）
            if isinstance(interval_data, dict):
                if instance.interval:
                    # 更新现有interval
                    for key, value in interval_data.items():
                        setattr(instance.interval, key, value)
                    instance.interval.save()
                else:
                    # 创建新的interval
                    instance.interval = IntervalSchedule.objects.create(**interval_data)
            # 如果是对象类型（通过interval_id设置）
            else:
                instance.interval = interval_data
        elif 'interval' in validated_data:
            # 清除interval
            instance.interval = None

        # 处理嵌套的crontab字段
        crontab_data = validated_data.pop('crontab', None)
        if crontab_data:
            # 如果是字典类型（新创建）
            if isinstance(crontab_data, dict):
                if instance.crontab:
                    # 更新现有crontab
                    for key, value in crontab_data.items():
                        setattr(instance.crontab, key, value)
                    instance.crontab.save()
                else:
                    # 创建新的crontab
                    instance.crontab = CrontabSchedule.objects.create(**crontab_data)
            # 如果是对象类型（通过crontab_id设置）
            else:
                instance.crontab = crontab_data
        elif 'crontab' in validated_data:
            # 清除crontab
            instance.crontab = None

        # 更新其他字段
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        return instance


class TaskInfoSerializer(serializers.Serializer):
    """任务信息序列化器"""

    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    module = serializers.CharField(read_only=True)


class TaskResultSerializer(serializers.Serializer):
    """任务执行结果序列化器"""

    task_id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    result = serializers.CharField(read_only=True, allow_null=True)
    date_done = serializers.DateTimeField(read_only=True)
    traceback = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)


class TaskExecuteSerializer(serializers.Serializer):
    """任务执行请求序列化器"""

    task_name = serializers.CharField(required=True)
    args = serializers.JSONField(required=False, default=[])
    kwargs = serializers.JSONField(required=False, default={})


class TaskLogSerializer(serializers.ModelSerializer):
    """定时任务日志序列化器"""

    # 嵌套序列化关联的定时任务信息
    periodic_task_name = serializers.SerializerMethodField()
    # 状态的显示文本
    status_display = serializers.SerializerMethodField()
    # 格式化执行时间
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", required=False, allow_null=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = TaskLog
        fields = [
            "id",
            "periodic_task",
            "periodic_task_name",
            "task_name",
            "task_id",
            "status",
            "status_display",
            "result",
            "error_message",
            "start_time",
            "end_time",
            "duration",
            "args",
            "kwargs",
            "created_at",
        ]
        read_only_fields = fields  # 所有字段都是只读的

    def get_periodic_task_name(self, obj):
        """获取定时任务的名称"""
        if obj.periodic_task:
            return obj.periodic_task.name
        return None

    def get_status_display(self, obj):
        """获取状态的显示文本"""
        return obj.get_status_display()
