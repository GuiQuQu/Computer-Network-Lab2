# 停等协议
from socket import socket

MAX_TIMER = 3  # 最大计时器数字


def main():
    pass


def make_pkt(data, seq):
    """
    :param data: 数据
    :param seq: 序号
    :return:
    数据格式
    seq data
    """
    return seq + " " + data


def make_ack(seq):
    """
    ack
    :return:
    """
    return seq + " ack"


class StopWaitClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.timer = MAX_TIMER

    def __send(self):
        pkt = make_pkt()
        pass

    def receive(self):
        pass

    def time_out(self):
        pass

    def check_pkt(self, seq, check_sum):
        pass


class StopWaitServer:
    def __init__(self):
        pass

    def send(self):
        pass

    def receive(self):
        pass


if __name__ == '__main__':
    main()
