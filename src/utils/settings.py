from PyQt6.QtCore import QSettings
import logging

class SettingsManager:
    """
    Handles persistence of user settings and GUI preferences.
    Uses QSettings for OS-native storage.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.settings = QSettings("LogicFabric", "PixelPilot")
            cls._instance._setup_defaults()
        return cls._instance

    def _setup_defaults(self):
        """Ensure default values exist."""
        if not self.settings.contains("gui/port_size"):
            self.settings.setValue("gui/port_size", 12)
        if not self.settings.contains("gui/link_thickness"):
            self.settings.setValue("gui/link_thickness", 2)
        if not self.settings.contains("engine/refresh_ms"):
            self.settings.setValue("engine/refresh_ms", 50)

    def get(self, key, default=None):
        return self.settings.value(key, default)

    def set(self, key, value):
        self.settings.setValue(key, value)
        self.settings.sync()

def get_settings():
    return SettingsManager()
