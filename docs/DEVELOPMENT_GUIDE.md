# 后端管理系统开发指南

## 1. 开发环境搭建

### 1.1 环境要求

- Python 3.10+（推荐3.12）
- Django 5.2.5+
- Django REST Framework 3.16.1+
- Redis 6.0+
- PostgreSQL 14+ / MySQL 8.0+ / SQLite 3（开发环境）

### 1.2 安装步骤

#### 1.2.1 克隆代码库

```bash
# 使用Git克隆代码库
git clone https://github.com/your-username/backend_management_system.git
cd backend_management_system
```

#### 1.2.2 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

#### 1.2.3 安装依赖

项目支持两种依赖管理方式：pip和poetry。

**使用pip安装依赖：**

```bash
# 确保pip是最新版本
pip install --upgrade pip

# 安装开发依赖
pip install -r requirements_dev.txt

# 或安装生产依赖
pip install -r requirements.txt
```

**使用poetry安装依赖（推荐）：**

```bash
# 安装poetry（如果尚未安装）
pip install poetry

# 安装项目依赖
poetry install

# 激活poetry虚拟环境
poetry shell
```

#### 1.2.4 配置环境变量

复制示例环境文件并配置：

```bash
cp .env.example .env

# 编辑.env文件设置自己的配置
# Windows
notepad .env
# Linux/macOS
vim .env
```

主要环境变量说明：

- `SECRET_KEY`: Django项目密钥
- `DEBUG`: 调试模式（开发环境设为True）
- `ALLOWED_HOSTS`: 允许访问的主机名
- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL
- `CELERY_BROKER_URL`: Celery消息队列URL
- `CELERY_RESULT_BACKEND`: Celery结果后端URL

编辑`.env`文件，设置开发环境配置：

```
SECRET_KEY=development-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置 (默认SQLite)
# DATABASE_ENGINE=django.db.backends.sqlite3
# DATABASE_NAME=db.sqlite3

# Redis配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 1.2.5 运行数据库迁移

```bash
# 生成迁移文件（如果有模型变更）
python manage.py makemigrations

# 执行数据库迁移
python manage.py migrate
```

**注意事项：**
- 在修改模型后，必须运行`makemigrations`命令生成迁移文件
- 迁移文件应与代码一起提交到版本控制系统
- 在合并分支时，如果遇到迁移冲突，应手动解决冲突

#### 1.2.6 创建超级用户

```bash
# 创建超级用户
python manage.py createsuperuser

# 按照提示输入用户名、邮箱和密码
```

#### 1.2.7 启动开发服务器

**启动HTTP开发服务器：**

```bash
# 启动Django开发服务器（默认端口8000）
python manage.py runserver

# 或指定端口
python manage.py runserver 8080
```

**启动WebSocket服务（用于实时功能）：**

```bash
# 使用Daphne启动ASGI服务器，同时支持HTTP和WebSocket
daphne -b 127.0.0.1 -p 8001 backend_management.asgi:application
```

**启动Celery工作节点（用于异步任务和定时任务）：**

```bash
# 启动Celery工作节点
celery -A backend_management worker --loglevel=info

# 启动Celery Beat（用于定时任务）
celery -A backend_management beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

开发服务器将在 http://127.0.0.1:8000/ 启动。

## 2. 项目结构

后端管理系统采用标准的Django项目结构，主要包含以下模块：

```
backend_management_system/
├── backend_management/    # 项目配置目录
│   ├── __init__.py        # 初始化文件
│   ├── asgi.py            # ASGI入口
│   ├── celery.py          # Celery配置
│   ├── settings.py        # 项目设置
│   ├── urls.py            # 主URL配置
│   └── wsgi.py            # WSGI入口
├── dashboard/             # 主要应用模块
│   ├── __init__.py        # 初始化文件
│   ├── admin.py           # 后台管理注册
│   ├── apps.py            # 应用配置
│   ├── captcha.py         # 验证码处理
│   ├── consumers.py       # WebSocket消费者
│   ├── filters.py         # 过滤器
│   ├── management/        # 自定义管理命令
│   ├── middleware/        # 自定义中间件
│   ├── migrations/        # 数据库迁移文件
│   ├── mixins.py          # 视图混入类
│   ├── models.py          # 数据模型
│   ├── permissions.py     # 权限控制
│   ├── routing.py         # WebSocket路由
│   ├── serializers.py     # 序列化器
│   ├── task_serializers.py # 任务序列化器
│   ├── task_utils.py      # 任务工具函数
│   ├── task_views_api.py  # 任务API视图
│   ├── tasks.py           # Celery任务
│   ├── tests.py           # 应用测试
│   ├── throttles/         # 访问节流控制
│   ├── urls.py            # 应用URL配置
│   ├── utils/             # 应用工具函数
│   └── views_api.py       # API视图
├── docs/                  # 项目文档
├── tests/                 # 集成测试用例
├── media/                 # 媒体文件存储
├── static_root/           # 静态文件收集目录
├── requirements.txt       # 生产依赖
├── pyproject.toml         # Poetry项目配置
├── poetry.lock            # Poetry依赖锁文件
└── manage.py              # Django管理脚本
```

