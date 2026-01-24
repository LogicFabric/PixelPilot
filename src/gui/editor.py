from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QListWidget, 
    QGroupBox, QFormLayout, QSpinBox, QWidget
)
from PyQt6.QtCore import Qt

from src.core.rules import Rule, PixelColorCondition, KeyPressAction, MouseClickAction, LogicEvaluator

class RuleEditor(QDialog):
    def __init__(self, parent=None, rule: Rule = None):
        super().__init__(parent)
        self.setWindowTitle("PLC Rule Editor")
        self.resize(700, 500)
        self.rule = rule
        
        # Data holders
        self.conditions = []
        self.actions = []
        
        self.init_ui()
        
        if rule:
            self.load_rule(rule)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Rule Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Rule Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter rule name...")
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # --- PLC Modules Section ---
        modules_layout = QHBoxLayout()

        # 1. INPUT MODULES (Conditions)
        input_group = QGroupBox("1. Input Modules (Conditions)")
        input_layout = QVBoxLayout()
        self.input_list = QListWidget()
        input_layout.addWidget(self.input_list)
        
        btn_add_input = QPushButton("+ Add Input")
        btn_add_input.clicked.connect(self.add_input_dialog)
        input_layout.addWidget(btn_add_input)
        
        btn_rem_input = QPushButton("- Remove Input")
        btn_rem_input.clicked.connect(self.remove_input)
        input_layout.addWidget(btn_rem_input)
        
        input_group.setLayout(input_layout)
        modules_layout.addWidget(input_group)

        # 2. PROCESS MODULE (Logic)
        process_group = QGroupBox("2. Process Module (Logic)")
        process_layout = QFormLayout()
        
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["AND (All Inputs must be True)", "OR (Any Input must be True)"])
        process_layout.addRow("Logic Gate:", self.logic_combo)
        
        # Placeholder for timers or other process logic
        self.hold_time_spin = QSpinBox()
        self.hold_time_spin.setRange(0, 10000)
        self.hold_time_spin.setSuffix(" ms")
        process_layout.addRow("Hold Time:", self.hold_time_spin)
        
        process_group.setLayout(process_layout)
        modules_layout.addWidget(process_group)

        # 3. OUTPUT MODULES (Actions)
        output_group = QGroupBox("3. Output Modules (Actions)")
        output_layout = QVBoxLayout()
        self.output_list = QListWidget()
        output_layout.addWidget(self.output_list)
        
        btn_add_output = QPushButton("+ Add Output")
        btn_add_output.clicked.connect(self.add_output_dialog)
        output_layout.addWidget(btn_add_output)
        
        btn_rem_output = QPushButton("- Remove Output")
        btn_rem_output.clicked.connect(self.remove_output)
        output_layout.addWidget(btn_rem_output)
        
        output_group.setLayout(output_layout)
        modules_layout.addWidget(output_group)

        main_layout.addLayout(modules_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Rule")
        btn_save.clicked.connect(self.save_rule)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)

    def load_rule(self, rule: Rule):
        self.name_input.setText(rule.name)
        # Load logic
        if rule.logic_type == "OR":
            self.logic_combo.setCurrentIndex(1)
        else:
            self.logic_combo.setCurrentIndex(0)
            
        # Refill lists (Need a way to describe objects back to text, or store them)
        # For prototype simplicity, we assume we are creating NEW rules mostly, 
        # or we rely on the implementation details of objects having a string repr.
        pass

    def add_input_dialog(self):
        # Determine type
        # For minimal viable product, hardcode a Pixel Check Dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Input")
        layout = QFormLayout(dlg)
        
        x_spin = QSpinBox()
        x_spin.setRange(0, 5000)
        y_spin = QSpinBox()
        y_spin.setRange(0, 5000)
        
        r_spin = QSpinBox(); r_spin.setRange(0, 255)
        g_spin = QSpinBox(); g_spin.setRange(0, 255)
        b_spin = QSpinBox(); b_spin.setRange(0, 255)
        
        layout.addRow("X:", x_spin)
        layout.addRow("Y:", y_spin)
        layout.addRow("R:", r_spin)
        layout.addRow("G:", g_spin)
        layout.addRow("B:", b_spin)
        
        btn = QPushButton("Add")
        btn.clicked.connect(dlg.accept)
        layout.addRow(btn)
        
        if dlg.exec():
            # Create object
            cond = PixelColorCondition(x_spin.value(), y_spin.value(), (r_spin.value(), g_spin.value(), b_spin.value()))
            self.conditions.append(cond)
            self.input_list.addItem(f"PixelColor ({x_spin.value()},{y_spin.value()}) == RGB({r_spin.value()},{g_spin.value()},{b_spin.value()})")

    def remove_input(self):
        row = self.input_list.currentRow()
        if row >= 0:
            self.input_list.takeItem(row)
            self.conditions.pop(row)

    def add_output_dialog(self):
        # Key Press Dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Output")
        layout = QFormLayout(dlg)
        
        key_input = QLineEdit()
        layout.addRow("Key Code:", key_input)
        
        btn = QPushButton("Add")
        btn.clicked.connect(dlg.accept)
        layout.addRow(btn)
        
        if dlg.exec():
            act = KeyPressAction(key_input.text())
            self.actions.append(act)
            self.output_list.addItem(f"KeyPress '{key_input.text()}'")

    def remove_output(self):
        row = self.output_list.currentRow()
        if row >= 0:
            self.output_list.takeItem(row)
            self.actions.pop(row)

    def save_rule(self):
        name = self.name_input.text() or "Untitled Rule"
        logic = "OR" if self.logic_combo.currentIndex() == 1 else "AND"
        
        self.rule = Rule(name, self.conditions, self.actions, logic_type=logic)
        self.accept()
        
    def get_rule(self):
        return self.rule
