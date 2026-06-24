from django.db import migrations

def add_permissions(apps, schema_editor):
    Permission = apps.get_model('dashboard', 'Permission')
    Menu = apps.get_model('dashboard', 'Menu')
    MenuButton = apps.get_model('dashboard', 'MenuButton')
    
    # 创建租户管理权限
    tenant_permission = Permission.objects.create(
        name='租户管理',
        code='tenant_management',
        description='租户管理权限'
    )
    
    # 创建工作流管理权限
    workflow_permission = Permission.objects.create(
        name='工作流管理',
        code='workflow_management',
        description='工作流管理权限'
    )
    
    # 创建租户配置权限
    tenant_config_permission = Permission.objects.create(
        name='租户配置',
        code='tenant_config',
        description='租户配置权限',
        parent=tenant_permission
    )
    
    # 创建工作流定义权限
    workflow_def_permission = Permission.objects.create(
        name='流程定义管理',
        code='workflow_definition',
        description='流程定义管理权限',
        parent=workflow_permission
    )
    
    # 创建工作流实例权限
    workflow_instance_permission = Permission.objects.create(
        name='流程实例管理',
        code='workflow_instance',
        description='流程实例管理权限',
        parent=workflow_permission
    )
    
    # 创建工作流任务权限
    workflow_task_permission = Permission.objects.create(
        name='工作流任务',
        code='workflow_task',
        description='工作流任务处理权限',
        parent=workflow_permission
    )
    
    # 创建租户管理菜单
    tenant_menu = Menu.objects.create(
        name='租户管理',
        sort=20,
        web_path='/tenants',
        component='Tenant',
        component_name='Tenant',
        status=True,
        visible=True,
        icon='Building'
    )
    
    # 创建工作流管理菜单
    workflow_menu = Menu.objects.create(
        name='工作流管理',
        sort=21,
        web_path='/workflow',
        component='Workflow',
        component_name='Workflow',
        status=True,
        visible=True,
        icon='GitBranch'
    )
    
    # 创建租户管理按钮权限
    MenuButton.objects.create(
        menu=tenant_menu,
        name='查询租户',
        value='tenant_view',
        api='/api/tenant/tenants/',
        method=0
    )
    
    MenuButton.objects.create(
        menu=tenant_menu,
        name='创建租户',
        value='tenant_create',
        api='/api/tenant/tenants/',
        method=1
    )
    
    MenuButton.objects.create(
        menu=tenant_menu,
        name='编辑租户',
        value='tenant_edit',
        api='/api/tenant/tenants/',
        method=2
    )
    
    MenuButton.objects.create(
        menu=tenant_menu,
        name='删除租户',
        value='tenant_delete',
        api='/api/tenant/tenants/',
        method=3
    )
    
    # 创建工作流管理按钮权限
    MenuButton.objects.create(
        menu=workflow_menu,
        name='查看流程',
        value='workflow_view',
        api='/api/workflow/definitions/',
        method=0
    )
    
    MenuButton.objects.create(
        menu=workflow_menu,
        name='创建流程',
        value='workflow_create',
        api='/api/workflow/definitions/',
        method=1
    )
    
    MenuButton.objects.create(
        menu=workflow_menu,
        name='编辑流程',
        value='workflow_edit',
        api='/api/workflow/definitions/',
        method=2
    )
    
    MenuButton.objects.create(
        menu=workflow_menu,
        name='删除流程',
        value='workflow_delete',
        api='/api/workflow/definitions/',
        method=3
    )
    
    MenuButton.objects.create(
        menu=workflow_menu,
        name='启动流程',
        value='workflow_start',
        api='/api/workflow/instances/{id}/start/',
        method=1
    )
    
    MenuButton.objects.create(
        menu=workflow_menu,
        name='认领任务',
        value='task_claim',
        api='/api/workflow/tasks/{id}/claim/',
        method=1
    )
    
    MenuButton.objects.create(
        menu=workflow_menu,
        name='完成任务',
        value='task_complete',
        api='/api/workflow/tasks/{id}/complete/',
        method=1
    )


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_tenant_and_workflow'),
    ]

    operations = [
        migrations.RunPython(add_permissions),
    ]
