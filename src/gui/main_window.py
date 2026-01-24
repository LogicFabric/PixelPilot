from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QGroupBox, QListWidget, QGraphicsView
)
from PyQt6.QtCore import QThread, pyqtSlot, Qt
import logging

from .styles import DARK_THEME
from .workers import EngineWorker
from .graph.scene import FBDScene
from src.core.graph import InputNode, ProcessNode, OutputNode
from src.core.rules import PixelColorCondition, KeyPressAction

from PyQt6.QtGui import QPainter

logger = logging.getLogger(__name__)

class LoggerAdapter(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    def emit(self, record):
        msg = self.format(record)
        self.callback(msg)

class MainWindow(QMainWindow):
    def __init__(self, engine, vision_mgr, input_mgr):
        super().__init__()
        self.engine = engine
        self.vision_mgr = vision_mgr
        self.input_mgr = input_mgr
        
        self.setWindowTitle("PixelPilot - FBD Editor")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_THEME)
        
        # Threading
        self.thread = None
        self.worker = None

        self._init_ui()
        self._setup_logging_redirect()
       
        # Link engine to graph (Hack for V1: engine needs to know likely about graph)
        # Ideally engine executes graph directly.
        # engine.set_graph(self.scene.graph)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Bar: Status & Controls
        control_layout = QHBoxLayout()
        self.status_label = QLabel("Status: STOPPED")
        self.status_label.setStyleSheet("color: #eb5757; font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        self.btn_start = QPushButton("Start (F5)")
        self.btn_start.clicked.connect(self.start_engine)
        self.btn_start.setShortcut("F5")
        
        self.btn_stop = QPushButton("Stop (F6)")
        self.btn_stop.clicked.connect(self.stop_engine)
        self.btn_stop.setShortcut("F6")
        self.btn_stop.setEnabled(False)
        
        self.btn_analyzer = QPushButton("Input Analyzer")
        self.btn_analyzer.clicked.connect(self.open_input_analyzer)
        
        control_layout.addStretch()
        control_layout.addWidget(self.btn_analyzer)
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        main_layout.addLayout(control_layout)
        
        # Canvas Area
        canvas_layout = QHBoxLayout()
        
        # Palette (Left)
        palette_layout = QVBoxLayout()
        btn_add_input = QPushButton("Add Input Block")
        btn_add_input.clicked.connect(self.add_input_node)
        
        btn_add_process = QPushButton("Add Process Block")
        btn_add_process.clicked.connect(self.add_process_node)
        
        btn_add_output = QPushButton("Add Output Block")
        btn_add_output.clicked.connect(self.add_output_node)
        
        palette_layout.addWidget(btn_add_input)
        palette_layout.addWidget(btn_add_process)
        palette_layout.addWidget(btn_add_output)
        palette_layout.addStretch()
        
        canvas_layout.addLayout(palette_layout)

        # Graph View
        self.scene = FBDScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        canvas_layout.addWidget(self.view)
        main_layout.addLayout(canvas_layout)

        # Logs Bottom
        self.log_console = QTextEdit()
        self.log_console.setMaximumHeight(150)
        self.log_console.setReadOnly(True)
        main_layout.addWidget(self.log_console)

    def add_input_node(self):
        # Placeholder preset
        c = PixelColorCondition(100, 100, (255, 255, 255))
        node = InputNode("Pixel Check", c)
        self.scene.add_visual_node(node, 100, 100)
    
    def add_process_node(self):
        node = ProcessNode("AND Logic", "AND")
        self.scene.add_visual_node(node, 300, 100)
        
    def add_output_node(self):
        a = KeyPressAction("space")
        node = OutputNode("Press Space", a)
        self.scene.add_visual_node(node, 500, 100)


    def _setup_logging_redirect(self):
        # Create a handler that pipes to our update_log method
        # Note: In a real app, signals should satisfy thread-safety
        # Here we just want internal logs to show up.
        # Since standard logging is thread-safe, direct emit might be risky if called from background
        # But signals are thread-safe.
        pass

    @pyqtSlot(str)
    def append_log(self, message):
        self.log_console.append(message)
        # Auto scroll
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def refresh_rules(self):
        self.rules_list.clear()
        for rule in self.engine.rules:
            self.rules_list.addItem(f"{rule.name} ({len(rule.conditions)} In, {len(rule.actions)} Out)")
        if self.rules_list.count() == 0:
             self.rules_list.addItem("No rules loaded.")

    def open_add_rule(self):
        editor = RuleEditor(self)
        if editor.exec():
            new_rule = editor.get_rule()
            if new_rule:
                self.engine.add_rule(new_rule)
                self.append_log(f"Added Rule: {new_rule.name}")
                self.refresh_rules()

    def delete_rule(self):
        row = self.rules_list.currentRow()
        # Check if row is valid and we are not selecting "No rules loaded" placeholder
        if row >= 0 and self.engine.rules:
             # Need to implement remove in engine, for now just pop list (not thread safe really without lock, but engine has lock)
             # Engine doesn't expose remove yet.
             # Let's assume we can modify list directly or add remove method.
             # Accessing engine.rules is direct list access.
             try:
                rule_to_remove = self.engine.rules[row]
                self.engine.rules.remove(rule_to_remove) # This is not strictly thread safe if engine is iterating.
                self.append_log(f"Removed Rule: {rule_to_remove.name}")
                self.refresh_rules()
             except IndexError:
                 pass

    def start_engine(self):
        if self.thread is not None:
             if self.thread.isRunning():
                return
             # If thread exists but not running (rare/zombie), clean it? 
             # For now, assume if self.thread is not None, it might be in cleanup.
             # The cleanup in on_engine_stopped should handle it.

        self.log_console.append(">>> Starting Engine...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("Status: RUNNING")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;") # Green

        # Setup Thread
        self.thread = QThread()
        self.worker = EngineWorker(self.engine)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.log_message.connect(self.append_log)
        
        # When thread finishes (stopped), reset UI and cleanup references
        self.thread.finished.connect(self.on_engine_stopped)
        
        self.thread.start()

    def stop_engine(self):
        if self.worker:
            self.log_console.append(">>> Stopping requested...")
            self.worker.stop()
            self.btn_stop.setEnabled(False) # Prevent spam

    def on_engine_stopped(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Status: STOPPED")
        self.status_label.setStyleSheet("color: #eb5757; font-weight: bold;")
        self.log_console.append(">>> Engine Stopped.")
        
        # Cleanup references to avoid "RuntimeError: wrapped C/C++ object... has been deleted"
        self.thread = None
        self.worker = None

    def open_input_analyzer(self):
        from .analyzer import InputAnalyzerDialog
        dlg = InputAnalyzerDialog(self.input_mgr, self)
        dlg.exec()
