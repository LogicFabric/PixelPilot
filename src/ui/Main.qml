import QtQuick
import QtQuick.Controls
import PixelPilot
import "components"

// @AI-CONTRACT (UI Framework: Qt Quick ONLY)
// NEVER suggest or use QWidget or .ui files.
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
