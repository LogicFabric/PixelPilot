#!/usr/bin/env python3
"""
Simple test to verify the engine doesn't stop immediately.
This simulates what happens when the engine is started.
"""
import time
import sys
from unittest.mock import Mock, MagicMock

# Mock the PyQt6 modules
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()

from src.gui.workers import EngineWorker

def test_engine_keep_alive():
    """Test that the worker keeps the thread alive while engine is running."""
    
    # Create a mock engine
    mock_engine = Mock()
    mock_engine.is_running.side_effect = [True, True, False]  # Starts running, stays running, then stops
    mock_engine.start = Mock()  # Non-blocking start
    mock_engine.stop = Mock()
    
    # Create worker
    worker = EngineWorker(mock_engine)
    
    # Track if finished was called
    finished_called = []
    def track_finished():
        finished_called.append(True)
    
    worker.finished.connect(track_finished)
    
    # Run the worker (this would normally be in a QThread)
    print("Starting worker...")
    start_time = time.time()
    
    try:
        worker.run()
    except Exception as e:
        print(f"Worker raised exception: {e}")
    
    elapsed = time.time() - start_time
    
    print(f"Worker finished after {elapsed:.2f} seconds")
    print(f"Engine.is_running() was called: {mock_engine.is_running.called}")
    print(f"Finished signal emitted: {len(finished_called) > 0}")
    
    # The worker should have kept running for at least a short time
    assert elapsed >= 0.2, f"Worker exited too quickly ({elapsed:.2f}s). Expected at least 0.2s"
    print("✓ Test passed: Worker kept thread alive while engine was running")

if __name__ == "__main__":
    test_engine_keep_alive()
