from PyQt6.QtCore import QThread, pyqtSignal, QObject
import logging
import traceback

logger = logging.getLogger(__name__)

class EngineWorker(QObject):
    """
    Worker object that runs the engine loop in a separate thread.
    Uses generic QThread worker pattern (moveToThread).
    """
    finished = pyqtSignal()
    log_message = pyqtSignal(str)
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        """Blocking run method called by the thread."""
        try:
            self.log_message.emit("Engine thread started.")
            # Use blocking=True so the worker thread doesn't exit immediately
            self.engine.start(blocking=True) 
        except Exception as e:
            self.log_message.emit(f"Engine crashed: {e}")
            self.log_message.emit(traceback.format_exc())
        finally:
            self.finished.emit()
            self.log_message.emit("Engine thread stopped.")

    def stop(self):
        """Signal the engine to stop."""
        self.engine.stop()
