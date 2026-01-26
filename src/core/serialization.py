"""Graph serialization system for PixelPilot.

Provides JSON-based serialization and deserialization of Function Block
Diagrams, allowing users to save and load automation workflows.
"""

import json
from typing import Dict, Any, List, Type
from pathlib import Path

from .graph import Graph, Node, InputNode, ProcessNode, OutputNode
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
    
    Supports saving graphs to JSON files and loading them back,
    preserving all node configurations, connections, and positions.
    
    Example:
        >>> serializer = GraphSerializer()
        >>> json_str = serializer.serialize(my_graph)
        >>> with open('workflow.pp', 'w') as f:
        >>>     f.write(json_str)
        >>>
        >>> with open('workflow.pp', 'r') as f:
        >>>     json_str = f.read()
        >>> graph = serializer.deserialize(json_str)
    """
    
    @staticmethod
    def serialize(graph: Graph) -> str:
        """
        Serialize a graph to JSON string.
        
        Args:
            graph: Graph instance to serialize
            
        Returns:
            JSON string representation
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Build node data
            nodes_data = []
            for node in graph.nodes:
                node_dict = {
                    'id': node.id,
                    'type': type(node).__name__,
                    'name': node.name,
                    'position': list(node.position),  # Convert tuple to list for JSON
                }
                
                # Add type-specific configuration
                if isinstance(node, InputNode):
                    node_dict['condition'] = GraphSerializer._serialize_condition(node.condition)
                elif isinstance(node, ProcessNode):
                    node_dict['logic_type'] = node.logic_type
                elif isinstance(node, OutputNode):
                    node_dict['action'] = GraphSerializer._serialize_action(node.action)
                
                nodes_data.append(node_dict)
            
            # Build link data
            links_data = []
            for link in graph.links:
                link_dict = {
                    'source_node_id': link.source.node.id,
                    'source_port': link.source.name,
                    'target_node_id': link.target.node.id,
                    'target_port': link.target.name
                }
                links_data.append(link_dict)
            
            # Build complete data structure
            data = {
                'version': SERIALIZATION_VERSION,
                'type': 'PixelPilot_Graph',
                'nodes': nodes_data,
                'links': links_data
            }
            
            return json.dumps(data, indent=2)
            
        except Exception as e:
            raise SerializationError(f"Failed to serialize graph: {e}")
    
    @staticmethod
    def deserialize(json_str: str) -> Graph:
        """
        Deserialize a graph from JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            Reconstructed Graph instance
            
        Raises:
            DeserializationError: If deserialization fails
            InvalidFileFormatError: If file format is invalid
        """
        try:
            data = json.loads(json_str)
            
            # Validate format
            if data.get('type') != 'PixelPilot_Graph':
                raise InvalidFileFormatError("Not a valid PixelPilot graph file")
            
            # Check version compatibility
            file_version = data.get('version', '0.0')
            if not GraphSerializer._is_compatible_version(file_version):
                raise InvalidFileFormatError(
                    f"Incompatible file version: {file_version} "
                    f"(current: {SERIALIZATION_VERSION})"
                )
            
            # Create graph
            graph = Graph()
            node_map = {}  # Map IDs to node instances
            
            # Deserialize nodes
            for node_data in data.get('nodes', []):
                node = GraphSerializer._deserialize_node(node_data)
                graph.add_node(node)
                node_map[node_data['id']] = node
            
            # Deserialize links
            for link_data in data.get('links', []):
                source_node = node_map[link_data['source_node_id']]
                target_node = node_map[link_data['target_node_id']]
                
                graph.add_link(
                    source_node, link_data['source_port'],
                    target_node, link_data['target_port']
                )
            
            return graph
            
        except json.JSONDecodeError as e:
            raise DeserializationError(f"Invalid JSON: {e}")
        except KeyError as e:
            raise DeserializationError(f"Missing required field: {e}")
        except Exception as e:
            raise DeserializationError(f"Failed to deserialize graph: {e}")
    
    @staticmethod
    def save_to_file(graph: Graph, filepath: str) -> None:
        """
        Save graph to file.
        
        Args:
            graph: Graph to save
            filepath: Path to save file
        """
        json_str = GraphSerializer.serialize(graph)
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(json_str)
    
    @staticmethod
    def load_from_file(filepath: str) -> Graph:
        """
        Load graph from file.
        
        Args:
            filepath: Path to load from
            
        Returns:
            Loaded Graph instance
        """
        with open(filepath, 'r') as f:
            json_str = f.read()
        
        return GraphSerializer.deserialize(json_str)
    
    # ==================== Helper Methods ====================
    
    @staticmethod
    def _serialize_condition(condition: Condition) -> Dict[str, Any]:
        """Serialize a Condition object to dictionary."""
        cond_type = type(condition).__name__
        
        if isinstance(condition, PixelColorCondition):
            return {
                'type': cond_type,
                'x': condition.x,
                'y': condition.y,
                'target_rgb': list(condition.target_rgb),
                'tolerance': condition.tolerance
            }
        elif isinstance(condition, RegionColorCondition):
            return {
                'type': cond_type,
                'region': list(condition.region),
                'target_rgb': list(condition.target_rgb),
                'tolerance': condition.tolerance
            }
        elif isinstance(condition, TimerCondition):
            return {
                'type': cond_type,
                'interval_seconds': condition.interval,
                'timer_id': condition.timer_id
            }
        elif isinstance(condition, KeyPressCondition):
            return {
                'type': cond_type,
                'key_code': condition.key_code
            }
        else:
            raise SerializationError(f"Unknown condition type: {cond_type}")
    
    @staticmethod
    def _deserialize_condition(cond_data: Dict[str, Any]) -> Condition:
        """Deserialize a Condition object from dictionary."""
        cond_type = cond_data['type']
        
        if cond_type == 'PixelColorCondition':
            return PixelColorCondition(
                x=cond_data['x'],
                y=cond_data['y'],
                target_rgb=tuple(cond_data['target_rgb']),
                tolerance=cond_data.get('tolerance', 10)
            )
        elif cond_type == 'RegionColorCondition':
            return RegionColorCondition(
                region=tuple(cond_data['region']),
                target_rgb=tuple(cond_data['target_rgb']),
                tolerance=cond_data.get('tolerance', 10)
            )
        elif cond_type == 'TimerCondition':
            return TimerCondition(
                interval_seconds=cond_data['interval_seconds'],
                timer_id=cond_data['timer_id']
            )
        elif cond_type == 'KeyPressCondition':
            return KeyPressCondition(
                key_code=cond_data['key_code']
            )
        else:
            raise DeserializationError(f"Unknown condition type: {cond_type}")
    
    @staticmethod
    def _serialize_action(action: Action) -> Dict[str, Any]:
        """Serialize an Action object to dictionary."""
        action_type = type(action).__name__
        
        if isinstance(action, KeyPressAction):
            return {
                'type': action_type,
                'key_code': action.key_code
            }
        elif isinstance(action, MouseClickAction):
            return {
                'type': action_type,
                'x': action.x,
                'y': action.y,
                'button': action.button
            }
        elif isinstance(action, WaitAction):
            return {
                'type': action_type,
                'seconds': action.seconds
            }
        elif isinstance(action, SetStateAction):
            return {
                'type': action_type,
                'key': action.key,
                'value': action.value
            }
        else:
            raise SerializationError(f"Unknown action type: {action_type}")
    
    @staticmethod
    def _deserialize_action(action_data: Dict[str, Any]) -> Action:
        """Deserialize an Action object from dictionary."""
        action_type = action_data['type']
        
        if action_type == 'KeyPressAction':
            return KeyPressAction(key_code=action_data['key_code'])
        elif action_type == 'MouseClickAction':
            return MouseClickAction(
                x=action_data['x'],
                y=action_data['y'],
                button=action_data.get('button', 'left')
            )
        elif action_type == 'WaitAction':
            return WaitAction(seconds=action_data['seconds'])
        elif action_type == 'SetStateAction':
            return SetStateAction(
                key=action_data['key'],
                value=action_data['value']
            )
        else:
            raise DeserializationError(f"Unknown action type: {action_type}")
    
    @staticmethod
    def _deserialize_node(node_data: Dict[str, Any]) -> Node:
        """Deserialize a Node object from dictionary."""
        node_type = node_data['type']
        name = node_data['name']
        position = tuple(node_data['position'])
        
        if node_type == 'InputNode':
            condition = GraphSerializer._deserialize_condition(node_data['condition'])
            node = InputNode(name, condition)
        elif node_type == 'ProcessNode':
            logic_type = node_data.get('logic_type', 'AND')
            node = ProcessNode(name, logic_type)
        elif node_type == 'OutputNode':
            action = GraphSerializer._deserialize_action(node_data['action'])
            node = OutputNode(name, action)
        else:
            raise DeserializationError(f"Unknown node type: {node_type}")
        
        # Restore ID and position
        node.id = node_data['id']
        node.position = position
        
        return node
    
    @staticmethod
    def _is_compatible_version(file_version: str) -> bool:
        """Check if file version is compatible with current serializer."""
        # Simple major version check (e.g., "1.0" compatible with "1.x")
        current_major = SERIALIZATION_VERSION.split('.')[0]
        file_major = file_version.split('.')[0]
        return current_major == file_major
