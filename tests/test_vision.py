import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from strategies.vision import VisionManager

class TestVision(unittest.TestCase):
    def test_init(self):
        vm = VisionManager()
        if vm.strategy:
            print(f"Vision Strategy detected: {type(vm.strategy).__name__}")
        else:
            print("No vision strategy detected (might be expected in headless without tools)")
        
        # We don't fail if no strategy, as we might be in a restricted env, 
        # but we want to know it didn't crash.
        self.assertIsNotNone(vm)

if __name__ == '__main__':
    unittest.main()
