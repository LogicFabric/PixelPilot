from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QSpinBox, 
    QLineEdit, QComboBox, QPushButton, QLabel, QHBoxLayout, QWidget
)
from src.core.graph import InputNode, ProcessNode, OutputNode
from src.core.rules import PixelColorCondition, KeyPressCondition, KeyPressAction, MouseClickAction

class NodeConfigDialog(QDialog):
    """Base class for node configuration."""
    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.setWindowTitle(f"Configure {node.name}")
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.layout.addLayout(self.form)
        
        # Name field
        self.name_edit = QLineEdit(self.node.name)
        self.form.addRow("Name:", self.name_edit)
        
        self.add_custom_fields()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_and_close)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        self.layout.addLayout(btn_layout)

    def add_custom_fields(self):
        pass

    def save_and_close(self):
        self.node.name = self.name_edit.text()
        self.save_custom_fields()
        self.accept()

    def save_custom_fields(self):
        pass

class InputConfigDialog(NodeConfigDialog):
    def add_custom_fields(self):
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Pixel Color", "Key Press"])
        self.form.addRow("Trigger Type:", self.type_combo)
        self.type_combo.currentIndexChanged.connect(self.toggle_mode)
        
        # ---- Pixel Fields ----
        self.pixel_widget = QWidget()
        pixel_form = QFormLayout(self.pixel_widget)
        pixel_form.setContentsMargins(0,0,0,0)
        
        self.x_spin = QSpinBox(); self.x_spin.setRange(0, 5000)
        self.y_spin = QSpinBox(); self.y_spin.setRange(0, 5000)
        self.r_spin = QSpinBox(); self.r_spin.setRange(0, 255)
        self.g_spin = QSpinBox(); self.g_spin.setRange(0, 255)
        self.b_spin = QSpinBox(); self.b_spin.setRange(0, 255)
        
        pixel_form.addRow("X:", self.x_spin)
        pixel_form.addRow("Y:", self.y_spin)
        pixel_form.addRow("R:", self.r_spin)
        pixel_form.addRow("G:", self.g_spin)
        pixel_form.addRow("B:", self.b_spin)
        
        self.form.addRow(self.pixel_widget)
        
        # ---- Key Fields ----
        self.key_widget = QWidget()
        key_form = QFormLayout(self.key_widget)
        key_form.setContentsMargins(0,0,0,0)
        
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("e.g. 'space' or 'a'")
        key_form.addRow("Key Code:", self.key_edit)
        
        self.form.addRow(self.key_widget)
        
        # Init values
        if isinstance(self.node.condition, PixelColorCondition):
            self.type_combo.setCurrentIndex(0)
            self.x_spin.setValue(self.node.condition.x)
            self.y_spin.setValue(self.node.condition.y)
            self.r_spin.setValue(self.node.condition.target_rgb[0])
            self.g_spin.setValue(self.node.condition.target_rgb[1])
            self.b_spin.setValue(self.node.condition.target_rgb[2])
        elif isinstance(self.node.condition, KeyPressCondition):
            self.type_combo.setCurrentIndex(1)
            self.key_edit.setText(self.node.condition.key_code)
            
        self.toggle_mode()

    def toggle_mode(self):
        is_pixel = (self.type_combo.currentIndex() == 0)
        self.pixel_widget.setVisible(is_pixel)
        self.key_widget.setVisible(not is_pixel)

    def save_custom_fields(self):
        if self.type_combo.currentIndex() == 0:
            # Pixel Mode
            rgb = (self.r_spin.value(), self.g_spin.value(), self.b_spin.value())
            if not isinstance(self.node.condition, PixelColorCondition):
                self.node.condition = PixelColorCondition(0,0,(0,0,0))
            
            self.node.condition.x = self.x_spin.value()
            self.node.condition.y = self.y_spin.value()
            self.node.condition.target_rgb = rgb
        else:
            # Key Mode
            code = self.key_edit.text()
            if not isinstance(self.node.condition, KeyPressCondition):
                self.node.condition = KeyPressCondition(code)
            else:
                self.node.condition.key_code = code

class ProcessConfigDialog(NodeConfigDialog):
    def add_custom_fields(self):
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["AND", "OR", "NOT", "NAND", "XOR"])
        self.logic_combo.setCurrentText(self.node.logic_type)
        self.form.addRow("Logic Type:", self.logic_combo)

    def save_custom_fields(self):
        self.node.logic_type = self.logic_combo.currentText()

class OutputConfigDialog(NodeConfigDialog):
    def add_custom_fields(self):
        if isinstance(self.node.action, KeyPressAction):
            self.key_edit = QLineEdit(self.node.action.key_code)
            self.form.addRow("Key Code:", self.key_edit)
            self.form.addRow(QLabel("Special Keys: 'space', 'enter', 'esc', 'shift', 'ctrl'"))

    def save_custom_fields(self):
        if isinstance(self.node.action, KeyPressAction):
            self.node.action.key_code = self.key_edit.text()
