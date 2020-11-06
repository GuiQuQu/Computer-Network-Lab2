import threading

from SR.sr import Sr


def main():
    sr_client1 = Sr('client1', '', 12138, '127.0.0.1', 12139)
    c1_send = threading.Thread(target=sr_client1.begin_send)
    c1_rcv = threading.Thread(target=sr_client1.begin_rcv_with_loss)
    c1_send.start()
    c1_rcv.start()


if __name__ == '__main__':
    main()
