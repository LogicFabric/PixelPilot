from abc import ABC, abstractmethod
from typing import List, Tuple, Any
import time
from .state import StateManager

class Condition(ABC):
    @abstractmethod
    def evaluate(self, state: StateManager, vision_provider=None) -> bool:
        pass

class PixelColorCondition(Condition):
    def __init__(self, x: int, y: int, target_rgb: Tuple[int, int, int], tolerance: int = 10):
        self.x = x
        self.y = y
        self.target_rgb = target_rgb
        self.tolerance = tolerance

    def evaluate(self, state: StateManager, vision_provider=None) -> bool:
        if not vision_provider: return False
        current_color = vision_provider.get_pixel(self.x, self.y)
        if not current_color: return False
        return sum(abs(current_color[i] - self.target_rgb[i]) for i in range(3)) <= self.tolerance

class RegionColorCondition(Condition):
    def __init__(self, region: Tuple[int, int, int, int], target_rgb: Tuple[int, int, int], tolerance: int = 10):
        self.region = region
        self.target_rgb = target_rgb
        self.tolerance = tolerance

    def evaluate(self, state: StateManager, vision_provider=None) -> bool:
        if not vision_provider: return False
        return vision_provider.search_color(self.region, self.target_rgb, self.tolerance) is not None

class TimerCondition(Condition):
    def __init__(self, interval_seconds: float, timer_id: str):
        self.interval = interval_seconds
        self.timer_id = timer_id

    def evaluate(self, state: StateManager, vision_provider=None) -> bool:
        last_time = state.get(f"timer_{self.timer_id}", 0.0)
        return (time.time() - last_time) >= self.interval

    def reset_timer(self, state: StateManager):
        state.set(f"timer_{self.timer_id}", time.time())

class Action(ABC):
    @abstractmethod
    def execute(self, state: StateManager, input_provider=None):
        pass

class KeyPressAction(Action):
    def __init__(self, key_code: str):
        self.key_code = key_code

    def execute(self, state: StateManager, input_provider=None):
        if input_provider: input_provider.press_key(self.key_code)

class MouseClickAction(Action):
    def __init__(self, x: int, y: int, button: str = 'left'):
        self.x = x
        self.y = y
        self.button = button

    def execute(self, state: StateManager, input_provider=None):
        if input_provider: input_provider.click_mouse(self.x, self.y, self.button)

class WaitAction(Action):
    def __init__(self, seconds: float):
        self.seconds = seconds

    def execute(self, state: StateManager, input_provider=None):
        time.sleep(self.seconds)

class SetStateAction(Action):
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value

    def execute(self, state: StateManager, input_provider=None):
        state.set(self.key, self.value)

class LogicEvaluator:
    @staticmethod
    def evaluate_and(conditions: List[Condition], state: StateManager, vision_provider) -> bool:
        return all(cond.evaluate(state, vision_provider) for cond in conditions)

    @staticmethod
    def evaluate_or(conditions: List[Condition], state: StateManager, vision_provider) -> bool:
        return any(cond.evaluate(state, vision_provider) for cond in conditions)

class Rule:
    def __init__(self, name: str, conditions: List[Condition], actions: List[Action], logic_type: str = 'AND'):
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.logic_type = logic_type.upper()

    def check_and_execute(self, state: StateManager, vision_provider, input_provider):
        match = False
        if self.logic_type == 'AND':
            match = LogicEvaluator.evaluate_and(self.conditions, state, vision_provider)
        elif self.logic_type == 'OR':
            match = LogicEvaluator.evaluate_or(self.conditions, state, vision_provider)
        
        if match:
            for action in self.actions:
                action.execute(state, input_provider)
            for cond in self.conditions:
                if isinstance(cond, TimerCondition):
                    cond.reset_timer(state)
