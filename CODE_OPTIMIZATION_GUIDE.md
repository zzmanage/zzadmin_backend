# 代码优化指南

## 前言

本指南基于对系统前后端代码的分析，总结了发现的不规范问题和优化建议，旨在提高代码质量、可维护性和性能。

## 一、前端代码优化

### 1. API调用统一封装

**问题**：
- 大量API函数中存在重复的try-catch错误处理模式
- 错误日志格式不一致
- 代码冗余，维护成本高

**解决方案**：
- 已创建统一的API请求包装器 `src/utils/api/apiRequestWrapper.js`
- 提供了 `apiGet`, `apiPost`, `apiPut`, `apiPatch`, `apiDelete` 等简化函数
- 提供了统一的错误处理函数 `handleApiError`

**使用示例**：
```javascript
// 优化前
const getUserList = async (params = {}) => {
  try {
    const response = await service({ 
      method: 'GET',
      url: '/api/users/',
      params: params
    });
    return response.data;
  } catch (error) {
    console.error("获取用户列表失败:", error.message);
    throw error;
  }
};

// 优化后
const getUserList = async (params = {}) => {
  return apiGet('/api/users/', params, '获取用户列表');
};

// 在组件中使用统一的错误处理
async function fetchUserList() {
  try {
    const data = await getUserList({ page: 1, page_size: 10 });
    // 处理成功响应
    return data;
  } catch (error) {
    const errorMessage = handleApiError(error, '获取用户列表失败');
    ElMessage.error(errorMessage);
    return { results: [], count: 0 };
  }
}
```

### 2. 配置文件优化

**问题**：
- API URL路径在各文件中硬编码，不利于统一管理
- 配置项较少，缺少一些常见的配置如请求超时时间
- 环境判断逻辑可以更清晰

**解决方案**：
- 优化 `src/config/index.js` 文件，增加API路径前缀配置
- 添加请求超时时间等通用配置
- 规范环境变量获取和使用方式

**建议实现**：
```javascript
// 从环境变量中读取配置
const env = import.meta.env.MODE || 'development';

// API路径前缀
const API_PREFIX = '/api';

// 从环境变量中获取API基础URL，如果不存在则使用默认值
const VITE_APP_API_BASE_URL = import.meta.env.VITE_APP_API_BASE_URL || 'http://localhost:8000';

// 构建完整的API基础URL
const buildApiBaseUrl = (baseUrl, prefix) => {
  // 确保baseUrl不以斜杠结尾
  const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  // 确保prefix以斜杠开头
  const cleanPrefix = prefix.startsWith('/') ? prefix : `/${prefix}`;
  return `${cleanBaseUrl}${cleanPrefix}`;
};

const EnvConfig = {
    development: {
        baseUrl: VITE_APP_API_BASE_URL,
        baseApi: buildApiBaseUrl(VITE_APP_API_BASE_URL, API_PREFIX),
        mockApi: '',
        timeout: 15000,
        retryCount: 0
    },
    test: {
        baseUrl: VITE_APP_API_BASE_URL,
        baseApi: buildApiBaseUrl(VITE_APP_API_BASE_URL, API_PREFIX),
        mockApi: '',
        timeout: 15000,
        retryCount: 1
    },
    production: {
        baseUrl: VITE_APP_API_BASE_URL,
        baseApi: buildApiBaseUrl(VITE_APP_API_BASE_URL, API_PREFIX),
        mockApi: '',
        timeout: 10000,
        retryCount: 1
    }
};

export default {
    env,
    mock: false,
    apiPrefix: API_PREFIX,
    ...EnvConfig[env]
};
```

### 3. 前端API文件重构建议

**问题**：
- 目前已完成了部分API文件的规范化（如user.js, file.js等）
- 仍有一些文件可能存在直接使用service的情况
- 硬编码的URL路径较多

**解决方案**：
- 所有API文件统一使用新的API请求包装器
- 在API文件顶部定义基础URL路径，避免硬编码
- 统一错误处理模式，使用handleApiError函数