## 3. 代码规范

### 3.1 Python代码规范

项目遵循PEP 8代码规范，使用black进行代码格式化，flake8进行代码检查：

```bash
# 格式化代码
black .

# 检查代码
flake8 .
```

### 3.2 命名规范

- 类名：使用大驼峰命名法，如`UserViewSet`
- 函数/方法名：使用小写字母加下划线，如`get_user_list`
- 变量名：使用小写字母加下划线，如`user_count`
- 常量：使用全大写字母加下划线，如`MAX_PAGE_SIZE`
- 模块名：使用小写字母加下划线，如`user_management`

### 3.3 注释规范

- 为所有公共函数和方法添加文档字符串
- 复杂逻辑添加行注释
- 模型字段添加`verbose_name`和`help_text`

```python
class User(models.Model):
    """用户模型"""
    username = models.CharField(max_length=150, unique=True, verbose_name="用户名", help_text="登录用户名")
    password = models.CharField(max_length=128, verbose_name="密码")
    
    def get_full_name(self):
        """\返回用户的完整名称"""
        return self.name or self.username
```

## 4. 开发流程

### 4.1 分支管理

项目采用Git分支管理，标准分支结构如下：

- `main`：主分支，包含生产环境代码
- `develop`：开发分支，包含最新开发代码
- `feature/xxx`：特性分支，用于开发新功能
- `bugfix/xxx`：修复分支，用于修复bug

### 4.2 开发步骤

1. 从`develop`分支创建新的特性分支
2. 开发新功能或修复bug
3. 编写单元测试
4. 运行测试确保通过
5. 提交代码并推送到远程仓库
6. 创建合并请求(Merge Request)到`develop`分支
7. 代码审查通过后合并到`develop`分支

### 4.3 创建新功能

#### 4.3.1 创建新模型

在`dashboard/models.py`文件中添加新的模型类：

```python
class NewFeature(models.Model):
    """新功能模型"""
    name = models.CharField(max_length=100, verbose_name="名称")
    description = models.TextField(blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "新功能"
        verbose_name_plural = "新功能管理"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
```

#### 4.3.2 创建序列化器

在`dashboard/serializers.py`中添加新的序列化器：

```python
class NewFeatureSerializer(serializers.ModelSerializer):
    """新功能序列化器"""
    
    class Meta:
        model = NewFeature
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
```

#### 4.3.3 创建视图集

在`dashboard/views_api.py`中添加新的视图集：

