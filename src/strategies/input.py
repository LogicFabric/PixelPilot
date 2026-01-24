import platform
import logging
import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Set, Callable, List

logger = logging.getLogger(__name__)

# Try importing dependencies
try:
    import pynput
    from pynput import keyboard as pynput_kb
    from pynput.keyboard import Controller as KeyboardController, Key
    from pynput.mouse import Controller as MouseController, Button
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    import evdev
    from evdev import UInput, ecodes as e, InputDevice, list_devices
    import select
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False

class InputStrategy(ABC):
    def __init__(self):
        self.pressed_keys: Set[str] = set()
        self.listeners: List[Callable[[str, bool], None]] = [] # callbacks(key_code, is_pressed)

    @abstractmethod
    def press_key(self, key_code: str):
        pass
    
    @abstractmethod
    def click_mouse(self, x: int, y: int, button: str = 'left'):
        pass
    
    @abstractmethod
    def move_mouse(self, x: int, y: int):
        pass

    @abstractmethod
    def start_listening(self):
        """Start a background thread/process to listen for global inputs."""
        pass

    def add_listener(self, callback: Callable[[str, bool], None]):
        """Callback format: func(key_code_str, is_pressed_bool)"""
        self.listeners.append(callback)

    def is_key_pressed(self, key_code: str) -> bool:
        return key_code.lower() in self.pressed_keys

    def _notify_listeners(self, key_code: str, pressed: bool):
        key_code = key_code.lower()
        if pressed:
            self.pressed_keys.add(key_code)
        else:
            self.pressed_keys.discard(key_code)
            
        for cb in self.listeners:
            try:
                cb(key_code, pressed)
            except Exception as err:
                logger.error(f"Listener callback error: {err}")

class PynputStrategy(InputStrategy):
    """Fallback input strategy using pynput (Cross-platform)."""
    def __init__(self):
        super().__init__()
        if not HAS_PYNPUT:
            raise ImportError("pynput is not installed")
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        logger.info("Initialized Pynput Strategy")
        self._listener_thread = None

    def press_key(self, key_code: str):
        try:
            if hasattr(Key, key_code):
                key = getattr(Key, key_code)
            else:
                key = key_code
            self.keyboard.press(key)
            self.keyboard.release(key)
        except Exception as err:
            logger.error(f"Pynput press_key failed: {err}")

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        self.move_mouse(x, y)
        btn = Button.left
        if button == 'right': btn = Button.right
        elif button == 'middle': btn = Button.middle
        self.mouse.click(btn, 1)

    def move_mouse(self, x: int, y: int):
        self.mouse.position = (x, y)

    def start_listening(self):
        if self._listener_thread: return
        
        def on_press(key):
            k = self._key_to_str(key)
            self._notify_listeners(k, True)

        def on_release(key):
            k = self._key_to_str(key)
            self._notify_listeners(k, False)
        
        self.listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        logger.info("Pynput Listener started")

    def _key_to_str(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            return str(key).replace('Key.', '')
        except:
            return str(key)

class EvdevStrategy(InputStrategy):
    """Primary Linux strategy using uinput and raw device reading."""
    def __init__(self):
        super().__init__()
        if not HAS_EVDEV:
            raise ImportError("evdev is not installed")
        
        try:
            self.ui = UInput()
            logger.info("Initialized Evdev Strategy (UInput)")
        except PermissionError:
            raise PermissionError("No permission to access /dev/uinput")
        except Exception as err:
            raise RuntimeError(f"Failed to create UInput device: {err}")

        self.key_map = {
            'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, # ... (would need full map)
            'space': e.KEY_SPACE, 'enter': e.KEY_ENTER, 'esc': e.KEY_ESC,
        }
        
        self._listening = False
        self._thread = None

    def press_key(self, key_code: str):
        # Naive mapping for now. Real implementation needs a robust map.
        # Fallback: try to find by name in ecodes
        code = self.key_map.get(key_code.lower())
        if not code:
            # Try dynamic lookup
            attr = f"KEY_{key_code.upper()}"
            if hasattr(e, attr):
                code = getattr(e, attr)
        
        if code:
            self.ui.write(e.EV_KEY, code, 1)
            self.ui.write(e.EV_KEY, code, 0)
            self.ui.syn()
        else:
            logger.warning(f"Evdev: Unknown key code {key_code}")

    def move_mouse(self, x: int, y: int):
        # Stub
        pass

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        # Stub for click
        btn = e.BTN_LEFT
        if button == 'right': btn = e.BTN_RIGHT
        self.ui.write(e.EV_KEY, btn, 1)
        self.ui.write(e.EV_KEY, btn, 0)
        self.ui.syn()

    def start_listening(self):
        if self._listening: return
        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Evdev Listener started (scanning devices...)")

    def _listen_loop(self):
        # 1. Find keyboards
        devices = []
        try:
            for path in list_devices():
                try:
                    dev = InputDevice(path)
                    # Simple heuristic: has keys
                    if e.EV_KEY in dev.capabilities():
                        devices.append(dev)
                        logger.debug(f"Found input device: {dev.name}")
                except:
                    pass
        except Exception as err:
            logger.error(f"Error scanning devices: {err}")
            return

        if not devices:
            logger.warning("No input devices found for listener.")
            return

        # 2. Select Loop
        # Needs to be robust to disconnects, but for MVP simple select
        fds = {dev.fd: dev for dev in devices}
        
        while self._listening:
            try:
                r, w, x = select.select(fds, [], [], 1.0)
                for fd in r:
                    dev = fds[fd]
                    for event in dev.read():
                        if event.type == e.EV_KEY:
                            key_evt = evdev.categorize(event)
                            # key_evt.keycode is either string or list of strings
                            k = key_evt.keycode
                            if isinstance(k, list): k = k[0]
                            k = str(k).replace("KEY_", "").lower()
                            
                            pressed = (event.value == 1) # 1=down, 0=up, 2=hold
                            if event.value != 2: # Ignore hold repeats for trigger logic usually
                                self._notify_listeners(k, pressed)
            except Exception as outer_err:
                 # Device might have disconnected
                 logger.error(f"Listener loop error: {outer_err}")
                 break

class InputManager:
    """Auto-detects and manages the best input strategy."""
    def __init__(self):
        self.strategy: Optional[InputStrategy] = None
        self._init_strategy()

    def _init_strategy(self):
        # 1. Try Evdev
        if platform.system() == 'Linux':
            try:
                self.strategy = EvdevStrategy()
            except Exception as e:
                logger.warning(f"Evdev strategy failed ({e}), falling back...")
        
        # 2. Try Pynput
        if not self.strategy:
            try:
                self.strategy = PynputStrategy()
            except Exception as e:
                logger.error(f"Pynput strategy failed: {e}")
                self.strategy = None
        
        if self.strategy:
            # Auto-start listener for analyzer/conditions
            try:
                self.strategy.start_listening()
            except Exception as e:
                logger.error(f"Failed to start input listener: {e}")

    def press_key(self, key_code: str):
        if self.strategy: self.strategy.press_key(key_code)

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        if self.strategy: self.strategy.click_mouse(x, y, button)
            
    def move_mouse(self, x: int, y: int):
        if self.strategy: self.strategy.move_mouse(x, y)
    
    def is_key_pressed(self, key_code: str) -> bool:
        if self.strategy: return self.strategy.is_key_pressed(key_code)
        return False
        
    def add_listener(self, cb):
        if self.strategy: self.strategy.add_listener(cb)
