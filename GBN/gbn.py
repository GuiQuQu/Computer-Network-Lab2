# GBN协议
import select
import threading
import time
from socket import *

MAX_TIMER = 3  # 最大计时器数字
CLIENT_HOST = '127.0.0.1'
CLIENT_PORT = 12138
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12139
MAX_SEQ_NUM = 256
"""
要处理的问题
1.解决发送线程和接受线程的相互阻塞问题
2.序号使用完之后要重新分配序号  send过程 和rcv_data过程  √
"""


def main():
    client1 = Gbn('client1', '', 12138, '127.0.0.1', 12139)
    client2 = Gbn('client2', '', 12139, '127.0.0.1', 12138)
    c1_send = threading.Thread(target=client1.begin_send)
    c1_ack = threading.Thread(target=client1.check_ack)
    c1_rcv = threading.Thread(target=client1.begin_rcv)
    c2_send = threading.Thread(target=client2.begin_send)
    c2_ack = threading.Thread(target=client2.check_ack)
    c2_rcv = threading.Thread(target=client2.begin_rcv)

    c1_send.start()
    c1_rcv.start()
    c1_ack.start()

    c2_ack.start()
    c2_send.start()
    c2_rcv.start()


def make_pkt(data, seq):
    """
    数据格式
    seq data
    """
    pkt = str(str(seq) + " " + str(data))
    return pkt.encode('utf-8')


def make_ack(seq):
    """
    ack seq
    """
    ack = str("ack " + str(seq))
    return ack.encode('utf-8')


def get_data(name):
    data = input(name + ',请输入要发送的信息:\n')
    return data


class Gbn:
    def __init__(self, name, client_ip, client_port, remote_ip, remote_port, n=5):
        # 基本信息
        self.name = name
        # 发送方
        self.base = 0
        self.next_seq_num = self.base
        self.n = n
        self.timer = 0
        # 接受方
        self.except_seq_num = 0
        # 套接字
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((client_ip, client_port))
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        # 数据分组缓存
        self.send_cache = [b'0'] * self.n
        self.lock = threading.Lock()
        # path = self.name + ".txt"
        # self.log = open(path, 'w')

    def begin_send(self):
        while True:
            self.lock.acquire()
            data = get_data(self.name)
            self.lock.release()
            self.__send(data)  # 发送数据
            self.__rcv_ack()
            time.sleep(2)

    def check_ack(self):
        while True:
            self.__rcv_ack()  # 检查ack

    def __send(self, data):
        readable, writeable, errors = select.select([], [self.socket, ], [], 1)
        if len(writeable) > 0:
            if self.next_seq_num < MAX_SEQ_NUM:  # 还有可以使用的序号
                if self.next_seq_num < self.base + self.n:  # 窗口内还有序号
                    pkt = make_pkt(data, self.next_seq_num)
                    self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
                    print(self.name, 'Send,seq=', self.next_seq_num)
                    self.send_cache[
                        self.next_seq_num % self.n] = pkt  # 如果窗口大小是5，->0,1,2,3,4 当next_seq_num=5时，这个数据包的缓存放到0号位置
                    self.next_seq_num = self.next_seq_num + 1
                    if self.next_seq_num == self.base:
                        self.timer = 0
                else:
                    print('窗口满！')
            else:
                if self.base >= MAX_SEQ_NUM:  # 序号内的所有分组都已经被接收
                    self.base = 0
                    self.next_seq_num = 0

    def __rcv_ack(self):
        # 接受ack  非阻塞方式
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(1024)
            ack_message = byte.decode()
            if 'ACK' in ack_message:
                ack_message = ack_message.split()
                ret_seq = int(ack_message[1])
                print(self.name, ' receive ACK,seq=', ret_seq)
                self.base = ret_seq + 1
                if self.base == self.next_seq_num:
                    self.timer = -1
                else:
                    self.timer = 0
        else:
            self.timer = self.timer + 1
            if self.timer > MAX_TIMER:
                self.timeout()

    def timeout(self):
        print("Client Time Out,seq=", self.base)
        i = self.base
        self.timer = 0
        while i < self.next_seq_num:
            pkt = self.send_cache[i % self.n]
            self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
            i = i + 1

    def begin_rcv(self):
        while True:
            self.rcv_data()

    def rcv_data(self):  # GBN 接受端的方法
        # 跳过数据检查 只检查序列号
        # 只有当缓冲区有资源时，才会读取
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            ret_seq = int(message[0])
            print(self.name, ' receive data,seq=', ret_seq)
            ack = make_ack(ret_seq)
            if ret_seq == self.except_seq_num:
                print(self.name, ' receive expect data')
                self.except_seq_num = (self.except_seq_num + 1) % MAX_SEQ_NUM
            self.socket.sendto(ack, (self.remote_ip, self.remote_port))


class GbnServer:
    def __init__(self):
        pass

    def __send(self):
        pass

    def __receive(self):
        pass


if __name__ == '__main__':
    main()
