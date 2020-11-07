# GBN协议
import select
import threading
import time
from socket import *
import random

MAX_TIMER = 3  # 最大计时器数字
CLIENT_HOST = '127.0.0.1'
CLIENT_PORT = 12138
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12139
MAX_SEQ_NUM = 6
"""
要处理的问题
1.解决发送线程和接受线程的相互阻塞问题
2.序号使用完之后要重新分配序号  send过程 和rcv_data过程  √
"""


def main():
    client1 = Gbn('client1', '', 12138, '127.0.0.1', 12139)
    client2 = Gbn('client2', '', 12139, '127.0.0.1', 12138)
    c1_send = threading.Thread(target=client1.begin_send)
    c1_rcv = threading.Thread(target=client1.begin_rcv)
    c2_send = threading.Thread(target=client2.begin_send)
    c2_rcv = threading.Thread(target=client2.begin_rcv)

    c1_send.start()
    c1_rcv.start()

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
    ack = str(str(seq) + " ack")
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
        # self.send_flag = False
        self.ack = make_ack(0)

    def begin_send(self):
        while True:
            data = get_data(self.name)
            self.__send(data)  # 发送数据
            time.sleep(1)

    def __send(self, data):
        readable, writeable, errors = select.select([], [self.socket, ], [], 1)
        if len(writeable) > 0:
            if self.next_seq_num < MAX_SEQ_NUM:  # 还有可以使用的序号
                pass
            else:
                if self.base >= MAX_SEQ_NUM:  # 序号内的所有分组都已经被接收
                    self.base = 0
                    self.next_seq_num = 0
                else:
                    print('序号用尽,请等待')
                    # self.timeout()
                    return
            if self.next_seq_num < self.base + self.n:  # 窗口内还有序号
                pkt = make_pkt(data, self.next_seq_num)
                self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
                self.send_flag = True
                print(self.name, 'Send,pkt seq=', self.next_seq_num, 'base=', self.base, 'next_seq_num=',
                      self.next_seq_num, 'timer=', self.timer)
                self.send_cache[
                    self.next_seq_num % self.n] = pkt  # 如果窗口大小是5，->0,1,2,3,4 当next_seq_num=5时，这个数据包的缓存放到0号位置
                if self.next_seq_num == self.base:  # 没有未确认的数据，重启定时器
                    self.timer = 0
                self.next_seq_num = self.next_seq_num + 1
            else:
                print('窗口满！')

    def __rcv_data_with_loss(self):
        """
        模拟引入丢包 丢包有2种，1是丢失pkt，2是丢失ack
        丢失pkt可以通过不接受数据模拟
        丢失ack可以通过不发送ack模拟
        跳过数据检查 只检查序列号
        """
        # 只有当缓冲区有资源时，才会读取
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        if len(readable) > 0:
            is_rcv = random.random()
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 分开接受ack和接受数据
                if is_rcv < 0.3:  # 接受之后不处理数据
                    print("refuse_pkt", ',content=', message)
                    return
                # print(self.name, 'receive data,seq=', ret_seq)
                if ret_seq == self.except_seq_num:
                    self.ack = make_ack(self.except_seq_num)  # 构造返回的ack
                    print(self.name, ' receive expected data,seq=', self.except_seq_num, ',content=\"', message, '\"')
                    self.except_seq_num = (self.except_seq_num + 1) % MAX_SEQ_NUM
                else:
                    print('NO expected data,content=', message)
                is_ack = random.random()
                if is_ack < 0.5:  # 有0.5的概率不发送ack报文
                    self.socket.sendto(self.ack, (self.remote_ip, self.remote_port))
                else:
                    print('no_ack=', is_ack, 'ack_message=', self.ack)
            else:
                self.base = ret_seq + 1
                # if self.next_seq_num - self.base > 0:
                # self.send_flag = False  # 有未确认的数据就记超时
                # 本来的想法是发送了数据之后在来判断超时
                # timeout之后会发送多个send
                # 但是一个标志只能处理收到了一个了ack报文
                # 当 3 4 5 被重发之后，收到了3的ack之后，这个标志为False
                # 如果4的pkt丢失或者ack丢失，就无法为4记超时
                print(self.name, 'receive ACK,seq=', ret_seq, 'base=', self.base, 'next_seq_num=',
                      self.next_seq_num)
                if self.base == self.next_seq_num:
                    self.timer = -1  # 收到ack之后后面没有未确认的数据，停止计时器
                else:
                    self.timer = 0  # 收到ack之后，后面还有未确认的数据，重启计时器
        else:
            if self.next_seq_num > self.base:  # 读不到资源(ack)并且存在未确认的数据
                self.timer = self.timer + 1
                if self.timer > MAX_TIMER:
                    self.timeout()

    def timeout(self):
        print("Sender Time Out,seq=", self.base)
        i = self.base
        self.timer = 0
        while i < self.next_seq_num:
            pkt = self.send_cache[i % self.n]
            self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
            i = i + 1

    def begin_rcv(self):
        while True:
            self.rcv_data()

    def begin_rcv_with_loss(self):
        while True:
            self.__rcv_data_with_loss()

    def rcv_data(self):  # GBN 接受端的方法 + 接受ack
        # 跳过数据检查 只检查序列号
        # 只有当缓冲区有资源时，才会读取
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 分开接受ack和接受数据
                if ret_seq == self.except_seq_num:
                    self.ack = make_ack(self.except_seq_num)  # 构造返回的ack
                    print(self.name, ' receive expected data,seq=', self.except_seq_num, ',content=\"', message, '\"')
                    self.except_seq_num = (self.except_seq_num + 1) % MAX_SEQ_NUM
                else:
                    print('NO expected data,content=', message)
                self.socket.sendto(self.ack, (self.remote_ip, self.remote_port))
            else:
                self.base = ret_seq + 1
                print(self.name, 'receive ACK,seq=', ret_seq, 'base=', self.base, 'next_seq_num=',
                      self.next_seq_num)
                if self.base == self.next_seq_num:
                    self.timer = -1  # 收到ack之后后面没有未确认的数据，停止计时器
                else:
                    self.timer = 0  # 收到ack之后，后面还有未确认的数据，重启计时器
        else:
            if self.next_seq_num > self.base:  # 读不到资源(ack)并且存在未确认的数据
                self.timer = self.timer + 1
                if self.timer > MAX_TIMER:
                    self.timeout()


class GbnServer:
    def __init__(self):
        pass

    def __send(self):
        pass

    def __receive(self):
        pass


if __name__ == '__main__':
    main()
