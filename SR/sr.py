# SR协议
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
MAX_SEQ_NUM = 11
"""
要处理的问题
1.解决发送线程和接受线程的相互阻塞问题
2.序号使用完之后要重新分配序号  send过程 和rcv_data过程  √
"""


def main():
    pass


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


class Sr:
    def __init__(self, name, client_ip, client_port, remote_ip, remote_port, n=5):
        # 基本信息
        self.name = name
        # 发送方
        self.base = 0
        self.next_seq_num = self.base
        self.n = n
        self.timer = 0
        self.send_cache = [b'0'] * self.n  # 发送方缓存
        self.send_log = [0] * self.n  # 发送方记录  0表示没有收到ack，1表示收到了ack
        # 接受方
        self.rcv_base = 0
        self.rcv_cache = [b'0'] * self.n  # 接受方缓存
        self.rcv_log = [0] * self.n  # 接受方记录
        # 套接字
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((client_ip, client_port))
        self.remote_ip = remote_ip
        self.remote_port = remote_port
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
                    return
            if self.next_seq_num < self.base + self.n:  # 窗口内还有序号
                pkt = make_pkt(data, self.next_seq_num)
                self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
                print(self.name, 'Send,pkt seq=', self.next_seq_num, 'base=', self.base, 'next_seq_num=',
                      self.next_seq_num, 'timer=', self.timer)
                self.send_cache[
                    self.next_seq_num % self.n] = pkt  # 如果窗口大小是5，->0,1,2,3,4 当next_seq_num=5时，这个数据包的缓存放到0号位置
                self.send_log[self.next_seq_num % self.n] = 0
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
                    print("refuse pkt", ',content=', message)
                    return
                is_ret_ack = False
                if self.rcv_base <= ret_seq < self.rcv_base + self.n:  # 在接受范围内，发送ack
                    is_ret_ack = True
                    self.rcv_cache[ret_seq % self.n] = message
                    self.rcv_log[ret_seq % self.n] = 1
                    print(self.name, ' receive data in window,seq=', ret_seq, 'rcv_base=', self.rcv_base, 'rcv_end=',
                          self.rcv_base + self.n, ',content=\"',
                          message, '\"')
                    # 更新rcv_base
                    for i in range(self.n):
                        if self.rcv_log[self.rcv_base % self.n] == 1:
                            # 上交数据
                            print('deliver data,seq=', self.rcv_base, 'content=',
                                  self.rcv_cache[self.rcv_base % self.n])
                            self.rcv_log[self.rcv_base % self.n] = 0  #
                            if self.rcv_base < MAX_SEQ_NUM:
                                self.rcv_base = self.rcv_base + 1
                                if self.rcv_base == MAX_SEQ_NUM:  # 只会收到0~MAX_SEQ_NUM序号的字段
                                    self.rcv_base = 0
                        else:
                            break
                elif self.rcv_base - self.n <= ret_seq < self.rcv_base:  # 已经接受但是发送端还没有收到ack
                    is_ret_ack = True
                    pass
                else:
                    print('OVER WINDOW DATA,rcv_base=', self.rcv_base, 'content=', message)
                if is_ret_ack:
                    is_ack = random.random()
                    self.ack = make_ack(ret_seq)  # 构造返回的ack
                    if is_ack < 0.5:  # 有0.5的概率不发送ack报文
                        print('Send ACK,content=', self.ack)
                        self.socket.sendto(self.ack, (self.remote_ip, self.remote_port))
                    else:
                        print('no_ack=', is_ack, 'ack_message=', self.ack)
            else:  # 收到ack
                self.send_log[ret_seq % self.n] = 1
                for i in range(self.base, self.next_seq_num):
                    if self.send_log[self.base % self.n] == 1:  # 前面有已经接受ack的分组
                        self.base = self.base + 1  # self.base不会超过next_seq_num,next_seq_num前面不会有发送还未确认的分组
                    else:
                        break
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
        # 重发第一个未确认分组
        print("Sender Time Out,seq=", self.base)
        pkt = self.send_cache[self.base % self.n]
        self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
        self.timer = 0

    def begin_rcv(self):
        while True:
            self.rcv_data()

    def begin_rcv_with_loss(self):
        while True:
            self.__rcv_data_with_loss()

    def rcv_data(self):  # GBN 接受端的方法 + 接受ack
        # 只有当缓冲区有资源时，才会读取
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 分开接受ack和接受数据
                is_ret_ack = False
                if self.rcv_base <= ret_seq < self.rcv_base + self.n:  # 在接受范围内，发送ack
                    is_ret_ack = True
                    self.rcv_cache[ret_seq % self.n] = message
                    self.rcv_log[ret_seq % self.n] = 1
                    print(self.name, ' receive data in window,seq=', ret_seq, 'rcv_base=', self.rcv_base, 'rcv_end=',
                          self.rcv_base + self.n, ',content=\"',
                          message, '\"')
                    # 更新rcv_base
                    # old_rcv_base = self.rcv_base
                    for i in range(self.n):
                        if self.rcv_log[self.rcv_base % self.n] == 1:
                            # 上交数据
                            print('deliver data,seq=', self.rcv_base, 'content=',
                                  self.rcv_cache[self.rcv_base % self.n])
                            self.rcv_log[self.rcv_base % self.n] = 0  #
                            if self.rcv_base < MAX_SEQ_NUM:
                                self.rcv_base = self.rcv_base + 1
                                if self.rcv_base == MAX_SEQ_NUM:  # 只会收到0~MAX_SEQ_NUM序号的字段
                                    self.rcv_base = 0
                        else:
                            break
                elif self.rcv_base - self.n <= ret_seq < self.rcv_base:  # 已经接受但是发送端还没有收到ack
                    is_ret_ack = True
                    pass
                else:
                    print('OVER WINDOW DATA,rcv_base=', self.rcv_base, 'content=', message)
                if is_ret_ack:
                    self.ack = make_ack(ret_seq)  # 构造返回的ack
                    print('Send ACK,content=', self.ack)
                    self.socket.sendto(self.ack, (self.remote_ip, self.remote_port))
            else:  # 收到ack
                self.send_log[ret_seq % self.n] = 1
                for i in range(self.base, self.next_seq_num):
                    if self.send_log[self.base % self.n] == 1:  # 前面有已经接受ack的分组
                        self.base = self.base + 1  # self.base不会超过next_seq_num,next_seq_num前面不会有发送还未确认的分组
                    else:
                        break
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


if __name__ == '__main__':
    main()
