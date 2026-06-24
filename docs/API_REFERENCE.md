# 后端管理系统 API 参考文档

本文档提供后端管理系统所有API端点的详细说明，包括请求格式、响应结构、参数说明等。

## 版本信息

当前版本：v1.0.1

## 基础URL

所有API请求的基础URL为：`http://your-domain.com/api/v1/`

## 认证方式

本系统使用Token认证方式。登录成功后，服务器会返回一个token，后续请求需要在HTTP头中包含此token。

```
Authorization: Token your_token_here
```

## API使用示例

### 登录示例

```bash
# 使用curl登录
curl -X POST http://your-domain.com/api/v1/auth/login/ -H "Content-Type: application/json" -d '{"username": "admin", "password": "yourpassword"}'

# 成功响应
{
  "token": "your_token_here",
  "user_id": 1,
  "username": "admin",
  "name": "管理员",
  "department": "技术部",
  "roles": ["超级管理员"]
}
```

### 使用Token访问API

```bash
# 使用获取的token访问其他API
curl -X GET http://your-domain.com/api/v1/users/ -H "Authorization: Token your_token_here" -H "Content-Type: application/json"
```

## API 端点列表

### 认证

- **POST /auth/login/** - 用户登录
  - **请求体**：`{"username": "用户名", "password": "密码"}`
  - **响应**：成功时返回200状态码和用户信息
    ```json
    {
      "token": "认证令牌", 
      "user_id": 1, 
      "username": "admin", 
      "email": "admin@example.com",
      "name": "管理员",
      "department": "技术部",
      "roles": ["超级管理员"]
    }
    ```
  - **错误响应**：失败时返回400/401状态码
    ```json
    {
      "error": "用户名或密码错误"
    }
    ```

- **POST /auth/logout/** - 用户登出
  - **需要认证**：Token认证
  - **响应**：204 No Content

- **GET /auth/check/** - 检查认证状态
  - **响应**：`{"authenticated": true/false, "user_id": 1, "username": "admin"}`

### 部门管理

- **GET /departments/** - 获取部门列表
  - **需要认证**：Token认证
  - **查询参数**：可选 `parent_id` (按父部门过滤)
  - **响应**：部门列表
    ```json
    {
      "count": 3,
      "next": null,
      "previous": null,
      "results": [
        {"id": 1, "name": "技术部", "description": "负责系统开发", "parent": null},
        {"id": 2, "name": "市场部", "description": "负责市场推广", "parent": null},
        {"id": 3, "name": "前端组", "description": "负责前端开发", "parent": 1}
      ]
    }
    ```

- **POST /departments/** - 创建新部门
  - **需要认证**：Token认证
  - **请求体**：`{"name": "新部门", "description": "部门描述", "parent_id": 1}`
  - **响应**：创建成功的部门详情

- **GET /departments/{id}/** - 获取指定部门详情
  - **需要认证**：Token认证
  - **响应**：部门详情

- **PUT /departments/{id}/** - 更新指定部门
  - **需要认证**：Token认证
  - **请求体**：`{"name": "更新后的部门名", "description": "更新后的描述"}`
  - **响应**：更新后的部门详情

- **DELETE /departments/{id}/** - 删除指定部门
  - **需要认证**：Token认证
  - **响应**：204 No Content (成功) 或 400 (存在子部门或关联用户时失败)

### 角色管理

- **GET /roles/** - 获取角色列表
  - **需要认证**：Token认证
  - **响应**：角色列表及每个角色的权限信息

- **POST /roles/** - 创建新角色
  - **需要认证**：Token认证
  - **请求体**：`{"name": "新角色", "description": "角色描述", "permission_ids": [1, 2, 3]}`
  - **响应**：创建成功的角色详情

- **GET /roles/{id}/** - 获取指定角色详情
  - **需要认证**：Token认证
  - **响应**：角色详情及拥有的权限列表

- **PUT /roles/{id}/** - 更新指定角色
  - **需要认证**：Token认证
  - **请求体**：`{"name": "更新后的角色名", "permission_ids": [1, 2, 4]}`
  - **响应**：更新后的角色详情

- **DELETE /roles/{id}/** - 删除指定角色
  - **需要认证**：Token认证
  - **响应**：204 No Content (成功) 或 400 (有关联用户时失败)

- **GET /roles/{id}/permissions_tree/** - 获取指定角色的菜单权限树
  - **需要认证**：Token认证
  - **响应**：角色菜单权限树结构，标记已拥有的权限
    ```json
    [
      {
        "id": 123,
        "name": "首页",
        "web_path": "/dashboard",
        "component": "dashboard/index",
        "icon": "home",
        "visible": true,
        "sort": 1,
        "parent_id": null,
        "buttons": [
          {
            "id": 9,
            "name": "View",
            "value": "view",
            "api": "/api/dashboard/data",
            "method": 0,
            "method_display": "GET",
            "selected": true
          }
        ],
        "children": []
      },
      {
        "id": 124,
        "name": "权限管理",
        "web_path": "/permission",
        "component": "permission/index",
        "icon": "lock",
        "visible": true,
        "sort": 2,
        "parent_id": null,
        "buttons": [
          {
            "id": 10,
            "name": "Add",
            "value": "add",
            "api": "/api/permissions",
            "method": 1,
            "method_display": "POST",
            "selected": true
          },
          {
            "id": 11,
            "name": "Edit",
            "value": "edit",
            "api": "/api/permissions/{id}",
            "method": 2,
            "method_display": "PUT",
            "selected": true
          },
          {
            "id": 12,
            "name": "Delete",
            "value": "delete",
            "api": "/api/permissions/{id}",
            "method": 3,
            "method_display": "DELETE",
            "selected": true
          }
        ],
        "children": []
      }
    ]
    ```

### 权限管理

- **GET /permissions/** - 获取权限列表
  - **需要认证**：Token认证
  - **查询参数**：可选 `module` (按模块过滤)
  - **响应**：权限列表
    ```json
    {
      "count": 5,
      "next": null,
      "previous": null,
      "results": [
        {"id": 1, "name": "用户查看", "code": "view_user", "description": "查看用户信息"},
        {"id": 2, "name": "用户创建", "code": "add_user", "description": "创建新用户"},
        {"id": 3, "name": "用户编辑", "code": "change_user", "description": "编辑用户信息"},
        {"id": 4, "name": "用户删除", "code": "delete_user", "description": "删除用户"},
        {"id": 5, "name": "用户导入导出", "code": "import_export_user", "description": "导入导出用户数据"}
      ]
    }
    ```

- **POST /permissions/** - 创建新权限
  - **需要认证**：Token认证
  - **请求体**：`{"name": "新权限", "code": "new_permission", "description": "权限描述", "module": "用户管理"}`
  - **响应**：创建成功的权限详情

- **GET /permissions/{id}/** - 获取指定权限详情
  - **需要认证**：Token认证
  - **响应**：权限详情

- **PUT /permissions/{id}/** - 更新指定权限
  - **需要认证**：Token认证
  - **请求体**：`{"name": "更新后的权限名", "description": "更新后的描述"}`
  - **响应**：更新后的权限详情

- **DELETE /permissions/{id}/** - 删除指定权限
  - **需要认证**：Token认证
  - **响应**：204 No Content (成功) 或 400 (有关联角色时失败)

- **GET /permissions/tree/** - 获取完整的权限树（包含菜单和按钮）
  - **需要认证**：Token认证
  - **响应**：权限树结构，包含菜单和按钮权限
    ```json
    [
      {
        "id": 123,
        "name": "首页",
        "web_path": "/dashboard",
        "component": "dashboard/index",
        "icon": "home",
        "visible": true,
        "sort": 1,
        "children": [],
        "buttons": [
          {
            "id": 9,
            "name": "View",
            "value": "view",
            "api": "/api/dashboard/data",
            "method": 0,
            "method_display": "GET",
            "sort": 1
          }
        ]
      },
      {
        "id": 124,
        "name": "权限管理",
        "web_path": "/permission",
        "component": "permission/index",
        "icon": "lock",
        "visible": true,
        "sort": 2,
        "children": [],
        "buttons": [
          {
            "id": 10,
            "name": "Add",
            "value": "add",
            "api": "/api/permissions",
            "method": 1,
            "method_display": "POST",
            "sort": 2
          },
          {
            "id": 11,
            "name": "Edit",
            "value": "edit",
            "api": "/api/permissions/{id}",
            "method": 2,
            "method_display": "PUT",
            "sort": 3
          },
          {
            "id": 12,
            "name": "Delete",
            "value": "delete",
            "api": "/api/permissions/{id}",
            "method": 3,
            "method_display": "DELETE",
            "sort": 4
          }
        ]
      }
    ]
    ```

### 用户管理

- **GET /users/** - 获取用户列表
  - **需要认证**：Token认证
  - **查询参数**：可选 `department_id`, `status`, `username`, `employee_no`, `page`, `page_size`
  - **响应**：分页的用户列表
    ```json
    {
      "count": 10,
      "next": "http://your-domain.com/api/v1/users/?page=2",
      "previous": null,
      "results": [
        {
          "id": 1,
          "username": "admin",
          "name": "管理员",
          "email": "admin@example.com",
          "department": {"id": 1, "name": "技术部"},
          "roles": [{"id": 1, "name": "超级管理员"}],
          "status": true,
          "employee_no": "EMP001",
          "mobile": "13800138000"
        },
        ...
      ]
    }
    ```

- **POST /users/** - 创建新用户
  - **需要认证**：Token认证
  - **请求体**：`{"username": "newuser", "password": "password123", "name": "新用户", "email": "newuser@example.com", "department_id": 1, "status": true, "role_ids": [1, 2], "employee_no": "EMP002"}`
  - **响应**：创建成功的用户详情

- **GET /users/{id}/** - 获取指定用户详情
  - **需要认证**：Token认证
  - **响应**：用户详细信息

- **PUT /users/{id}/** - 更新指定用户
  - **需要认证**：Token认证
  - **请求体**：`{"name": "更新后的用户名", "email": "updated@example.com", "department_id": 2, "status": true, "role_ids": [1]}`
  - **响应**：更新后的用户详情

- **DELETE /users/{id}/** - 删除指定用户
  - **需要认证**：Token认证
  - **响应**：204 No Content

- **GET /users/me/** - 获取当前登录用户信息
  - **需要认证**：Token认证
  - **响应**：当前用户的详细信息

- **POST /users/{id}/reset_password/** - 重置用户密码
  - **需要认证**：Token认证
  - **请求体**：`{"new_password": "newpassword123"}`
  - **响应**：`{"success": true, "message": "密码重置成功"}`

- **GET /users/export/** - 导出用户数据
  - **需要认证**：Token认证
  - **响应**：下载Excel格式的用户数据文件

- **POST /users/import/** - 导入用户数据
  - **需要认证**：Token认证
  - **请求格式**：multipart/form-data
  - **请求参数**：file (Excel文件)
  - **响应**：`{"success": true, "imported_count": 5, "failed_count": 0}`

- **DELETE /users/batch_delete/** - 批量删除用户
  - **需要认证**：Token认证
  - **请求体**：`{"ids": [1, 2, 3]}`
  - **响应**：`{"success": true, "deleted_count": 3}`

### 操作日志

- **GET /operation_logs/** - 获取操作日志列表
  - **需要认证**：Token认证
  - **查询参数**：可选 `user_id`, `action`, `model_name`, `start_date`, `end_date`, `operation_type`, `page`, `page_size`
  - **响应**：分页的操作日志列表
    ```json
    {
      "count": 100,
      "next": "http://your-domain.com/api/v1/operation_logs/?page=2",
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {"id": 1, "username": "admin", "name": "管理员"},
          "action": "登录系统",
          "model_name": "User",
          "model_id": 1,
          "details": "用户admin成功登录系统",
          "ip_address": "127.0.0.1",
          "created_at": "2024-11-06T10:30:00Z"
        },
        {
          "id": 2,
          "user": {"id": 1, "username": "admin", "name": "管理员"},
          "action": "创建用户",
          "model_name": "User",
          "model_id": 2,
          "details": "创建用户newuser",
          "ip_address": "127.0.0.1",
          "created_at": "2024-11-06T10:35:00Z"
        },
        ...
      ]
    }
    ```

- **GET /operation_logs/{id}/** - 获取指定操作日志详情
  - **需要认证**：Token认证
  - **响应**：操作日志详细信息

### 消息管理

- **POST /messages/** - 发送消息
  - **需要认证**：Token认证
  - **请求体**：`{"title": "系统通知", "content": "这是一条测试通知", "recipient_ids": [1, 2, 3], "is_broadcast": false, "message_type": "通知", "priority": "普通"}`
  - **参数说明**：`title`(消息标题), `content`(消息内容), `recipient_ids`(接收者ID列表), `is_broadcast`(是否广播消息), `message_type`(消息类型), `priority`(优先级)
  - **响应**：`{"success": true, "message_id": 1, "sent_count": 3}`

- **GET /user_messages/** - 查询用户消息
  - **需要认证**：Token认证
  - **查询参数**：可选 `is_read`(按消息是否已读过滤), `message_title`(按消息标题模糊搜索), `page`, `page_size`
  - **响应**：分页的用户消息列表
    ```json
    {
      "count": 20,
      "next": "http://your-domain.com/api/v1/user_messages/?page=2",
      "previous": null,
      "results": [
        {
          "id": 1,
          "message": {
            "id": 1,
            "title": "系统通知",
            "content": "这是一条测试通知",
            "message_type": "通知",
            "priority": "普通",
            "sender": {"id": 1, "username": "admin"}
          },
          "is_read": false,
          "created_at": "2024-11-06T11:00:00Z"
        },
        ...
      ]
    }
    ```

- **POST /user_messages/{id}/mark_as_read/** - 标记消息为已读
  - **需要认证**：Token认证
  - **响应**：`{"success": true, "message": "消息已标记为已读"}`

- **POST /user_messages/mark_all_as_read/** - 标记所有消息为已读
  - **需要认证**：Token认证
  - **响应**：`{"success": true, "message": "所有消息已标记为已读", "count": 5}`

- **DELETE /user_messages/{id}/** - 删除用户消息
  - **需要认证**：Token认证
  - **响应**：204 No Content

## 权限控制

除了认证相关的API外，其他所有API都需要认证后才能访问。系统使用RBAC（基于角色的访问控制）模型实现细粒度的权限控制。

### 权限继承关系

系统支持权限的继承关系，例如：
- 超级管理员角色拥有所有权限
- 拥有编辑权限通常意味着同时拥有查看权限

### 权限检查流程

1. 用户登录获取Token
2. 发起API请求时在Header中携带Token
3. 系统验证Token有效性
4. 系统检查用户角色是否拥有对应API的访问权限
5. 根据权限检查结果决定是否允许访问

### 自定义权限实现

开发者可以通过继承`rest_framework.permissions.BasePermission`类来实现自定义权限控制逻辑：

```python
from rest_framework import permissions

class CustomObjectPermission(permissions.BasePermission):
    """自定义对象级权限控制"""
    
    def has_permission(self, request, view):
        # 视图级权限检查
        return request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        # 对象级权限检查
        # 例如，只允许用户修改自己的信息
        if view.action in ['update', 'partial_update', 'destroy']:
            return obj.id == request.user.id
        return True
```

## 数据模型

### Department（部门）
- **id**: 部门ID (主键)
- **name**: 部门名称 (唯一, 必填)
- **description**: 部门描述
- **parent**: 上级部门（自关联, 可为空）
- **status**: 状态 (布尔值, 默认为True)
- **created_at**: 创建时间 (自动生成)
- **updated_at**: 更新时间 (自动更新)
- **created_by**: 创建人
- **updated_by**: 更新人

### Role（角色）
- **id**: 角色ID (主键)
- **name**: 角色名称 (唯一, 必填)
- **description**: 角色描述
- **permissions**: 拥有的权限（多对多关系）
- **status**: 状态 (布尔值, 默认为True)
- **created_at**: 创建时间 (自动生成)
- **updated_at**: 更新时间 (自动更新)
- **created_by**: 创建人
- **updated_by**: 更新人

### Permission（权限）
- **id**: 权限ID (主键)
- **name**: 权限名称 (唯一, 必填)
- **code**: 权限代码 (唯一, 必填)
- **description**: 权限描述
- **module**: 所属模块
- **created_at**: 创建时间 (自动生成)
- **updated_at**: 更新时间 (自动更新)

### User（用户）
- **id**: 用户ID (主键)
- **username**: 用户名 (唯一, 必填)
- **password**: 密码 (加密存储)
- **email**: 邮箱 (唯一, 必填)
- **is_active**: 是否激活 (布尔值, 默认为True)
- **is_staff**: 是否为工作人员 (布尔值)
- **is_superuser**: 是否为超级用户 (布尔值)
- **last_login**: 最后登录时间
- **date_joined**: 注册时间

### UserProfile（用户扩展信息）
- **id**: 用户扩展ID (主键)
- **user**: 关联的Django用户（一对一关系, 必填）
- **department**: 所属部门 (外键)
- **roles**: 所属角色（多对多关系）
- **mobile**: 手机号码
- **avatar**: 头像 (文件路径)
- **name**: 姓名 (必填)
- **employee_no**: 工号 (唯一)
- **gender**: 性别 (0:女, 1:男)
- **user_type**: 用户类型（0:后台用户, 1:前台用户, 默认为0）
- **status**: 状态 (布尔值, 默认为True)
- **created_at**: 创建时间 (自动生成)
- **updated_at**: 更新时间 (自动更新)

### OperationLog（操作日志）
- **id**: 日志ID (主键)
- **user**: 操作用户 (外键, 可为空)
- **action**: 操作类型 (CREATE, UPDATE, DELETE, LOGIN, LOGOUT等)
- **model_name**: 操作的模型名称
- **model_id**: 操作的模型ID
- **details**: 操作详情 (JSON格式)
- **ip_address**: IP地址
- **user_agent**: 用户代理
- **created_at**: 创建时间 (自动生成)

### Message（消息）
- **id**: 消息ID (主键)
- **title**: 消息标题 (必填)
- **content**: 消息内容 (必填)
- **sender**: 发送者 (外键, 可为空表示系统消息)
- **message_type**: 消息类型 (通知, 提醒, 公告等)
- **priority**: 优先级 (普通, 重要, 紧急)
- **created_at**: 创建时间 (自动生成)

### UserMessage（用户消息关联）
- **id**: 关联ID (主键)
- **user**: 接收用户 (外键, 必填)
- **message**: 消息内容 (外键, 必填)
- **is_read**: 是否已读 (布尔值, 默认为False)
- **read_at**: 阅读时间
- **created_at**: 创建时间 (自动生成)

### APIWhitelist（API白名单）
- **id**: ID (主键)
- **path**: API路径 (必填)
- **method**: 请求方法 (GET, POST等)
- **description**: 描述
- **created_at**: 创建时间 (自动生成)
- **updated_at**: 更新时间 (自动更新)