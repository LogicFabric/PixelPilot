import QtQuick

Item {
    width: parent.width
    height: parent.height
    
    // Dark gray background
    Rectangle {
        anchors.fill: parent
        color: "#1e1e1e"
    }
    
    // Grid pattern using Canvas
    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = canvas.context
            ctx.reset()
            
            // Set grid properties
            var gridSize = 20
            var lineColor = "#3e3e3e"
            
            // Draw vertical lines
            ctx.strokeStyle = lineColor
            ctx.lineWidth = 1
            
            for (var x = 0; x < width; x += gridSize) {
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, height)
                ctx.stroke()
            }
            
            // Draw horizontal lines
            for (var y = 0; y < height; y += gridSize) {
                ctx.beginPath()
                ctx.moveTo(0, y)
                ctx.lineTo(width, y)
                ctx.stroke()
            }
        }
        
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
}