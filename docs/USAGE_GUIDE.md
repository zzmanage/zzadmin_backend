# 后端管理系统使用指南

## 1. 系统概述

后端管理系统是一个基于Django和Django REST Framework开发的企业级后台管理API服务。该系统提供完整的用户权限管理、部门管理、角色管理、操作日志记录、消息管理等核心功能，为企业应用提供坚实的后端支持。系统支持前后端分离架构，可与各种前端框架无缝集成。

## 2. 系统架构

系统采用前后端分离架构，主要包含以下核心组件：

- **用户管理模块**：负责用户的创建、编辑、删除和权限管理
- **部门管理模块**：组织结构管理，支持多层级部门结构
- **角色管理模块**：基于RBAC模型的权限控制
- **权限管理模块**：细粒度的功能权限控制
- **操作日志模块**：记录用户的关键操作
- **消息管理模块**：提供系统消息的发送和接收功能
- **任务管理模块**：处理系统中的异步任务和定时任务
- **菜单管理模块**：配置和管理系统菜单和按钮权限
- **API白名单模块**：管理无需认证的API端点
- **数据字典模块**：管理系统中的基础数据配置
- **WebSocket服务**：提供实时通信功能

## 3. 快速入门

### 3.1 登录系统

系统当前版本支持Token认证方式。

```bash
# 登录API请求示例
POST /api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

登录成功后，系统会返回Token，用于后续API请求的身份验证：

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "email": "admin@example.com",
    "department": null,
    "roles": ["超级管理员"]
  }
}
```

### 3.2 基本请求格式

所有API请求都需要在请求头中包含认证信息：

```bash
Authorization: Token your-token
Content-Type: application/json
```

### 3.3 查看个人信息

```bash
GET /api/users/me/
```

### 3.4 登出系统

```bash
POST /api/auth/logout/
```

## 4. 核心功能使用指南

### 4.1 用户管理

#### 4.1.1 查询用户列表

```bash
GET /api/users/
# 可选过滤参数
get /api/users/?department_id=1&status=true&username=admin&page=1&page_size=10
```

参数说明：
- `department_id`：按部门ID过滤
- `status`：按用户状态过滤（true/false）
- `username`：按用户名模糊搜索
- `page`：分页页码（默认1）
- `page_size`：每页记录数（默认10）

响应示例：
```json
{
  "count": 20,
  "next": "http://your-domain.com/api/users/?page=2&page_size=10",
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
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-02T00:00:00Z"
    },
    ...
  ]
}
```

#### 4.1.2 创建新用户

```bash
POST /api/users/
Content-Type: application/json

{
  "username": "newuser",
  "password": "password123",
  "name": "新用户",
  "email": "newuser@example.com",
  "department_id": 1,
  "status": true,
  "role_ids": [1, 2]
}
```

#### 4.1.3 更新用户信息

```bash
PUT /api/users/1/
Content-Type: application/json

{
  "name": "更新后的用户名",
  "email": "updated@example.com",
  "department_id": 2,
  "status": true,
  "role_ids": [1]
}
```

#### 4.1.4 重置用户密码

```bash
POST /api/users/1/reset_password/
Content-Type: application/json

{
  "new_password": "newpassword123"
}
```

#### 4.1.5 获取用户详情

```bash
GET /api/users/1/
```

### 4.2 部门管理

#### 4.2.1 查询部门列表

```bash
GET /api/departments/
# 可选参数
get /api/departments/?name=技术&parent_id=1
```

响应示例：
```json
[
  {
    "id": 1,
    "name": "技术部",
    "parent": null,
    "description": "负责系统开发和维护",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "children": [
      {
        "id": 2,
        "name": "前端组",
        "parent": 1,
        "description": "负责前端开发",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "children": []
      }
    ]
  }
]
```

#### 4.2.2 创建新部门

```bash
POST /api/departments/
Content-Type: application/json

{
  "name": "新部门",
  "parent_id": 1,  # 父部门ID，可为null
  "description": "部门描述"
}
```

#### 4.2.3 更新部门信息

```bash
PUT /api/departments/1/
Content-Type: application/json

{
  "name": "更新后的部门名称",
  "parent_id": 2,  # 父部门ID，可为null
  "description": "更新后的描述"
}
```

### 4.3 角色管理

#### 4.3.1 查询角色列表

```bash
GET /api/roles/
# 可选参数
get /api/roles/?name=管理员&page=1&page_size=10
```

