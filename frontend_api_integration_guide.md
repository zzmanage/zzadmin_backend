# 前后端API响应格式统一接入指南

## 后端API响应格式变更

所有API响应现已统一为以下格式：

```json
{
  "code": 200,          // HTTP状态码或业务码
  "message": "操作成功", // 响应消息
  "data": {}            // 业务数据
}
```

## 前端接入方案

### 1. 创建或更新axios配置文件

创建或更新前端项目中的 axios 配置文件，添加统一的响应拦截器处理新格式：

```javascript
// src/utils/request.js 或类似文件
import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  timeout: 10000,
  withCredentials: true,
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

// 响应拦截器 - 统一处理后端响应格式
api.interceptors.response.use(
  response => {
    const res = response.data;
    
    // 检查是否是统一格式响应
    if (res && typeof res === 'object' && 'code' in res && 'message' in res && 'data' in res) {
      // 成功响应：直接返回data部分给调用者
      if (res.code >= 200 && res.code < 300) {
        return res.data;
      } else {
        // 错误响应：抛出错误供调用者处理
        const error = new Error(res.message || '请求失败');
        error.code = res.code;
        error.data = res.data;
        return Promise.reject(error);
      }
    }
    
    // 兼容处理：如果不是统一格式，直接返回响应数据
    // 这种情况在后端完全统一后将不会出现
    console.warn('API响应格式不统一，返回原始数据', res);
    return res;
  },
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
        return api(originalRequest);
      } catch (err) {
        // 刷新失败，跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(new Error('登录已过期，请重新登录'));
      }
    }
    
    // 处理其他错误
    let errorMessage = '请求失败';
    let errorCode = 500;
    
    // 尝试从响应中提取统一格式的错误信息
    if (error.response?.data) {
      const res = error.response.data;
      if (res && typeof res === 'object' && 'code' in res && 'message' in res) {
        errorMessage = res.message;
        errorCode = res.code;
      } else if (res?.error) {
        errorMessage = res.error;
      } else if (res?.detail) {
        errorMessage = res.detail;
      }
    }
    
    const apiError = new Error(errorMessage);
    apiError.code = errorCode;
    apiError.response = error.response;
    
    return Promise.reject(apiError);
  }
);

export default api;
```

### 2. API调用方式更新

更新前端API调用方式，适配统一的响应格式：

```javascript
// 导入配置好的axios实例
import api from '@/utils/request';

// 示例：登录接口调用
export const login = async (username, password, captcha, captchaKey) => {
  try {
    // 直接获取data部分，无需再手动解构
    const data = await api.post('/auth/login/', {
      username,
      password,
      captcha,
      captcha_key: captchaKey
    });
    
    // data 直接包含access_token, user_info等，无需 data.data 这样的访问方式
    return data;
  } catch (error) {
    // 错误处理
    console.error('登录失败:', error);
    throw error;
  }
};

// 示例：获取部门树数据
export const getDepartmentTree = async () => {
  try {
    const data = await api.get('/departments/tree/');
    return data; // 直接是部门树数据
  } catch (error) {
    console.error('获取部门树失败:', error);
    throw error;
  }
};
```

### 3. 全局错误处理

在前端应用中添加全局错误处理，统一展示错误信息：

```javascript
// src/utils/errorHandler.js
import { Message } from 'element-ui'; // 假设使用Element UI

export const handleApiError = (error) => {
  // 根据错误码进行不同处理
  const errorCode = error.code || error.response?.status || 500;
  const errorMessage = error.message || '操作失败，请稍后重试';
  
  // 记录错误日志
  console.error(`API错误 [${errorCode}]:`, errorMessage, error);
  
  // 显示错误消息
  Message.error(errorMessage);
  
  // 特殊错误码处理
  switch (errorCode) {
    case 401:
      // 未授权，可以在这里添加跳转到登录页的逻辑
      break;
    case 403:
      // 无权限
      Message.error('您没有权限执行此操作');
      break;
    case 404:
      // 资源不存在
      Message.error('请求的资源不存在');
      break;
    case 500:
      // 服务器错误
      if (process.env.NODE_ENV === 'production') {
        Message.error('服务器内部错误，请联系管理员');
      } else {
        Message.error(errorMessage);
      }
      break;
    default:
      // 其他错误
      Message.error(errorMessage);
  }
  
  return Promise.reject(error);
};

// 在main.js中注册全局错误处理
// Vue.prototype.$handleApiError = handleApiError;
```

### 4. 组件中使用示例

```javascript
// 组件中使用
import { login } from '@/api/auth';
import { handleApiError } from '@/utils/errorHandler';

export default {
  methods: {
    async onLogin() {
      try {
        const result = await login(this.username, this.password, this.captcha, this.captchaKey);
        // 直接使用result，无需再访问result.data
        this.$store.commit('SET_USER_INFO', result.user_info);
        localStorage.setItem('access_token', result.access);
        this.$router.push('/dashboard');
        this.$message.success('登录成功');
      } catch (error) {
        this.$handleApiError(error);
      }
    }
  }
};
```

## 迁移步骤

1. **更新后端API响应格式**：
   - 已在后端实现统一响应格式
   - 已修复所有视图的响应处理
   - 已增强APIResponseMiddleware确保格式统一

2. **更新前端axios配置**：
   - 创建或修改axios实例配置文件
   - 添加响应拦截器处理统一格式
   - 配置请求拦截器添加认证信息

3. **更新API调用代码**：
   - 修改所有API调用，适配新的响应格式
   - 直接使用响应的data部分，无需再解构

4. **添加全局错误处理**：
   - 实现统一的错误处理工具函数
   - 在应用中统一使用错误处理函数

5. **测试**：
   - 测试所有API接口响应是否符合统一格式
   - 测试前端处理是否正确
   - 验证错误情况的处理

## 注意事项

1. 确保后端所有API都已更新为统一格式
2. 前端迁移时需要批量修改所有API调用
3. 对于特殊情况，可以在响应拦截器中添加兼容逻辑
4. 迁移过程中保持前后端版本同步，避免格式不匹配
5. 推荐先在开发环境完成测试，再部署到生产环境