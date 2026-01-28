import unittest
import time
from src.core.graph import Graph, ProcessNode, TimerNode, ToggleNode
from src.core.state import StateManager

class TestLogicBlocks(unittest.TestCase):
    def setUp(self):
        self.state_mgr = StateManager()
        self.vision_mgr = None # Mocked
        self.input_mgr = None # Mocked

    def test_dynamic_process_node_and(self):
        node = ProcessNode("AND_Gate", "AND")
        node.add_input_port("In3")
        
        # All inputs False by default
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)
        
        # Set all to True
        node.inputs[0].value = True
        node.inputs[1].value = True
        node.inputs[2].value = True
        
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertTrue(node.out_port.value)
        
        # Set one to False
        node.inputs[2].value = False
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)

    def test_ton_timer(self):
        node = TimerNode("TON_Timer", "TON")
        node.delay_time = 100.0 # 100ms
        
        # Initial evaluate to set last_tick_time
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)
        
        # Set trigger
        node.in_port.value = True
        
        # Wait 50ms (not enough)
        time.sleep(0.05)
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)
        
        # Wait another 100ms (enough)
        time.sleep(0.1)
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertTrue(node.out_port.value)
        
        # Drop trigger, should reset
        node.in_port.value = False
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)

    def test_toggle_flip_flop(self):
        node = ToggleNode("FlipFlop")
        
        # Initial evaluate
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)
        
        # Trigger (Rising Edge)
        node.trig_port.value = True
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertTrue(node.out_port.value)
        
        # Keep trigger True, should stay True (not toggling again)
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertTrue(node.out_port.value)
        
        # Trigger False
        node.trig_port.value = False
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertTrue(node.out_port.value)
        
        # Trigger True again (Rising Edge)
        node.trig_port.value = True
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)
        
        # Reset
        node.trig_port.value = True # Should stay False if reset is active
        node.state = True # Manually set state to test reset
        node.reset_port.value = True
        node.evaluate(self.state_mgr, self.vision_mgr, self.input_mgr)
        self.assertFalse(node.out_port.value)

if __name__ == '__main__':
    unittest.main()
