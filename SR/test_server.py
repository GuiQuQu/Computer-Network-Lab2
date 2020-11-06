import threading

from SR.sr import Sr


def main():
    sr_server = Sr('server', '', 12139, '127.0.0.1', 12138)
    s_send = threading.Thread(target=sr_server.begin_send)
    s_rcv = threading.Thread(target=sr_server.begin_rcv_with_loss)
    s_send.start()
    s_rcv.start()


if __name__ == '__main__':
    main()
