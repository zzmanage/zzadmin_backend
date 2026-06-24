import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_management.settings')
import django
django.setup()

from dashboard.models import Menu

# 获取工作流管理
workflow_menu = Menu.objects.filter(name='工作流管理').first()
if workflow_menu:
    children = Menu.objects.filter(parent=workflow_menu.id)
    
    # 更新工作流定义图标
    definition = Menu.objects.filter(name='工作流定义', parent=workflow_menu.id).first()
    if definition:
        definition.icon = 'ant-file-text-outlined'  # FileTextOutlined - 适合定义/文档
        definition.save()
        print("OK - 工作流定义图标:", definition.icon)
    
    # 更新流程实例图标
    instance = Menu.objects.filter(name='流程实例', parent=workflow_menu.id).first()
    if instance:
        instance.icon = 'ant-play-circle-outlined'  # PlayCircleOutlined - 适合运行/实例
        instance.save()
        print("OK - 流程实例图标:", instance.icon)
    
    # 更新任务中心图标
    tasks = Menu.objects.filter(name='任务中心', parent=workflow_menu.id).first()
    if tasks:
        tasks.icon = 'ant-tasks-outlined'  # TasksOutlined - 适合任务
        tasks.save()
        print("OK - 任务中心图标:", tasks.icon)
    
    # 验证更新
    print("\n验证更新结果:")
    children = Menu.objects.filter(parent=workflow_menu.id)
    for child in children:
        print(f"  {child.name}: {child.icon}")

# 删除临时文件
import os
os.remove('check_submenu_icons.py')
