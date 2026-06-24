import logging
from typing import Dict, List, Any, Optional, Set, Union
from django.db.models import QuerySet, Prefetch
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TreeBuilder:
    """通用的树结构构建工具类
    
    提供优化的树结构构建功能，支持菜单树、角色权限树等各种树状结构的构建
    优化性能，避免递归调用带来的栈溢出问题
    """
    
    @staticmethod
    def build_tree(
        items: Union[QuerySet, List[Dict]], 
        id_field: str = 'id', 
        parent_id_field: str = 'parent_id', 
        children_field: str = 'children',
        sort_field: str = 'sort'
    ) -> List[Dict]:
        """通用的树结构构建方法，使用迭代方式替代递归，提高性能
        
        Args:
            items: 数据项列表或查询集
            id_field: ID字段名
            parent_id_field: 父ID字段名
            children_field: 子节点字段名
            sort_field: 排序字段名
        
        Returns:
            list: 树结构数据
        """
        # 创建节点映射字典，方便快速查找父节点
        node_map = {}
        root_nodes = []

        # 1. 先将所有节点放入字典中，并找出根节点
        for item in items:
            # 转换为字典格式（如果是模型实例）
            if hasattr(item, '__dict__'):
                item_data = {}
                # 获取所有非私有、非调用属性
                for field in dir(item):
                    if not field.startswith('_') and not callable(getattr(item, field)):
                        # 避免访问懒加载属性导致额外查询
                        try:
                            value = getattr(item, field)
                            # 跳过复杂对象，只保留简单数据类型
                            if isinstance(value, (str, int, float, bool, type(None), list, dict)):
                                item_data[field] = value
                        except:
                            continue
            else:
                item_data = dict(item)
            
            # 确保子节点列表存在
            item_data[children_field] = []
            
            item_id = item_data.get(id_field)
            if item_id is not None:
                node_map[item_id] = item_data
                
                # 记录根节点（parent_id为None的节点）
                parent_id = item_data.get(parent_id_field)
                if parent_id is None:
                    root_nodes.append(item_data)
        
        # 2. 构建父子关系
        for item_id, item_data in node_map.items():
            parent_id = item_data.get(parent_id_field)
            
            if parent_id is not None and parent_id in node_map:
                parent_node = node_map[parent_id]
                parent_node[children_field].append(item_data)
        
        # 3. 对每个节点的子节点按sort字段排序
        for node_id, node in node_map.items():
            if sort_field and node[children_field]:
                node[children_field].sort(key=lambda x: x.get(sort_field, 0))
        
        # 对根节点按sort字段排序
        if sort_field and root_nodes:
            root_nodes.sort(key=lambda x: x.get(sort_field, 0))
        
        return root_nodes
    
    @staticmethod
    def get_cached_tree(
        cache_key: str, 
        build_func, 
        timeout: int = 600, 
        refresh_cache: bool = False
    ) -> Any:
        """获取缓存的树结构，如果不存在则构建并缓存
        
        Args:
            cache_key: 缓存键
            build_func: 构建树的函数
            timeout: 缓存过期时间（秒）
            refresh_cache: 是否强制刷新缓存
        
        Returns:
            树结构数据
        """
        # 检查是否需要刷新缓存
        if refresh_cache:
            logger.debug(f"强制刷新缓存: {cache_key}")
            cache.delete(cache_key)
            cached_tree = None
        else:
            # 尝试从缓存获取
            cached_tree = cache.get(cache_key)
            if cached_tree:
                logger.debug(f"返回缓存的树结构: {cache_key}")
                return cached_tree
            else:
                logger.debug(f"未找到缓存的树结构，将重新构建: {cache_key}")
        
        # 构建树结构
        tree = build_func()
        
        # 缓存树结构
        cache.set(cache_key, tree, timeout)
        logger.debug(f"树结构已缓存: {cache_key}，过期时间: {timeout}秒")
        
        return tree


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
            # 对按钮按ID排序
            if 'buttons' in node:
                node['buttons'].sort(key=lambda x: x.get('id', 0))
        
        # 对根节点按sort字段排序
        root_nodes.sort(key=lambda x: x.get('sort', 0))
        
        return root_nodes
    
    @staticmethod
    def clear_menu_caches():
        """清除与菜单相关的所有缓存，兼容不同的缓存后端"""
        # 清除菜单树缓存
        cache.delete('menu_tree_active')
        
        # 清除角色权限树缓存
        if hasattr(cache, 'delete_pattern'):
            try:
                cache.delete_pattern('role_permissions_tree_*')
            except Exception as e:
                logger.debug(f"尝试清除角色权限树缓存时出错: {str(e)}，跳过此操作")
        
        # 清除用户权限缓存
        if hasattr(cache, 'delete_pattern'):
            try:
                cache.delete_pattern('user_permissions_*')
            except Exception as e:
                logger.debug(f"尝试清除用户权限缓存时出错: {str(e)}，跳过此操作")
    
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