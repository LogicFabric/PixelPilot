#include "WaylandScreenGrabber.h"
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDebug>

WaylandScreenGrabber::WaylandScreenGrabber(QObject *parent)
    : QObject(parent)
{
}

void WaylandScreenGrabber::initCapture()
{
    qDebug() << "Attempting to create Wayland screen capture session...";

    // Create DBus message to call org.freedesktop.portal.Desktop.CreateSession
    QDBusMessage message = QDBusMessage::createMethodCall(
        "org.freedesktop.portal.Desktop",           // Service
        "/org/freedesktop/portal/desktop",          // Path
        "org.freedesktop.portal.ScreenCast",        // Interface
        "CreateSession"                             // Method
    );

    // Add parameters for the CreateSession call
    QVariantMap options;
    options["handle_token"] = "pixel_pilot_session_123";
    options["session_handle_token"] = "session_token_456";
    
    message.setArguments(QVariantList() << options);

    // Send the message and get reply
    QDBusConnection connection = QDBusConnection::sessionBus();
    QDBusMessage reply = connection.call(message, QDBus::Block, 10000); // 10 second timeout

    if (reply.type() == QDBusMessage::ReplyMessage) {
        qDebug() << "DBus call successful!";
        handleDBusResponse(reply);
    } else {
        QString errorMessage = QString("DBus call failed: %1").arg(reply.errorName());
        qDebug() << errorMessage;
        emit errorOccurred(errorMessage);
    }
}

void WaylandScreenGrabber::handleDBusResponse(const QDBusMessage &message)
{
    // Extract the response data
    QList<QVariant> arguments = message.arguments();
    
    if (arguments.isEmpty()) {
        qWarning() << "Empty DBus response";
        return;
    }
    
    // The first argument should be a QVariantMap containing session info
    QVariant firstArg = arguments.first();
    
    if (firstArg.canConvert<QVariantMap>()) {
        QVariantMap responseMap = firstArg.value<QVariantMap>();
        
        if (responseMap.contains("session_handle")) {
            QString sessionPath = responseMap["session_handle"].toString();
            qDebug() << "Session created at path:" << sessionPath;
            emit sessionCreated(sessionPath);
        } else {
            qDebug() << "No session_handle found in response";
        }
    } else {
        qDebug() << "Unexpected response type:" << firstArg.typeName();
    }
}