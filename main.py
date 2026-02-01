import sys
import os
import logging
from PyQt6.QtWidgets import QApplication

from src.core.state import StateManager
from src.core.engine import AutomationEngine
from src.strategies.vision import VisionManager
from src.strategies.input import InputManager
from src.gui.main_window import MainWindow

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configure Logging using centralized utility
from src.utils.logger import setup_logger
# Force DEBUG level for console to provide verbose terminal output
logger = setup_logger("PixelPilot", level="DEBUG")

def main():
    logger.info("PixelPilot starting...")
    
    app = QApplication(sys.argv)

    try:
        # Initialize Core
        logger.info("Initializing State Manager...")
        state_mgr = StateManager()

        # Load configuration once
        from src.utils.config import get_config
        config = get_config()

        # Initialize Vision
        logger.info("Initializing Vision System...")
        vision_mgr = VisionManager(config=config)
        if vision_mgr.strategy:
            logger.info(f"Vision Strategy Active: {type(vision_mgr.strategy).__name__}")
        else:
            logger.critical("No valid vision strategy found!")

        # Initialize Input
        logger.info("Initializing Input System...")
        input_mgr = InputManager(config=config)
        if input_mgr.strategy:
             logger.info(f"Input Strategy Active: {type(input_mgr.strategy).__name__}")
        else:
             logger.critical("No valid input strategy found!")

        # Initialize Engine
        logger.info("Initializing Automation Engine...")
        engine = AutomationEngine(vision_mgr, input_mgr, state_mgr, config=config)

        # Initialize UI
        logger.info("Initializing GUI...")
        window = MainWindow(engine, vision_mgr, input_mgr)
        window.show()

        logger.info("Startup complete. Entering Event Loop.")
        sys.exit(app.exec())

    except Exception as e:
        logger.exception(f"Fatal error during startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
