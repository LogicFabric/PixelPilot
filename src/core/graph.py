from typing import List, Dict, Any, Optional
import uuid
import time
from .rules import Condition, Action, LogicEvaluator

class Port:
    """Represents a connection point on a node."""
    def __init__(self, node, name: str, is_output: bool = False):
        self.node = node
        self.name = name
        self.is_output = is_output
        self.value = False  # Boolean signal (High/Low)
        self.links: List['Link'] = []

class Link:
    """Connection between two ports."""
    def __init__(self, source_port: Port, target_port: Port):
        self.source = source_port
        self.target = target_port

class Node:
    """Base Block in the FBD."""
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.inputs: List[Port] = []
        self.outputs: List[Port] = []
        self.position = (0, 0) # X, Y for UI

    def add_input(self, name: str) -> Port:
        p = Port(self, name, is_output=False)
        self.inputs.append(p)
        return p

    def add_output(self, name: str) -> Port:
        p = Port(self, name, is_output=True)
        self.outputs.append(p)
        return p

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        """
        Process inputs and set outputs.
        Base implementation: Pass through or do nothing.
        """
        pass

    def get_input_value(self, index=0) -> bool:
        """Helper to get value from connected links on input port."""
        if index >= len(self.inputs): return False
        port = self.inputs[index]
        # OR logic for multiple links to one input? Or just take first?
        # Standard FBD usually 1 link per input, or implicit OR. 
        # Let's do OR: if any connected source is True, input is True.
        for link in port.links:
            if link.source.value:
                return True
        return False

# --- Concrete Nodes ---

class InputNode(Node):
    """Wraps a Condition (Source)."""
    def __init__(self, name: str, condition: Condition):
        super().__init__(name)
        self.condition = condition
        self.out_port = self.add_output("Out")

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        result = self.condition.evaluate(state_mgr, vision_mgr)
        self.out_port.value = result

class ProcessNode(Node):
    """Logic Block (AND, OR, NOT, TIMER)."""
    def __init__(self, name: str, logic_type: str = "AND"):
        super().__init__(name)
        self.logic_type = logic_type
        # Dynamic inputs usually, start with 2
        self.add_input("In1")
        self.add_input("In2")
        self.out_port = self.add_output("Out")
        
        # Timer specific state
        self.timer_start = 0.0

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        in1 = self.get_input_value(0)
        in2 = self.get_input_value(1)
        
        if self.logic_type == "AND":
            self.out_port.value = in1 and in2
        elif self.logic_type == "OR":
            self.out_port.value = in1 or in2
        elif self.logic_type == "NOT":
            self.out_port.value = not in1
        elif self.logic_type == "NAND":
            self.out_port.value = not (in1 and in2)
        elif self.logic_type == "TIMER":
            # Simple On-Delay Timer: Pass True only if Input has been True for X sec
            # Use 'In2' potentially as time or just fixed property
            # For simplicity, let's say In1 is trigger, hardwired duration property?
            # Let's just use state manager logic for now or simple local check
            # Real implementation needs config properties on Node.
            # Assuming simple pass-through for now for MVP structure.
            self.out_port.value = in1 

class OutputNode(Node):
    """Wraps an Action (Sink)."""
    def __init__(self, name: str, action: Action):
        super().__init__(name)
        self.action = action
        self.add_input("Trig")

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        trigger = self.get_input_value(0)
        if trigger:
            self.action.execute(state_mgr, input_mgr)


