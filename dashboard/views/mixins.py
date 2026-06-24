import logging
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class TreeViewMixin:
    """树结构视图混入类
    
    提供处理树结构数据的通用方法
    """
    
    def _build_tree(self, items, parent_id=None, id_field='id', parent_id_field='parent_id', children_field='children'):
        """递归构建树结构
        
        Args:
            items: 数据项列表
            parent_id: 父节点ID
            id_field: ID字段名
            parent_id_field: 父节点ID字段名
            children_field: 子节点字段名
        
        Returns:
            list: 树结构数据
        """
        tree = []
        for item in items:
            if item.get(parent_id_field) == parent_id:
                # 递归查找子节点
                children = self._build_tree(items, item.get(id_field), id_field, parent_id_field, children_field)
                if children:
                    item[children_field] = children
                tree.append(item)
        return tree
    
    def _build_tree_iterative(self, items):
        """迭代构建树结构，避免递归过深导致的栈溢出
        
        Args:
            items: 数据项列表
        
        Returns:
            list: 树结构数据
        """
        # 创建ID到节点的映射
        item_map = {item.get('id'): item for item in items}
        
        # 初始化根节点列表
        tree = []
        
        # 迭代构建树
        for item in items:
            parent_id = item.get('parent_id')
            if parent_id is None or parent_id not in item_map:
                # 根节点
                tree.append(item)
            else:
                # 子节点，添加到父节点的children列表中
                if 'children' not in item_map[parent_id]:
                    item_map[parent_id]['children'] = []
                item_map[parent_id]['children'].append(item)
        
        return tree
    
    def get_tree_cache_key(self, prefix=''):
        """生成树结构缓存键
        
        Args:
            prefix: 缓存键前缀
        
        Returns:
            str: 缓存键
        """
        user = self.request.user
        return f'{prefix}_tree_{user.id}'
    
    def _clear_tree_cache(self, prefix=''):
        """清除树结构相关缓存，兼容不同的缓存后端
        
        Args:
            prefix: 缓存键前缀
        """
        # 尝试使用delete_pattern方法（某些缓存后端如Redis支持）
        if hasattr(cache, 'delete_pattern'):
            try:
                cache.delete_pattern(f'{prefix}_tree_*')
            except Exception:
                # 如果delete_pattern调用失败，记录日志并继续
                logger.debug(f"尝试清除{prefix}树结构缓存时出错，跳过此操作")
    
    def tree(self, request, *args, **kwargs):
        """获取树结构数据的通用方法
        
        子类需要实现具体的树构建逻辑
        """
        raise NotImplementedError("子类必须实现tree方法")