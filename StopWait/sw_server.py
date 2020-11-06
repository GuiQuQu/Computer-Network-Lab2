import threading

from StopWait.stop_wait import StopWait


def main():
    sw_server = StopWait('server', '', 12311, '127.0.0.1', 12310)
    _send = threading.Thread(target=sw_server.begin_send)
    _rcv = threading.Thread(target=sw_server.begin_receive)
    _send.start()
    _rcv.start()


if __name__ == '__main__':
    main()
