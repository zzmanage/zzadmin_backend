# 前端项目与后端API联调指南

## 后端API基本信息

本指南将帮助您的前端项目与Backend Management System的后端API进行联调。

### 后端技术栈
- Django 5.2.5
- Django REST Framework 3.16.1
- JWT认证
- CORS支持

### 开发环境配置

1. **确保后端服务正在运行**
   ```bash
   cd d:\codes\backend_management_system
   venv\Scripts\activate
   python manage.py runserver
   ```

2. **默认访问地址**
   - API Base URL: `http://127.0.0.1:8000/api/`
   - API文档: `http://127.0.0.1:8000/swagger/` 或 `http://127.0.0.1:8000/redoc/`

## 认证方式

后端API支持三种认证方式：

1. **JWT认证** (推荐)
2. **Token认证**
3. **Session认证**

### JWT认证流程

1. **获取Token**
   ```
   POST /api/token/
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

2. **刷新Token**
   ```
   POST /api/token/refresh/
   {
     "refresh": "your_refresh_token"
   }
   ```

3. **验证Token**
   ```
   POST /api/token/verify/
   {
     "token": "your_access_token"
   }
   ```

4. **在请求头中使用Token**
   ```
   Authorization: Bearer your_access_token
   ```

## CORS配置

后端已经配置了CORS支持，允许所有来源的请求：

```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```

在生产环境中，建议修改为特定的允许来源：

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # 前端开发服务器地址
    "http://example.com",     # 生产环境前端地址
]
```

## 主要API端点

### 认证相关
- `POST /auth/login/` - 用户登录（支持验证码）
- `POST /auth/logout/` - 用户登出
- `GET /auth/check/` - 检查认证状态
- `GET /captcha/` - 获取验证码
- `POST /api/token/` - JWT Token获取
- `POST /api/token/refresh/` - JWT Token刷新
- `POST /api/token/verify/` - JWT Token验证

### 资源管理
- **部门管理**: `/api/departments/`
- **角色管理**: `/api/roles/`
- **权限管理**: `/api/permissions/`
- **用户管理**: `/api/users/`
- **岗位管理**: `/api/posts/`
- **菜单管理**: `/api/menus/`
- **字典管理**: `/api/dictionaries/`
- **API白名单**: `/api/api_whitelists/`
- **操作日志**: `/api/operation_logs/`
- **登录日志**: `/api/login_logs/`

### 权限树API（重要）
- **获取完整权限树**: `GET /api/permissions/tree/`
  - 获取系统中所有菜单和按钮的权限树结构
- **获取角色权限树**: `GET /api/roles/{id}/permissions_tree/`
  - 获取指定角色已拥有的菜单和按钮权限树结构，包含权限选中状态标记

## 前端项目配置

### Axios配置示例

```javascript
import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  timeout: 10000,
  withCredentials: true, // 允许携带cookie
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理token过期
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // 处理401错误（未授权）
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // 尝试刷新token
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('http://127.0.0.1:8000/api/token/refresh/', {
          refresh: refreshToken
        });
        
        // 保存新的token
        const { access } = response.data;
        localStorage.setItem('access_token', access);
        
        // 重发原始请求
        originalRequest.headers['Authorization'] = `Bearer ${access}`;
        return axios(originalRequest);
      } catch (err) {
        // 刷新失败，跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

### 登录功能实现示例

```javascript
import api from './api';

// 1. 获取验证码
export const getCaptcha = async () => {
  try {
    const response = await api.get('/captcha/');
    return response.data;
  } catch (error) {
    console.error('获取验证码失败:', error);
    throw error;
  }
};

// 2. 用户登录
export const login = async (username, password, captcha, captchaId) => {
  try {
    const response = await api.post('/auth/login/', {
      username,
      password,
      captcha,
      captcha_id: captchaId
    });
    
    // 保存token
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    
    return response.data;
  } catch (error) {
    console.error('登录失败:', error);
    throw error;
  }
};

// 3. 登出
export const logout = async () => {
  try {
    await api.post('/auth/logout/');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  } catch (error) {
    console.error('登出失败:', error);
    throw error;
  }
};

// 4. 检查认证状态
export const checkAuth = async () => {
  try {
    const response = await api.get('/auth/check/');
    return response.data;
  } catch (error) {
    console.error('检查认证状态失败:', error);
    throw error;
  }
};
```

## 调试工具

推荐使用以下工具进行API调试：

1. **Swagger UI** - 访问 `http://127.0.0.1:8000/swagger/`
2. **Redoc** - 访问 `http://127.0.0.1:8000/redoc/`
3. **Postman** - 可以导入Swagger文档进行API测试
4. **VS Code REST Client** - 在VS Code中直接测试API

## 常见问题与解决方案

### 1. CORS跨域问题

**问题描述**: 前端请求后端API时出现CORS错误

**解决方案**: 
- 确认后端已安装并配置了django-cors-headers
- 检查settings.py中的CORS配置是否正确
- 开发环境下可以设置`CORS_ALLOW_ALL_ORIGINS = True`

### 2. 认证失败

**问题描述**: 前端请求返回401未授权错误

**解决方案**: 
- 确认Token是否正确获取并在请求头中正确设置
- 检查Token是否过期，实现自动刷新机制
- 验证用户权限是否足够访问请求的资源

### 3. 请求超时

**问题描述**: 前端请求后端API时出现超时错误

**解决方案**: 
- 确认后端服务是否正在运行
- 检查网络连接是否正常
- 增加axios的timeout配置值
- 检查后端API是否存在性能问题

### 4. 验证码错误

**问题描述**: 验证码验证失败

**解决方案**: 
- 确保前端正确传递验证码和验证码ID
- 检查前后端字符编码是否一致
- 确认验证码是否过期（通常有效期较短）

## 部署环境配置

在生产环境中，需要进行以下配置：

1. **修改settings.py**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   CORS_ALLOWED_ORIGINS = ['https://your-frontend-domain.com']
   ```

2. **配置HTTPS**
   - 在生产环境中，建议使用HTTPS协议
   - 可以通过Nginx等反向代理配置SSL证书

3. **设置更安全的JWT配置**
   ```python
   SIMPLE_JWT = {
     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # 生产环境可以设置更短的有效期
     'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
     # 其他配置...
   }
   ```

4. **前端API地址配置**
   - 在前端项目中，将API基础地址配置为生产环境的后端地址
   - 建议使用环境变量管理不同环境的配置

## 其他资源

- [Django REST Framework官方文档](https://www.django-rest-framework.org/)
- [django-cors-headers文档](https://pypi.org/project/django-cors-headers/)
- [djangorestframework-simplejwt文档](https://django-rest-framework-simplejwt.readthedocs.io/)
- [drf-yasg文档](https://drf-yasg.readthedocs.io/)