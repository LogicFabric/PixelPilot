#!/usr/bin/env python3
"""
Test script to verify the vision system is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.strategies.vision import VisionManager, MockVisionStrategy

def test_mock_strategy():
    """Test that MockVisionStrategy works as expected"""
    print("Testing MockVisionStrategy...")
    
    # Create mock strategy
    mock_strategy = MockVisionStrategy()
    
    # Test get_pixel
    result = mock_strategy.get_pixel(100, 200)
    print(f"get_pixel(100, 200) = {result}")
    assert result == (0, 0, 0), f"Expected (0, 0, 0), got {result}"
    
    # Test search_color
    result = mock_strategy.search_color((0, 0, 100, 100), (255, 255, 255))
    print(f"search_color((0, 0, 100, 100), (255, 255, 255)) = {result}")
    assert result is None, f"Expected None, got {result}"
    
    print("MockVisionStrategy tests passed!")

def test_vision_manager():
    """Test that VisionManager can initialize with mock strategy"""
    print("\nTesting VisionManager with mock strategy...")
    
    # Test with mock=True
    vm = VisionManager(use_mock=True)
    assert vm.strategy is not None, "Should have a strategy"
    assert isinstance(vm.strategy, MockVisionStrategy), f"Should be MockVisionStrategy, got {type(vm.strategy)}"
    
    # Test that it works
    result = vm.get_pixel(0, 0)
    print(f"VisionManager get_pixel(0, 0) = {result}")
    assert result == (0, 0, 0), f"Expected (0, 0, 0), got {result}"
    
    print("VisionManager tests passed!")

if __name__ == "__main__":
    test_mock_strategy()
    test_vision_manager()
    print("\nAll tests passed!")