#ifndef WAYLANDSCREENGABBER_H
#define WAYLANDSCREENGABBER_H

#include <QObject>
#include <QDBusMessage>
#include <QTimer>
#include <QDebug>

class WaylandScreenGrabber : public QObject
{
    Q_OBJECT

public:
    explicit WaylandScreenGrabber(QObject *parent = nullptr);

public slots:
    void initCapture();

signals:
    void sessionCreated(QString path);
    void errorOccurred(QString message);

private:
    void handleDBusResponse(const QDBusMessage &message);
};

#endif // WAYLANDSCREENGABBER_H