## 二、后端代码优化

### 1. 异常处理优化

**优点**：
- 已实现全局异常处理中间件 `dashboard/middleware/exception_middleware.py`
- 已提供统一的异常处理装饰器 `handle_exceptions`

**建议改进**：
- 确保所有视图函数使用装饰器或中间件进行异常处理
- 避免在视图函数中重复编写异常处理代码
- 优化异常日志记录，确保包含足够的上下文信息

**建议实现**：
```python
from dashboard.utils.common_utils import handle_exceptions

class UserViewSet(viewsets.ModelViewSet):
    # ...
    
    @handle_exceptions(default_return={'error': '获取用户信息失败'})
    def retrieve(self, request, *args, **kwargs):
        # 简化的实现，不需要自己写try-except
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

### 2. 权限验证优化

**问题**：
- 在多个视图中发现了重复的权限验证逻辑
- 权限验证代码不够集中和统一

**解决方案**：
- 使用统一的权限验证函数 `check_user_permission`
- 为常见的权限模式创建自定义权限类
- 确保权限验证逻辑集中管理

### 3. 查询优化

**优点**：
- 部分视图已经使用了 `only` 和 `select_related` 优化查询
- 已实现缓存机制减少数据库查询

**建议改进**：
- 确保所有查询都使用 `only` 限制返回字段
- 为复杂查询添加适当的索引
- 避免在循环中进行数据库查询
- 统一缓存键的命名和过期时间管理

### 4. 代码冗余优化

**问题**：
- 在多个视图中发现了重复的代码模式，尤其是在 `get_queryset` 方法中
- 数据权限过滤逻辑在多处重复实现

**解决方案**：
- 创建通用的视图基类，封装重复的查询和过滤逻辑
- 实现统一的数据权限过滤机制
- 使用Mixin模式复用常见功能

**建议实现**：
```python
class DataPermissionViewSet(viewsets.ModelViewSet):
    """带数据权限控制的视图基类"""
    
    def get_queryset(self):
        user = self.request.user
        # 缓存键，包含用户ID和请求参数
        cache_key = f'{self.model.__name__.lower()}_queryset_{user.id}_{self.request.GET.urlencode()}'
        
        # 尝试从缓存获取数据
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            return cached_queryset
        
        # 统一的数据权限过滤逻辑
        queryset = self._apply_data_permissions(user)
        
        # 缓存查询结果
        cache.set(cache_key, queryset, 600)  # 缓存10分钟
        return queryset
    
    def _apply_data_permissions(self, user):
        # 具体的数据权限过滤逻辑
        # ...
```

## 三、代码规范建议

### 1. 命名规范
- 确保变量、函数和类的命名清晰、一致
- 遵循项目已有的命名约定
- 避免使用过于简写或模糊的命名

### 2. 注释规范
- 为复杂的逻辑添加适当的注释
- 为公共API添加文档字符串
- 遵循项目已有的注释风格

### 3. 代码风格
- 确保代码风格一致（使用isort、black等工具）
- 遵循项目已有的代码风格指南
- 定期运行代码检查工具

## 四、实施计划

1. **短期优化（1-2周）**
   - 应用新的API请求包装器优化所有前端API文件
   - 更新前端配置文件，统一管理URL路径
   - 确保所有后端视图使用统一的异常处理机制

2. **中期优化（2-4周）**
   - 创建通用的视图基类，减少后端代码冗余
   - 实现统一的数据权限过滤机制
   - 优化数据库查询和缓存策略

3. **长期优化（持续进行）**
   - 建立代码审查机制，确保新代码符合规范
   - 定期运行性能分析，发现并解决性能瓶颈
   - 持续重构和优化现有代码

## 五、总结

通过实施上述优化建议，可以显著提高系统的代码质量、可维护性和性能。优化过程中应遵循"小步快跑"的原则，确保每一步优化都经过充分测试，不会影响系统的正常运行。同时，应注重团队协作，确保所有开发人员理解并遵循新的代码规范和最佳实践。