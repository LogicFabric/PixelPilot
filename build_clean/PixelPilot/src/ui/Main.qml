import QtQuick
import QtQuick.Controls

Window {
    width: 1024
    height: 768
    visible: true
    title: "PixelPilot - Wayland Automation"
    color: "#2d2d2d"
    
    // Main NodeGraph container
    NodeGraph {
        anchors.fill: parent
    }
}