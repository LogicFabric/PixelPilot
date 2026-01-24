from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont

class VisualPort(QGraphicsRectItem):
    """Visual representation of a Port."""
    def __init__(self, port_data, parent=None):
        super().__init__(parent)
        self.port_data = port_data
        self.setRect(0, 0, 10, 10)
        
        if port_data.is_output:
            self.setBrush(QBrush(QColor("#e74c3c"))) # Red for output
        else:
            self.setBrush(QBrush(QColor("#2ecc71"))) # Green for input
            
        self.setPen(QPen(Qt.GlobalColor.black))
        
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
            vp.setPos(-5, y_offset)
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
            vp.setPos(self.width - 5, y_offset)
            self.visual_ports[port.name] = vp
            
            label = QGraphicsTextItem(port.name, self)
            label.setDefaultTextColor(QColor("#bdc3c7"))
            label.setFont(QFont("Arial", 8))
            label.setPos(self.width - 30, y_offset - 5)
            
            y_offset += 20

        # Adjust height if needed
        self.height = max(self.height, y_offset + 10)
        self.setRect(0, 0, self.width, self.height)

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
