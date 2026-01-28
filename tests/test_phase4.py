import unittest
from src.core.graph import Graph, OutputNode, Node, GroupNode
from src.core.rules import Action
from src.utils.settings import get_settings

class MockAction(Action):
    def __init__(self):
        self.call_count = 0
    def execute(self, state, input_provider=None):
        self.call_count += 1

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.settings = get_settings()

    def test_output_node_edge_detection(self):
        """Verify OutputNode only fires on rising edge."""
        action = MockAction()
        node = OutputNode("TestOutput", action)
        
        # 1. First evaluation, trigger False
        node.inputs[0].value = False
        node.evaluate(None, None, None)
        self.assertEqual(action.call_count, 0)
        
        # 2. Trigger True -> Should fire once
        node.inputs[0].value = True
        node.evaluate(None, None, None)
        self.assertEqual(action.call_count, 1)
        
        # 3. Trigger stays True -> Should NOT fire again
        node.evaluate(None, None, None)
        self.assertEqual(action.call_count, 1)
        
        # 4. Trigger False
        node.inputs[0].value = False
        node.evaluate(None, None, None)
        self.assertEqual(action.call_count, 1)
        
        # 5. Trigger True again -> Should fire second time
        node.inputs[0].value = True
        node.evaluate(None, None, None)
        self.assertEqual(action.call_count, 2)

    def test_settings_persistence(self):
        """Verify SettingsManager stores and retrieves values."""
        self.settings.set("test/value", 42)
        val = self.settings.get("test/value")
        self.assertEqual(int(val), 42)
        
        # Test default
        val_default = self.settings.get("nonexistent/key", "default_val")
        self.assertEqual(val_default, "default_val")

    def test_group_boundary_mapping_logic(self):
        """Verify GroupNode can add external ports and map them internally."""
        gn = GroupNode("TestGroup")
        
        # Add external input
        in_p = gn.add_external_input("MyIn")
        self.assertIn("MyIn", [p.name for p in gn.inputs])
        self.assertIn("MyIn", gn._input_mappings)
        
        # Check internal node creation
        int_node_id = gn._input_mappings["MyIn"]
        self.assertTrue(any(n.id == int_node_id for n in gn.sub_graph.nodes))
        
        # Add external output
        out_p = gn.add_external_output("MyOut")
        self.assertIn("MyOut", [p.name for p in gn.outputs])
        self.assertIn("MyOut", gn._output_mappings)

if __name__ == '__main__':
    unittest.main()
