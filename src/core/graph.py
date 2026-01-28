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
        self.is_memory_node = False # If True, breaks dependency cycles by using last tick's value

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
        """
        Helper to get value from connections on an input port.
        
        If links are connected, it returns True if any source is True (OR logic).
        If no links are connected, it returns the port's local value (fallback).
        """
        if index >= len(self.inputs): return False
        port = self.inputs[index]
        
        if port.links:
            for link in port.links:
                if link.source.value:
                    return True
            return False
            
        return port.value

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
    """Logic Block (AND, OR, NOT, NAND, etc.) with dynamic inputs."""
    def __init__(self, name: str, logic_type: str = "AND"):
        super().__init__(name)
        self.logic_type = logic_type
        self.out_port = self.add_output("Out")
        # Default to 2 inputs for backward compatibility
        self.add_input_port("In1")
        self.add_input_port("In2")

    def add_input_port(self, name: str) -> Port:
        """Add a named input port."""
        # Avoid duplicate names
        if any(p.name == name for p in self.inputs):
            return next(p for p in self.inputs if p.name == name)
        return self.add_input(name)

    def remove_input_port(self, name: str):
        """Remove an input port by name."""
        port = next((p for p in self.inputs if p.name == name), None)
        if port:
            # Clean up links
            for link in port.links[:]:
                if link.source and link.source.links:
                    link.source.links.remove(link)
                # We need to find the link in the graph's link list too, but Node doesn't have ref to Graph.
                # Usually link removal is managed by the Graph object.
                # For now, we assume the caller handles graph-level link cleanup.
                port.links.remove(link)
            self.inputs.remove(port)

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        # Only consider ports that have connections for AND/OR logic
        # This prevents unconnected inputs (False) from breaking AND gates
        connected_values = [self.get_input_value(i) for i, p in enumerate(self.inputs) if p.links]
        
        # If no connections, use all inputs (standard behavior)
        if not connected_values:
            input_values = [self.get_input_value(i) for i in range(len(self.inputs))]
        else:
            input_values = connected_values
        
        if not input_values and self.logic_type in ["AND", "OR", "NAND", "NOR"]:
             self.out_port.value = False
             return

        if self.logic_type == "AND":
            self.out_port.value = all(input_values)
        elif self.logic_type == "OR":
            self.out_port.value = any(input_values)
        elif self.logic_type == "NOT":
            self.out_port.value = not input_values[0] if input_values else True
        elif self.logic_type == "NAND":
            self.out_port.value = not all(input_values)
        elif self.logic_type == "NOR":
            self.out_port.value = not any(input_values)
        elif self.logic_type == "XOR":
            self.out_port.value = sum(input_values) % 2 == 1

class TimerNode(Node):
    """
    Advanced timing block supporting TON, TOF, and BLINK.
    """
    def __init__(self, name: str, timer_type: str = "TON"):
        super().__init__(name)
        self.timer_type = timer_type
        self.in_port = self.add_input("In")
        self.out_port = self.add_output("Out")
        
        # Properties (ms)
        self.delay_time = 1000.0  # Used for TON, TOF
        self.time_on = 500.0      # Used for BLINK
        self.time_off = 500.0     # Used for BLINK
        
        # State
        self.last_tick_time = None
        self.accumulator = 0.0
        self.is_running = False

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        now = time.perf_counter() * 1000.0 # Convert to ms
        
        if self.last_tick_time is None:
            self.last_tick_time = now
            return # Skip first tick to initialize
            
        dt = now - self.last_tick_time
        self.last_tick_time = now
        
        trigger = self.get_input_value(0)
        
        if self.timer_type == "TON":
            # On-Delay Timer
            if trigger:
                self.accumulator += dt
                if self.accumulator >= self.delay_time:
                    self.out_port.value = True
            else:
                self.accumulator = 0.0
                self.out_port.value = False
                
        elif self.timer_type == "TOF":
            # Off-Delay Timer
            if trigger:
                self.out_port.value = True
                self.accumulator = 0.0
            else:
                self.accumulator += dt
                if self.accumulator >= self.delay_time:
                    self.out_port.value = False
                    
        elif self.timer_type == "BLINK":
            # Pulse Generator
            if trigger:
                self.accumulator += dt
                total_cycle = self.time_on + self.time_off
                if total_cycle > 0:
                    phase = self.accumulator % total_cycle
                    self.out_port.value = phase < self.time_on
                else:
                    self.out_port.value = False
            else:
                self.accumulator = 0.0
                self.out_port.value = False