```python
class NewFeatureViewSet(OperationLogMixin, FilterMixin, viewsets.ModelViewSet):
    """新功能视图集"""
    queryset = NewFeature.objects.all()
    serializer_class = NewFeatureSerializer
    permission_classes = [IsAuthenticated, PermissionRequired]
    filterset_class = NewFeatureFilter  # 如果需要过滤器
    operation_module = "新功能管理"  # 操作日志模块名称
    
    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_operation_log(instance, '创建新功能')
        
    def perform_update(self, serializer):
        instance = serializer.save()
        self.create_operation_log(instance, '更新新功能')
        
    def perform_destroy(self, instance):
        self.create_operation_log(instance, '删除新功能')
        instance.delete()

    # 自定义批量操作示例
    @action(detail=False, methods=['delete'], url_path='batch_delete')
    def batch_delete(self, request):
        """批量删除功能"""
        try:
            ids = request.data.get('ids', [])
            if not ids:
                return Response({'error': '未提供要删除的ID列表'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 执行批量删除
            deleted_count, _ = self.get_queryset().filter(id__in=ids).delete()
            
            # 记录操作日志
            self.create_operation_log(None, f'批量删除{deleted_count}条记录', data={'ids': ids})
            
            return Response({'message': f'成功删除{deleted_count}条记录'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'批量删除失败: {str(e)}')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

#### 4.3.4 添加URL路由

在`dashboard/urls.py`中注册新的视图集路由：

```python
router = DefaultRouter()
router.register(r'new_features', NewFeatureViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

## 5. 权限树API开发说明

### 5.1 权限树API概述

权限树API是本系统的核心功能之一，用于获取完整的菜单权限树或指定角色的菜单权限树，包含菜单和按钮权限信息。这些API主要用于前端构建动态菜单和权限控制界面。

### 5.2 权限树API设计

系统提供两个主要的权限树API：

1. **获取完整权限树**: `GET /api/permissions/tree/`
   - 获取系统中所有菜单和按钮的权限树结构

2. **获取角色权限树**: `GET /api/roles/{id}/permissions_tree/`
   - 获取指定角色已拥有的菜单和按钮权限树结构，包含权限选中状态标记

### 5.3 权限树API实现

#### 5.3.1 完整权限树API实现

在`dashboard/views/permission_views.py`中实现：

```python
class PermissionViewSet(BaseViewSet, TreeViewMixin):
    # ... 其他代码 ...
    
    @action(detail=False, methods=["get"])  
    def tree(self, request):
        """获取完整的权限树（包含菜单和按钮）"""
        # 构建缓存键
        cache_key = self.get_cache_key('tree')
        
        # 尝试从缓存获取数据
        cached_tree = self._get_cached_data(cache_key)
        if cached_tree:
            return Response(cached_tree)
        
        # 优化查询：使用prefetch_related同时获取菜单和关联的按钮权限
        menus = (
            Menu.objects.filter(is_deleted=False)
            .order_by("sort")
            .select_related('parent')
            .prefetch_related(
                Prefetch('menuPermission',
                         queryset=MenuButton.objects.only(
                             'id', 'name', 'value', 'api', 'method', 'sort'
                         ))
            )
            .only(
                'id', 'name', 'sort', 'parent_id', 'status',
                'web_path', 'component', 'icon', 'visible'
            )
        )
        
        # 构建权限树
        menu_tree = self._build_permission_tree(menus)
        
        # 缓存权限树，设置过期时间为10分钟
        self._set_cached_data(cache_key, menu_tree, 600)
        
        return Response(menu_tree)
        
    def _build_permission_tree(self, menus):
        """迭代方式构建权限树，提高性能并避免栈溢出"""
        # 创建节点映射字典，方便快速查找父节点
        node_map = {}
        root_nodes = []
        
        # 1. 先将所有菜单节点放入字典中，并找出根节点
        for menu in menus:
            # 复制菜单数据
            menu_data = {
                "id": menu.id,
                "name": menu.name,
                "web_path": menu.web_path,
                "component": menu.component,
                "icon": menu.icon,
                "visible": menu.visible,
                "sort": menu.sort,
                "children": []  # 初始化子节点列表
            }
            
            node_map[menu.id] = menu_data
            
            # 记录根节点（parent_id为None的节点）
            if menu.parent_id is None:
                root_nodes.append(menu_data)
        
        # 2. 构建父子关系
        for menu in menus:
            if menu.parent_id is not None and menu.parent_id in node_map:
                # 如果当前节点有父节点且父节点存在于映射中
                parent_node = node_map[menu.parent_id]
                current_node = node_map[menu.id]
                parent_node['children'].append(current_node)
        
        # 3. 为每个菜单节点添加按钮权限
        for menu in menus:
            menu_node = node_map[menu.id]
            buttons = []
            
            # 从prefetch_related的结果中获取按钮权限
            for button in menu.menuPermission.all():
                button_data = {
                    "id": button.id,
                    "name": button.name,
                    "value": button.value,
                    "api": button.api,
                    "method": button.method,
                    "method_display": dict(MenuButton.METHOD_CHOICES).get(
                        button.method, ""
                    ),
                    "sort": button.sort,
                }
                buttons.append(button_data)
            
            # 对按钮按sort字段排序
            buttons.sort(key=lambda x: x.get('sort', 0))
            
            # 将按钮添加到菜单节点
            menu_node['buttons'] = buttons
        
        # 4. 对每个节点的子节点按sort字段排序
        for node_id, node in node_map.items():
            node['children'].sort(key=lambda x: x.get('sort', 0))
        
        # 对根节点按sort字段排序
        root_nodes.sort(key=lambda x: x.get('sort', 0))
        
        return root_nodes
```

#### 5.3.2 角色权限树API实现

在`dashboard/views/role_views.py`中实现：

```python
class RoleViewSet(BaseViewSet):
    # ... 其他代码 ...
    
    @action(detail=True, methods=["get"])  
    def permissions_tree(self, request, pk=None):
        """获取指定角色的菜单权限树，优化树构建性能"""
        # 权限检查已在中间件中实现
        role = self.get_object()
        
        # 尝试从缓存获取角色权限树
        cache_key = f'role_permissions_tree_{role.id}'
        cached_tree = cache.get(cache_key)
        
        if cached_tree:
            return Response(cached_tree)
        
        # 获取角色已有的权限ID列表
        role_permission_ids = set(role.permissions.values_list("id", flat=True))  # 使用集合提高查找效率
        
        # 优化查询：使用prefetch_related同时获取菜单和关联的按钮权限，并只获取必要字段
        menus = (
            self._get_menus_for_permission_tree()
        )
        
        # 将菜单按钮权限按菜单ID分组
        buttons_by_menu = self._group_buttons_by_menu(menus, role_permission_ids)
        
        # 构建包含按钮权限的菜单树 - 使用迭代方式替代递归
        menu_tree_with_buttons = self._build_menu_tree_with_buttons(
            menus, buttons_by_menu
        )
        
        # 缓存角色权限树，设置过期时间为5分钟
        cache.set(cache_key, menu_tree_with_buttons, 300)
        
        return Response(menu_tree_with_buttons)
        
    def _get_menus_for_permission_tree(self):
        """获取用于构建权限树的菜单查询集"""
        return (
            Menu.objects.filter(is_deleted=False)
            .order_by("sort")
            .select_related('parent')
            .prefetch_related(
                Prefetch('menuPermission',
                         queryset=MenuButton.objects.only(
                             'id', 'name', 'value', 'api', 'method', 'menu_id'
                         ))
            )
            .only(
                'id', 'name', 'sort', 'parent_id', 'status',
                'web_path', 'component', 'icon', 'visible'
            )
        )
        
    def _group_buttons_by_menu(self, menus, role_permission_ids):
        """将菜单按钮权限按菜单ID分组，并标记角色是否拥有该权限"""
        buttons_by_menu = {}
        
        for menu in menus:
            menu_buttons = []
            
            # 从prefetch_related的结果中获取按钮权限
            for button in menu.menuPermission.all():
                button_data = {
                    "id": button.id,
                    "name": button.name,
                    "value": button.value,
                    "api": button.api,
                    "method": button.method,
                    "method_display": dict(MenuButton.METHOD_CHOICES).get(
                        button.method, ""
                    ),
                    "selected": button.id in role_permission_ids  # 标记该权限是否被角色拥有
                }
                menu_buttons.append(button_data)
                
            # 对按钮按id排序（或根据需要选择其他排序字段）
            menu_buttons.sort(key=lambda x: x.get('id', 0))
            
            # 将按钮列表添加到字典中
            buttons_by_menu[menu.id] = menu_buttons
            
        return buttons_by_menu
        
    def _build_menu_tree_with_buttons(self, menus, buttons_by_menu):
        """使用迭代方式构建包含按钮权限的菜单树，提高性能并避免栈溢出"""
        # 创建节点映射字典，方便快速查找父节点
        node_map = {}
        root_nodes = []
        
        # 先将所有菜单节点放入字典中，并准备数据
        menu_list = []
        for menu in menus:
            # 复制菜单数据
            menu_data = {
                "id": menu.id,
                "name": menu.name,
                "web_path": menu.web_path,
                "component": menu.component,
                "icon": menu.icon,
                "visible": menu.visible,
                "sort": menu.sort,
                "parent_id": menu.parent_id,
                "buttons": buttons_by_menu.get(menu.id, []),  # 添加菜单下的按钮权限
                "children": []  # 初始化子节点列表
            }
            
            node_map[menu.id] = menu_data
            menu_list.append(menu_data)
        
        # 构建树结构
        # 1. 构建父子关系
        for menu_data in menu_list:
            if menu_data['parent_id'] is not None and menu_data['parent_id'] in node_map:
                parent_node = node_map[menu_data['parent_id']]
                parent_node['children'].append(menu_data)
        
        # 2. 找出所有根节点
        for menu_data in menu_list:
            if menu_data['parent_id'] is None:
                root_nodes.append(menu_data)
        
        # 3. 对每个节点的子节点按sort字段排序
        for node_id, node in node_map.items():
            node['children'].sort(key=lambda x: x.get('sort', 0))
        
        # 4. 对根节点按sort字段排序
        root_nodes.sort(key=lambda x: x.get('sort', 0))
        
        return root_nodes
```

### 5.4 权限树构建工具类

系统提供了`MenuTreeBuilder`工具类，用于构建菜单树和角色权限树：

```python
class MenuTreeBuilder:
    """菜单树构建工具类
    
    专门用于构建菜单树和角色权限树
    """
    
    @staticmethod
    def build_menu_tree(
        menus: QuerySet, 
        menu_model_class=None,
        include_buttons: bool = False,
        role_permission_ids: Optional[Set[int]] = None
    ) -> List[Dict]:
        """构建菜单树，支持包含按钮权限
        
        Args:
            menus: 菜单查询集
            menu_model_class: 菜单模型类，用于获取关联的按钮
            include_buttons: 是否包含按钮权限
            role_permission_ids: 角色已有的权限ID集合（用于标记选中状态）
        
        Returns:
            list: 菜单树结构
        """
        # 创建节点映射字典，方便快速查找父节点
        node_map = {}
        root_nodes = []
        
        # 1. 先将所有菜单节点放入字典中
        for menu in menus:
            # 复制菜单数据
            menu_data = {
                "id": menu.id,
                "parent_id": menu.parent_id,
                "name": menu.name,
                "web_path": menu.web_path,
                "component": menu.component,
                "icon": menu.icon,
                "visible": menu.visible,
                "sort": menu.sort,
                "is_link": getattr(menu, 'is_link', False),
                "is_catalog": getattr(menu, 'is_catalog', False),
                "component_name": getattr(menu, 'component_name', ''),
                "status": getattr(menu, 'status', True),
                "cache": getattr(menu, 'cache', False),
                "children": []
            }
            
            # 如果需要包含按钮权限
            if include_buttons:
                menu_data["buttons"] = []
                # 获取菜单关联的按钮权限
                if hasattr(menu, 'menuPermission'):
                    for button in menu.menuPermission.all():
                        button_data = {
                            "id": button.id,
                            "name": button.name,
                            "value": button.value,
                            "api": button.api,
                            "method": button.method,
                            "method_display": dict(button.METHOD_CHOICES).get(button.method, "") if hasattr(button, 'METHOD_CHOICES') else "",
                            "selected": button.id in role_permission_ids if role_permission_ids else False,
                        }
                        menu_data["buttons"].append(button_data)
            
            node_map[menu.id] = menu_data
            
            # 记录根节点
            if menu.parent_id is None:
                root_nodes.append(menu_data)
        
        # 2. 构建父子关系
        for menu in menus:
            if menu.parent_id is not None and menu.parent_id in node_map:
                parent_node = node_map[menu.parent_id]
                current_node = node_map[menu.id]
                parent_node['children'].append(current_node)
                
        # 3. 对每个节点的子节点按sort字段排序
        for node_id, node in node_map.items():
            node['children'].sort(key=lambda x: x.get('sort', 0))
            
        # 4. 对根节点按sort字段排序
        root_nodes.sort(key=lambda x: x.get('sort', 0))
        
        return root_nodes
        
    @staticmethod
    def clear_role_permission_cache(role_id: int):
        """清除指定角色的权限树缓存"""
        cache.delete(f'role_permissions_tree_{role_id}')
        
        # 清除用户权限缓存
        if hasattr(cache, 'delete_pattern'):
            try:
                cache.delete_pattern('user_permissions_*')
            except Exception as e:
                logger.debug(f"尝试清除用户权限缓存时出错: {str(e)}，跳过此操作")
```

### 5.5 权限树API性能优化

权限树API的实现包含多项性能优化措施：

1. **缓存机制**：使用缓存存储权限树数据，避免重复计算
   - 完整权限树缓存10分钟
   - 角色权限树缓存5分钟

2. **优化数据库查询**：使用`select_related`和`prefetch_related`减少数据库查询次数
   - 一次性预加载所有需要的数据
   - 使用`only`方法只选择需要的字段

3. **迭代方式构建树**：使用迭代而非递归方式构建树结构
   - 避免递归深度过大导致的栈溢出问题
   - 提高大数据量下的性能

4. **数据结构优化**：使用字典映射快速查找节点
   - 避免在树构建过程中频繁遍历查找父节点
   - 提高树构建效率

### 5.6 调用权限树API的注意事项

1. **认证要求**：权限树API需要Token认证
   - 确保在请求头中包含有效的Authorization Token

2. **缓存策略**：了解API的缓存机制
   - 修改权限后，需要清除相关缓存才能看到最新结果
   - 使用`MenuTreeBuilder.clear_role_permission_cache(role_id)`清除指定角色的权限树缓存

3. **性能考虑**：处理大量菜单和权限时的注意事项
   - 系统已经优化了大量数据下的性能表现
   - 仍建议合理控制菜单和按钮的数量，避免过度膨胀

4. **错误处理**：API调用可能出现的错误及处理方法
   - 权限错误：确保用户有足够的权限访问API
   - 服务器错误：查看服务器日志获取详细错误信息

## 6. 测试权限树API

### 6.1 单元测试

在`dashboard/tests.py`中添加权限树API的单元测试：

```python
class PermissionTreeAPITest(TestCase):
    """权限树API测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试菜单和按钮
        self.root_menu = Menu.objects.create(
            name="首页",
            web_path="/dashboard",
            component="dashboard/index",
            icon="home",
            visible=True,
            sort=1
        )
        
        self.permission_menu = Menu.objects.create(
            name="权限管理",
            web_path="/permission",
            component="permission/index",
            icon="lock",
            visible=True,
            sort=2
        )
        
        # 创建按钮权限
        self.view_button = MenuButton.objects.create(
            menu=self.root_menu,
            name="View",
            value="view",
            api="/api/dashboard/data",
            method=0
        )
        
        self.add_button = MenuButton.objects.create(
            menu=self.permission_menu,
            name="Add",
            value="add",
            api="/api/permissions",
            method=1
        )
        
        self.edit_button = MenuButton.objects.create(
            menu=self.permission_menu,
            name="Edit",
            value="edit",
            api="/api/permissions/{id}",
            method=2
        )
        
        self.delete_button = MenuButton.objects.create(
            menu=self.permission_menu,
            name="Delete",
            value="delete",
            api="/api/permissions/{id}",
            method=3
        )
        
        # 创建测试角色和用户
        self.role = Role.objects.create(
            name="测试角色",
            key="test_role"
        )
        
        # 分配权限给角色
        self.role.permissions.add(self.view_button, self.add_button)
        
        # 创建测试用户并分配角色
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword"
        )
        
        # 假设用户模型有profile和roles字段
        # self.user.profile.roles.add(self.role)
        
        # 获取Token用于认证
        self.token = Token.objects.create(user=self.user)
    
    def test_get_permissions_tree(self):
        """测试获取完整权限树"""
        # 设置认证Token
        headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}
        
        # 发送请求
        response = self.client.get('/api/permissions/tree/', **headers)
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查响应数据结构
        tree_data = response.json()
        self.assertIsInstance(tree_data, list)
        self.assertEqual(len(tree_data), 2)  # 应该有两个根菜单
        
        # 检查第一个菜单是否为首页
        self.assertEqual(tree_data[0]['name'], "首页")
        self.assertEqual(len(tree_data[0]['buttons']), 1)  # 首页应该有一个按钮
        
        # 检查第二个菜单是否为权限管理
        self.assertEqual(tree_data[1]['name'], "权限管理")
        self.assertEqual(len(tree_data[1]['buttons']), 3)  # 权限管理应该有三个按钮
    
    def test_get_role_permissions_tree(self):
        """测试获取角色权限树"""
        # 设置认证Token
        headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}
        
        # 发送请求
        response = self.client.get(f'/api/roles/{self.role.id}/permissions_tree/', **headers)
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查响应数据结构
        tree_data = response.json()
        self.assertIsInstance(tree_data, list)
        
        # 找到首页菜单
        root_menu = next(menu for menu in tree_data if menu['name'] == "首页")
        self.assertTrue(root_menu['buttons'][0]['selected'])  # View按钮应该被选中
        
        # 找到权限管理菜单
        permission_menu = next(menu for menu in tree_data if menu['name'] == "权限管理")
        
        # 检查按钮选中状态
        add_button = next(btn for btn in permission_menu['buttons'] if btn['name'] == "Add")
        self.assertTrue(add_button['selected'])  # Add按钮应该被选中
        
        edit_button = next(btn for btn in permission_menu['buttons'] if btn['name'] == "Edit")
        self.assertFalse(edit_button['selected'])  # Edit按钮不应该被选中
        
        delete_button = next(btn for btn in permission_menu['buttons'] if btn['name'] == "Delete")
        self.assertFalse(delete_button['selected'])  # Delete按钮不应该被选中
```

## 7. 前端集成说明

### 7.1 获取并使用权限树数据

前端可以使用以下方法获取并使用权限树数据：

```javascript
// 获取完整权限树示例
async function getFullPermissionTree() {
  try {
    const response = await api.get('/api/permissions/tree/');
    const permissionTree = response.data;
    
    // 使用权限树数据构建菜单
    buildMenu(permissionTree);
    
    return permissionTree;
  } catch (error) {
    console.error('获取权限树失败:', error);
    throw error;
  }
}

// 获取角色权限树示例
async function getRolePermissionTree(roleId) {
  try {
    const response = await api.get(`/api/roles/${roleId}/permissions_tree/`);
    const rolePermissionTree = response.data;
    
    // 使用角色权限树数据构建权限选择界面
    buildPermissionSelector(rolePermissionTree);
    
    return rolePermissionTree;
  } catch (error) {
    console.error('获取角色权限树失败:', error);
    throw error;
  }
}

// 构建菜单示例
function buildMenu(permissionTree) {
  permissionTree.forEach(menu => {
    // 创建菜单项
    const menuItem = createMenuItem(menu);
    
    // 如果有子菜单，递归创建
    if (menu.children && menu.children.length > 0) {
      const subMenu = createSubMenu();
      menu.children.forEach(subMenuItem => {
        subMenu.appendChild(createMenuItem(subMenuItem));
      });
      menuItem.appendChild(subMenu);
    }
    
    // 添加到菜单容器
    menuContainer.appendChild(menuItem);
  });
}

// 构建权限选择界面示例
function buildPermissionSelector(rolePermissionTree) {
  rolePermissionTree.forEach(menu => {
    // 创建菜单复选框
    const menuCheckbox = createCheckbox({
      id: menu.id,
      name: menu.name,
      type: 'menu'
    });
    
    // 创建按钮权限复选框组
    const buttonGroup = createButtonGroup(menu.name);
    
    menu.buttons.forEach(button => {
      const buttonCheckbox = createCheckbox({
        id: button.id,
        name: button.name,
        type: 'button',
        checked: button.selected
      });
      buttonGroup.appendChild(buttonCheckbox);
    });
    
    // 添加到权限选择器容器
    permissionContainer.appendChild(menuCheckbox);
    permissionContainer.appendChild(buttonGroup);
  });
}

在`dashboard/urls.py`中注册新的视图集：

```python
router.register(r'new_features', NewFeatureViewSet)
```

#### 4.3.5 创建数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. 测试指南

项目使用pytest进行单元测试和API测试。完整的测试策略、环境配置和最佳实践请参考[TEST_GUIDE.md](TEST_GUIDE.md)。

### 5.1 测试命令

项目测试文件存放在`tests/`目录下：

```bash
# 运行所有测试
pytest

# 运行特定模块的测试
pytest tests/test_user_api.py

# 生成测试覆盖率报告
pytest --cov=dashboard tests/
```

### 5.2 API测试最佳实践

API测试应遵循`docs/API_TEST_BEST_PRACTICES.md`中的最佳实践，包括测试环境隔离与清理、严格的断言标准和全面的测试覆盖。

## 6. 错误处理与日志记录

### 6.1 错误处理最佳实践

在API开发中，正确的错误处理对于提高系统的健壮性和用户体验至关重要。项目采用统一的异常处理机制：

1. **使用Django REST Framework的异常处理**：

系统使用DRF内置的异常处理机制，并通过中间件进行统一处理。示例代码：

```python
# 在dashboard/middleware/custom_exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback
from django.conf import settings

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # 调用DRF的默认异常处理
    response = exception_handler(exc, context)
    request = context.get('request')
    view = context.get('view')
    
    # 记录异常信息
    if response is None:
        # 未被DRF处理的异常
        logger.error(f"未处理的异常: {str(exc)}", 
                    exc_info=True,
                    extra={
                        'request': request,
                        'view': view.__class__.__name__ if view else None
                    })
        
        # 返回统一的500错误响应
        if settings.DEBUG:
            return Response({
                'error': '服务器内部错误',
                'detail': str(exc),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'error': '服务器内部错误',
                'detail': '请联系管理员获取帮助'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 已被DRF处理的异常，确保响应格式一致
    if isinstance(response.data, dict) and 'detail' in response.data:
        response.data = {'error': response.data['detail']}
        
    return response
```

2. **在settings.py中配置自定义异常处理**：

```python
REST_FRAMEWORK = {
    # ...其他配置
    'EXCEPTION_HANDLER': 'dashboard.middleware.custom_exception_handler.custom_exception_handler',
    # ...其他配置
}
```

### 6.2 日志记录规范

1. **配置日志格式**：确保日志包含足够的上下文信息

```python
# 在settings.py中配置日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'dashboard': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

2. **正确记录日志**：

```python
# 在代码中使用日志
import logging
logger = logging.getLogger(__name__)

# 记录不同级别的日志
logger.debug('这是调试信息')  # 仅在调试模式下有用的详细信息
logger.info('这是一般信息')   # 记录正常的操作
logger.warning('这是警告信息') # 记录可能的问题，但不会阻止程序运行
logger.error('这是错误信息')   # 记录错误，但程序可以继续运行
logger.critical('这是严重错误') # 记录导致程序终止的严重错误

# 记录异常信息
try:
    # 可能抛出异常的代码
except Exception as e:
    logger.error(f'操作失败: {str(e)}', exc_info=True)  # exc_info=True会包含完整的堆栈跟踪
```

## 7. 性能优化

### 7.1 数据库优化

- 使用`select_related`和`prefetch_related`减少数据库查询
- 对频繁查询的字段添加索引
- 使用分页限制返回数据量

```python
# 使用select_related优化查询
queryset = User.objects.select_related('department').all()

# 使用prefetch_related优化多对多关系查询
queryset = User.objects.prefetch_related('roles').all()
```

### 7.2 缓存策略

项目使用Redis作为缓存后端，实现了多级缓存策略：

1. **Django缓存框架集成**：

```python
# 在settings.py中配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 缓存超时设置（秒）
CACHE_MIDDLEWARE_SECONDS = 60 * 15  # 15分钟
```

2. **视图级缓存**：

```python
# 使用缓存_page装饰器缓存整个视图响应
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view

@api_view(['GET'])
@cache_page(60 * 15)  # 缓存15分钟
def get_statistics(request):
    # 视图逻辑
    pass
```

3. **使用缓存工具类**：

项目在`dashboard/utils/cache_utils.py`中提供了缓存工具类，用于更灵活的缓存管理：

```python
from django.core.cache import cache
import hashlib
from django.utils.translation import gettext_lazy as _

class CacheManager:
    """缓存管理类"""
    
    @staticmethod
    def generate_key(prefix, *args):
        """生成唯一的缓存键"""
        key_parts = [prefix] + list(args)
        key_str = ':'.join(str(part) for part in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @classmethod
    def set(cls, prefix, value, timeout=3600, *args):
        """设置缓存"""
        key = cls.generate_key(prefix, *args)
        cache.set(key, value, timeout)
        return key
    
    @classmethod
    def get(cls, prefix, *args):
        """获取缓存"""
        key = cls.generate_key(prefix, *args)
        return cache.get(key)
    
    @classmethod
    def delete(cls, prefix, *args):
        """删除缓存"""
        key = cls.generate_key(prefix, *args)
        cache.delete(key)
```

4. **常见用例**：

```python
from dashboard.utils.cache_utils import CacheManager

# 缓存用户数据
user_data = {'id': 1, 'name': '张三'}
CacheManager.set('user_profile', user_data, timeout=3600, user_id=1)

# 获取缓存的用户数据
cached_user = CacheManager.get('user_profile', user_id=1)

# 清除特定用户的缓存
CacheManager.delete('user_profile', user_id=1)
```

5. **缓存失效策略**：
- 使用合理的缓存过期时间
- 数据更新时主动清除相关缓存
- 关键业务数据谨慎使用缓存
- 考虑使用缓存版本控制

## 7. 常见开发问题解决

### 7.1 数据库迁移冲突

**问题**：执行`migrate`命令时出现迁移冲突

**解决方案**：
- 检查并删除重复的迁移文件
- 使用`python manage.py migrate --fake`命令跳过已应用的迁移
- 对于复杂冲突，考虑重新生成迁移文件
- 使用`python manage.py showmigrations`查看迁移状态

### 7.2 依赖包版本冲突

**问题**：安装依赖时出现版本冲突

**解决方案**：
- 检查并更新`requirements.txt`中的版本约束
- 创建新的虚拟环境重新安装依赖
- 使用`pip check`检查已安装包的兼容性
- 使用`poetry`管理依赖可更好地解决版本冲突问题

### 7.3 API文档生成失败

**问题**：无法生成或访问Swagger/ReDoc文档

**解决方案**：
- 确保`drf-yasg`包已正确安装
- 检查URL配置中是否正确注册了文档视图
- 验证模型和序列化器定义是否符合规范
- 运行`python manage.py collectstatic`确保静态文件正确收集

### 7.4 WebSocket连接问题

**问题**：无法建立WebSocket连接

**解决方案**：
- 确保Daphne服务器已启动
- 检查浏览器控制台是否有连接错误
- 验证routing.py中的WebSocket路由配置
- 确认CORS设置是否允许WebSocket连接

### 7.5 Celery任务执行失败

**问题**：Celery异步任务执行失败

**解决方案**：
- 检查Redis服务是否正常运行
- 查看Celery工作节点日志了解具体错误
- 确认任务参数正确且序列化支持
- 验证任务依赖的服务是否可用

### 7.1 数据库迁移冲突

**问题**：执行`migrate`命令时出现迁移冲突

**解决方案**：
- 检查并删除重复的迁移文件
- 使用`python manage.py migrate --fake`命令跳过已应用的迁移
- 对于复杂冲突，考虑重新生成迁移文件

### 7.2 依赖包版本冲突

**问题**：安装依赖时出现版本冲突

**解决方案**：
- 检查并更新`requirements.txt`中的版本约束
- 创建新的虚拟环境重新安装依赖
- 使用`pip check`检查已安装包的兼容性

### 7.3 API文档生成失败

**问题**：无法生成或访问Swagger/ReDoc文档

**解决方案**：
- 确保`drf-yasg`包已正确安装
- 检查URL配置中是否正确注册了文档视图
- 验证模型和序列化器定义是否符合规范

## 8. 代码审查指南

代码提交前应进行自我审查，确保：

- 遵循项目代码规范
- 所有功能都有相应的测试用例
- 代码逻辑清晰，注释完整
- 没有遗留调试代码
- 没有明显的性能问题

## 9. 开发工具推荐

- **IDE**：PyCharm、VSCode
- **代码格式化**：black, isort
- **代码检查**：flake8, pylint
- **测试框架**：pytest, coverage
- **数据库管理**：DBeaver, pgAdmin
- **API测试**：Postman, Insomnia

## 10. 团队协作规范

为确保团队高效协作和代码质量，项目遵循以下协作规范：

### 10.1 Git工作流

- 采用Git Flow工作流
- 功能开发在`feature/`分支进行
- Bug修复在`bugfix/`分支进行
- 每日从`develop`分支拉取最新代码
- 提交前进行代码自检和格式化
- 提交信息应清晰描述所做更改，格式为：`类型(模块): 简短描述`
  - 类型：feat（新功能）、fix（bug修复）、docs（文档更新）、style（格式调整）、refactor（代码重构）、test（测试）、chore（构建过程或辅助工具变更）
  
### 10.2 代码审查流程

1. 完成功能开发或Bug修复后，创建合并请求(Merge Request)到`develop`分支
2. 至少邀请1名团队成员进行代码审查
3. 审查者应检查代码是否符合规范、逻辑是否清晰、是否有测试覆盖
4. 作者根据审查意见进行修改
5. 所有评论解决后，由审查者合并代码

### 10.3 开发最佳实践

- 遵循"代码即文档"原则，保持代码自解释性
- 保持提交粒度合理，每个提交解决一个具体问题
- 遇到技术难题及时与团队讨论
- 定期更新开发环境依赖
- 及时响应代码审查评论
- 记录并分享开发经验和技巧

### 10.4 沟通协作

- 使用项目管理工具（如Jira、Trello）跟踪任务进度
- 每日站会同步工作进展和遇到的问题
- 重要决策通过会议讨论并记录
- 技术文档及时更新和共享

## 11. 最后更新时间

最后更新时间：2024-11-06