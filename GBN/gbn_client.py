import threading

from GBN.gbn import Gbn


def main():
    client1 = Gbn('client1', '', 12138, '127.0.0.1', 12139)
    c1_send = threading.Thread(target=client1.begin_send)
    c1_rcv = threading.Thread(target=client1.begin_rcv)
    c1_send.start()
    c1_rcv.start()


if __name__ == '__main__':
    main()