响应示例：
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "超级管理员",
      "description": "系统最高权限角色",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z",
      "permissions": [
        {"id": 1, "name": "查看用户", "codename": "view_user"},
        {"id": 2, "name": "创建用户", "codename": "add_user"}
      ]
    },
    ...
  ]
}
```

#### 4.3.2 创建新角色

```bash
POST /api/roles/
Content-Type: application/json

{
  "name": "新角色",
  "description": "角色描述",
  "permission_ids": [1, 2, 3]
}
```

#### 4.3.3 更新角色信息

```bash
PUT /api/roles/1/
Content-Type: application/json

{
  "name": "更新后的角色名称",
  "description": "更新后的描述",
  "permission_ids": [1, 2]
}
```

#### 4.3.4 删除角色

```bash
DELETE /api/roles/1/
```

#### 4.3.5 获取角色详情

```bash
GET /api/roles/1/
```

### 4.4 权限管理

#### 4.4.1 查询权限列表

```bash
GET /api/permissions/
# 可选参数
get /api/permissions/?name=用户&content_type=1&page=1&page_size=10
```

响应示例：
```json
{
  "count": 50,
  "next": "http://your-domain.com/api/permissions/?page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "查看用户",
      "codename": "view_user",
      "content_type": {"id": 1, "name": "用户"},
      "created_at": "2023-01-01T00:00:00Z"
    },
    ...
  ]
}
```

#### 4.4.2 获取权限树

```bash
GET /api/permissions/tree/
```

这个API返回系统所有权限的树形结构，方便前端展示权限选择组件。

响应示例：
```json
[
  {
    "id": 1,
    "name": "用户管理",
    "children": [
      {
        "id": 2,
        "name": "查看用户",
        "codename": "view_user"
      },
      {
        "id": 3,
        "name": "创建用户",
        "codename": "add_user"
      }
    ]
  },
  ...
]
```

### 4.5 操作日志查询

#### 4.5.1 查询操作日志列表

```bash
GET /api/operation_logs/
# 可选过滤参数
get /api/operation_logs/?username=admin&operation_type=login&start_time=2023-01-01&end_time=2023-01-31&page=1&page_size=10
```

参数说明：
- `username`：操作用户名
- `operation_type`：操作类型
- `start_time`：开始时间（格式：YYYY-MM-DD）
- `end_time`：结束时间（格式：YYYY-MM-DD）
- `page`：分页页码（默认1）
- `page_size`：每页记录数（默认10）

响应示例：
```json
{
  "count": 150,
  "next": "http://your-domain.com/api/operation_logs/?page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "admin",
      "operation_type": "login",
      "operation_desc": "用户登录",
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "status": true,
      "error_message": null,
      "created_at": "2023-01-01T10:30:00Z"
    },
    ...
  ]
}
```

### 4.6 消息管理

#### 4.6.1 发送消息

```bash
POST /api/messages/send/
Content-Type: application/json

{
  "title": "消息标题",
  "content": "消息内容",
  "recipient_ids": [1, 2, 3],  # 接收用户ID列表
  "is_urgent": false
}
```

响应示例：
```json
{
  "id": 1,
  "title": "消息标题",
  "content": "消息内容",
  "sender": {"id": 1, "name": "管理员"},
  "is_urgent": false,
  "sent_at": "2023-01-01T12:00:00Z"
}
```

#### 4.6.2 查询用户消息

```bash
GET /api/messages/
# 可选参数
get /api/messages/?is_read=false&page=1&page_size=10
```

参数说明：
- `is_read`: 是否已读（true/false）
- `page`: 页码
- `page_size`: 每页数量

响应示例：
```json
{
  "count": 20,
  "next": "http://your-domain.com/api/messages/?page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "消息标题",
      "content": "消息内容",
      "sender": {"id": 1, "name": "管理员"},
      "is_urgent": false,
      "is_read": false,
      "sent_at": "2023-01-01T12:00:00Z"
    },
    ...
  ]
}
```

#### 4.6.3 标记消息为已读

```bash
POST /api/messages/1/read/
```

#### 4.6.4 批量标记消息为已读

```bash
POST /api/messages/batch_read/
Content-Type: application/json

{
  "message_ids": [1, 2, 3]
}
```

## 5. 高级功能

### 5.1 批量操作

系统支持对用户、部门、角色等资源进行批量操作。

#### 5.1.1 批量删除

```bash
DELETE /api/users/batch_delete/
Content-Type: application/json

