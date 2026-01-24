import platform
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

# Try importing dependencies
try:
    import pynput
    from pynput.keyboard import Controller as KeyboardController, Key
    from pynput.mouse import Controller as MouseController, Button
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    import evdev
    from evdev import UInput, ecodes as e
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False

class InputStrategy(ABC):
    @abstractmethod
    def press_key(self, key_code: str):
        pass
    
    @abstractmethod
    def click_mouse(self, x: int, y: int, button: str = 'left'):
        pass
    
    @abstractmethod
    def move_mouse(self, x: int, y: int):
        pass

class PynputStrategy(InputStrategy):
    """Fallback input strategy using pynput (Cross-platform)."""
    def __init__(self):
        if not HAS_PYNPUT:
            raise ImportError("pynput is not installed")
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        logger.info("Initialized Pynput Strategy")

    def press_key(self, key_code: str):
        # Handle special keys if needed, for now assuming char or simple string
        # simplistic mapping approach
        try:
            # Check if it's a special key attribute in pynput.keyboard.Key
            if hasattr(Key, key_code):
                key = getattr(Key, key_code)
            else:
                key = key_code
            
            self.keyboard.press(key)
            self.keyboard.release(key)
        except Exception as err:
            logger.error(f"Pynput press_key failed: {err}")

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        # Move first
        self.move_mouse(x, y)
        btn = Button.left
        if button == 'right': btn = Button.right
        elif button == 'middle': btn = Button.middle
        
        self.mouse.click(btn, 1)

    def move_mouse(self, x: int, y: int):
        self.mouse.position = (x, y)

class EvdevStrategy(InputStrategy):
    """Primary Linux strategy using uinput (requires permissions)."""
    def __init__(self):
        if not HAS_EVDEV:
            raise ImportError("evdev is not installed")
        
        # Mapping for capability checks could be added here
        try:
            self.ui = UInput()
            logger.info("Initialized Evdev Strategy (UInput)")
        except PermissionError:
            raise PermissionError("No permission to access /dev/uinput")
        except Exception as err:
            raise RuntimeError(f"Failed to create UInput device: {err}")

        # Simple mapping from string to evdev ecodes
        self.key_map = {
            'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, # ... expand as needed
            'enter': e.KEY_ENTER, 'space': e.KEY_SPACE, 'esc': e.KEY_ESC,
            # Add more keys as needed
        }

    def press_key(self, key_code: str):
        # Convert key_code to ecode
        code = self.key_map.get(key_code.lower())
        if code:
            self.ui.write(e.EV_KEY, code, 1) # Down
            self.ui.write(e.EV_KEY, code, 0) # Up
            self.ui.syn()
        else:
            logger.warning(f"Evdev: Unknown key code {key_code}")

    def move_mouse(self, x: int, y: int):
        # UInput generic relative mouse usually; absolute requires configuring capabilities
        # For simplicity in this demo, automating absolute mouse via uinput is tricky 
        # without proper ABS setup. 
        # Fallback to pure relative or setup ABS axis.
        # Given complexity, often people use pynput for mouse on linux too unless restricted.
        # Let's try ABS if initialized, else warn.
        logger.warning("Evdev absolute mouse move not fully implemented in this stub.")
        pass

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        self.move_mouse(x, y)
        btn = e.BTN_LEFT
        if button == 'right': btn = e.BTN_RIGHT
        
        self.ui.write(e.EV_KEY, btn, 1)
        self.ui.write(e.EV_KEY, btn, 0)
        self.ui.syn()

class InputManager:
    """Auto-detects and manages the best input strategy."""
    def __init__(self):
        self.strategy: Optional[InputStrategy] = None
        self._init_strategy()

    def _init_strategy(self):
        # 1. Try Evdev (Linux Preferred)
        if platform.system() == 'Linux':
            try:
                self.strategy = EvdevStrategy()
            except (PermissionError, RuntimeError, ImportError) as e:
                logger.warning(f"Evdev strategy failed ({e}), falling back...")
        
        # 2. Try Pynput (Fallback)
        if not self.strategy:
            try:
                self.strategy = PynputStrategy()
            except Exception as e:
                logger.error(f"Pynput strategy failed: {e}")
                self.strategy = None

    def press_key(self, key_code: str):
        if self.strategy:
            self.strategy.press_key(key_code)

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        if self.strategy:
            self.strategy.click_mouse(x, y, button)
            
    def move_mouse(self, x: int, y: int):
        if self.strategy:
            self.strategy.move_mouse(x, y)
