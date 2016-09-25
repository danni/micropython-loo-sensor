import socket
import time
from machine import Pin

import _config


UNKNOWN = const(0)
VACANT = const(1)
OCCUPIED = const(2)

status = UNKNOWN

sensor = Pin(13)
sensor.init(Pin.IN, Pin.PULL_UP)


def http_get(path, host=_config.HOST, port=_config.PORT):
    """
    Connect a websocket.
    """

    sock = socket.socket()
    addr = socket.getaddrinfo(host, port)

    try:
        sock.connect(addr[0][4])

        def send_header(header, *args):
            sock.send(header % args + '\r\n')

        send_header(b'GET %s HTTP/1.1', path or '/')
        send_header(b'Host: %s:%s', host, port)
        send_header(b'')

        header = sock.readline()[:-2]
        assert header == b'HTTP/1.1 200 OK', header

        # We don't (currently) need these headers
        while header:
            header = sock.readline()[:-2]

    finally:
        sock.close()


while True:
    try:
        value = sensor.value()

        # Sensor is pull-down, a LOW value means something is blocking it.
        if value == 0:
            new_status = OCCUPIED
        elif value == 1:
            new_status = VACANT

        if status != new_status:
            print("Status %s -> %s" % (status, new_status))
            status = new_status

            path = '/update/'

            if status == OCCUPIED:
                path += 'occupied'
            elif status == VACANT:
                path += 'vacant'
            else:
                path += 'unknown'

            print("GET", path)
            http_get(path)
            print("Done")

    except:
        print("Failed!")

    finally:
        time.sleep(0.5)
