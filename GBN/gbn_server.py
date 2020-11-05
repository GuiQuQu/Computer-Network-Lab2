import threading

from GBN.gbn import Gbn


def main():
    server = Gbn('server', '', 12139, '127.0.0.1', 12138)
    s_send = threading.Thread(target=server.begin_send)
    s_rcv = threading.Thread(target=server.begin_rcv)
    s_send.start()
    s_rcv.start()


if __name__ == '__main__':
    main()
