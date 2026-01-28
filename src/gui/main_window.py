from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QGroupBox, QListWidget, QGraphicsView,
    QMenuBar, QFileDialog, QMessageBox, QDialog, QFormLayout, QSpinBox
)
from PyQt6.QtCore import QThread, pyqtSlot, Qt, QTimer
import logging

from .styles import DARK_THEME
from .workers import EngineWorker
from .graph.scene import FBDScene
from src.core.graph import InputNode, ProcessNode, OutputNode
from src.core.rules import PixelColorCondition, KeyPressAction
from src.core.serialization import GraphSerializer
from src.core.exceptions import SerializationError, DeserializationError
from src.utils.settings import get_settings

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
        self.current_file = None  # Track currently loaded file
        
        self.setWindowTitle("PixelPilot - FBD Editor")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_THEME)
        
        # Threading
        self.thread = None
        self.worker = None

        self._create_menu_bar()
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
        btn_add_input.setToolTip("Generic Input (Pixel Check, Key Press, etc.)")
        
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
        
        # Configure scroll bars - show only when needed
        from PyQt6.QtCore import Qt
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Better drag behavior
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        canvas_layout.addWidget(self.view)
        main_layout.addLayout(canvas_layout)
        
        # Live Wire Debugging Timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_live_wires)
        self.refresh_timer.start(50) # 50ms = 20Hz refresh

        # Logs Bottom
        self.log_console = QTextEdit()
        self.log_console.setMaximumHeight(150)
        self.log_console.setReadOnly(True)
        main_layout.addWidget(self.log_console)

    def add_input_node(self):
        # Default: Pixel check (configurable via double-click)
        c = PixelColorCondition(100, 100, (255, 255, 255))
        node = InputNode("Input Block", c)
        self.scene.add_visual_node(node, 100, 100)
    
    def add_process_node(self):
        node = ProcessNode("Process Block", "AND")
        self.scene.add_visual_node(node, 300, 100)
        
    def add_output_node(self):
        a = KeyPressAction("space")
        node = OutputNode("Output Block", a)
        self.scene.add_visual_node(node, 500, 100)


    def update_live_wires(self):
        """Update the visual state of links and ports in the scene for real-time debugging."""
        if not self.engine.is_running():
            return
            
        from .graph.graphics import VisualLink, VisualPort
        # Update all links and ports to show signal flow
        for item in self.scene.items():
            if isinstance(item, (VisualLink, VisualPort)):
                item.update_status()

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
        # Link current graph to engine before starting
        self.engine.set_graph(self.scene.graph)
        
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
    
    def _create_menu_bar(self):
        """Create menu bar with File and Edit menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")

        # ... existing File menu actions ...
        # (I will keep the existing ones by using a more precise replacement)
        
        # New action
        new_action = file_menu.addAction("&New")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_graph)
        
        # Open action
        open_action = file_menu.addAction("&Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_graph)
        
        # Save action
        save_action = file_menu.addAction("&Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_graph)
        
        # Save As action
        save_as_action = file_menu.addAction("Save &As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_graph_as)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        settings_action = edit_menu.addAction("&Settings")
        settings_action.triggered.connect(self.open_settings)

    def open_settings(self):
        """Open the Settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.refresh_ui_from_settings()

    def refresh_ui_from_settings(self):
        """Update scene and visual elements after settings change."""
        s = get_settings()
        ms = int(s.get("engine/refresh_ms", 50))
        self.refresh_timer.setInterval(ms)
        
        from .graph.graphics import VisualNode, VisualPort, VisualLink
        port_size = int(s.get("gui/port_size", 12))
        
        for item in self.scene.items():
            if isinstance(item, VisualPort):
                item.size = port_size
                item.setRect(-port_size/2, -port_size/2, port_size, port_size)
            elif isinstance(item, VisualLink):
                item.update_path()
            elif isinstance(item, VisualNode):
                # Optionally re-layout if port pos changes, but VisualNode uses fixed offsets in _setup_ports
                # For now, just call update() to repaint
                item.update()
    
    def new_graph(self):
        """Create a new empty graph."""
        # Confirm if there are unsaved changes
        if len(self.scene.graph.nodes) > 0:
            reply = QMessageBox.question(
                self, 'New Graph',
                'This will clear the current graph. Continue?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Clear scene
        self.scene.clear()
        self.scene.graph.nodes.clear()
        self.scene.graph.links.clear()
        self.scene.visual_nodes.clear()
        self.current_file = None
        self.setWindowTitle("PixelPilot - FBD Editor")
        self.append_log("New graph created")
    
    def save_graph(self):
        """Save graph to current file or prompt for location."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_graph_as()
    
    def save_graph_as(self):
        """Save graph to a new file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Graph",
            "",
            "PixelPilot Files (*.pp);;All Files (*)"
        )
        
        if filename:
            if not filename.endswith('.pp'):
                filename += '.pp'
            self._save_to_file(filename)
    
    def _save_to_file(self, filename: str):
        """Actually save the graph to file."""
        try:
            GraphSerializer.save_to_file(self.scene.graph, filename)
            self.current_file = filename
            self.setWindowTitle(f"PixelPilot - {filename}")
            self.append_log(f"Graph saved to {filename}")
            QMessageBox.information(self, "Success", f"Graph saved successfully to {filename}")
        except SerializationError as e:
            logger.error(f"Failed to save graph: {e}")
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save graph:\n{str(e)}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error saving graph: {e}")
            QMessageBox.critical(
                self, "Save Error",
                f"Unexpected error:\n{str(e)}"
            )
    
    def load_graph(self):
        """Load graph from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Graph",
            "",
            "PixelPilot Files (*.pp);;All Files (*)"
        )
        
        if filename:
            self._load_from_file(filename)
    
    def _load_from_file(self, filename: str):
        """Actually load the graph from file."""
        from PyQt6.QtWidgets import QApplication
        
        try:
            # Show status message
            self.append_log(f"Loading graph from {filename}...")
            QApplication.processEvents()  # Keep GUI responsive
            
            # Load graph
            graph = GraphSerializer.load_from_file(filename)
            
            self.append_log(f"Loaded {len(graph.nodes)} nodes, {len(graph.links)} links")
            QApplication.processEvents()
            
            # Clear current scene
            self.scene.clear()
            
            # Rebuild scene from loaded graph
            self.scene.graph = graph
            self.scene.visual_nodes.clear()
            
            # Create visual nodes with progress updates
            for i, node in enumerate(graph.nodes):
                if i % 5 == 0:  # Update every 5 nodes
                    self.append_log(f"Creating visual nodes... {i}/{len(graph.nodes)}")
                    QApplication.processEvents()  # Keep GUI responsive
                
                # Note: add_visual_node already calls graph.add_node, 
                # but our graph already has the nodes, so we need custom logic
                vn = self.scene._create_visual_node_from_existing(node)
            
            self.append_log("Recreating connections...")
            QApplication.processEvents()
            
            # Recreate visual links
            for link in graph.links:
                try:
                    source_vnode = self.scene.visual_nodes[link.source.node.id]
                    target_vnode = self.scene.visual_nodes[link.target.node.id]
                    
                    # Find port visual items
                    src_port = None
                    for child in source_vnode.childItems():
                        if hasattr(child, 'port_data') and child.port_data == link.source:
                            src_port = child
                            break
                    
                    tgt_port = None
                    for child in target_vnode.childItems():
                        if hasattr(child, 'port_data') and child.port_data == link.target:
                            tgt_port = child
                            break
                    
                    if src_port and tgt_port:
                        from .graph.graphics import VisualLink
                        vl = VisualLink(src_port, tgt_port)
                        self.scene.addItem(vl)
                except Exception as e:
                    logger.warning(f"Failed to recreate link: {e}")
            
            self.current_file = filename
            self.setWindowTitle(f"PixelPilot - {filename}")
            self.append_log(f"✓ Graph loaded successfully!")
            QMessageBox.information(self, "Success", f"Graph loaded successfully!\n{len(graph.nodes)} nodes, {len(graph.links)} connections")
            
        except DeserializationError as e:
            logger.error(f"Failed to load graph: {e}")
            QMessageBox.critical(
                self, "Load Error",
                f"Failed to load graph:\n{str(e)}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error loading graph: {e}")
            QMessageBox.critical(
                self, "Load Error",
                f"Unexpected error:\n{str(e)}"
            )

class SettingsDialog(QDialog):
    """Dialog for editing user preferences."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = get_settings()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.port_size_spin = QSpinBox()
        self.port_size_spin.setRange(8, 32)
        self.port_size_spin.setValue(int(self.settings.get("gui/port_size", 12)))
        form.addRow("Connector Size (px):", self.port_size_spin)

        self.refresh_ms_spin = QSpinBox()
        self.refresh_ms_spin.setRange(10, 500)
        self.refresh_ms_spin.setValue(int(self.settings.get("engine/refresh_ms", 50)))
        form.addRow("Visual Refresh (ms):", self.refresh_ms_spin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(save)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def accept(self):
        self.settings.set("gui/port_size", self.port_size_spin.value())
        self.settings.set("engine/refresh_ms", self.refresh_ms_spin.value())
        super().accept()
