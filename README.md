# 通用后台管理系统

## 项目简介

通用后台管理系统是一个基于Django和Vue.js开发的企业级全栈管理平台，采用前后端分离架构设计。后端提供RESTful API服务，前端提供现代化的用户界面，系统支持完整的用户权限管理、部门管理、角色管理、操作日志记录、权限树API以及接口白名单管理等核心功能，为企业应用提供全面的管理解决方案。

## 项目特性

- **RBAC 权限体系**：完善的角色基础上的权限控制
- **多租户支持**：完整的租户隔离和管理功能
- **工作流引擎**：支持BPMN 2.0标准的工作流设计、执行和监控
- **用户组织管理**：支持多层级部门结构和用户管理
- **操作日志记录**：记录用户的关键操作，便于审计
- **WebSocket 支持**：实时消息通知功能
- **定时任务支持**：基于 Celery 的任务调度
- **系统监控**：Redis、数据库、服务状态监控
- **消息中心**：站内消息通知和用户消息设置

## 项目功能

### 后端核心功能
- **用户管理**: 用户CRUD、密码重置、权限分配等
- **部门管理**: 部门层级管理、部门用户关联
- **角色管理**: 角色CRUD、角色权限分配
- **权限管理**: 功能权限、数据权限的精细化控制
- **操作日志**: 用户操作记录、审计追踪
- **登录日志**: 用户登录行为记录
- **消息管理**: 系统消息发送、接收、阅读状态管理
- **数据字典**: 系统参数配置、字典项管理

### 接口白名单管理
- **白名单查询**: 支持按URL地址、请求方法和数据权限状态进行精确查询
- **白名单管理**: 提供添加、编辑、删除单个白名单的能力
- **批量操作**: 支持批量删除选中的白名单记录
- **缓存刷新**: 提供手动刷新白名单缓存的功能，确保配置变更实时生效
- **数据权限控制**: 可针对每个白名单接口独立配置数据权限状态

### 前端功能特色
- **组件化设计**: 高度复用的表单、表格、分页等UI组件
- **响应式布局**: 适配不同屏幕尺寸的设备
- **统一的交互体验**: 一致的操作流程和视觉反馈
- **完善的数据处理**: 多格式响应处理和错误提示机制

## 技术栈

### 后端技术栈
- Django 5.2.5
- Django REST Framework 3.16.1
- Redis 6.0+
- Celery 5.4.0
- Channels 4.0.0 (WebSocket 支持)
- PostgreSQL/MySQL/SQLite (数据库)
- drf-yasg 1.21.5 (API 文档)

### 前端技术栈
- Vue 3 (Composition API)
- Vite
- Element Plus
- Pinia
- Axios
- Vue Router
- SCSS

## 项目结构

### 后端项目结构
```
backend_management_system/
├── backend_management/     # Django项目配置
├── dashboard/              # 主应用
│   ├── management/          # 管理命令
│   ├── middleware/          # 中间件
│   ├── mixins/              # Mixin类
│   ├── models/              # 数据模型
│   │   ├── system/          # 系统管理模型
│   │   ├── tenant/          # 租户模型
│   │   └── workflow/        # 工作流模型
│   ├── serializers/         # API序列化器
│   ├── views/               # API视图
│   │   ├── system/          # 系统管理视图
│   │   ├── tenant/          # 租户管理视图
│   │   └── workflow/        # 工作流视图
│   └── workflow/            # 工作流引擎
│       ├── engine.py        # 引擎协调器
│       ├── parser.py        # BPMN解析器
│       ├── task_creator.py  # 任务创建器
│       ├── navigator.py     # 流程导航器
│       └── assigner.py      # 任务分配器
├── common/                  # 公共模块
├── docs/                    # 项目文档
├── monitor/                  # 监控应用
├── tests/                   # 测试文件
├── manage.py                # Django管理脚本
└── requirements.txt        # 依赖文件
```

### 前端项目结构
```
zzadmin_web/
├── src/
│   ├── api/                 # API请求封装
│   ├── assets/              # 静态资源
│   ├── components/          # 可复用组件
│   │   └── WorkflowDesigner/ # 工作流设计器
│   ├── composables/         # 组合式函数
│   ├── config/              # 配置文件
│   ├── router/              # 路由配置
│   ├── store/               # 状态管理
│   ├── tests/               # 测试文件
│   ├── utils/               # 工具函数
│   │   ├── api/             # API工具
│   │   └── common/          # 通用工具
│   ├── views/               # 页面视图组件
│   │   └── monitor/         # 监控页面
│   ├── App.vue              # 根组件
│   └── main.js              # 入口文件
├── package.json
└── vite.config.js
```

## 快速开始

### 1. 环境准备

#### 必要软件
- Python 3.10+ （推荐3.12）
- Redis 6.0+ （用于WebSocket和Celery支持）

#### 环境变量配置

项目使用`.env`文件管理环境变量。首先创建环境变量文件：

```bash
# 复制示例环境变量文件
cp .env.example .env

# 编辑.env文件设置自己的配置
# Windows系统可直接编辑.env文件
notepad .env
```

主要环境变量说明：
- `SECRET_KEY`: Django项目密钥
- `DEBUG`: 是否开启调试模式（开发环境设为True）
- `ALLOWED_HOSTS`: 允许访问的主机名/IP
- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL

### 2. 安装依赖

