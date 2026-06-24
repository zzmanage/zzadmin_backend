"""
流程解析器模块
负责 BPMN XML 解析和节点/流转提取
"""
import re
from typing import Dict, List, Any, Optional


class WorkflowParser:
    """工作流解析器 - 单一职责，只负责解析"""
    
    # 节点类型映射
    NODE_TYPE_MAPPING = {
        'startEvent': 'start',
        'endEvent': 'end',
        'userTask': 'userTask',
        'task': 'task',
        'exclusiveGateway': 'gateway',
        'parallelGateway': 'gateway',
        'inclusiveGateway': 'gateway',
    }
    
    # 节点默认名称
    DEFAULT_NODE_NAMES = {
        'startEvent': '开始',
        'endEvent': '结束',
        'task': '任务',
        'userTask': '用户任务',
        'exclusiveGateway': '排他网关',
        'parallelGateway': '并行网关',
        'inclusiveGateway': '包容网关',
    }
    
    def __init__(self):
        self._node_handlers = {}  # 预留的节点处理器注册表
    
    def parse_xml(self, xml: str) -> Dict[str, Any]:
        """
        解析 BPMN XML
        
        Args:
            xml: BPMN XML 字符串
            
        Returns:
            dict: 包含 nodes, transitions, startNode 的字典
        """
        nodes = self._parse_nodes(xml)
        transitions = self._parse_transitions(xml)
        start_node = next((n for n in nodes if n.get('type') == 'start'), None)
        
        return {
            'nodes': nodes,
            'transitions': transitions,
            'startNode': start_node
        }
    
    def _parse_nodes(self, xml: str) -> List[Dict[str, Any]]:
        """解析所有节点"""
        nodes = []
        
        # 尝试详细解析（包括扩展属性）
        node_pattern = r'<(startEvent|endEvent|task|userTask|exclusiveGateway|parallelGateway|inclusiveGateway)\s+([^>]+)>([^<]*(?:<(?!\/\1)[^<]*)*)<\/\1>'
        matches = re.findall(node_pattern, xml, re.DOTALL)
        
        for node_type, attrs, content in matches:
            node = self._parse_single_node(node_type, attrs, content)
            if node:
                nodes.append(node)
        
        # 如果详细解析失败，尝试简单解析
        if not nodes:
            simple_pattern = r'<(startEvent|endEvent|task|userTask|exclusiveGateway)\s+([^>]+)>'
            simple_matches = re.findall(simple_pattern, xml)
            
            for node_type, attrs in simple_matches:
                node = self._parse_single_node_simple(node_type, attrs)
                if node:
                    nodes.append(node)
        
        return nodes
    
    def _parse_single_node(self, node_type: str, attrs: str, content: str) -> Optional[Dict[str, Any]]:
        """解析单个节点的详细信息"""
        # 提取 id 和 name
        id_match = re.search(r'id="([^"]+)"', attrs)
        name_match = re.search(r'name="([^"]+)"', attrs)
        
        node_id = id_match.group(1) if id_match else None
        node_name = name_match.group(1) if name_match else self._get_default_node_name(node_type)
        node_type_normalized = self._normalize_node_type(node_type)
        
        if not node_id:
            return None
        
        # 解析扩展属性
        node_config = self._parse_node_extension(content)
        
        return {
            'key': node_id,
            'name': node_name,
            'type': node_type_normalized,
            **node_config
        }
    
    def _parse_single_node_simple(self, node_type: str, attrs: str) -> Optional[Dict[str, Any]]:
        """简单解析单个节点（无扩展属性）"""
        id_match = re.search(r'id="([^"]+)"', attrs)
        name_match = re.search(r'name="([^"]+)"', attrs)
        
        node_id = id_match.group(1) if id_match else None
        node_name = name_match.group(1) if name_match else self._get_default_node_name(node_type)
        node_type_normalized = self._normalize_node_type(node_type)
        
        if not node_id:
            return None
        
        return {
            'key': node_id,
            'name': node_name,
            'type': node_type_normalized,
            'assigneeType': 'specific',
            'candidateUsers': [],
            'candidateRoles': [],
            'assignmentStrategy': 'ANYONE',
            'assigneeExpression': '',
            'assigneeRelation': '',
            'multiInstanceType': 'parallel',
            'gatewayType': 'exclusive',
        }
    
    def _parse_transitions(self, xml: str) -> List[Dict[str, Any]]:
        """解析所有流转"""
        transitions = []
        
        transition_pattern = r'<sequenceFlow\s+([^>]+)>'
        matches = re.findall(transition_pattern, xml)
        
        for attrs in matches:
            source_ref_match = re.search(r'sourceRef="([^"]+)"', attrs)
            target_ref_match = re.search(r'targetRef="([^"]+)"', attrs)
            
            if source_ref_match and target_ref_match:
                # 解析条件表达式
                condition_expr_match = re.search(
                    r'name="conditionExpression"[^>]*value="([^"]*)"', 
                    attrs
                )
                
                transition = {
                    'from': source_ref_match.group(1),
                    'to': target_ref_match.group(1)
                }
                
                if condition_expr_match:
                    transition['conditionExpression'] = condition_expr_match.group(1)
                
                transitions.append(transition)
        
        return transitions
    
    def _parse_node_extension(self, content: str) -> Dict[str, Any]:
        """解析节点扩展属性（审批人配置等）"""
        config = {
            'assigneeType': 'specific',
            'candidateUsers': [],
            'candidateRoles': [],
            'assignmentStrategy': 'ANYONE',
            'assigneeExpression': '',
            'assigneeRelation': '',
            'multiInstanceType': 'parallel',
            'gatewayType': 'exclusive',
            'loopCardinality': None,
        }
        
        if not content:
            return config
        
        # 解析 camunda:properties
        prop_matches = re.findall(
            r'<camunda:property\s+name="([^"]+)"\s+value="([^"]*)"\s*/?>',
            content
        )
        
        for name, value in prop_matches:
            if name == 'assigneeType':
                config['assigneeType'] = value
            elif name == 'candidateUsers':
                config['candidateUsers'] = [v.strip() for v in value.split(',') if v.strip()]
            elif name == 'candidateRoles':
                config['candidateRoles'] = [v.strip() for v in value.split(',') if v.strip()]
            elif name == 'assignmentStrategy':
                config['assignmentStrategy'] = value
            elif name == 'assigneeExpression':
                config['assigneeExpression'] = value
            elif name == 'assigneeRelation':
                config['assigneeRelation'] = value
            elif name == 'multiInstanceType':
                config['multiInstanceType'] = value
            elif name == 'gatewayType':
                config['gatewayType'] = value
            elif name == 'loopCardinality':
                config['loopCardinality'] = int(value) if value.isdigit() else None
        
        # 解析扩展属性中的 assigneeExpression (alternative format)
        expr_match = re.search(
            r'name=["\']assigneeExpression["\'][^>]*value=["\']([^"\']+)["\']', 
            content
        )
        if expr_match:
            config['assigneeExpression'] = expr_match.group(1)
        
        return config
    
    def _normalize_node_type(self, node_type: str) -> str:
        """将 BPMN 节点类型转换为内部类型"""
        return self.NODE_TYPE_MAPPING.get(node_type, 'task')
    
    def _get_default_node_name(self, node_type: str) -> str:
        """获取节点类型的默认名称"""
        return self.DEFAULT_NODE_NAMES.get(node_type, '节点')