class ToggleNode(Node):
    """
    Stateful latching logic (T-Flip-Flop).
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.trig_port = self.add_input("Trigger")
        self.reset_port = self.add_input("Reset")
        self.out_port = self.add_output("Out")
        
        self.state = False
        self.prev_trigger = False

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        trigger = self.get_input_value(0)
        reset = self.get_input_value(1)
        
        # Rising Edge Detection
        if trigger and not self.prev_trigger:
            self.state = not self.state
            
        self.prev_trigger = trigger
        
        if reset:
            self.state = False
            
        self.out_port.value = self.state

class GroupInput(Node):
    """Special internal node for GroupNode inputs."""
    def __init__(self, name: str):
        super().__init__(name)
        self.out_port = self.add_output("Out")
        self.value = False

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        self.out_port.value = self.value

class GroupOutput(Node):
    """Special internal node for GroupNode outputs."""
    def __init__(self, name: str):
        super().__init__(name)
        self.in_port = self.add_input("In")
        self.value = False

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        self.value = self.get_input_value(0)

class GroupNode(Node):
    """
    Encapsulates a sub-graph as a single node.
    """
    def __init__(self, name: str):
        super().__init__(name)
        self.sub_graph = Graph()
        # Mapping: external_port_id -> internal_node_id
        self._input_mappings = {} 
        self._output_mappings = {}

    def add_external_input(self, name: str):
        port = self.add_input(name)
        internal_input = GroupInput(f"Internal_{name}")
        self.sub_graph.add_node(internal_input)
        self._input_mappings[port.name] = internal_input.id
        return port

    def add_external_output(self, name: str):
        port = self.add_output(name)
        internal_output = GroupOutput(f"Internal_{name}")
        self.sub_graph.add_node(internal_output)
        self._output_mappings[port.name] = internal_output.id
        return port

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        # Local node map for efficiency
        internal_node_map = {n.id: n for n in self.sub_graph.nodes}
        
        # 1. Forward external inputs to internal nodes
        for i, port in enumerate(self.inputs):
            internal_node_id = self._input_mappings.get(port.name)
            if internal_node_id in internal_node_map:
                internal_node_map[internal_node_id].value = self.get_input_value(i)
            
        # 2. Execute sub-graph (Recursive)
        self.sub_graph.execute(state_mgr, vision_mgr, input_mgr)
        
        # 3. Collect internal results to external outputs
        for i, port in enumerate(self.outputs):
            internal_node_id = self._output_mappings.get(port.name)
            if internal_node_id in internal_node_map:
                port.value = internal_node_map[internal_node_id].value

class OutputNode(Node):
    """Wraps an Action (Sink)."""
    def __init__(self, name: str, action: Action):
        super().__init__(name)
        self.action = action
        self.add_input("Trig")
        self.prev_trigger = False # State for edge detection

    def evaluate(self, state_mgr, vision_mgr, input_mgr):
        trigger = self.get_input_value(0)
        
        # Default to Rising-Edge Triggering for most actions
        # This prevents rapid-fire when signal stays High
        if trigger and not self.prev_trigger:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Output action triggered: {self.name} ({type(self.action).__name__})")
            
            try:
                self.action.execute(state_mgr, input_mgr)
            except Exception as e:
                logger.error(f"Failed to execute output action {self.name}: {e}")
        
        self.prev_trigger = trigger


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
        
        Feedback loops (cycles) are supported if they contain at least one
        MemoryNode (or any node with is_memory_node = True). Memory nodes
        effectively break the dependency chain for the current tick by 
        providing values from the previous tick.
        
        Returns:
            List of nodes in execution order
            
        Raises:
            CyclicGraphError: If the graph contains cycles that are not broken by memory nodes
        """
        from .exceptions import CyclicGraphError
        
        # Build adjacency list and in-degree count
        in_degree = {node.id: 0 for node in self.nodes}
        adj_list = {node.id: [] for node in self.nodes}
        node_map = {node.id: node for node in self.nodes}
        
        # Count incoming edges for each node
        for link in self.links:
            # Memory nodes break the cycle: their outputs are available at start of tick
            # so they don't count as a "dependency" for the target node's evaluation
            if getattr(link.source.node, 'is_memory_node', False):
                continue
                
            source_id = link.source.node.id
            target_id = link.target.node.id
            adj_list[source_id].append(target_id)
            in_degree[target_id] += 1
        
        # Kahn's algorithm: Start with nodes that have no dependencies (including memory node targets)
        queue = [node for node in self.nodes if in_degree[node.id] == 0]
        sorted_nodes = []
        
        while queue:
            # Sort queue by ID to ensure deterministic execution order for same-level nodes
            queue.sort(key=lambda n: n.id)
            
            # Process node with no remaining dependencies
            node = queue.pop(0)
            sorted_nodes.append(node)
            
            # Reduce in-degree for all neighbors
            for neighbor_id in adj_list[node.id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    neighbor = node_map[neighbor_id]
                    queue.append(neighbor)
        
        # If not all nodes processed, there's a hard cycle (no memory node to break it)
        if len(sorted_nodes) != len(self.nodes):
            remaining = [node.name for node in self.nodes if node not in sorted_nodes]
            raise CyclicGraphError(
                f"Graph contains unbreakable cycles! Stuck at nodes: {remaining}. "
                "Feedback loops must be broken by a Memory Node to ensure deterministic execution."
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
