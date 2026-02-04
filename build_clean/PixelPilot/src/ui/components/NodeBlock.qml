import QtQuick

Item {
    id: nodeBlock
    
    width: 160
    height: 80
    
    // Main rectangle with rounded corners
    Rectangle {
        id: blockRect
        anchors.fill: parent
        radius: 8
        color: "#2d2d2d"
        border.color: "#555555"
        border.width: 1
        
        // Header bar - blue by default
        Rectangle {
            id: headerBar
            width: parent.width
            height: 25
            color: "#3478e6"  // Blue header
            radius: 8  // Rounded corners matching the block
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            
            Text {
                id: titleText
                text: "Input: OCR"
                color: "white"
                font.pixelSize: 12
                anchors.centerIn: parent
                font.bold: true
            }
        }
        
        // Input port (left)
        Rectangle {
            id: inputPort
            width: 12
            height: 12
            radius: 6
            color: "#4caf50"  // Green for input
            anchors.left: parent.left
            anchors.leftMargin: -6
            anchors.verticalCenter: parent.height / 2
            
            // Add a border to make it more visible
            border.color: "white"
            border.width: 1
        }
        
        // Output port (right)
        Rectangle {
            id: outputPort
            width: 12
            height: 12
            radius: 6
            color: "#ff9800"  // Orange for output
            anchors.right: parent.right
            anchors.rightMargin: -6
            anchors.verticalCenter: parent.height / 2
            
            // Add a border to make it more visible
            border.color: "white"
            border.width: 1
        }
    }
    
    // Drag handler for moving the block
    DragHandler {
        id: dragHandler
        target: nodeBlock
        onActiveChanged: {
            if (active) {
                nodeBlock.z = 10  // Bring to front when dragging
            } else {
                nodeBlock.z = 0   // Return to normal z-order
            }
        }
    }
}