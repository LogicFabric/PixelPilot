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
    def __init__(self, vision_manager, input_manager, state_manager: StateManager):
        from src.utils.config import get_config
        
        self.vision = vision_manager
        self.input = input_manager
        self.state = state_manager
        self.rules: List[Rule] = []
        self._running = False
        self._paused = False
        
        # Load configuration
        config = get_config()
        self._target_hz = config.get('engine.target_hz', default=30)
        
        self._lock = threading.Lock()

    def add_rule(self, rule: Rule):
        with self._lock:
            self.rules.append(rule)

    def start(self):
        if self._running:
            return
        self._running = True
        self._paused = False
        logger.info("Engine started.")
        self._run_loop()

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
        The main loop. In a real GUI app, this usually runs in a separate thread (managed by the Worker).
        Here we define the logic of a single 'tick' or the continuous loop if run directly.
        For QThread integration, the Worker will likely call a 'process_frame' method or 
        we can have a blocking loop here if run in a thread. 
        Let's implement a blocking loop that checks self._running.
        """
        delay = 1.0 / self._target_hz
        
        while self._running:
            start_time = time.time()
            
            if not self._paused:
                self._process_frame()
                
            elapsed = time.time() - start_time
            sleep_time = max(0, delay - elapsed)
            time.sleep(sleep_time)
            
        logger.info("Engine loop exited.")

    def _process_frame(self):
        # 1. Update Vision (if strategy implies polling, though simple strategies usually pull on demand)
        # self.vision.update() 
        
        # 2. Check Rules
        # We copy list to avoid lock contention issues during iteration if rules are added dynamically
        with self._lock:
            current_rules = list(self.rules)
            
        for rule in current_rules:
            try:
                rule.check_and_execute(self.state, self.vision, self.input)
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")
