"""
流程引擎核心模块
负责流程解析、任务创建和流程推进
采用协调器模式，委托给专业组件处理
"""
from django.db import transaction
from django.contrib.auth.models import User
from ..models import WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowTransition
from .parser import WorkflowParser, ConditionEvaluator
from .task_creator import TaskCreator
from .navigator import FlowNavigator
from .assigner import AssignmentRegistry


class WorkflowEngine:
    """工作流引擎 - 协调器角色，负责协调各组件"""
    
    # 单例或类级别的组件实例
    _parser = WorkflowParser()
    _task_creator = TaskCreator()
    _navigator = FlowNavigator(parser=_parser)
    
    # 初始化导航器
    _navigator.set_task_creator(_task_creator)
    
    @classmethod
    def parse_bpmn_xml(cls, xml):
        """解析BPMN XML，提取节点和流转信息"""
        return cls._parser.parse_xml(xml)
    
    @classmethod
    def start_workflow(cls, definition_id, user, business_key=None, data=None):
        """启动流程实例并创建初始任务"""
        definition = WorkflowDefinition.objects.get(id=definition_id)

        # 创建流程实例
        instance = WorkflowInstance.objects.create(
            definition=definition,
            business_key=business_key,
            data=data or {},
            status=1,  # 运行中
            created_by=user,
            tenant=definition.tenant
        )

        # 解析流程定义并创建初始任务
        cls._navigator.navigate_from_start(instance, instance.definition.flow_json)

        return instance

    @classmethod
    def complete_task(cls, task_id, user, comment=None, data=None):
        """完成任务并推进流程"""
        task = WorkflowTask.objects.get(id=task_id)
        instance = task.instance

        # 更新任务状态
        task.status = 2  # 已完成
        if not task.assignee:
            task.assignee = user
        task.comment = comment
        task.data = data or {}
        task.save()

        # 创建流转记录
        WorkflowTransition.objects.create(
            task=task,
            from_state='claimed' if task.status == 1 else 'created',
            to_state='completed',
            transition_name='complete',
            comment=comment,
            data=data or {},
            operator=user,
            tenant=instance.tenant
        )

        # 推进流程到下一个任务
        cls._navigator.advance_workflow(instance, task, instance.definition.flow_json)

    @classmethod
    def claim_task(cls, task_id, user, comment=None):
        """认领任务"""
        task = WorkflowTask.objects.get(id=task_id)

        if task.status != 0:
            raise ValueError('任务状态不允许认领')

        # 更新任务状态
        task.status = 1  # 处理中
        task.assignee = user
        task.comment = comment
        task.save()

        # 创建流转记录
        WorkflowTransition.objects.create(
            task=task,
            from_state='created',
            to_state='claimed',
            transition_name='claim',
            comment=comment,
            data={},
            operator=user,
            tenant=task.tenant
        )

        return task

    @classmethod
    def reject_task(cls, task_id, user, comment=None, data=None):
        """拒绝任务"""
        task = WorkflowTask.objects.get(id=task_id)
        instance = task.instance

        # 更新任务状态
        task.status = 3  # 已拒绝
        task.comment = comment
        task.data = data or {}
        task.save()

        # 创建流转记录
        WorkflowTransition.objects.create(
            task=task,
            from_state='claimed' if task.status == 1 else 'created',
            to_state='rejected',
            transition_name='reject',
            comment=comment,
            data=data or {},
            operator=user,
            tenant=instance.tenant
        )

        return task
    
    # 保留向后兼容的方法（可以逐步废弃）
    
    @classmethod
    def get_default_node_name(cls, node_type):
        """获取节点类型的默认名称"""
        return cls._parser._get_default_node_name(node_type)

    @classmethod
    def get_node_type(cls, node_type):
        """将BPMN节点类型转换为工作流引擎使用的类型"""
        return cls._parser._normalize_node_type(node_type)
    
    @classmethod
    def _parse_node_extension(cls, content: str) -> dict:
        """解析节点的扩展属性（审批人配置等）"""
        return cls._parser._parse_node_extension(content)
    
    @classmethod
    def _create_task(cls, instance, node):
        """创建单个任务 - 使用任务创建器"""
        return cls._task_creator.create_task(instance, node)
    
    @classmethod
    def _handle_gateway(cls, instance, gateway_node, nodes, transitions):
        """处理网关节点"""
        cls._navigator._handle_gateway(instance, gateway_node, nodes, transitions)
    
    @classmethod
    def _evaluate_condition(cls, condition: str, instance) -> bool:
        """评估条件表达式"""
        return ConditionEvaluator.evaluate(condition, instance.data or {})
    
    @classmethod
    def _create_initial_tasks(cls, instance):
        """根据流程定义创建初始任务"""
        cls._navigator.navigate_from_start(instance, instance.definition.flow_json)
    
    @classmethod
    def _advance_workflow(cls, instance, completed_task):
        """推进流程到下一个节点"""
        cls._navigator.advance_workflow(instance, completed_task, instance.definition.flow_json)
