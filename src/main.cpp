#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QTimer>
#include "backend/WaylandScreenGrabber.h"

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    
    // @AI-CONTRACT (UI Framework: Qt Quick ONLY)
    // NEVER suggest or use QWidget or .ui files
    QQmlApplicationEngine engine;
    
    // Load the QML file from the module URI
    const QUrl url(u"qrc:/PixelPilot/src/ui/Main.qml"_qs);
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);
    
    engine.load(url);
    
    // Create and initialize the Wayland screen grabber
    // @AI-CONTRACT (Wayland Capture)
    // NEVER use QScreen::grabWindow or QPixmap::grabWindow. MUST route all capture through WaylandGrabber.
    WaylandScreenGrabber* screenGrabber = new WaylandScreenGrabber(&app);
    
    // @AI-CONTRACT (Signal Syntax: Qt 6)
    // MUST use Qt 6 function-pointer syntax. NO old macros.
    QTimer::singleShot(0, screenGrabber, &WaylandScreenGrabber::initCapture);
    
    return app.exec();
}