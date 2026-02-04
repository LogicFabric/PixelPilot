cmake_minimum_required(VERSION 3.16)
project(PixelPilotApp)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Find required Qt packages
find_package(Qt6 REQUIRED COMPONENTS Quick Core Gui Concurrent DBus)

add_executable(PixelPilotApp
    src/main.cpp
    src/backend/WaylandScreenGrabber.cpp
)

# Bundle QML files into the binary
qt_add_qml_module(PixelPilotApp
    URI "PixelPilot"
    VERSION 1.0
    QML_FILES 
        src/ui/Main.qml
        src/ui/NodeGraph.qml
        src/ui/components/GridBackground.qml
        src/ui/components/NodeBlock.qml
)

target_link_libraries(PixelPilotApp PRIVATE
    Qt6::Quick
    Qt6::Core
    Qt6::Gui
    Qt6::Concurrent
    Qt6::DBus
)

# Include directories for backend
target_include_directories(PixelPilotApp PRIVATE
    src/backend
)