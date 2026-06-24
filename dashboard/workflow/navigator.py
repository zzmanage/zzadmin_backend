"""
流程导航器模块
负责流程流转控制和节点处理
"""
from typing import Dict, List, Any, Optional
from .parser import WorkflowParser, ConditionEvaluator


class FlowNavigator:
    """流程导航器 - 单一职责，只负责流程流转"""
    
    def __init__(self, parser: WorkflowParser = None):
        """
        初始化流程导航器
        
        Args:
            parser: 工作流解析器（可选，默认创建新实例）
        """
        self._parser = parser or WorkflowParser()
        self._node_handlers = {}
        self._task_creator = None
    
    def set_task_creator(self, task_creator):
        """设置任务创建器"""
        self._task_creator = task_creator
    
    def set_node_handler(self, node_type: str, handler):
        """设置节点类型对应的处理器"""
        self._node_handlers[node_type] = handler
    
    def navigate_from_node(self, instance, current_node_key: str, nodes: List[Dict], transitions: List[Dict]):
        """
        从指定节点开始导航流程
        
        Args:
            instance: 流程实例
            current_node_key: 当前节点Key
            nodes: 节点列表
            transitions: 流转列表
        """
        # 获取当前节点的输出流转
        outgoing_transitions = [t for t in transitions if t.get('from') == current_node_key]
        
        for transition in outgoing_transitions:
            target_key = transition.get('to')
            target_node = self._find_node(nodes, target_key)
            
            if target_node:
                self._process_node(instance, target_node, nodes, transitions)
    
    def navigate_from_start(self, instance, flow_json: Dict[str, Any]):
        """
        从开始节点导航流程
        
        Args:
            instance: 流程实例
            flow_json: 流程定义JSON
        """
        # 获取节点和流转
        nodes, transitions = self._get_nodes_and_transitions(instance, flow_json)
        
        if not nodes:
            return
        
        # 查找开始节点
        start_node = next((n for n in nodes if n.get('type') == 'start'), None)
        
        if not start_node:
            return
        
        # 从开始节点的下一个节点开始导航
        self.navigate_from_node(instance, start_node.get('key'), nodes, transitions)
    
    def advance_workflow(self, instance, completed_task, flow_json: Dict[str, Any]):
        """
        推进流程到下一个节点
        
        Args:
            instance: 流程实例
            completed_task: 已完成的任务
            flow_json: 流程定义JSON
        """
        nodes, transitions = self._get_nodes_and_transitions(instance, flow_json)
        
        if not nodes:
            instance.status = 2  # 完成
            instance.save()
            return
        
        # 获取已完成任务的输出流转
        completed_key = completed_task.task_def_key
        next_transitions = [t for t in transitions if t.get('from') == completed_key]
        
        has_next_task = False
        for transition in next_transitions:
            target_key = transition.get('to')
            target_node = self._find_node(nodes, target_key)
            
            if target_node:
                result = self._process_node(instance, target_node, nodes, transitions)
                if result:
                    has_next_task = True
        
        # 如果没有下一个任务且没有到达结束节点，也标记为完成
        if not has_next_task and instance.status == 1:
            instance.status = 2
            instance.save()
    
    def _get_nodes_and_transitions(self, instance, flow_json: Dict[str, Any]) -> tuple:
        """获取节点和流转列表"""
        nodes = flow_json.get('nodes', [])
        transitions = flow_json.get('transitions', [])
        
        if not nodes and flow_json.get('xml'):
            parsed_data = self._parser.parse_xml(flow_json['xml'])
            nodes = parsed_data['nodes']
            transitions = parsed_data['transitions']
        
        return nodes, transitions
    
    def _find_node(self, nodes: List[Dict], node_key: str) -> Optional[Dict]:
        """查找节点"""
        return next((n for n in nodes if n.get('key') == node_key), None)
    
    def _process_node(self, instance, node: Dict, nodes: List[Dict], transitions: List[Dict]) -> bool:
        """
        处理节点
        
        Returns:
            bool: 是否处理成功
        """
        node_type = node.get('type')
        
        # 如果有专门的处理器，使用它
        if node_type in self._node_handlers:
            handler = self._node_handlers[node_type]
            return handler.handle(instance, node, {'task_creator': self._task_creator})
        
        # 根据节点类型处理
        if node_type == 'end':
            # 结束节点
            instance.status = 2
            instance.save()
            return False
        
        elif node_type in ['task', 'userTask']:
            # 任务节点，创建任务
            if self._task_creator:
                self._task_creator.create_task(instance, node)
            return True
        
        elif node_type == 'gateway':
            # 网关节点
            return self._handle_gateway(instance, node, nodes, transitions)
        
        return False
    
    def _handle_gateway(self, instance, gateway_node: Dict, nodes: List[Dict], transitions: List[Dict]) -> bool:
        """处理网关"""
        gateway_type = gateway_node.get('gatewayType', 'exclusive')
        
        if gateway_type == 'exclusive':
            return self._handle_exclusive_gateway(instance, gateway_node, nodes, transitions)
        elif gateway_type == 'parallel':
            return self._handle_parallel_gateway(instance, gateway_node, nodes, transitions)
        elif gateway_type == 'inclusive':
            return self._handle_inclusive_gateway(instance, gateway_node, nodes, transitions)
        
        return False
    
    def _handle_exclusive_gateway(self, instance, gateway_node: Dict, nodes: List[Dict], transitions: List[Dict]) -> bool:
        """处理排他网关 - 只选择一条满足条件的路径"""
        outgoing_transitions = [t for t in transitions if t.get('from') == gateway_node.get('key')]
        
        # 评估每个流转的条件
        for transition in outgoing_transitions:
            condition = transition.get('conditionExpression', '')
            if ConditionEvaluator.evaluate(condition, instance.data or {}):
                # 找到满足条件的流转
                target_key = transition.get('to')
                target_node = self._find_node(nodes, target_key)
                
                if target_node:
                    return self._process_node(instance, target_node, nodes, transitions)
        
        # 如果没有满足条件的，默认选择第一个
        if outgoing_transitions:
            first_target_key = outgoing_transitions[0].get('to')
            target_node = self._find_node(nodes, first_target_key)
            if target_node:
                return self._process_node(instance, target_node, nodes, transitions)
        
        return False
    
    def _handle_parallel_gateway(self, instance, gateway_node: Dict, nodes: List[Dict], transitions: List[Dict]) -> bool:
        """处理并行网关 - 同时执行所有分支"""
        outgoing_transitions = [t for t in transitions if t.get('from') == gateway_node.get('key')]
        
        has_result = False
        for transition in outgoing_transitions:
            target_key = transition.get('to')
            target_node = self._find_node(nodes, target_key)
            
            if target_node:
                result = self._process_node(instance, target_node, nodes, transitions)
                if result:
                    has_result = True
        
        return has_result
    
    def _handle_inclusive_gateway(self, instance, gateway_node: Dict, nodes: List[Dict], transitions: List[Dict]) -> bool:
        """处理包容网关 - 执行所有满足条件的分支"""
        outgoing_transitions = [t for t in transitions if t.get('from') == gateway_node.get('key')]
        
        has_result = False
        for transition in outgoing_transitions:
            condition = transition.get('conditionExpression', '')
            if ConditionEvaluator.evaluate(condition, instance.data or {}):
                target_key = transition.get('to')
                target_node = self._find_node(nodes, target_key)
                
                if target_node:
                    result = self._process_node(instance, target_node, nodes, transitions)
                    if result:
                        has_result = True
        
        return has_result
