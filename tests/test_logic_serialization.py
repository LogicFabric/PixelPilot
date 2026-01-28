import unittest
import json
from src.core.graph import Graph, ProcessNode, TimerNode, ToggleNode
from src.core.serialization import GraphSerializer

class TestLogicSerialization(unittest.TestCase):
    def test_process_node_port_serialization(self):
        graph = Graph()
        node = ProcessNode("DynamicAND", "AND")
        node.add_input_port("In3")
        node.add_input_port("In4")
        graph.add_node(node)
        
        # Serialize
        json_str = GraphSerializer.serialize(graph)
        data = json.loads(json_str)
        
        # Check node data
        node_data = data['nodes'][0]
        self.assertEqual(node_data['name'], "DynamicAND")
        self.assertIn('input_ports', node_data)
        self.assertEqual(len(node_data['input_ports']), 4) # In1, In2, In3, In4
        self.assertIn("In4", node_data['input_ports'])
        
        # Deserialize
        new_graph = GraphSerializer.deserialize(json_str)
        new_node = new_graph.nodes[0]
        self.setIsinstance(new_node, ProcessNode)
        self.assertEqual(len(new_node.inputs), 4)
        self.assertEqual(new_node.inputs[3].name, "In4")

    def test_timer_node_serialization(self):
        graph = Graph()
        node = TimerNode("TestTimer", "BLINK")
        node.delay_time = 2500.0
        node.time_on = 1200.0
        graph.add_node(node)
        
        # Serialize
        json_str = GraphSerializer.serialize(graph)
        data = json.loads(json_str)
        
        # Check node data
        node_data = data['nodes'][0]
        self.assertEqual(node_data['timer_type'], "BLINK")
        self.assertEqual(node_data['delay_time'], 2500.0)
        self.assertEqual(node_data['time_on'], 1200.0)
        
        # Deserialize
        new_graph = GraphSerializer.deserialize(json_str)
        new_node = new_graph.nodes[0]
        self.setIsinstance(new_node, TimerNode)
        self.assertEqual(new_node.timer_type, "BLINK")
        self.assertEqual(new_node.delay_time, 2500.0)
        self.assertEqual(new_node.time_on, 1200.0)

    def setIsinstance(self, obj, cls):
        self.assertTrue(isinstance(obj, cls), f"{obj} is not an instance of {cls}")

if __name__ == '__main__':
    unittest.main()
