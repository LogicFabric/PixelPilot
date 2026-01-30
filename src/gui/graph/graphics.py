from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsRectItem, QMenu
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont

from src.utils.settings import get_settings
from .dialogs import InputConfigDialog, ProcessConfigDialog, OutputConfigDialog
from src.core.graph import InputNode, ProcessNode, OutputNode

class VisualPort(QGraphicsRectItem):
    """Visual representation of a Port."""
    def __init__(self, port_data, parent=None):
        super().__init__(parent)
        self.port_data = port_data
        
        # Load size from settings
        settings = get_settings()
        self.size = int(settings.get("gui/port_size", 12))
        self.setRect(-self.size/2, -self.size/2, self.size, self.size)
        
        if port_data.is_output:
            self.setBrush(QBrush(QColor("#e74c3c"))) # Red for output
        else:
            self.setBrush(QBrush(QColor("#2ecc71"))) # Green for input
            
        self.setPen(QPen(Qt.GlobalColor.black))
        self.update_status()
        
        # Make ports more clickable by increasing their z-value
        self.setZValue(1) # Higher than nodes
        
        # Set flags to ensure ports receive mouse events
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                     QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def update_status(self):
        """Update port color based on current value."""
        is_active = self.port_data.value
        
        if is_active:
            # Active signal: Bright Cyan glow
            self.setBrush(QBrush(QColor("#00f2ff")))
            self.setPen(QPen(QColor("#ffffff"), 2))
        else:
            # Inactive signal: Use standard Red/Green
            if self.port_data.is_output:
                self.setBrush(QBrush(QColor("#e74c3c"))) # Red
            else:
                self.setBrush(QBrush(QColor("#2ecc71"))) # Green
            self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.update() # Force repaint
        
class VisualNode(QGraphicsRectItem):
    """Visual representation of a Node."""
    def __init__(self, node_data):
        super().__init__()
        self.node_data = node_data
        
        self.width = 150
        self.height = 80
        self.setRect(0, 0, self.width, self.height)
        
        # Style
        self.setBrush(QBrush(QColor("#34495e")))
        self.setPen(QPen(QColor("#ecf0f1"), 2))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        # Title
        self.title_item = QGraphicsTextItem(node_data.name, self)
        self.title_item.setDefaultTextColor(QColor("#ecf0f1"))
        self.title_item.setPos(5, 5)
        
        self.visual_ports = {}
        self._setup_ports()

    def _setup_ports(self):
        # Inputs on left
        y_offset = 30
        for i, port in enumerate(self.node_data.inputs):
            vp = VisualPort(port, self)
            vp.setPos(0, y_offset)
            self.visual_ports[port.name] = vp
            
            label = QGraphicsTextItem(port.name, self)
            label.setDefaultTextColor(QColor("#bdc3c7"))
            label.setFont(QFont("Arial", 8))
            label.setPos(10, y_offset - 5)
            
            y_offset += 20
            
        # Outputs on right
        y_offset = 30
        for i, port in enumerate(self.node_data.outputs):
            vp = VisualPort(port, self)
            vp.setPos(self.width, y_offset)
            self.visual_ports[port.name] = vp
            
            label = QGraphicsTextItem(port.name, self)
            label.setDefaultTextColor(QColor("#bdc3c7"))
            label.setFont(QFont("Arial", 8))
            label.setPos(self.width - 30, y_offset - 5)
            
            y_offset += 20

        # Adjust height if needed
        self.height = max(self.height, y_offset + 10)
        self.setRect(0, 0, self.width, self.height)
    
    def _update_port_labels(self):
        """Update port labels without recreating ports to preserve connections."""
        # Only update labels, don't recreate ports
        
        # Find all existing labels and remove them
        labels_to_remove = []
        for item in self.childItems():
            if isinstance(item, QGraphicsTextItem) and item != self.title_item:
                labels_to_remove.append(item)
        
        visited_labels = set()
        
        # Update input port labels
        y_offset = 30
        for port in self.node_data.inputs:
            # Check if this port has a visual representation
            visual_port = self.visual_ports.get(port.name)
            if visual_port:
                # Create new label
                label = QGraphicsTextItem(port.name, self)
                label.setDefaultTextColor(QColor("#bdc3c7"))
                label.setFont(QFont("Arial", 8))
                label.setPos(10, y_offset - 5)
                visited_labels.add(label)
            y_offset += 20
        
        # Update output port labels
        y_offset = 30
        for port in self.node_data.outputs:
            visual_port = self.visual_ports.get(port.name)
            if visual_port:
                label = QGraphicsTextItem(port.name, self)
                label.setDefaultTextColor(QColor("#bdc3c7"))
                label.setFont(QFont("Arial", 8))
                label.setPos(self.width - 30, y_offset - 5)
                visited_labels.add(label)
            y_offset += 20
        
        # Remove old labels
        for label in labels_to_remove:
            if label not in visited_labels:
                self.scene().removeItem(label)

    def mouseDoubleClickEvent(self, event):
        """Consume the event - let the scene handle double-click behavior."""
        # Let the scene handle double-click events exclusively
        # This prevents duplicate config dialogs
        event.accept()

class VisualLink(QGraphicsPathItem):
    """Visual line connecting two ports."""
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setZValue(-1) # Behind nodes
        
        pen = QPen(QColor("#f1c40f"), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        self.setPen(pen)
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        self.update_path()

    def update_path(self):
        if not self.start_item or not self.end_item:
            return
            
        p1 = self.start_item.mapToScene(self.start_item.rect().center())
        p2 = self.end_item.mapToScene(self.end_item.rect().center())
        
        path = QPainterPath()
        path.moveTo(p1)
        
        dx = p2.x() - p1.x()
        ctrl1 = QPointF(p1.x() + dx * 0.5, p1.y())
        ctrl2 = QPointF(p2.x() - dx * 0.5, p2.y())
        path.cubicTo(ctrl1, ctrl2, p2)
        
        self.setPath(path)

    def update_status(self):
        """Update link color based on signal value."""
        if not self.start_item or not hasattr(self.start_item, 'port_data'):
            return
            
        is_active = self.start_item.port_data.value
        
        if is_active:
            # Active signal: Bright Cyan/Aqua with thicker line
            pen = QPen(QColor("#00f2ff"), 3)
        else:
            # Inactive signal: Standard Gold
            pen = QPen(QColor("#f1c40f"), 2)
            
        self.setPen(pen)
        self.update() # Force repaint
