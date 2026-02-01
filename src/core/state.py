from typing import Any, Dict, Optional
from threading import Lock

class StateManager:
    """
    Thread-safe dictionary wrapper for sharing state between rules.
    Singleton-ish usage pattern is expected but not enforced strictly here
    to allow dependency injection.
    """
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._lock = Lock()

    def set(self, key: str, value: Any) -> None:
        """Set a variable in the shared state."""
        with self._lock:
            self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a variable from the shared state."""
        with self._lock:
            return self._state.get(key, default)

    def delete(self, key: str) -> None:
        """Remove a variable from the shared state."""
        with self._lock:
            if key in self._state:
                del self._state[key]

    def clear(self) -> None:
        """Clear all state."""
        with self._lock:
            self._state.clear()
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        with self._lock:
            return key in self._state
