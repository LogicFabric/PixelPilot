from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSlot, QObject, pyqtSignal

class Signals(QObject):
    input_detected = pyqtSignal(str, bool)

class InputAnalyzerDialog(QDialog):
    def __init__(self, input_manager, parent=None):
        super().__init__(parent)
        self.input_mgr = input_manager
        self.setWindowTitle("Input Analyzer")
        self.resize(400, 500)
        
        # Signals redirect (thread safety)
        self.signals = Signals()
        self.signals.input_detected.connect(self.on_input)
        
        self.init_ui()
        
        # Start listening
        self.input_mgr.add_listener(self.listener_callback)

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Press keys or buttons to see them here:"))
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        
        self.lbl_last = QLabel("Last Key: None")
        self.lbl_last.setStyleSheet("font-size: 18px; font-weight: bold; color: #007acc;")
        layout.addWidget(self.lbl_last)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def listener_callback(self, key, pressed):
        self.signals.input_detected.emit(key, pressed)

    @pyqtSlot(str, bool)
    def on_input(self, key, pressed):
        state = "Pressed" if pressed else "Released"
        msg = f"[{state}] Code: {key}"
        self.log_view.append(msg)
        if pressed:
            self.lbl_last.setText(f"Last Key: {key}")
