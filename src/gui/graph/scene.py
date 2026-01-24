from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPathItem
from PyQt6.QtCore import Qt, QLineF
from PyQt6.QtGui import QColor, QPen, QTransform, QBrush

from src.core.graph import Graph, Node
from .graphics import VisualNode, VisualLink, VisualPort

class FBDScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor("#2c3e50")))
        self.setSceneRect(0, 0, 5000, 5000)
        
        self.graph = Graph()
        self.visual_nodes = {}
        
        # Interaction state
        self.temp_link = None
        self.start_port_item = None

    def add_visual_node(self, node: Node, x: int, y: int):
        node.position = (x, y)
        self.graph.add_node(node)
        
        vn = VisualNode(node)
        vn.setPos(x, y)
        self.addItem(vn)
        self.visual_nodes[node.id] = vn

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, VisualPort):
            self.start_port_item = item
            self.temp_link = QGraphicsPathItem() # Placeholder
            self.temp_link.setPen(QPen(QColor("#f1c40f"), 2, Qt.PenStyle.DashLine))
            self.addItem(self.temp_link)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_link and self.start_port_item:
            # Draw temp line
            p1 = self.start_port_item.mapToScene(self.start_port_item.rect().center())
            p2 = event.scenePos()
            line = QLineF(p1, p2)
            # Simple line for drag visual
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(p2)
            self.temp_link.setPath(path)
            
        super().mouseMoveEvent(event)
        
        # Update existing links if dragging nodes
        if self.selectedItems():
            for item in self.items():
                if isinstance(item, VisualLink):
                    item.update_path()

    def mouseReleaseEvent(self, event):
        if self.temp_link:
            self.removeItem(self.temp_link)
            self.temp_link = None
            
            # Check drop target
            end_item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(end_item, VisualPort) and end_item != self.start_port_item:
                # Validate inputs vs outputs
                src = self.start_port_item
                tgt = end_item
                
                # Check different nodes
                if src.parentItem() == tgt.parentItem():
                    super().mouseReleaseEvent(event)
                    return
                
                # Link logic in core
                self.graph.add_link(
                    src.port_data.node, src.port_data.name,
                    tgt.port_data.node, tgt.port_data.name
                )
                
                # Add Visual Link
                vl = VisualLink(src, tgt)
                self.addItem(vl)
                
            self.start_port_item = None
            
        super().mouseReleaseEvent(event)
