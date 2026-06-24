from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_message_expire_time_message_status_and_more'),
    ]

    operations = [
        # 创建租户模型
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='租户名称')),
                ('domain', models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='租户域名')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='租户编码')),
                ('status', models.IntegerField(choices=[(0, '未激活'), (1, '正常'), (2, '暂停'), (3, '已删除')], default=1, verbose_name='租户状态')),
                ('contact_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='联系人')),
                ('contact_phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='联系电话')),
                ('contact_email', models.EmailField(blank=True, null=True, verbose_name='联系邮箱')),
                ('max_users', models.IntegerField(default=100, verbose_name='最大用户数')),
                ('max_storage', models.BigIntegerField(default=10737418240, verbose_name='最大存储空间(字节)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='有效期至')),
            ],
            options={
                'verbose_name': '租户',
                'verbose_name_plural': '租户管理',
                'ordering': ['-created_at'],
            },
        ),
        # 创建租户用户关联模型
        migrations.CreateModel(
            name='TenantUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', '租户管理员'), ('manager', '租户经理'), ('user', '普通用户')], default='user', max_length=20, verbose_name='租户角色')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='加入时间')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_users', to='dashboard.tenant', verbose_name='租户')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_tenants', to='auth.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': '租户用户',
                'verbose_name_plural': '租户用户管理',
            },
        ),
        # 创建租户配置模型
        migrations.CreateModel(
            name='TenantSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('settings', models.JSONField(default=dict, verbose_name='配置内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='dashboard.tenant', verbose_name='租户')),
            ],
            options={
                'verbose_name': '租户配置',
                'verbose_name_plural': '租户配置管理',
            },
        ),
        # 添加联合唯一约束
        migrations.AlterUniqueTogether(
            name='tenantuser',
            unique_together={('tenant', 'user')},
        ),
        # 为现有模型添加租户字段
        migrations.AddField(
            model_name='department',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='department_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='permission',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='permission_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='menubutton',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='menubutton_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='role',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='role_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='userprofile_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='loginlog',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='loginlog_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),

        migrations.AddField(
            model_name='apiwhitelist',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='apiwhitelist_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='menu',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='menu_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='dictionary',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dictionary_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='operationlog',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='operationlog_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='post',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='post_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='message',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='message_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='usermessage',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usermessage_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='button',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='button_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        migrations.AddField(
            model_name='file',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='file_tenant', to='dashboard.tenant', verbose_name='所属租户'),
        ),
        # 创建工作流定义模型
        migrations.CreateModel(
            name='WorkflowDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='流程名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='流程编码')),
                ('description', models.TextField(blank=True, null=True, verbose_name='流程描述')),
                ('flow_json', models.JSONField(verbose_name='流程定义JSON')),
                ('status', models.IntegerField(choices=[(0, '草稿'), (1, '已发布'), (2, '已禁用')], default=1, verbose_name='状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_definitions', to='dashboard.tenant', verbose_name='所属租户')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_definitions_created', to='auth.user', verbose_name='创建人')),
            ],
            options={
                'verbose_name': '工作流定义',
                'verbose_name_plural': '工作流定义管理',
                'ordering': ['-created_at'],
            },
        ),
        # 创建工作流实例模型
        migrations.CreateModel(
            name='WorkflowInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_key', models.CharField(blank=True, max_length=100, null=True, verbose_name='业务主键')),
                ('business_type', models.CharField(blank=True, max_length=50, null=True, verbose_name='业务类型')),
                ('status', models.IntegerField(choices=[(0, '待启动'), (1, '运行中'), (2, '已完成'), (3, '已终止'), (4, '已撤回')], default=0, verbose_name='状态')),
                ('data', models.JSONField(default=dict, verbose_name='流程数据')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='启动时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_instances', to='dashboard.tenant', verbose_name='所属租户')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_instances_created', to='auth.user', verbose_name='创建人')),
                ('definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='dashboard.workflowdefinition', verbose_name='流程定义')),
            ],
            options={
                'verbose_name': '工作流实例',
                'verbose_name_plural': '工作流实例管理',
                'ordering': ['-created_at'],
            },
        ),
        # 创建工作流任务模型
        migrations.CreateModel(
            name='WorkflowTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_def_key', models.CharField(max_length=100, verbose_name='任务定义Key')),
                ('task_name', models.CharField(max_length=100, verbose_name='任务名称')),
                ('candidate_users', models.JSONField(default=list, verbose_name='候选用户列表')),
                ('candidate_roles', models.JSONField(default=list, verbose_name='候选角色列表')),
                ('status', models.IntegerField(choices=[(0, '待处理'), (1, '处理中'), (2, '已完成'), (3, '已拒绝'), (4, '已跳过')], default=0, verbose_name='状态')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='处理意见')),
                ('data', models.JSONField(default=dict, verbose_name='任务数据')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始处理时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_tasks', to='dashboard.tenant', verbose_name='所属租户')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='dashboard.workflowinstance', verbose_name='流程实例')),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_tasks_assigned', to='auth.user', verbose_name='处理人')),
            ],
            options={
                'verbose_name': '工作流任务',
                'verbose_name_plural': '工作流任务管理',
                'ordering': ['-created_at'],
            },
        ),
        # 创建工作流流转记录模型
        migrations.CreateModel(
            name='WorkflowTransition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_state', models.CharField(max_length=50, verbose_name='源状态')),
                ('to_state', models.CharField(max_length=50, verbose_name='目标状态')),
                ('transition_name', models.CharField(max_length=100, verbose_name='流转名称')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='操作备注')),
                ('data', models.JSONField(default=dict, verbose_name='流转数据')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_transitions', to='dashboard.tenant', verbose_name='所属租户')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transitions', to='dashboard.workflowtask', verbose_name='关联任务')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_transitions', to='auth.user', verbose_name='操作人')),
            ],
            options={
                'verbose_name': '工作流流转记录',
                'verbose_name_plural': '工作流流转记录管理',
                'ordering': ['-created_at'],
            },
        ),
    ]
