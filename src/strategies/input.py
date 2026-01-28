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
    """
    Primary Linux strategy using uinput and raw device reading.
    
    Provides low-level control over keyboard and mouse through evdev/uinput.
    Requires proper permissions (access to /dev/uinput and /dev/input/*).
    
    Attributes:
        ui: UInput virtual device for simulating events
        key_map: Mapping of common key names to evdev codes
        screen_width: Screen width for absolute mouse positioning
        screen_height: Screen height for absolute mouse positioning
    """
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        super().__init__()
        if not HAS_EVDEV:
            from ..core.exceptions import InputStrategyError
            raise InputStrategyError("evdev module is not installed")
        
        # Screen dimensions for mouse positioning
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        try:
            # Create UInput device with simplified capabilities
            # Note: Absolute positioning requires special setup, using basic capabilities
            cap = {
                e.EV_KEY: [
                    # Mouse buttons
                    e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE,
                    # Common keyboard keys
                    e.KEY_A, e.KEY_B, e.KEY_C, e.KEY_D, e.KEY_E, e.KEY_F,
                    e.KEY_G, e.KEY_H, e.KEY_I, e.KEY_J, e.KEY_K, e.KEY_L,
                    e.KEY_M, e.KEY_N, e.KEY_O, e.KEY_P, e.KEY_Q, e.KEY_R,
                    e.KEY_S, e.KEY_T, e.KEY_U, e.KEY_V, e.KEY_W, e.KEY_X,
                    e.KEY_Y, e.KEY_Z,
                    e.KEY_SPACE, e.KEY_ENTER, e.KEY_ESC, e.KEY_TAB,
                    e.KEY_BACKSPACE, e.KEY_DELETE,
                    e.KEY_LEFTSHIFT, e.KEY_RIGHTSHIFT,
                    e.KEY_LEFTCTRL, e.KEY_RIGHTCTRL,
                    e.KEY_LEFTALT, e.KEY_RIGHTALT,
                ],
                # Using relative mouse movement instead of absolute (more compatible)
                e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL]
            }
            
            self.ui = UInput(cap, name='pixelpilot-virtual-input')
            logger.info(f"Initialized Evdev Strategy (relative mouse mode)")
            
        except PermissionError:
            from ..core.exceptions import PermissionError as PPPermissionError
            raise PPPermissionError(
                "No permission to access /dev/uinput. "
                "Run: sudo usermod -a -G input $USER && sudo modprobe uinput"
            )
        except Exception as err:
            from ..core.exceptions import InputStrategyError
            raise InputStrategyError(f"Failed to create UInput device: {err}")

        self.key_map = {
            'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D,
            'e': e.KEY_E, 'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H,
            'i': e.KEY_I, 'j': e.KEY_J, 'k': e.KEY_K, 'l': e.KEY_L,
            'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O, 'p': e.KEY_P,
            'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
            'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X,
            'y': e.KEY_Y, 'z': e.KEY_Z,
            'space': e.KEY_SPACE, 'enter': e.KEY_ENTER, 'esc': e.KEY_ESC,
            'tab': e.KEY_TAB, 'backspace': e.KEY_BACKSPACE, 'delete': e.KEY_DELETE,
            'shift': e.KEY_LEFTSHIFT, 'ctrl': e.KEY_LEFTCTRL, 'alt': e.KEY_LEFTALT,
        }
        
        self._listening = False
        self._thread = None

    def press_key(self, key_code: str):
        """
        Simulate a key press.
        
        Args:
            key_code: Key to press (e.g., 'a', 'space', 'enter')
        """
        code = self.key_map.get(key_code.lower())
        if not code:
            # Try dynamic lookup
            attr = f"KEY_{key_code.upper()}"
            if hasattr(e, attr):
                code = getattr(e, attr)
        
        if code:
            self.ui.write(e.EV_KEY, code, 1)  # Key down
            self.ui.write(e.EV_KEY, code, 0)  # Key up
            self.ui.syn()
        else:
            logger.warning(f"Evdev: Unknown key code '{key_code}'")

    def move_mouse(self, x: int, y: int):
        """
        Move mouse to position using relative movement.
        
        Note: Evdev doesn't easily support absolute positioning without
        additional setup. This uses pynput fallback for mouse positioning.
        Keyboard input still uses evdev for better compatibility.
        
        Args:
            x: X coordinate (0 to screen_width)
            y: Y coordinate (0 to screen_height)
        """
        # For mouse positioning, we need to fall back to another method
        # as relative positioning requires knowing current position
        logger.warning("Evdev mouse positioning not fully supported, use pynput for mouse")
        pass

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        """
        Click mouse at position.
        
        Note: Mouse positioning is limited in evdev. This only sends the click event.
        You may need to use pynput strategy for full mouse control.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button ('left', 'right', 'middle')
        """
        # Just click without moving (movement not reliably supported)
        btn = e.BTN_LEFT
        if button == 'right':
            btn = e.BTN_RIGHT
        elif button == 'middle':
            btn = e.BTN_MIDDLE
            
        self.ui.write(e.EV_KEY, btn, 1)  # Button down
        self.ui.write(e.EV_KEY, btn, 0)  # Button up
        self.ui.syn()

    def start_listening(self) -> bool:
        """Starts listening in a background thread. Returns True if devices were found."""
        if self._listening: return True
        
        # Check if we have devices before starting
        devices = self._get_kb_devices()
        if not devices:
            logger.warning("Evdev: No input devices found to listen to.")
            return False
            
        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, args=(devices,), daemon=True)
        self._thread.start()
        logger.info(f"Evdev Listener started (Monitoring {len(devices)} devices).")
        return True

    def _listen_loop(self, devices=None):
        if devices is None:
            devices = self._get_kb_devices()

        if not devices:
            logger.warning("No input devices found for listener.")
            self._listening = False
            return

        # 2. Select Loop
        # Needs to be robust to disconnects, but for MVP simple select
        fds = {dev.fd: dev for dev in devices}
        
        while self._listening:
            try:
                # Re-scan if no devices or just periodically
                if not devices:
                    devices = self._get_kb_devices()
                    fds = {dev.fd: dev for dev in devices}
                    if not devices:
                        time.sleep(2)
                        continue

                r, w, x = select.select(fds, [], [], 1.0)
                for fd in r:
                    dev = fds[fd]
                    try:
                        for event in dev.read():
                            if event.type == e.EV_KEY:
                                key_evt = evdev.categorize(event)
                                k = key_evt.keycode
                                if isinstance(k, list): k = k[0]
                                k = str(k).replace("KEY_", "").lower()
                                
                                pressed = (event.value == 1) # 1=down, 0=up, 2=hold
                                if event.value != 2:
                                    self._notify_listeners(k, pressed)
                    except (IOError, OSError) as inner_err:
                        logger.warning(f"Device disconnected: {dev.name}")
                        devices.remove(dev)
                        del fds[fd]
            except Exception as err:
                 logger.error(f"Listener loop error: {err}")
                 time.sleep(2) # Prevent rapid-fire logging if error persists

    def _get_kb_devices(self):
        """Helper to find all keyboard devices."""
        kb_devices = []
        try:
            for path in list_devices():
                try:
                    dev = InputDevice(path)
                    if e.EV_KEY in dev.capabilities():
                        kb_devices.append(dev)
                except:
                    pass
        except:
            pass
        return kb_devices