{
  "ids": [1, 2, 3]
}
```

#### 5.1.2 批量启用/禁用

```bash
POST /api/users/batch_enable/
Content-Type: application/json

{
  "ids": [1, 2, 3],
  "status": true  # true为启用，false为禁用
}
```

### 5.2 数据导入导出

系统支持用户数据的导入导出。

#### 5.2.1 导出用户数据

```bash
GET /api/users/export/
# 可选参数
get /api/users/export/?department_id=1
```

该API返回Excel格式的用户数据文件。

#### 5.2.2 导入用户数据

```bash
POST /api/users/import/
Content-Type: multipart/form-data

# 表单参数
file: <Excel文件>
```

响应示例：
```json
{
  "success_count": 10,
  "fail_count": 2,
  "fail_messages": [
    "第3行：用户名已存在",
    "第8行：邮箱格式不正确"
  ]
}```

## 6. 常见问题与解决方案

### 6.1 认证失败

如果收到认证失败的错误，请检查：

1. Token是否过期 - 可以通过重新登录获取新Token
2. Token格式是否正确 - 确保请求头中包含正确的Token格式 `Token your-token`
3. 是否在请求头中正确设置了Authorization
4. 用户账号是否被禁用

### 6.2 数据验证失败

如果收到数据验证失败的错误，请检查：

1. 请求参数是否符合要求
2. 必填字段是否都已填写
3. 字段格式是否正确（如邮箱、手机号等）
4. 数据长度是否符合限制

### 6.3 数据库约束错误

如果收到数据库约束错误，请检查：

1. 外键关联是否存在
2. 唯一约束是否被违反
3. 数据类型是否匹配
4. 数据完整性约束是否被破坏

### 6.4 权限不足

如果收到权限不足的错误，请检查：

1. 当前用户是否拥有执行该操作的权限
2. 角色权限配置是否正确

## 7. 工作流管理

### 7.1 概述

系统提供完整的工作流引擎，支持：
- 可视化流程设计（BPMN 2.0 标准）
- 多种任务分配策略（指定用户、角色、表达式、关系）
- 会签支持（并行/串行）
- 条件网关（排他、并行、包容）
- 任务自动分配和通知

### 7.2 核心概念

| 概念 | 说明 |
|------|------|
| **工作流定义** | 流程模板，定义流程的结构和规则 |
| **流程实例** | 工作流定义的具体执行实例 |
| **任务** | 流程中需要人工处理的工作单元 |
| **审批人配置** | 任务的分配规则 |
| **网关** | 控制流程流转路径 |

### 7.3 工作流定义API

#### 7.3.1 查询工作流列表

```bash
GET /api/workflows/
```

响应示例：
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "请假审批流程",
      "key": "leave_approval",
      "description": "员工请假审批流程",
      "version": 1,
      "status": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 7.3.2 创建工作流定义

```bash
POST /api/workflows/
Content-Type: application/json

{
  "name": "请假审批流程",
  "key": "leave_approval",
  "description": "员工请假审批流程",
  "definition_value": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>...",
  "nodes": [
    {
      "key": "start",
      "name": "开始",
      "type": "startEvent"
    },
    {
      "key": "approve",
      "name": "审批",
      "type": "userTask",
      "assigneeType": "role",
      "candidateRoles": ["2"]
    }
  ]
}
```

#### 7.3.3 获取工作流详情

```bash
GET /api/workflows/1/
```

#### 7.3.4 更新工作流

```bash
PUT /api/workflows/1/
```

#### 7.3.5 删除工作流

```bash
DELETE /api/workflows/1/
```

#### 7.3.6 部署工作流

```bash
POST /api/workflows/1/deploy/
```

### 7.4 流程实例API

#### 7.4.1 查询流程实例列表

```bash
GET /api/workflow_instances/
# 可选参数
get /api/workflow_instances/?status=0&definition_id=1
```

参数说明：
- `status`: 实例状态（0=运行中, 1=已完成, 2=已取消）
- `definition_id`: 按工作流定义过滤
- `initiator`: 按发起人过滤

响应示例：
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "definition": {
        "id": 1,
        "name": "请假审批流程"
      },
      "status": 0,
      "status_display": "运行中",
      "initiator": {"id": 1, "name": "张三"},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 7.4.2 启动流程实例

```bash
POST /api/workflow_instances/
Content-Type: application/json

