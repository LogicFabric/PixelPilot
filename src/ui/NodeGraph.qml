import QtQuick

Item {
    id: nodeGraph
    
    // Main container for the entire graph
    width: parent.width
    height: parent.height
    
    // World item that can be panned
    Item {
        id: world
        width: parent.width * 2  // Large enough to allow panning
        height: parent.height * 2
        
        // Grid background
        GridBackground {
            anchors.fill: parent
        }
        
        // Test node 1
        NodeBlock {
            id: testNode1
            x: 100
            y: 100
        }
        
        // Test node 2
        NodeBlock {
            id: testNode2
            x: 300
            y: 200
        }
        
        // Test node 3
        NodeBlock {
            id: testNode3
            x: 500
            y: 150
            // Change title to show different type
            Text {
                text: "Process: Filter"
                color: "white"
                font.pixelSize: 12
                anchors.centerIn: parent
                font.bold: true
                z: 1
            }
        }
    }
    
    // Pan functionality - click and drag the background to move view
    MouseArea {
        id: panMouseArea
        anchors.fill: parent
        drag.target: world
        drag.axis: Drag.XAndYAxis
        drag.minimumX: -parent.width
        drag.maximumX: 0
        drag.minimumY: -parent.height
        drag.maximumY: 0
        
        // Handle panning with mouse
        onPressed: {
            // Capture the initial position for panning
        }
        
        onPositionChanged: {
            // Update the world position based on mouse movement
        }
    }
    
    // Optional zoom functionality (structure ready)
    // This would be implemented with Scale attached to world item
}