class ConditionEvaluator:
    """条件表达式评估器 - 单一职责，只负责评估条件"""
    
    @staticmethod
    def evaluate(condition: str, context: Dict[str, Any]) -> bool:
        """
        评估条件表达式
        
        Args:
            condition: 条件表达式字符串
            context: 上下文数据字典
            
        Returns:
            bool: 条件是否满足
        """
        if not condition:
            return True
        
        try:
            # 处理 ${variable:name} 格式
            var_match = re.search(r'\$\{variable:(\w+)\}', condition)
            if var_match:
                var_name = var_match.group(1)
                value = context.get(var_name)
                
                return ConditionEvaluator._evaluate_comparison(condition, value)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def _evaluate_comparison(condition: str, value: Any) -> bool:
        """评估比较表达式"""
        try:
            # 提取比较操作符和阈值
            if '>' in condition:
                parts = condition.split('>')
                threshold = float(parts[-1].strip())
                return float(value or 0) > threshold
            elif '<' in condition:
                parts = condition.split('<')
                threshold = float(parts[-1].strip())
                return float(value or 0) < threshold
            elif '==' in condition:
                parts = condition.split('==')
                expected = parts[-1].strip().strip('"\'')
                return str(value) == expected
            elif '!=' in condition:
                parts = condition.split('!=')
                expected = parts[-1].strip().strip('"\'')
                return str(value) != expected
            
            return True
        except (ValueError, TypeError):
            return False
