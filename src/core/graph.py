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
    """Manage nodes and execution."""
    def __init__(self):
        self.nodes: List[Node] = []
        self.links: List[Link] = []

    def add_node(self, node: Node):
        self.nodes.append(node)

    def add_link(self, source_node: Node, source_port_name: str, target_node: Node, target_port_name: str):
        # Find ports
        src = next((p for p in source_node.outputs if p.name == source_port_name), None)
        tgt = next((p for p in target_node.inputs if p.name == target_port_name), None)
        
        if src and tgt:
            link = Link(src, tgt)
            src.links.append(link)
            tgt.links.append(link)
            self.links.append(link)

    def execute(self, state_mgr, vision_mgr, input_mgr):
        """
        Execute the graph.
        Naive approach: Multiple passes or Topological sort.
        Since we have simple logic without loops (hopefully), we can just:
        1. Evaluate all InputNodes
        2. Evaluate all ProcessNodes (might need ordered pass if chained)
        3. Evaluate all OutputNodes
        
        Better: Topological Sort execution.
        """
        # 1. Inputs
        for node in self.nodes:
            if isinstance(node, InputNode):
                node.evaluate(state_mgr, vision_mgr, input_mgr)
        
        # 2. Process (Iterative or Sorted)
        # Simple iterative propagation for MVP (multiple passes if deep depth, or just sort)
        # Let's do a simple multi-pass for depth=3
        for _ in range(3): 
            for node in self.nodes:
                if isinstance(node, ProcessNode):
                    node.evaluate(state_mgr, vision_mgr, input_mgr)
                    
        # 3. Outputs
        for node in self.nodes:
            if isinstance(node, OutputNode):
                node.evaluate(state_mgr, vision_mgr, input_mgr)
