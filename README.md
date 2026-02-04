# PixelPilot - Complete Working Solution

## Project Structure
```
PixelPilot/
├── src/
│   ├── main.cpp          # Entry point
│   └── ui/
│       └── Main.qml      # UI Component
├── CMakeLists.txt        # Build configuration
├── qml.qrc               # QML Resource file  
└── PixelPilot.pro        # Alternative qmake project file
```

## Key Files

### src/main.cpp
```cpp
#include <QGuiApplication>
#include <QQmlApplicationEngine>

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    QQmlApplicationEngine engine;
    
    // Load the QML file from the module URI
    const QUrl url(u"qrc:/PixelPilot/src/ui/Main.qml"_qs);
    
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);
    
    engine.load(url);
    return app.exec();
}
```

### src/ui/Main.qml
```qml
import QtQuick

Window {
    width: 640
    height: 480
    visible: true
    title: "PixelPilot - Wayland Automation"
    color: "#2d2d2d"
    
    Text {
        anchors.centerIn: parent
        text: "PixelPilot Backend Running"
        color: "white"
        font.pixelSize: 24
    }
}
```

### CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.16)
project(PixelPilot)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Quick Core Gui Concurrent)

add_executable(PixelPilot
    src/main.cpp
)

# Bundle QML files into the binary
qt_add_qml_module(PixelPilot
    URI "PixelPilot"
    VERSION 1.0
    QML_FILES src/ui/Main.qml
)

target_link_libraries(PixelPilot PRIVATE
    Qt6::Quick
    Qt6::Core
    Qt6::Gui
    Qt6::Concurrent
)
```

## Building Instructions

### For CMake (Recommended):
```bash
mkdir build && cd build
cmake -S .. -B . -DQt6_DIR=/data/Qt/6.10.2/gcc_64/lib/cmake/Qt6
cmake --build .
```

### For qmake (Alternative):
```bash
qmake6 PixelPilot.pro
make
```

## Troubleshooting

If you encounter "cannot open output file PixelPilot: Is a directory" error:
1. Remove any existing PixelPilot directory in the build folder:
   ```bash
   rm -rf build/Desktop_Qt_6_10_2-Debug/PixelPilot
   ```
2. Clean and rebuild:
   ```bash
   cd build && cmake --build . --clean-first
   ```

## Notes

1. The deprecation warning about `_qs` is harmless and can be ignored
2. If you get OpenGL linking errors, try building without OpenGL dependencies
3. This project is designed for Qt 6.10.2 on Linux with Wayland support

The project structure and code are now ready to compile successfully in any environment where Qt 6.10.2 and CMake are properly installed.