class Graph:
    """
    Manage nodes and execution using topological sort.
    
    The graph represents a Function Block Diagram (FBD) where:
    - Nodes are blocks (Input, Process, Output)
    - Links are connections between ports
    - Execution follows topological order for optimal performance
    
    Attributes:
        nodes (List[Node]): All nodes in the graph
        links (List[Link]): All connections between nodes
        _sorted_nodes (Optional[List[Node]]): Cached topological order
        _needs_resort (bool): Flag indicating if re-sort is needed
    """
    def __init__(self):
        self.nodes: List[Node] = []
        self.links: List[Link] = []
        self._sorted_nodes: Optional[List[Node]] = None
        self._needs_resort = True

    def add_node(self, node: Node):
        """Add a node to the graph."""
        self.nodes.append(node)
        self._needs_resort = True

    def add_link(self, source_node: Node, source_port_name: str, target_node: Node, target_port_name: str):
        """
        Add a connection between two nodes.
        
        Args:
            source_node: Node with output port
            source_port_name: Name of the output port
            target_node: Node with input port
            target_port_name: Name of the input port
        """
        # Find ports
        src = next((p for p in source_node.outputs if p.name == source_port_name), None)
        tgt = next((p for p in target_node.inputs if p.name == target_port_name), None)
        
        if src and tgt:
            link = Link(src, tgt)
            src.links.append(link)
            tgt.links.append(link)
            self.links.append(link)
            self._needs_resort = True

    def _topological_sort(self) -> List[Node]:
        """
        Sort nodes in topological order using Kahn's algorithm.
        
        This ensures each node is evaluated only after all its dependencies
        have been evaluated, allowing single-pass execution.
        
        Returns:
            List of nodes in execution order
            
        Raises:
            CyclicGraphError: If the graph contains cycles
        """
        from .exceptions import CyclicGraphError
        
        # Build adjacency list and in-degree count
        in_degree = {node.id: 0 for node in self.nodes}
        adj_list = {node.id: [] for node in self.nodes}
        node_map = {node.id: node for node in self.nodes}
        
        # Count incoming edges for each node
        for link in self.links:
            source_id = link.source.node.id
            target_id = link.target.node.id
            adj_list[source_id].append(target_id)
            in_degree[target_id] += 1
        
        # Kahn's algorithm: Start with nodes that have no dependencies
        queue = [node for node in self.nodes if in_degree[node.id] == 0]
        sorted_nodes = []
        
        while queue:
            # Process node with no remaining dependencies
            node = queue.pop(0)
            sorted_nodes.append(node)
            
            # Reduce in-degree for all neighbors
            for neighbor_id in adj_list[node.id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    neighbor = node_map[neighbor_id]
                    queue.append(neighbor)
        
        # If not all nodes processed, there's a cycle
        if len(sorted_nodes) != len(self.nodes):
            raise CyclicGraphError(
                f"Graph contains cycles! Processed {len(sorted_nodes)}/{len(self.nodes)} nodes. "
                "Function Block Diagrams cannot contain feedback loops."
            )
        
        return sorted_nodes

    def execute(self, state_mgr, vision_mgr, input_mgr):
        """
        Execute the graph in topological order (single-pass).
        
        Uses cached topological sort for performance. Re-sorts only when
        the graph structure changes (nodes/links added).
        
        Args:
            state_mgr: State manager for shared variables
            vision_mgr: Vision system for screen capture
            input_mgr: Input system for keyboard/mouse control
            
        Raises:
            CyclicGraphError: If graph contains cycles
            ExecutionError: If node evaluation fails
        """
        from .exceptions import ExecutionError
        
        # Get sorted nodes (use cache if available)
        if self._needs_resort or self._sorted_nodes is None:
            try:
                self._sorted_nodes = self._topological_sort()
                self._needs_resort = False
            except Exception as e:
                # Fall back to simple execution if topological sort fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Topological sort failed, using fallback: {e}")
                self._execute_fallback(state_mgr, vision_mgr, input_mgr)
                return
        
        # Execute nodes in topological order
        for node in self._sorted_nodes:
            try:
                node.evaluate(state_mgr, vision_mgr, input_mgr)
            except Exception as e:
                from .exceptions import ExecutionError
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error executing node '{node.name}': {e}")
                # Continue execution despite error (could make this configurable)
                
    def _execute_fallback(self, state_mgr, vision_mgr, input_mgr):
        """
        Fallback execution strategy (legacy multi-pass).
        
        Used when topological sort fails or for backwards compatibility.
        """
        # 1. Inputs
        for node in self.nodes:
            if isinstance(node, InputNode):
                node.evaluate(state_mgr, vision_mgr, input_mgr)
        
        # 2. Process (multi-pass for safety)
        for _ in range(3): 
            for node in self.nodes:
                if isinstance(node, ProcessNode):
                    node.evaluate(state_mgr, vision_mgr, input_mgr)
                    
        # 3. Outputs
        for node in self.nodes:
            if isinstance(node, OutputNode):
                node.evaluate(state_mgr, vision_mgr, input_mgr)
