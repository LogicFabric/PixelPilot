#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QTimer>
#include "backend/WaylandScreenGrabber.h"

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
    
    // Create and initialize the Wayland screen grabber
    WaylandScreenGrabber* screenGrabber = new WaylandScreenGrabber(&app);
    
    // Initialize capture after the app starts (0ms delay)
    QTimer::singleShot(0, screenGrabber, &WaylandScreenGrabber::initCapture);
    
    return app.exec();
}