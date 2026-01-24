import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.rules import Rule, PixelColorCondition, StateManager, KeyPressAction

class MockVision:
    def get_pixel(self, x, y):
        # Always return white
        return (255, 255, 255)

class MockInput:
    def __init__(self):
        self.pressed = []
    def press_key(self, key):
        self.pressed.append(key)

class TestRules(unittest.TestCase):
    def test_basic_rule(self):
        state = StateManager()
        vision = MockVision()
        inp = MockInput()
        
        # Condition: Pixel at 10,10 must be white (255,255,255)
        cond = PixelColorCondition(10, 10, (255, 255, 255))
        # Action: Press 'A'
        act = KeyPressAction('A')
        
        rule = Rule("TestRule", [cond], [act])
        
        # Execute
        rule.check_and_execute(state, vision, inp)
        
        self.assertIn('A', inp.pressed)

if __name__ == '__main__':
    unittest.main()