{
  "definition_id": 1,
  "variables": {
    "leave_type": "年假",
    "days": 3
  }
}
```

#### 7.4.3 获取实例详情

```bash
GET /api/workflow_instances/1/
```

#### 7.4.4 取消流程实例

```bash
POST /api/workflow_instances/1/cancel/
```

### 7.5 任务API

#### 7.5.1 查询任务列表

```bash
GET /api/workflow_tasks/
# 可选参数
get /api/workflow_tasks/?status=0&assignee_id=1
```

参数说明：
- `status`: 任务状态（0=待处理, 1=处理中, 2=已完成, 3=已拒绝）
- `assignee_id`: 按审批人过滤
- `instance_id`: 按流程实例过滤

响应示例：
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "task_name": "部门主管审批",
      "task_def_key": "manager_approve",
      "instance": {
        "id": 1,
        "definition_name": "请假审批流程"
      },
      "assignee": {"id": 2, "name": "李四"},
      "status": 0,
      "status_display": "待处理",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 7.5.2 获取任务详情

```bash
GET /api/workflow_tasks/1/
```

#### 7.5.3 完成任务

```bash
POST /api/workflow_tasks/1/complete/
Content-Type: application/json

{
  "variables": {
    "approved": true,
    "comment": "同意"
  }
}
```

#### 7.5.4 拒绝任务

```bash
POST /api/workflow_tasks/1/reject/
Content-Type: application/json

{
  "comment": "材料不齐全，请补充"
}
```

#### 7.5.5 转交任务

```bash
POST /api/workflow_tasks/1/transfer/
Content-Type: application/json

{
  "user_id": 3
}
```

### 7.6 审批人配置说明

创建工作流时，可在节点配置中设置审批人：

```json
{
  "key": "manager_approve",
  "name": "部门主管审批",
  "type": "userTask",
  "assigneeType": "specific",
  "candidateUsers": ["1", "2"],
  "candidateRoles": [],
  "assignmentStrategy": "ANYONE"
}
```

| 字段 | 说明 |
|------|------|
| `assigneeType` | 分配方式：`specific`=指定用户, `role`=指定角色, `initiator`=发起人, `expression`=表达式, `relation`=关系 |
| `candidateUsers` | 候选用户ID列表 |
| `candidateRoles` | 候选角色ID列表 |
| `assignmentStrategy` | 分配策略：`ANYONE`=任意一人, `CONSENSUS`=全员, `ROUND_ROBIN`=轮询, `QUORUM`=按比例 |

### 7.7 获取用户和角色列表（用于配置）

```bash
# 获取用户列表
GET /api/users/

# 获取角色列表
GET /api/roles/
```

## 8. API版本控制

系统支持API版本控制，当前版本为v1。新版本的API将通过URL路径进行区分，例如：

```bash
GET /api/v2/users/
```

注意：版本升级可能导致API不兼容，请在升级前查看版本变更文档。

## 8. 性能优化建议

### 8.1 合理使用分页

对于大数据量的查询，建议使用分页功能，避免一次性加载过多数据。

```bash
# 推荐使用方式
get /api/users/?page=1&page_size=10
```

### 8.2 优化查询条件

在查询数据时，尽量使用索引字段作为过滤条件，提高查询效率。

### 8.3 减少不必要的嵌套查询

对于复杂查询，避免过多的嵌套关联查询，可以考虑使用预加载或延迟加载策略。

### 8.4 使用缓存

对于频繁访问且不经常变动的数据，可以使用缓存机制提高访问速度。

## 9. 安全注意事项

### 9.1 保护Token安全

不要在客户端明文存储Token，避免通过HTTP明文传输Token。建议使用HTTPS协议进行通信。

### 9.2 定期修改密码

建议用户定期修改密码，使用强密码策略（包含大小写字母、数字和特殊字符）。

### 9.3 限制敏感操作

对于敏感操作，建议添加二次验证机制，如短信验证码、邮箱验证等。

### 9.4 防止SQL注入

不要在前端拼接SQL语句，所有查询都应使用参数化查询或ORM框架提供的查询方式。

## 10. WebSocket服务

系统提供WebSocket服务，用于实时通信功能，如消息推送、通知等。

### 10.1 连接WebSocket

```javascript
// JavaScript示例
const socket = new WebSocket('ws://your-domain.com/ws/');

socket.onopen = function(e) {
  console.log('WebSocket连接已建立');
  // 发送认证信息
  socket.send(JSON.stringify({
    type: 'auth',
    token: 'your-token'
  }));
};

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};
```

## 11. 最后更新时间

本指南最后更新时间：2024-11-06