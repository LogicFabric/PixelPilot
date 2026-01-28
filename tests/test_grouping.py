import unittest
import json
from src.core.graph import Graph, ProcessNode, GroupNode, GroupInput, GroupOutput
from src.core.serialization import GraphSerializer
from src.core.state import StateManager

class TestGrouping(unittest.TestCase):
    def setUp(self):
        self.state_mgr = StateManager()
        self.vision_mgr = None
        self.input_mgr = None

    def test_basic_group_execution(self):
        """Verify that GroupNode correctly processes signals through its sub-graph."""
        # Create a group that ANDs two inputs
        group = GroupNode("AND_Group")
        group.add_external_input("In1")
        group.add_external_input("In2")
        group.add_external_output("Out")
        
        # Internal logic
        and_node = ProcessNode("Internal_AND", "AND")
        group.sub_graph.add_node(and_node)
        
        # Find internal mapping nodes
        internal_in1 = next(n for n in group.sub_graph.nodes if n.id == group._input_mappings["In1"])
        internal_in2 = next(n for n in group.sub_graph.nodes if n.id == group._input_mappings["In2"])
        internal_out = next(n for n in group.sub_graph.nodes if n.id == group._output_mappings["Out"])
        
        # Link internal nodes
        group.sub_graph.add_link(internal_in1, "Out", and_node, "In1")
        group.sub_graph.add_link(internal_in2, "Out", and_node, "In2")
        group.sub_graph.add_link(and_node, "Out", internal_out, "In")
        
        # Test 1: Both False (inputs[0] is In1, inputs[1] is In2)
        # Note: GroupNode.get_input_value(i) reads from port.value if no links connected
        group.inputs[0].value = False
        group.inputs[1].value = False
        group.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(group.outputs[0].value)
        
        # Test 2: One True
        group.inputs[0].value = True
        group.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(group.outputs[0].value)
        
        # Test 3: Both True
        group.inputs[1].value = True
        group.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertTrue(group.outputs[0].value)

    def test_recursive_serialization(self):
        """Verify that nested graphs save and load correctly."""
        main_graph = Graph()
        group = GroupNode("NestedGroup")
        group.add_external_input("Trigger")
        main_graph.add_node(group)
        
        # Serialize
        json_str = GraphSerializer.serialize(main_graph)
        data = json.loads(json_str)
        
        # Verify structure
        node_data = data['nodes'][0]
        self.assertEqual(node_data['type'], "GroupNode")
        self.assertIn('sub_graph', node_data)
        self.assertEqual(len(node_data['sub_graph']['nodes']), 1) # Should have GroupInput
        
        # Deserialize
        new_graph = GraphSerializer.deserialize(json_str)
        new_group = new_graph.nodes[0]
        self.assertTrue(isinstance(new_group, GroupNode))
        self.assertEqual(len(new_group.sub_graph.nodes), 1)
        self.assertIn("Trigger", new_group._input_mappings)
        self.assertEqual(len(new_group.inputs), 1)
        self.assertEqual(new_group.inputs[0].name, "Trigger")

if __name__ == '__main__':
    unittest.main()
