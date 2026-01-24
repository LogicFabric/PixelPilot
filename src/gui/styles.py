
DARK_THEME = """
QMainWindow {
    background-color: #2b2b2b;
    color: #e0e0e0;
}

QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    font-size: 14px;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #3c3f41;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #007acc;
}

/* Buttons */
QPushButton {
    background-color: #3c3f41;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 80px;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #4c5052;
    border-color: #007acc;
}
QPushButton:pressed {
    background-color: #007acc;
    border-color: #005f9e;
}
QPushButton:disabled {
    background-color: #2b2b2b;
    color: #666;
    border-color: #444;
}

/* Text Inputs and Consoles */
QTextEdit, QLineEdit, QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #3c3f41;
    border-radius: 3px;
    color: #dcdCDC;
    selection-background-color: #264f78;
}

/* Status Bar & Labels */
QLabel {
    color: #cccccc;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
