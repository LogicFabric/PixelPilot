import time
import logging
import threading
from typing import List, Optional

from .rules import Rule
from .state import StateManager

logger = logging.getLogger(__name__)

class AutomationEngine:
    """
    Runs the main automation loop.
    
    Executes graph at configurable frequency (default 30 Hz),
    iterating through all nodes and evaluating them in topological order.
    
    Attributes:
        vision: Vision manager for screen capture
        input: Input manager for keyboard/mouse control  
        state: State manager for shared variables
        rules: List of automation rules (legacy, use graph instead)
        _running: Whether engine is currently running
        _paused: Whether engine is paused
        _target_hz: Target execution frequency
        _lock: Thread lock for rule list protection
    """
    def __init__(self, vision_manager, input_manager, state_manager: StateManager, config=None):
        self.vision = vision_manager
        self.input = input_manager
        self.state = state_manager
        self.rules: List[Rule] = []
        self.graph = None # Primary FBD graph
        self._running = False
        self._paused = False
        
        # Load configuration via Dependency Injection
        self._config = config if config is not None else {}
        # Support both Config object and dictionary
        if hasattr(self._config, 'get'):
            self._target_hz = self._config.get('engine.target_hz', 30)
        else:
            self._target_hz = self._config.get('engine.target_hz', 30)
        
        self._lock = threading.Lock()

    def set_graph(self, graph):
        """Set the active graph for execution."""
        with self._lock:
            self.graph = graph

    def add_rule(self, rule: Rule):
        with self._lock:
            self.rules.append(rule)

    def start(self, blocking=False):
        """
        Start the engine.
        
        Args:
            blocking: If True, blocks until engine stops. Otherwise starts in background thread.
        """
        if self._running:
            return
            
        self._running = True
        self._paused = False
        logger.info(f"Engine started (Target: {self._target_hz} Hz).")
        
        if blocking:
            self._run_loop()
        else:
            self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._loop_thread.start()
            
        logger.info(f"Engine started (Target: {self._target_hz} Hz).")

    def stop(self):
        self._running = False
        logger.info("Engine stopping...")

    def pause(self):
        self._paused = True
        logger.info("Engine paused.")

    def resume(self):
        self._paused = False
        logger.info("Engine resumed.")

    def is_running(self):
        return self._running

    def _run_loop(self):
        """
        Main execution loop with high-precision drift compensation and error trapping.
        """
        frame_duration = 1.0 / self._target_hz
        next_frame_time = time.perf_counter()
        
        logger.info(f"Precision timing loop active at {self._target_hz}Hz.")
        
        try:
            while self._running:
                if not self._paused:
                    try:
                        self._process_frame()
                    except Exception as e:
                        logger.error(f"Fatal error in _process_frame: {e}", exc_info=True)
                        # We don't stop the engine on a single frame error, unless requested
                    
                # Calculate next frame boundary
                next_frame_time += frame_duration
                
                # Compensation logic
                now = time.perf_counter()
                sleep_time = next_frame_time - now
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -frame_duration:
                    next_frame_time = now
                    logger.warning("Engine frame drop detected: processing took too long.")
        except Exception as e:
            logger.critical(f"Engine thread crashed: {e}", exc_info=True)
        finally:
            self._running = False
            logger.info("Engine loop exited.")

    def _process_frame(self):
        with self._lock:
            graph = self.graph
            current_rules = list(self.rules)
            
        # 1. Execute Graph (Primary)
        if graph:
            try:
                graph.execute(self.state, self.vision, self.input)
            except Exception as e:
                logger.error(f"Error executing graph: {e}")
                
        # 2. Check Rules (Legacy/Fallback)
        for rule in current_rules:
            try:
                rule.check_and_execute(self.state, self.vision, self.input)
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")

