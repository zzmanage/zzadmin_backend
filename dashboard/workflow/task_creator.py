"""
任务创建器模块
负责根据节点配置创建任务
"""
from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User
from ..models import WorkflowTask


class TaskCreator:
    """任务创建器 - 单一职责，只负责创建任务"""
    
    def __init__(self, assignee_resolver=None):
        """
        初始化任务创建器
        
        Args:
            assignee_resolver: 审批人解析器（可选）
        """
        self._assignee_resolver = assignee_resolver
    
    def create_task(self, instance, node: Dict[str, Any]) -> WorkflowTask:
        """
        创建单个任务
        
        Args:
            instance: 流程实例
            node: 节点配置
            
        Returns:
            WorkflowTask: 创建的任务对象
        """
        # 解析审批人
        assignee = self._resolve_assignee(instance, node)
        
        # 创建任务
        task = WorkflowTask.objects.create(
            instance=instance,
            task_def_key=node.get('key'),
            task_name=node.get('name'),
            assignee=assignee,
            candidate_users=node.get('candidateUsers', []),
            candidate_roles=node.get('candidateRoles', []),
            status=0 if not assignee else 1,
            data={},
            tenant=instance.tenant
        )
        
        # 处理多实例（会签）
        if node.get('assigneeType') == 'multiInstance':
            self._create_multi_instance_tasks(instance, node, task)
        
        return task
    
    def _resolve_assignee(self, instance, node: Dict[str, Any]) -> Optional[User]:
        """解析审批人"""
        if self._assignee_resolver:
            return self._assignee_resolver(node, instance)
        
        # 默认使用 AssignmentRegistry
        from .assigner import AssignmentRegistry
        return AssignmentRegistry.resolve_assignee(node, instance)
    
    def _create_multi_instance_tasks(self, instance, node: Dict[str, Any], first_task: WorkflowTask):
        """创建多实例任务（会签）"""
        multi_instance_type = node.get('multiInstanceType', 'parallel')
        
        if multi_instance_type != 'parallel':
            return
        
        # 获取所有审批人
        users = self._get_multi_instance_users(instance, node)
        
        # 为其他用户创建任务
        for user in users[1:]:
            WorkflowTask.objects.create(
                instance=instance,
                task_def_key=f"{node.get('key')}_{user.id}",
                task_name=node.get('name'),
                assignee=user,
                candidate_users=[str(user.id)],
                status=0,
                data={},
                tenant=instance.tenant
            )
    
    def _get_multi_instance_users(self, instance, node: Dict[str, Any]) -> List[User]:
        """获取多实例的所有审批人"""
        users = []
        assignee_type = node.get('assigneeType', 'specific')
        
        if assignee_type == 'specific':
            for user_id in node.get('candidateUsers', []):
                user = User.objects.filter(id=int(user_id)).first()
                if user:
                    users.append(user)
        elif assignee_type == 'role':
            for role_id in node.get('candidateRoles', []):
                role_users = User.objects.filter(user_roles__role_id=int(role_id))
                users.extend(role_users)
        
        return users


class NodeHandlerRegistry:
    """节点处理器注册表 - 开闭原则，支持扩展"""
    
    _handlers = {}
    
    @classmethod
    def register(cls, node_type: str, handler_class):
        """注册节点处理器"""
        cls._handlers[node_type] = handler_class
    
    @classmethod
    def get_handler(cls, node_type: str):
        """获取节点处理器"""
        handler_class = cls._handlers.get(node_type)
        if handler_class:
            return handler_class()
        
        # 返回默认处理器
        return DefaultNodeHandler()
    
    @classmethod
    def create_node_handlers(cls) -> Dict[str, Any]:
        """创建所有节点处理器（供协调器使用）"""
        return {
            node_type: cls.get_handler(node_type)
            for node_type in cls._handlers.keys()
        }


class DefaultNodeHandler:
    """默认节点处理器"""
    
    def handle(self, instance, node: Dict[str, Any], context: Dict[str, Any]):
        """处理节点（创建任务等）"""
        task_creator = context.get('task_creator')
        if task_creator:
            return task_creator.create_task(instance, node)
        return None


# 注册默认的节点处理器
NodeHandlerRegistry.register('task', DefaultNodeHandler)
NodeHandlerRegistry.register('userTask', DefaultNodeHandler)