```bash
# 进入项目目录
cd backend_management_system

# 创建虚拟环境（如果没有）
python -m venv venv

# 激活虚拟环境
  # Windows
  venv\Scripts\activate
  # macOS/Linux
  source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

### 2. 数据库迁移

```bash
python manage.py migrate
```

### 3. 创建超级用户

```bash
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
# 启动Django开发服务器（HTTP API）
python manage.py runserver
```

服务器将在 http://127.0.0.1:8000/ 启动

### 5. 启动WebSocket服务（可选）

```bash
# 使用Daphne启动ASGI服务器，同时支持HTTP和WebSocket
daphne -b 127.0.0.1 -p 8001 backend_management.asgi:application
```

### 6. 启动Celery工作节点（可选）

```bash
# 启动Celery工作节点
source venv/bin/activate  # 确保激活虚拟环境
celery -A backend_management worker -l info

# 启动Celery Beat（用于定时任务）
celery -A backend_management beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 7. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块的测试
pytest tests/test_auth.py

# 生成测试覆盖率报告
pytest --cov=dashboard --cov-report=html
```

### 8. 访问API文档

启动服务器后，可以访问以下地址查看API文档：
- Swagger文档: http://127.0.0.1:8000/swagger/
- ReDoc文档: http://127.0.0.1:8000/redoc/

## API 文档

系统提供了完整的API文档，包括API端点、请求格式、响应结构和参数说明。

- **API参考文档**：请查看[docs/API_REFERENCE.md](docs/API_REFERENCE.md)获取详细的API端点说明
- **交互式文档**：启动系统后访问`/swagger/`或`/redoc/`获取自动生成的交互式API文档
- **前后端联调指南**：请参考[README_API_INTEGRATION.md](README_API_INTEGRATION.md)文件，获取前后端项目的集成和联调指南

## API 认证

本项目使用Token认证方式。登录成功后，会返回一个token，后续请求需要在HTTP头中包含此token：

```
Authorization: Token your_token_here
```

## 开发说明

### 创建新的API端点

1. 在 `dashboard/models.py` 中定义数据模型
2. 在 `dashboard/serializers.py` 中创建序列化器
3. 在 `dashboard/views_api.py` 中创建视图集
4. 在 `dashboard/urls.py` 中注册视图集到路由器

### 添加权限控制

可以在视图集或视图方法上添加自定义权限控制：

```python
from rest_framework import permissions

class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 自定义权限逻辑
        pass

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [CustomPermission]
    # ...
```

## 项目自动化脚本

为了简化开发流程，项目提供了自动化脚本，可以在代码变更后自动执行一系列命令。

### 使用方法

#### Windows环境

```bash
# 运行所有操作（安装依赖、格式化代码、运行测试等）
update_project.bat --all

# 仅安装依赖
update_project.bat --install

# 仅运行测试
update_project.bat --test
```

#### Linux/macOS环境

```bash
# 为脚本添加执行权限
chmod +x update_project.sh

# 运行所有操作
./update_project.sh --all

# 仅安装依赖和执行数据库迁移
./update_project.sh --install --migrate
```

### 可用选项

- `--install` - 安装项目依赖
- `--test` - 运行测试并生成覆盖率报告
- `--format` - 格式化代码
- `--migrate` - 执行数据库迁移
- `--docs` - 生成项目文档
- `--quality` - 检查代码质量
- `--menus` - 初始化系统菜单
- `--all` - 执行所有上述操作

## 常见问题解答

### 1. 如何解决依赖安装失败的问题？

如果遇到依赖包版本冲突，可以尝试以下解决方案：

```bash
# 更新pip到最新版本
pip install --upgrade pip

# 清除pip缓存
pip cache purge

# 重新安装依赖
pip install -r requirements.txt
```

### 2. Redis连接失败怎么办？

确保Redis服务正在运行，并检查.env文件中的REDIS_URL配置是否正确：

```bash
# 检查Redis服务状态
# Windows
redis-cli ping
# Linux/macOS
systemctl status redis
```

### 3. 如何重置数据库？

```bash
# 删除数据库文件（仅SQLite）
del db.sqlite3

# 删除所有迁移文件
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 重新生成迁移文件并执行迁移
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. 前端项目如何与后端API联调？

请参考 `README_API_INTEGRATION.md` 文件，其中包含详细的API联调指南。

### 5. 如何部署到生产环境？

请参考 `DEPLOYMENT.md` 文件，其中包含完整的生产环境部署指南。

## 文档

项目提供以下文档，帮助您更好地使用和开发系统：

- [使用指南](docs/USAGE_GUIDE.md) - 详细介绍系统功能和使用方法
- [开发指南](docs/DEVELOPMENT_GUIDE.md) - 开发环境配置、代码规范和开发流程
- [测试指南](docs/TEST_GUIDE.md) - 测试策略、环境配置和测试流程
- [DevOps闭环链文档](docs/DEVOPS_PIPELINE.md) - 从开发到部署的完整流程
- [API测试最佳实践](docs/API_TEST_BEST_PRACTICES.md) - API测试用例编写标准
- [部署文档](DEPLOYMENT.md) - 生产环境部署指南
- [前端与后端API联调指南](README_API_INTEGRATION.md) - 前后端协作指南

## 联系我们

如有任何问题或建议，请随时联系我们的开发团队。