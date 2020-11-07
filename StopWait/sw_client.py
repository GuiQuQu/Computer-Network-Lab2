import threading

from StopWait.stop_wait import StopWait


def main():
    sw_client1 = StopWait('client1', '', 12310, '127.0.0.1', 12311)
    sw_send = threading.Thread(target=sw_client1.begin_send)
    sw_rcv = threading.Thread(target=sw_client1.begin_receive)
    sw_send.start()
    sw_rcv.start()


def get_file():
    sw_client1 = StopWait('client1', '', 12310, '127.0.0.1', 12311)
    sw_send = threading.Thread(target=sw_client1.begin_send)
    sw_rcv = threading.Thread(target=sw_client1.begin_receive_file)
    sw_send.start()
    sw_rcv.start()


if __name__ == '__main__':
    # main()
    get_file()
