from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt

class FBGraphicsView(QGraphicsView):
    """
    Custom Graphics View that handles drag behavior appropriately for FBD connectors.
    Prevents rubber band selection when dragging from ports.
    """
    def __init__(self, scene=None):
        super().__init__(scene)
        # Default to rubber band drag for normal operations
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
    def mousePressEvent(self, event):
        """
        Override mouse press to disable rubber band drag when interacting with ports.
        """
        # Get the item at the click position
        scene_pos = self.mapToScene(event.pos())
        items = self.scene().items(scene_pos)
        
        port_found = False
        for item in items:
            from .graphics import VisualPort
            if isinstance(item, VisualPort):
                port_found = True
                break
        
        if port_found:
            # Temporarily disable rubber band drag when clicking on ports
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            # Re-enable rubber band drag for normal operations
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """
        Restore normal drag mode after mouse release.
        """
        # Always restore rubber band drag after release
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().mouseReleaseEvent(event)