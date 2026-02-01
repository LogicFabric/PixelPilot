"""Tests for graph execution and topological sort."""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.graph import Graph, InputNode, ProcessNode, OutputNode
from core.rules import PixelColorCondition, KeyPressAction
from core.state import StateManager
from core.exceptions import CyclicGraphError


class MockVision:
    """Mock vision provider for testing."""
    def get_pixel(self, x, y):
        return (255, 255, 255)
    
    def search_color(self, region, target, tolerance=10):
        return (region[0] + 10, region[1] + 10)


class MockInput:
    """Mock input provider for testing."""
    def __init__(self):
        self.pressed_keys = []
    
    def press_key(self, key):
        self.pressed_keys.append(key)
    
    def click_mouse(self, x, y, button='left'):
        pass
    
    def move_mouse(self, x, y):
        pass


class TestGraphExecution(unittest.TestCase):
    """Test suite for graph execution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state = StateManager()
        self.vision = MockVision()
        self.input = MockInput()
    
    def test_simple_chain_execution(self):
        """Test execution of simple input -> process -> output chain."""
        graph = Graph()
        
        # Create nodes
        cond = PixelColorCondition(10, 10, (255, 255, 255))
        input_node = InputNode("Input", cond)
        
        process_node = ProcessNode("AND", "AND")
        
        action = KeyPressAction("space")
        output_node = OutputNode("Output", action)
        
        # Add to graph
        graph.add_node(input_node)
        graph.add_node(process_node)
        graph.add_node(output_node)
        
        # Link: Input -> Process.In1, Process -> Output
        graph.add_link(input_node, "Out", process_node, "In1")
        graph.add_link(process_node, "Out", output_node, "Trig")
        
        # Execute
        graph.execute(self.state, self.vision, self.input)
        
        # Input evaluates to True (white pixel)
        # Process gets one True input (other is False) -> AND = False
        # Output should not trigger
        self.assertEqual(len(self.input.pressed_keys), 0)
    
    def test_topological_sort_order(self):
        """Test that topological sort produces correct execution order."""
        graph = Graph()
        
        # Create diamond pattern:
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        
        nodeA = InputNode("A", PixelColorCondition(0, 0, (255, 255, 255)))
        nodeB = ProcessNode("B", "NOT")
        nodeC = ProcessNode("C", "NOT")
        nodeD = OutputNode("D", KeyPressAction("x"))
        
        graph.add_node(nodeA)
        graph.add_node(nodeB)
        graph.add_node(nodeC)
        graph.add_node(nodeD)
        
        graph.add_link(nodeA, "Out", nodeB, "In1")
        graph.add_link(nodeA, "Out", nodeC, "In1")
        graph.add_link(nodeB, "Out", nodeD, "Trig")
        graph.add_link(nodeC, "Out", nodeD, "Trig")
        
        # Get topological order
        sorted_nodes = graph._topological_sort()
        
        # A must come before B and C
        idx_A = sorted_nodes.index(nodeA)
        idx_B = sorted_nodes.index(nodeB)
        idx_C = sorted_nodes.index(nodeC)
        idx_D = sorted_nodes.index(nodeD)
        
        self.assertLess(idx_A, idx_B)
        self.assertLess(idx_A, idx_C)
        self.assertLess(idx_B, idx_D)
        self.assertLess(idx_C, idx_D)
    
    def test_cycle_detection(self):
        """Test that cyclic graphs are detected."""
        graph = Graph()
        
        # Create cycle: A -> B -> C -> A
        nodeA = ProcessNode("A", "AND")
        nodeB = ProcessNode("B", "AND")
        nodeC = ProcessNode("C", "AND")
        
        graph.add_node(nodeA)
        graph.add_node(nodeB)
        graph.add_node(nodeC)
        
        graph.add_link(nodeA, "Out", nodeB, "In1")
        graph.add_link(nodeB, "Out", nodeC, "In1")
        graph.add_link(nodeC, "Out", nodeA, "In1")
        
        # Should raise CyclicGraphError
        with self.assertRaises(CyclicGraphError):
            graph._topological_sort()
    
    def test_caching_behavior(self):
        """Test that topological sort is cached and reused."""
        graph = Graph()
        
        node1 = InputNode("Input", PixelColorCondition(0, 0, (255, 255, 255)))
        node2 = OutputNode("Output", KeyPressAction("a"))
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_link(node1, "Out", node2, "Trig")
        
        # First execution should cache
        graph.execute(self.state, self.vision, self.input)
        first_sorted = graph._sorted_nodes
        
        # Second execution should reuse cache
        graph.execute(self.state, self.vision, self.input)
        second_sorted = graph._sorted_nodes
        
        self.assertIs(first_sorted, second_sorted)
        
        # Adding node should invalidate cache
        node3 = ProcessNode("Process", "AND")
        graph.add_node(node3)
        
        self.assertTrue(graph._needs_resort)


if __name__ == '__main__':
    unittest.main()
