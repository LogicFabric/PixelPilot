import threading
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import core components 
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.state import StateManager
from src.core.engine import AutomationEngine
from src.core.graph import Graph, Node, InputNode, ProcessNode, OutputNode
from src.strategies.vision import VisionManager, MockVisionStrategy
from src.strategies.input import InputManager

# Initialize FastAPI app
app = FastAPI(title="PixelPilot API Server", version="0.1.0")

# Global state management
state_manager = StateManager()
graph = Graph()

# Create a vision manager that will use mock strategy for headless environments
try:
    # Try to initialize with the default (will auto-detect and fallback)
    vision_manager = VisionManager(use_mock=False)
    
    # If we're in a headless environment or if no valid strategy was found, force mock
    if vision_manager.strategy is None:
        print("No valid vision strategy found, forcing mock strategy")
        vision_manager = VisionManager(use_mock=True)
        
except Exception as e:
    print(f"Failed to initialize vision manager, using mock: {e}")
    vision_manager = VisionManager(use_mock=True)

engine = AutomationEngine(
    vision_manager=vision_manager,
    input_manager=InputManager(),
    state_manager=state_manager
)

# Store node IDs for linking
node_id_map: Dict[str, str] = {}

class NodeCreate(BaseModel):
    type: str  # "Input", "Process", "Output"
    name: str

class LinkCreate(BaseModel):
    source_node: str  # Can be ID or name
    target_node: str  # Can be ID or name
    source_port: str = "Out"
    target_port: str = "In"

class EngineControl(BaseModel):
    action: str  # "start" or "stop"

@app.get("/health")
async def health_check():
    """Check if the server is running and get node count."""
    return {
        "status": "ok", 
        "nodes": len(graph.nodes),
        "vision_strategy": type(vision_manager.strategy).__name__ if vision_manager.strategy else "None"
    }

@app.post("/graph/node")
async def add_node(node: NodeCreate):
    """Add a new node to the graph."""
    try:
        # Create node based on type
        if node.type == "Input":
            # For now, create a simple input node with dummy condition
            from src.core.rules import Condition
            condition = Condition(lambda state, vision, input_mgr: True)  # Dummy condition
            new_node = InputNode(node.name, condition)
            
        elif node.type == "Process":
            new_node = ProcessNode(node.name)
            
        elif node.type == "Output":
            # For now, create a simple output node with dummy action
            from src.core.rules import Action
            action = Action(lambda state, input_mgr: None)  # Dummy action
            new_node = OutputNode(node.name, action)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown node type: {node.type}")
        
        # Add to graph
        graph.add_node(new_node)
        node_id_map[node.name] = new_node.id
        
        return {
            "message": f"Node '{node.name}' added successfully",
            "id": new_node.id,
            "type": node.type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add node: {str(e)}")

@app.post("/graph/link")
async def link_nodes(link: LinkCreate):
    """Link two nodes together."""
    try:
        # Find source and target nodes
        source_node = None
        target_node = None
        
        # Try to find by ID first, then by name
        for node in graph.nodes:
            if node.id == link.source_node or node.name == link.source_node:
                source_node = node
            if node.id == link.target_node or node.name == link.target_node:
                target_node = node
                
        if not source_node:
            raise HTTPException(status_code=404, detail=f"Source node '{link.source_node}' not found")
        if not target_node:
            raise HTTPException(status_code=404, detail=f"Target node '{link.target_node}' not found")
        
        # Create link
        graph.add_link(source_node, link.source_port, target_node, link.target_port)
        
        return {
            "message": f"Linked '{source_node.name}' to '{target_node.name}'",
            "source": source_node.id,
            "target": target_node.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link nodes: {str(e)}")

@app.post("/engine/control")
async def control_engine(control: EngineControl):
    """Control the automation engine."""
    try:
        if control.action == "start":
            # Set the graph in the engine
            engine.set_graph(graph)
            # Start engine in background thread
            engine.start(blocking=False)
            return {"message": "Engine started successfully"}
            
        elif control.action == "stop":
            engine.stop()
            return {"message": "Engine stopped successfully"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {control.action}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to control engine: {str(e)}")

# Start the engine in background when server starts
def start_engine_background():
    """Start the automation engine in a background thread."""
    # Set the graph in the engine
    engine.set_graph(graph)
    # Start engine in background thread
    engine.start(blocking=False)

# Initialize and start the engine when the server starts
if __name__ == "__main__":
    # This is just for running directly, but normally it will be run via uvicorn
    start_engine_background()