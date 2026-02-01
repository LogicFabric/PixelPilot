import sys
import os
import unittest
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from strategies.input import InputManager, PynputStrategy

class TestInput(unittest.TestCase):
    def test_init(self):
        """Test detection logic."""
        im = InputManager()
        self.assertIsNotNone(im)
        if im.strategy:
            print(f"Input Strategy detected: {type(im.strategy).__name__}")
        
    def test_pynput_explicit(self):
        """Test Pynput specifically (safe on most envs)."""
        try:
            ps = PynputStrategy()
            # Just move mouse slightly to test no crash
            ps.move_mouse(10, 10)
        except ImportError:
            print("Pynput not installed, skipping test")

if __name__ == '__main__':
    unittest.main()
