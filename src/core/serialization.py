"""Graph serialization system for PixelPilot.

Provides JSON-based serialization and deserialization of Function Block
Diagrams, allowing users to save and load automation workflows.
"""

import json
from typing import Dict, Any, List, Type
from pathlib import Path

from .graph import (
    Graph, Node, InputNode, ProcessNode, OutputNode, 
    TimerNode, ToggleNode, GroupNode, GroupInput, GroupOutput
)
from .rules import (
    Condition, Action,
    PixelColorCondition, RegionColorCondition, TimerCondition, KeyPressCondition,
    KeyPressAction, MouseClickAction, WaitAction, SetStateAction
)
from .exceptions import SerializationError, DeserializationError, InvalidFileFormatError


# Version for file format compatibility checking
SERIALIZATION_VERSION = "1.0"


class GraphSerializer:
    """
    Handles serialization and deserialization of FBD graphs.
    """
    
    @staticmethod
    def serialize(graph: Graph) -> str:
        """Serialize a graph to JSON string."""
        try:
            data = GraphSerializer._serialize_graph_to_dict(graph)
            data['version'] = SERIALIZATION_VERSION
            data['type'] = 'PixelPilot_Graph'
            return json.dumps(data, indent=2)
        except Exception as e:
            raise SerializationError(f"Failed to serialize graph: {e}")

    @staticmethod
    def _serialize_graph_to_dict(graph: Graph) -> Dict[str, Any]:
        """Internal helper for recursive serialization."""
        nodes_data = []
        for node in graph.nodes:
            node_dict = {
                'id': node.id,
                'type': type(node).__name__,
                'name': node.name,
                'position': list(node.position),
            }
            
            # Type-specific serialization
            if isinstance(node, InputNode):
                node_dict['condition'] = GraphSerializer._serialize_condition(node.condition)
            elif isinstance(node, ProcessNode):
                node_dict['logic_type'] = node.logic_type
                node_dict['input_ports'] = [p.name for p in node.inputs]
            elif isinstance(node, TimerNode):
                node_dict['timer_type'] = node.timer_type
                node_dict['delay_time'] = node.delay_time
                node_dict['time_on'] = node.time_on
                node_dict['time_off'] = node.time_off
            elif isinstance(node, GroupNode):
                node_dict['sub_graph'] = GraphSerializer._serialize_graph_to_dict(node.sub_graph)
                node_dict['input_mappings'] = node._input_mappings
                node_dict['output_mappings'] = node._output_mappings
            elif isinstance(node, OutputNode):
                node_dict['action'] = GraphSerializer._serialize_action(node.action)
            
            nodes_data.append(node_dict)
        
        links_data = []
        for link in graph.links:
            links_data.append({
                'source_node_id': link.source.node.id,
                'source_port': link.source.name,
                'target_node_id': link.target.node.id,
                'target_port': link.target.name
            })
            
        return {'nodes': nodes_data, 'links': links_data}
    
    @staticmethod
    def deserialize(json_str: str) -> Graph:
        """Deserialize a graph from JSON string."""
        try:
            data = json.loads(json_str)
            
            if data.get('type') != 'PixelPilot_Graph':
                raise InvalidFileFormatError("Not a valid PixelPilot graph file")
            
            file_version = data.get('version', '0.0')
            if not GraphSerializer._is_compatible_version(file_version):
                raise InvalidFileFormatError(f"Incompatible file version: {file_version}")
            
            graph = Graph()
            GraphSerializer._deserialize_graph_from_dict(data, graph)
            return graph
            
        except json.JSONDecodeError as e:
            raise DeserializationError(f"Invalid JSON: {e}")
        except Exception as e:
            raise DeserializationError(f"Failed to deserialize graph: {e}")

    @staticmethod
    def _deserialize_graph_from_dict(data: Dict[str, Any], graph: Graph):
        """Internal helper for recursive deserialization."""
        node_map = {}
        
        # 1. Reconstruct Nodes
        for node_data in data.get('nodes', []):
            node = GraphSerializer._deserialize_node(node_data)
            graph.add_node(node)
            node_map[node_data['id']] = node
            
        # 2. Reconstruct Links
        for link_data in data.get('links', []):
            source_node = node_map.get(link_data['source_node_id'])
            target_node = node_map.get(link_data['target_node_id'])
            
            if source_node and target_node:
                graph.add_link(
                    source_node, link_data['source_port'],
                    target_node, link_data['target_port']
                )
    
    @staticmethod
    def save_to_file(graph: Graph, filepath: str) -> None:
        json_str = GraphSerializer.serialize(graph)
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(json_str)
    
    @staticmethod
    def load_from_file(filepath: str) -> Graph:
        with open(filepath, 'r') as f:
            json_str = f.read()
        return GraphSerializer.deserialize(json_str)
    
    # ==================== Helper Methods ====================
    
    @staticmethod
    def _serialize_condition(condition: Condition) -> Dict[str, Any]:
        cond_type = type(condition).__name__
        if isinstance(condition, PixelColorCondition):
            return {
                'type': cond_type, 'x': condition.x, 'y': condition.y,
                'target_rgb': list(condition.target_rgb), 'tolerance': condition.tolerance
            }
        elif isinstance(condition, RegionColorCondition):
            return {
                'type': cond_type, 'region': list(condition.region),
                'target_rgb': list(condition.target_rgb), 'tolerance': condition.tolerance
            }
        elif isinstance(condition, TimerCondition):
            return {
                'type': cond_type, 'interval_seconds': condition.interval, 'timer_id': condition.timer_id
            }
        elif isinstance(condition, KeyPressCondition):
            return { 'type': cond_type, 'key_code': condition.key_code }
        return {}

    @staticmethod
    def _deserialize_condition(cond_data: Dict[str, Any]) -> Condition:
        cond_type = cond_data['type']
        if cond_type == 'PixelColorCondition':
            return PixelColorCondition(cond_data['x'], cond_data['y'], tuple(cond_data['target_rgb']), cond_data.get('tolerance', 10))
        elif cond_type == 'RegionColorCondition':
            return RegionColorCondition(tuple(cond_data['region']), tuple(cond_data['target_rgb']), cond_data.get('tolerance', 10))
        elif cond_type == 'TimerCondition':
            return TimerCondition(cond_data['interval_seconds'], cond_data['timer_id'])
        elif cond_type == 'KeyPressCondition':
            return KeyPressCondition(cond_data['key_code'])
        raise DeserializationError(f"Unknown condition type: {cond_type}")

    @staticmethod
    def _serialize_action(action: Action) -> Dict[str, Any]:
        action_type = type(action).__name__
        if isinstance(action, KeyPressAction):
            return { 'type': action_type, 'key_code': action.key_code }
        elif isinstance(action, MouseClickAction):
            return { 'type': action_type, 'x': action.x, 'y': action.y, 'button': action.button }
        elif isinstance(action, WaitAction):
            return { 'type': action_type, 'seconds': action.seconds }
        elif isinstance(action, SetStateAction):
            return { 'type': action_type, 'key': action.key, 'value': action.value }
        return {}

    @staticmethod
    def _deserialize_action(action_data: Dict[str, Any]) -> Action:
        action_type = action_data['type']
        if action_type == 'KeyPressAction':
            return KeyPressAction(action_data['key_code'])
        elif action_type == 'MouseClickAction':
            return MouseClickAction(action_data['x'], action_data['y'], action_data.get('button', 'left'))
        elif action_type == 'WaitAction':
            return WaitAction(action_data['seconds'])
        elif action_type == 'SetStateAction':
            return SetStateAction(action_data['key'], action_data['value'])
        raise DeserializationError(f"Unknown action type: {action_type}")

    @staticmethod
    def _deserialize_node(node_data: Dict[str, Any]) -> Node:
        node_type = node_data['type']
        name = node_data['name']
        
        if node_type == 'InputNode':
            condition = GraphSerializer._deserialize_condition(node_data['condition'])
            node = InputNode(name, condition)
        elif node_type == 'ProcessNode':
            node = ProcessNode(name, node_data.get('logic_type', 'AND'))
            if 'input_ports' in node_data:
                node.inputs = []
                for p in node_data['input_ports']: node.add_input_port(p)
        elif node_type == 'TimerNode':
            node = TimerNode(name, node_data.get('timer_type', 'TON'))
            node.delay_time = node_data.get('delay_time', 1000.0)
            node.time_on = node_data.get('time_on', 500.0)
            node.time_off = node_data.get('time_off', 500.0)
        elif node_type == 'ToggleNode':
            node = ToggleNode(name)
        elif node_type == 'GroupNode':
            node = GroupNode(name)
            if 'sub_graph' in node_data:
                GraphSerializer._deserialize_graph_from_dict(node_data['sub_graph'], node.sub_graph)
            node._input_mappings = node_data.get('input_mappings', {})
            node._output_mappings = node_data.get('output_mappings', {})
            # We must also ensure the external ports exist on the node itself 
            # based on the mappings (keys are port names)
            for port_name in node._input_mappings.keys():
                if not any(p.name == port_name for p in node.inputs):
                    node.add_input(port_name) # simplified re-adding
            for port_name in node._output_mappings.keys():
                if not any(p.name == port_name for p in node.outputs):
                    node.add_output(port_name)
        elif node_type == 'GroupInput':
            node = GroupInput(name)
        elif node_type == 'GroupOutput':
            node = GroupOutput(name)
        elif node_type == 'OutputNode':
            action = GraphSerializer._deserialize_action(node_data['action'])
            node = OutputNode(name, action)
        else:
            raise DeserializationError(f"Unknown node type: {node_type}")
        
        node.id = node_data['id']
        node.position = tuple(node_data['position'])
        return node
    
    @staticmethod
    def _is_compatible_version(file_version: str) -> bool:
        return file_version.split('.')[0] == SERIALIZATION_VERSION.split('.')[0]
