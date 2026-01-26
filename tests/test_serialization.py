"""Tests for graph serialization functionality."""

import unittest
import json
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.graph import Graph, InputNode, ProcessNode, OutputNode
from core.rules import PixelColorCondition, KeyPressAction
from core.serialization import GraphSerializer
from core.exceptions import DeserializationError, InvalidFileFormatError


class TestGraphSerialization(unittest.TestCase):
    """Test suite for graph serialization/deserialization."""
    
    def setUp(self):
        """Set up test graph."""
        self.graph = Graph()
        
        # Create test nodes
        cond = PixelColorCondition(100, 200, (255, 128, 0), tolerance=15)
        input_node = InputNode("Test Input", cond)
        input_node.position = (50, 100)
        
        process_node = ProcessNode("Test AND", "AND")
        process_node.position = (250, 100)
        
        action = KeyPressAction("space")
        output_node = OutputNode("Test Output", action)
        output_node.position = (450, 100)
        
        # Add to graph
        self.graph.add_node(input_node)
        self.graph.add_node(process_node)
        self.graph.add_node(output_node)
        
        # Add links
        self.graph.add_link(input_node, "Out", process_node, "In1")
        self.graph.add_link(process_node, "Out", output_node, "Trig")
        
        self.input_node = input_node
        self.process_node = process_node
        self.output_node = output_node
    
    def test_serialize_to_string(self):
        """Test serialization to JSON string."""
        json_str = GraphSerializer.serialize(self.graph)
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        
        # Check structure
        self.assertEqual(data['type'], 'PixelPilot_Graph')
        self.assertEqual(len(data['nodes']), 3)
        self.assertEqual(len(data['links']), 2)
        
        # Verify node data
        input_data = next(n for n in data['nodes'] if n['type'] == 'InputNode')
        self.assertEqual(input_data['name'], 'Test Input')
        self.assertEqual(input_data['position'], [50, 100])
        self.assertEqual(input_data['condition']['type'], 'PixelColorCondition')
        self.assertEqual(input_data['condition']['x'], 100)
        self.assertEqual(input_data['condition']['y'], 200)
        self.assertEqual(input_data['condition']['target_rgb'], [255, 128, 0])
        self.assertEqual(input_data['condition']['tolerance'], 15)
    
    def test_deserialize_from_string(self):
        """Test deserialization from JSON string."""
        json_str = GraphSerializer.serialize(self.graph)
        loaded_graph = GraphSerializer.deserialize(json_str)
        
        # Verify structure
        self.assertEqual(len(loaded_graph.nodes), 3)
        self.assertEqual(len(loaded_graph.links), 2)
        
        # Find loaded nodes
        input_node = next(n for n in loaded_graph.nodes if isinstance(n, InputNode))
        process_node = next(n for n in loaded_graph.nodes if isinstance(n, ProcessNode))
        output_node = next(n for n in loaded_graph.nodes if isinstance(n, OutputNode))
        
        # Verify input node
        self.assertEqual(input_node.name, 'Test Input')
        self.assertEqual(input_node.position, (50, 100))
        self.assertIsInstance(input_node.condition, PixelColorCondition)
        self.assertEqual(input_node.condition.x, 100)
        self.assertEqual(input_node.condition.y, 200)
        self.assertEqual(input_node.condition.target_rgb, (255, 128, 0))
        self.assertEqual(input_node.condition.tolerance, 15)
        
        # Verify process node
        self.assertEqual(process_node.name, 'Test AND')
        self.assertEqual(process_node.logic_type, 'AND')
        
        # Verify output node
        self.assertEqual(output_node.name, 'Test Output')
        self.assertIsInstance(output_node.action, KeyPressAction)
        self.assertEqual(output_node.action.key_code, 'space')
    
    def test_save_and_load_file(self):
        """Test saving to and loading from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pp', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save
            GraphSerializer.save_to_file(self.graph, temp_file)
            self.assertTrue(os.path.exists(temp_file))
            
            # Load
            loaded_graph = GraphSerializer.load_from_file(temp_file)
            
            # Verify
            self.assertEqual(len(loaded_graph.nodes), 3)
            self.assertEqual(len(loaded_graph.links), 2)
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_invalid_json(self):
        """Test deserialization with invalid JSON."""
        with self.assertRaises(DeserializationError):
            GraphSerializer.deserialize("not valid json {")
    
    def test_invalid_file_type(self):
        """Test deserialization with wrong file type."""
        invalid_data = json.dumps({'type': 'SomethingElse', 'data': []})
        
        with self.assertRaises(InvalidFileFormatError):
            GraphSerializer.deserialize(invalid_data)
    
    def test_preserve_node_ids(self):
        """Test that node IDs are preserved across serialization."""
        original_ids = {node.id for node in self.graph.nodes}
        
        json_str = GraphSerializer.serialize(self.graph)
        loaded_graph = GraphSerializer.deserialize(json_str)
        
        loaded_ids = {node.id for node in loaded_graph.nodes}
        
        self.assertEqual(original_ids, loaded_ids)


if __name__ == '__main__':
    unittest.main()
