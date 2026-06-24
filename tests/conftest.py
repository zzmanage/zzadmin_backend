import os

import django
import pytest
from rest_framework.test import APIClient


# 设置Django设置模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_management.settings")

# 确保Django应用已加载

django.setup()


@pytest.fixture
def api_client():
    """返回一个REST framework的API客户端实例"""
    return APIClient()


@pytest.fixture
def admin_user(django_user_model):
    """创建并返回一个超级用户"""
    user = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="1234"
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """返回一个已认证的API客户端实例"""
    # 直接使用force_authenticate方法进行认证，不依赖内部属性
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def auth_client(authenticated_client):
    """返回一个已认证的API客户端实例（authenticated_client的别名）"""
    return authenticated_client


@pytest.fixture
def superuser(admin_user):
    """返回一个超级用户（admin_user的别名）"""
    return admin_user


@pytest.fixture
def department_model():
    """返回Department模型类"""
    from dashboard.models import Department

    return Department


@pytest.fixture
def role_model():
    """返回Role模型类"""
    from dashboard.models import Role

    return Role


@pytest.fixture
def user_profile_model():
    """返回UserProfile模型类"""
    from dashboard.models import UserProfile

    return UserProfile


@pytest.fixture
def permission_model():
    """返回Permission模型类"""
    from dashboard.models import Permission

    return Permission


@pytest.fixture
def test_permission(permission_model, admin_user):
    """创建并返回一个测试权限对象"""
    permission = permission_model.objects.create(
        name="测试权限",
        code="test_permission",
        description="这是一个测试权限",
        created_by=admin_user,
        updated_by=admin_user,
    )
    return permission


@pytest.fixture
def menu_model():
    """返回Menu模型类"""
    from dashboard.models import Menu

    return Menu


@pytest.fixture
def menu_button_model():
    """返回MenuButton模型类"""
    from dashboard.models import MenuButton

    return MenuButton


@pytest.fixture
def test_menu(menu_model, admin_user):
    """创建并返回一个测试菜单对象"""
    menu = menu_model.objects.create(
        name="测试菜单",
        web_path="/test",
        component="TestComponent",
        sort=1,
        status=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
    return menu


@pytest.fixture
def test_menu_button(menu_button_model, test_menu, admin_user):
    """创建并返回一个测试菜单按钮对象"""
    menu_button = menu_button_model.objects.create(
        menu=test_menu,
        name="测试按钮",
        value="test_button",
        api="/api/test",
        method=0,
        created_by=admin_user,
        updated_by=admin_user,
    )
    return menu_button


@pytest.fixture
def test_department(department_model, admin_user):
    """创建并返回一个测试部门对象"""
    department = department_model.objects.create(
        name="测试部门",
        description="这是一个测试部门",
        key="test_department",
        sort=1,
        status=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
    return department


@pytest.fixture
def test_role(role_model, test_menu_button, admin_user):
    """创建并返回一个测试角色对象"""
    role = role_model.objects.create(
        name="测试角色",
        description="这是一个测试角色",
        key="test_role",
        sort=1,
        status=True,
        data_range=0,
        created_by=admin_user,
        updated_by=admin_user,
    )

    # 添加菜单按钮权限
    role.permissions.add(test_menu_button)

    return role


@pytest.fixture
def test_user(
    django_user_model, user_profile_model, test_department, test_role, admin_user
):
    """创建并返回一个测试用户对象"""
    # 创建基础用户
    user = django_user_model.objects.create_user(
        username="testuser", email="testuser@example.com", password="testuser123"
    )

    # 创建用户扩展信息
    profile = user_profile_model.objects.create(
        user=user,
        department=test_department,
        mobile="13800138000",
        employee_no="EMP001",
        name="测试用户",
        created_by=admin_user,
        updated_by=admin_user,
    )

    # 添加角色 - 使用add方法正确处理多对多关系
    profile.roles.add(test_role)

    return user