class HybridInputStrategy(InputStrategy):
    """
    Hybrid Linux input strategy.
    
    Uses evdev for keyboard inputs (Performance + Scancodes)
    Uses pynput for mouse movements and clicks (Reliable window manager coordinates).
    
    This strategy provides the best of both worlds: low-latency keyboard control
    and compatible absolute mouse positioning on modern Linux desktops.
    """
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        super().__init__()
        self.evdev = None
        self.pynput = None
        
        try:
            self.evdev = EvdevStrategy(screen_width, screen_height)
            logger.info("Hybrid Part 1: Evdev initialized for keyboard")
        except Exception as e:
            logger.warning(f"Hybrid Part 1: Evdev failed ({e})")
            
        try:
            self.pynput = PynputStrategy()
            logger.info("Hybrid Part 2: Pynput initialized for mouse")
        except Exception as e:
            logger.error(f"Hybrid Part 2: Pynput failed ({e})")
            
        if not self.evdev and not self.pynput:
            raise RuntimeError("Hybrid Strategy failed: neither evdev nor pynput available")

    def press_key(self, key_code: str):
        # Prefer evdev for keyboard
        if self.evdev:
            self.evdev.press_key(key_code)
        elif self.pynput:
            self.pynput.press_key(key_code)

    def click_mouse(self, x: int, y: int, button: str = 'left'):
        # Prefer pynput for mouse
        if self.pynput:
            self.pynput.click_mouse(x, y, button)
        elif self.evdev:
            self.evdev.click_mouse(x, y, button)

    def move_mouse(self, x: int, y: int):
        # Prefer pynput for mouse
        if self.pynput:
            self.pynput.move_mouse(x, y)
        elif self.evdev:
            self.evdev.move_mouse(x, y)

    def start_listening(self):
        # Prefer evdev for global listening on Linux
        success = False
        if self.evdev:
            self.evdev.add_listener(self._on_strategy_event)
            success = self.evdev.start_listening()
            
        # Fallback to pynput if evdev failed or is missing
        if not success and self.pynput:
            logger.info("Falling back to Pynput for input listening...")
            self.pynput.add_listener(self._on_strategy_event)
            self.pynput.start_listening()
        elif success:
            logger.info("Hybrid listening active via Evdev.")

    def _on_strategy_event(self, key_code: str, pressed: bool):
        # Forward internal strategy events to the hybrid strategy's listeners
        self._notify_listeners(key_code, pressed)

class InputManager:
    """Auto-detects and manages the best input strategy."""
    def __init__(self, config=None):
        self._config = config
        self.strategy: Optional[InputStrategy] = None
        self._init_strategy()

    def _init_strategy(self):
        # 1. Try Hybrid on Linux
        if platform.system() == 'Linux':
            try:
                self.strategy = HybridInputStrategy()
                logger.info("Using HybridInputStrategy (evdev + pynput)")
            except Exception as e:
                logger.warning(f"Hybrid strategy failed ({e}), falling back to standard...")
        
        # 2. Try Standard Evdev
        if not self.strategy and platform.system() == 'Linux':
            try:
                self.strategy = EvdevStrategy()
            except Exception as e:
                logger.warning(f"Evdev strategy failed ({e}), falling back...")
        
        # 3. Try Pynput
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
