"""
任务分配器模块
支持多种分配策略：固定用户、角色、表达式、关系等
"""
import re
from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User
from django.db.models import Q


class TaskAssigner:
    """任务分配器基类"""
    
    def assign(self, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """
        执行任务分配
        
        Args:
            node: 节点配置信息
            instance: 流程实例
            **context: 额外的上下文信息
            
        Returns:
            User: 分配的用户对象，如果没有则返回None
        """
        raise NotImplementedError


class SpecificUserAssigner(TaskAssigner):
    """指定用户分配器"""
    
    def assign(self, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """分配给指定的单个用户"""
        candidate_users = node.get('candidateUsers', [])
        if candidate_users and len(candidate_users) > 0:
            # 取第一个用户
            user_id = int(candidate_users[0])
            return User.objects.filter(id=user_id).first()
        return None


class RoleAssigner(TaskAssigner):
    """角色分配器"""
    
    def assign(self, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """分配给拥有指定角色的用户"""
        candidate_roles = node.get('candidateRoles', [])
        if candidate_roles and len(candidate_roles) > 0:
            role_id = int(candidate_roles[0])
            # 查找拥有该角色的第一个用户
            return User.objects.filter(
                user_roles__role_id=role_id
            ).first()
        return None


class InitiatorAssigner(TaskAssigner):
    """发起人分配器"""
    
    def assign(self, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """分配给流程发起人"""
        return instance.created_by


class ExpressionAssigner(TaskAssigner):
    """表达式分配器 - 支持动态表达式"""
    
    # 支持的表达式模式
    EXPRESSION_PATTERNS = {
        # ${user:id} - 指定用户ID
        r'\$\{user:(\d+)\}': self._resolve_user_by_id,
        # ${user:username} - 指定用户名
        r'\$\{user:(\w+)\}': self._resolve_user_by_username,
        # ${role:id} - 指定角色ID
        r'\$\{role:(\d+)\}': self._resolve_user_by_role_id,
        # ${role:name} - 指定角色名
        r'\$\{role:(\w+)\}': self._resolve_user_by_role_name,
        # ${initiator} - 发起人
        r'\$\{initiator\}': self._resolve_initiator,
        # ${manager} - 上级
        r'\$\{manager\}': self._resolve_manager,
        # ${department.manager} - 部门主管
        r'\$\{department\.manager\}': self._resolve_department_manager,
        # ${last.approver} - 上一级审批人
        r'\$\{last\.approver\}': self._resolve_last_approver,
        # ${variable:name} - 流程变量
        r'\$\{variable:(\w+)\}': self._resolve_variable,
    }
    
    def assign(self, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """根据表达式动态分配"""
        assignee_expr = node.get('assigneeExpression', '')
        
        if not assignee_expr:
            return None
        
        # 尝试匹配各种表达式模式
        for pattern, resolver in self.EXPRESSION_PATTERNS.items():
            match = re.search(pattern, assignee_expr)
            if match:
                return resolver(self, match, instance, node, context)
        
        return None
    
    def _resolve_user_by_id(self, match, instance, node, context) -> Optional[User]:
        """解析 ${user:ID} 表达式"""
        user_id = int(match.group(1))
        return User.objects.filter(id=user_id).first()
    
    def _resolve_user_by_username(self, match, instance, node, context) -> Optional[User]:
        """解析 ${user:username} 表达式"""
        username = match.group(1)
        return User.objects.filter(username=username).first()
    
    def _resolve_user_by_role_id(self, match, instance, node, context) -> Optional[User]:
        """解析 ${role:ID} 表达式"""
        role_id = int(match.group(1))
        return User.objects.filter(user_roles__role_id=role_id).first()
    
    def _resolve_user_by_role_name(self, match, instance, node, context) -> Optional[User]:
        """解析 ${role:name} 表达式"""
        role_name = match.group(1)
        return User.objects.filter(user_roles__role__name=role_name).first()
    
    def _resolve_initiator(self, match, instance, node, context) -> Optional[User]:
        """解析 ${initiator} 表达式"""
        return instance.created_by
    
    def _resolve_manager(self, match, instance, node, context) -> Optional[User]:
        """解析 ${manager} 表达式 - 获取上级"""
        # 这里需要根据实际的用户模型关系来实现
        # 假设用户有 profile 或者 manager 字段
        initiator = instance.created_by
        
        # 尝试从用户配置中获取上级
        if hasattr(initiator, 'profile') and hasattr(initiator.profile, 'manager'):
            return initiator.profile.manager
        
        # 尝试从 user_roles 中查找
        # 假设上级角色是 'manager'
        manager = User.objects.filter(
            user_roles__role__name='manager'
        ).exclude(id=initiator.id).first()
        
        return manager
    
    def _resolve_department_manager(self, match, instance, node, context) -> Optional[User]:
        """解析 ${department.manager} 表达式 - 获取部门主管"""
        initiator = instance.created_by
        
        # 假设用户有部门信息
        if hasattr(initiator, 'profile') and hasattr(initiator.profile, 'department'):
            department = initiator.profile.department
            if department and hasattr(department, 'manager'):
                return department.manager
        
        # 否则返回任意一个 manager 角色用户
        return User.objects.filter(
            user_roles__role__name='部门主管'
        ).first()
    
    def _resolve_last_approver(self, match, instance, node, context) -> Optional[User]:
        """解析 ${last.approver} 表达式 - 获取上一级审批人"""
        # 获取最近完成的任务
        last_task = instance.tasks.filter(
            status=2  # 已完成
        ).order_by('-completed_at').first()
        
        if last_task and last_task.assignee:
            return last_task.assignee
        
        return None
    
    def _resolve_variable(self, match, instance, node, context) -> Optional[User]:
        """解析 ${variable:name} 表达式"""
        var_name = match.group(1)
        instance_data = instance.data or {}
        
        # 尝试从流程数据中获取用户ID或用户名
        value = instance_data.get(var_name)
        
        if not value:
            return None
        
        # 如果是用户ID
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            return User.objects.filter(id=int(value)).first()
        
        # 如果是用户名
        if isinstance(value, str):
            return User.objects.filter(username=value).first()
        
        return None


class RelationAssigner(TaskAssigner):
    """关系分配器 - 根据用户关系动态分配"""
    
    RELATIONS = {
        'supervisor': '直接上级',
        'department_head': '部门主管',
        'manager': '经理',
        'deputy': '代理人',
    }
    
    def assign(self, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """根据关系分配"""
        assignee_relation = node.get('assigneeRelation', '')
        
        if not assignee_relation or assignee_relation not in self.RELATIONS:
            return None
        
        initiator = instance.created_by
        
        if assignee_relation == 'supervisor':
            # 获取直接上级
            if hasattr(initiator, 'profile') and hasattr(initiator.profile, 'supervisor'):
                return initiator.profile.supervisor
            # 查找 manager 角色用户
            return User.objects.filter(
                user_roles__role__name='直接上级'
            ).exclude(id=initiator.id).first()
        
        elif assignee_relation == 'department_head':
            # 获取部门主管
            if hasattr(initiator, 'profile') and hasattr(initiator.profile, 'department'):
                department = initiator.profile.department
                if department and hasattr(department, 'head'):
                    return department.head
            return User.objects.filter(
                user_roles__role__name='部门主管'
            ).first()
        
        elif assignee_relation == 'manager':
            # 获取经理
            return User.objects.filter(
                user_roles__role__name='经理'
            ).first()
        
        elif assignee_relation == 'deputy':
            # 获取代理人
            if hasattr(initiator, 'profile') and hasattr(initiator.profile, 'deputy'):
                return initiator.profile.deputy
        
        return None


class MultiInstanceAssigner(TaskAssigner):
    """多实例分配器 - 支持会签"""
    
    def assign(self, node: Dict[str, Any], instance, **context) -> List[User]:
        """
        返回多个用户用于会签
        
        Returns:
            List[User]: 用户列表
        """
        assignee_type = node.get('assigneeType', 'specific')
        candidate_users = node.get('candidateUsers', [])
        candidate_roles = node.get('candidateRoles', [])
        multi_instance_type = node.get('multiInstanceType', 'parallel')  # parallel 或 sequential
        
        users = []
        
        if assignee_type == 'specific':
            # 指定多个用户
            for user_id in candidate_users:
                user = User.objects.filter(id=int(user_id)).first()
                if user:
                    users.append(user)
        
        elif assignee_type == 'role':
            # 指定角色下的所有用户
            for role_id in candidate_roles:
                role_users = User.objects.filter(user_roles__role_id=int(role_id))
                users.extend(role_users)
        
        return users


class AssignmentRegistry:
    """分配器注册表"""
    
    _assigners = {
        'specific': SpecificUserAssigner(),
        'role': RoleAssigner(),
        'initiator': InitiatorAssigner(),
        'expression': ExpressionAssigner(),
        'relation': RelationAssigner(),
        'multiInstance': MultiInstanceAssigner(),
    }
    
    @classmethod
    def get_assigner(cls, assignee_type: str) -> TaskAssigner:
        """获取指定类型的分配器"""
        return cls._assigners.get(assignee_type, SpecificUserAssigner())
    
    @classmethod
    def register(cls, name: str, assigner: TaskAssigner):
        """注册新的分配器"""
        cls._assigners[name] = assigner
    
    @classmethod
    def resolve_assignee(cls, node: Dict[str, Any], instance, **context) -> Optional[User]:
        """解析并分配任务"""
        assignee_type = node.get('assigneeType', 'specific')
        assigner = cls.get_assigner(assignee_type)
        return assigner.assign(node, instance, **context)
