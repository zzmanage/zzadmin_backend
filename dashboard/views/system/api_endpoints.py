import logging
import traceback
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.urls import get_resolver

from ...utils.cache_utils import CacheManager

logger = logging.getLogger(__name__)


class ApiEndpointViewSet(ViewSet):
    """API端点视图集
    
    提供查看系统中所有可用API端点的功能
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, **kwargs):
        """初始化视图集，设置缓存管理器"""
        super().__init__(**kwargs)
        self.cache_manager = CacheManager()
    
    def list(self, request):
        """获取所有可用的API端点列表
        
        Returns:
            Response: API端点列表数据
        """
        return self.all_endpoints(request)
        
    def all_endpoints(self, request):
        """获取所有可用的API端点列表
        
        Returns:
            Response: API端点列表数据
        """
        try:
            # 缓存键
            cache_key = f'api_endpoints_list_{request.user.id}'
            
            # 使用缓存管理器获取缓存数据
            cached_endpoints = self.cache_manager.get(cache_key)
            if cached_endpoints:
                return Response(cached_endpoints)

            # 获取所有URL模式
            resolver = get_resolver()
            api_endpoints = []

            # 遍历URL模式，收集API端点
            def traverse_url_patterns(patterns, prefix=''):
                for pattern in patterns:
                    if hasattr(pattern, 'url_patterns'):
                        # 如果是包含子URL模式的对象（如include）
                        traverse_url_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
                    else:
                        try:
                            # 获取URL模式的正则表达式
                            url_regex = prefix + str(pattern.pattern)

                            # 添加调试日志，查看所有URL
                            logger.debug(f"检查URL: {url_regex}")

                            # 规范化URL格式
                            url_path = url_regex.replace('^', '').replace('$', '')

                            # 只获取以/api/开头的API端点
                            if not url_path.startswith('api/'):
                                continue

                            # 检查视图函数是否有明确的HTTP方法
                            view = pattern.callback
                            methods = []

                            if hasattr(view, 'cls') and hasattr(view.cls, 'get_extra_actions'):
                                # 处理ViewSet类型的视图
                                viewset = view.cls
                                # 默认的CRUD操作
                                default_actions = {
                                    'create': 'POST',
                                    'list': 'GET',
                                    'retrieve': 'GET',
                                    'update': 'PUT',
                                    'partial_update': 'PATCH',
                                    'destroy': 'DELETE'
                                }
                                # 检查默认操作是否存在
                                for action_name, method in default_actions.items():
                                    if hasattr(viewset, action_name):
                                        methods.append(method)
                                # 获取额外操作
                                for action in viewset.get_extra_actions():
                                    methods.extend(action.mapping.keys())
                            elif hasattr(view, 'actions'):
                                # 处理APIView类型的视图
                                methods = list(view.actions.keys())
                            else:
                                # 默认添加GET方法
                                methods = ['GET']

                            # 去重
                            methods = list(set(methods))

                            # 添加到API端点列表
                            api_endpoints.append({
                                'url': url_path,
                                'methods': methods
                            })
                        except Exception as e:
                            logger.warning(f"处理URL模式时出错: {str(e)}")
                            # 继续处理下一个URL模式，不中断整个过程
                            continue

            # 开始遍历URL模式
            traverse_url_patterns(resolver.url_patterns)

            # 添加调试日志，显示收集到的端点数量
            logger.debug(f"共收集到{len(api_endpoints)}个API端点")

            # 使用缓存管理器缓存API端点列表5分钟
            self.cache_manager.set(cache_key, api_endpoints, 300)

            # 确保返回数据格式一致
            return Response(api_endpoints, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"获取API端点失败: {str(e)}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return Response(
                {"error": f"获取API端点失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )