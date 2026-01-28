from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPathItem
from PyQt6.QtCore import Qt, QLineF, QRectF
from PyQt6.QtGui import QColor, QPen, QTransform, QBrush

from src.core.graph import Graph, Node
from .graphics import VisualNode, VisualLink, VisualPort

class FBDScene(QGraphicsScene):
    """
    Dynamic canvas for Function Block Diagram editing.
    
    Starts with a compact size and expands automatically when
    nodes approach the edges. Scroll bars appear only when needed.
    """

    # Padding around nodes (pixels)
    PADDING = 100
    # Minimum scene size
    # Minimum scene size
    MIN_WIDTH = 600
    MIN_HEIGHT = 400

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor("#2c3e50")))
        # Start with minimum size - will expand as needed
        self.setSceneRect(0, 0, self.MIN_WIDTH, self.MIN_HEIGHT)
        
        self.graph = Graph()
        self.visual_nodes = {}
        
        # Interaction state
        self.temp_link = None
        self.start_port_item = None

    def keyPressEvent(self, event):
        """Handle deletion of selected items."""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self._delete_selected_items()
        super().keyPressEvent(event)

    def _delete_selected_items(self):
        """Remove selected nodes and links from both GUI and core graph."""
        selected = self.selectedItems()
        if not selected:
            return
            
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Separate items by type
        nodes_to_delete = [item for item in selected if isinstance(item, VisualNode)]
        links_to_delete = [item for item in selected if isinstance(item, VisualLink)]
        
        # 2. Process Links
        for vl in links_to_delete:
            # Remove from core graph
            # A Link object itself holds source/target ports.
            # We need to find the Link in graph.links that matches
            src_port = vl.start_item.port_data
            tgt_port = vl.end_item.port_data
            
            # Find and remove from graph
            found_core_link = None
            for link in self.graph.links:
                if link.source == src_port and link.target == tgt_port:
                    found_core_link = link
                    break
            
            if found_core_link:
                self.graph.links.remove(found_core_link)
                # Also remove from port link lists
                if found_core_link in src_port.links: src_port.links.remove(found_core_link)
                if found_core_link in tgt_port.links: tgt_port.links.remove(found_core_link)
            
            self.removeItem(vl)
            logger.info(f"Deleted link between {src_port.node.name} and {tgt_port.node.name}")

        # 3. Process Nodes
        for vn in nodes_to_delete:
            node = vn.node_data
            
            # Remove all associated visual links first
            for item in list(self.items()):
                if isinstance(item, VisualLink):
                    if item.start_item.port_data.node == node or item.end_item.port_data.node == node:
                        # Recursive delete for associated links logic (logical)
                        src_p = item.start_item.port_data
                        tgt_p = item.end_item.port_data
                        
                        links_matching = [l for l in self.graph.links if l.source == src_p and l.target == tgt_p]
                        for l in links_matching:
                            self.graph.links.remove(l)
                            if l in src_p.links: src_p.links.remove(l)
                            if l in tgt_p.links: tgt_p.links.remove(l)
                            
                        self.removeItem(item)

            # Remove node from graph
            if node in self.graph.nodes:
                self.graph.nodes.remove(node)
                
            self.removeItem(vn)
            self.visual_nodes.pop(node.id, None)
            logger.info(f"Deleted node: {node.name}")
            
        self.graph._needs_resort = True
        self.update_scene_rect()


    def add_visual_node(self, node: Node, x: int, y: int):
        node.position = (x, y)
        self.graph.add_node(node)
        
        vn = VisualNode(node)
        vn.setPos(x, y)
        self.addItem(vn)
        self.visual_nodes[node.id] = vn
        
        # Expand canvas if needed
        self.update_scene_rect()
        return vn
    
    def _create_visual_node_from_existing(self, node: Node):
        """
        Create visual representation for an already-loaded node.
        
        Used when loading from file where nodes are already in the graph.
        Does not call graph.add_node() again.
        """
        vn = VisualNode(node)
        vn.setPos(node.position[0], node.position[1])
        self.addItem(vn)
        self.visual_nodes[node.id] = vn
        
        # Expand canvas if needed
        self.update_scene_rect()
        return vn

    def mousePressEvent(self, event):
        # First check for ports at the click position
        items = self.items(event.scenePos())
        for item in items:
            if isinstance(item, VisualPort):
                self.start_port_item = item
                self.temp_link = QGraphicsPathItem() # Placeholder
                self.temp_link.setPen(QPen(QColor("#f1c40f"), 2, Qt.PenStyle.DashLine))
                self.temp_link.setZValue(1) # Higher priority than nodes
                self.addItem(self.temp_link)
                return  # Consume the event
        
        # If no port found, let the default behavior handle it
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
            # Auto-expand canvas if nodes near edge
            self.update_scene_rect()
    
    def update_scene_rect(self):
        """
        Dynamically adjust scene rect to fit all nodes with padding.
        Expands when nodes approach edges, shrinks when appropriate.
        """
        if not self.visual_nodes:
            # Reset to minimum if empty
            self.setSceneRect(0, 0, self.MIN_WIDTH, self.MIN_HEIGHT)
            return
        
        # Get bounding rect of all items
        items_rect = self.itemsBoundingRect()
        
        if items_rect.isEmpty():
            self.setSceneRect(0, 0, self.MIN_WIDTH, self.MIN_HEIGHT)
            return
        
        # Calculate required size with padding
        new_width = max(self.MIN_WIDTH, items_rect.right() + self.PADDING)
        new_height = max(self.MIN_HEIGHT, items_rect.bottom() + self.PADDING)
        
        # Only update if size changed significantly (avoid constant updates)
        current = self.sceneRect()
        if (abs(new_width - current.width()) > 50 or 
            abs(new_height - current.height()) > 50):
            self.setSceneRect(0, 0, new_width, new_height)

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
                vl.setZValue(1) # Higher priority than nodes
                self.addItem(vl)
                
            self.start_port_item = None
            
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        # The visual node is a group-like item, usually click hits the Rect or Child Text
        # VisualNode inherits QGraphicsRectItem, so 'item' might be the node itself or a child
        
        node_item = None
        if isinstance(item, VisualNode):
            node_item = item
        elif item and isinstance(item.parentItem(), VisualNode):
            node_item = item.parentItem()
            
        if node_item:
            self.open_config_dialog(node_item)
            
        super().mouseDoubleClickEvent(event)

    def open_config_dialog(self, visual_node):
        from .dialogs import InputConfigDialog, ProcessConfigDialog, OutputConfigDialog
        from src.core.graph import InputNode, ProcessNode, OutputNode
        
        node = visual_node.node_data
        dialog = None
        
        if isinstance(node, InputNode):
            dialog = InputConfigDialog(node)
        elif isinstance(node, ProcessNode):
            dialog = ProcessConfigDialog(node)
        elif isinstance(node, OutputNode):
            dialog = OutputConfigDialog(node)
            
        if dialog and dialog.exec():
            # Update Visuals if needed (e.g. name changed)
            visual_node.title_item.setPlainText(node.name)

    def contextMenuEvent(self, event):
        """Right-click menu for scene actions."""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        
        selected_nodes = [item for item in self.selectedItems() if isinstance(item, VisualNode)]
        
        if selected_nodes:
            group_action = menu.addAction("📦 Group Selected Nodes")
            group_action.triggered.connect(lambda: self.group_selected_nodes(selected_nodes))
        else:
            # General scene actions
            add_input = menu.addAction("📥 Add Input Block")
            # These would need access to MainWindow methods, but can be implemented via signals or parent calls
            
        menu.exec(event.screenPos())

    def group_selected_nodes(self, visual_nodes):
        """
        Encapsulate selected nodes into a single GroupNode.
        
        This moves nodes from the main graph to a sub-graph and
        reconstructs links where possible.
        """
        from src.core.graph import GroupNode
        import logging
        logger = logging.getLogger(__name__)
        
        if not visual_nodes:
            return
            
        group_node = GroupNode("New Group")
        node_ids = set(vn.node_data.id for vn in visual_nodes)
        
        # Calculate center for GroupNode placement
        center = QRectF()
        for vn in visual_nodes:
            center = center.united(vn.sceneBoundingRect())
        pos = center.center()

        # 1. Identify Links to transfer or remap
        internal_links = []
        boundary_links = [] # Links crossing the boundary: (src, tgt, is_src_internal)
        
        for link in list(self.graph.links):
            src_in = link.source.node.id in node_ids
            tgt_in = link.target.node.id in node_ids
            
            if src_in and tgt_in:
                internal_links.append(link)
                self.graph.links.remove(link)
            elif src_in:
                # Inside -> Outside (Source is internal)
                boundary_links.append((link, True))
                self.graph.links.remove(link)
            elif tgt_in:
                # Outside -> Inside (Target is internal)
                boundary_links.append((link, False))
                self.graph.links.remove(link)

        # 2. Transfer Nodes
        for vn in visual_nodes:
            node = vn.node_data
            if node in self.graph.nodes:
                self.graph.nodes.remove(node)
            group_node.sub_graph.add_node(node)
            
            # Remove from UI
            self.removeItem(vn)
            self.visual_nodes.pop(node.id, None)

        # 3. Handle Boundary Links (Auto-mapping)
        external_links_to_add = [] # (src_node, src_port, tgt_node, tgt_port)
        
        for link, is_src_internal in boundary_links:
            if is_src_internal:
                # Internal -> External
                # Create external port on group
                port_name = f"Out_{link.source.name}_{link.source.node.name[:5]}"
                ext_port = group_node.add_external_output(port_name)
                
                # Internal: Link source to GroupOutput
                # group_node.add_external_output already created the GroupOutput node
                int_output_id = group_node._output_mappings[port_name]
                int_output_node = next(n for n in group_node.sub_graph.nodes if n.id == int_output_id)
                group_node.sub_graph.add_link(link.source.node, link.source.name, int_output_node, "In")
                
                # External: Queue link from GroupNode to original target
                external_links_to_add.append((group_node, port_name, link.target.node, link.target.name))
            else:
                # External -> Internal
                # Create external port on group
                port_name = f"In_{link.target.name}_{link.target.node.name[:5]}"
                ext_port = group_node.add_external_input(port_name)
                
                # Internal: Link GroupInput to internal target
                int_input_id = group_node._input_mappings[port_name]
                int_input_node = next(n for n in group_node.sub_graph.nodes if n.id == int_input_id)
                group_node.sub_graph.add_link(int_input_node, "Out", link.target.node, link.target.name)
                
                # External: Queue link from original source to GroupNode
                external_links_to_add.append((link.source.node, link.source.name, group_node, port_name))

        # 4. Transfer Internal Links
        for link in internal_links:
            group_node.sub_graph.links.append(link)

        # 5. Remove all visual links associated with these nodes
        for item in list(self.items()):
            if isinstance(item, VisualLink):
                if (item.start_item.node_data.id in node_ids if hasattr(item.start_item, 'node_data') else False or 
                    item.end_item.node_data.id in node_ids if hasattr(item.end_item, 'node_data') else False):
                    # This check is a bit messy because VisualLink stores start_item which is a VisualPort
                    pass
        
        # Simpler: just clear all links and let the user/system redraw? 
        # No, let's just find items that belong to deleted nodes.
        for item in list(self.items()):
            if isinstance(item, VisualLink):
                # VisualLink.start_item is a VisualPort, parent is VisualNode
                src_vnode = item.start_item.parentItem()
                tgt_vnode = item.end_item.parentItem()
                if src_vnode in visual_nodes or tgt_vnode in visual_nodes:
                    self.removeItem(item)

        # 6. Add GroupNode to main graph
        v_group = self.add_visual_node(group_node, int(pos.x()), int(pos.y()))
        
        # 7. Add External visual links
        for src_node, src_p_name, tgt_node, tgt_p_name in external_links_to_add:
            self.graph.add_link(src_node, src_p_name, tgt_node, tgt_p_name)
            # Find visual items to create visual link
            # This is slow but needed for now
            src_v = self.visual_nodes.get(src_node.id)
            tgt_v = self.visual_nodes.get(tgt_node.id)
            if src_v and tgt_v:
                src_p = next((c for c in src_v.childItems() if hasattr(c, 'port_data') and c.port_data.name == src_p_name), None)
                tgt_p = next((c for c in tgt_v.childItems() if hasattr(c, 'port_data') and c.port_data.name == tgt_p_name), None)
                if src_p and tgt_p:
                    self.addItem(VisualLink(src_p, tgt_p))

        # Important: Trigger re-sort of main graph
        self.graph._needs_resort = True
        logger.info(f"Grouped {len(visual_nodes)} nodes into {group_node.name}. Boundary links re-mapped.")
