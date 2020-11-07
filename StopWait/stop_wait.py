# 停等协议
import os
import random
import select
import time
from socket import *

MAX_TIMER = 3  # 最大计时器数字
CLIENT_HOST = '127.0.0.1'
CLIENT_PORT = 12330
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12340


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
    seq ack
    """
    ack = str(str(seq) + " ack")
    return ack.encode('utf-8')


# 要实现全双工通信，既要做服务器，也要做客户端
def deliver_data(method):
    if method == 0:
        pass
    elif method == 1:  # 处理文件
        pass


class StopWait:
    def __init__(self, name, my_ip, my_port, remote_ip, remote_port):
        # 基本信息
        self.name = name
        # 发送方
        self.timer = MAX_TIMER
        self.seq = 0
        # 接受方
        self.except_seq = 0
        # 套接字
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((my_ip, my_port))
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        # 数据缓存
        self.send_cache = [b'0'] * 1
        self.wait_ack = False
        self.send_seq = 0

        self.__file_name = 'new'
        self.__file_size = 0

    def get_data(self):
        data = input(self.name + ',请输入要发送的信息:\n')
        return data

    def __send(self, data):
        # 发送完成数据之后，必须等待
        # 发送数据
        if not self.wait_ack:
            pkt = make_pkt(data, self.seq)
            self.send_cache[0] = pkt
            self.socket.sendto(pkt, (self.remote_ip, self.remote_port))
            print('Sender Send', 'Seq=', self.seq)
            self.timer = 0  # 启动定时器
            self.wait_ack = True
        else:
            print('发送失败,等待ack中,wait_ack=', self.seq)

    def begin_send(self):
        while True:
            data = self.get_data()
            self.__send(data)

    def begin_file_dis(self):
        path = input('请输入要发送的文件路径\n')
        filesize_bytes = os.path.getsize(path)
        self.__send('file')
        time.sleep(2)
        self.__send(path + " " + str(filesize_bytes))
        time.sleep(2)
        with open(path, 'rb') as file:
            while True:
                data = file.read(1024).decode()
                if len(data) <= 0: break
                self.__send(data)
                time.sleep(2)

    # 接收数据或者返回ack
    def __receive(self):
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        ret = ''
        # 非阻塞方式
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(65536)

            message = byte.decode().split()
            # 跳过数据包内容检查
            # 检查序号
            ret_seq = int(message[0])
            ret = byte.decode()[2:]
            if len(message) <= 1 or 'ack' != message[1]:  # 正常接受数据
                ack = make_ack(ret_seq)
                if ret_seq == self.except_seq:
                    print(self.name, 'receive expected pkt,content=', message)
                    self.except_seq = (self.except_seq + 1) % 2
                else:
                    print('NO expected pkt,expect_seq=', self.except_seq, 'content=', message)
                self.socket.sendto(ack, addr)
                print('Send ACK,ack is', ack)
            else:  # 获取到ack
                print('receive ACK,seq=', ret_seq, 'wait ACK=', self.seq)
                if ret_seq == self.seq:
                    self.seq = (self.seq + 1) % 2
                    self.wait_ack = False
        else:
            if self.wait_ack:
                self.timer = self.timer + 1
                if self.timer > MAX_TIMER:
                    self.__timeout()
        return ret

    def __receive_file(self, file, rcv_size):
        ret_size = rcv_size
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        # 非阻塞方式
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(65535)
            message = byte.decode().split()
            # 跳过数据包内容检查
            # 检查序号
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 正常接受数据
                ack = make_ack(ret_seq)
                if ret_seq == self.except_seq:
                    print(self.name, 'receive expected pkt,content=', message)
                    self.except_seq = (self.except_seq + 1) % 2
                    m = byte.decode('utf-8')[2:]
                    # print('content:\n')
                    ret_size = ret_size + len(m.encode())
                    print('rcv_size=', ret_size)
                    file.write(m.encode())
                else:
                    print('NO expected pkt,expect_seq=', self.except_seq, 'content=', message)
                self.socket.sendto(ack, addr)
                print('Send ACK,ack is', ack)
            else:  # 获取到ack
                print('receive ACK,seq=', ret_seq, 'wait ACK=', self.seq)
                if ret_seq == self.seq:
                    self.seq = (self.seq + 1) % 2
                    self.wait_ack = False
        else:
            if self.wait_ack:
                self.timer = self.timer + 1
                if self.timer > MAX_TIMER:
                    self.__timeout()
        return ret_size

    def receive_with_loss(self):
        """
        模拟引入丢包 丢包有2种，1是丢失pkt，2是丢失ack
        丢失pkt可以通过不接受数据模拟
        丢失ack可以通过不发送ack模拟
        跳过数据检查 只检查序列号
        """
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        # 非阻塞方式
        if len(readable) > 0:
            is_rcv = random.random()
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            # 跳过数据包内容检查
            # 检查序号
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 正常接受数据 /或者ack
                if is_rcv < 0.3:  # 接受之后不处理数据
                    print("refuse pkt", ',content=', message)
                    return
                if ret_seq == self.except_seq:
                    print(self.name, 'receive expected pkt,content=', message)
                    self.except_seq = (self.except_seq + 1) % 2
                else:
                    print('NO expected pkt,expect_seq=', self.except_seq, 'content=', message)
                is_ack = random.random()
                ack = make_ack(ret_seq)
                if is_ack < 0.5:  # 有0.5的概率不发送ack报文
                    print('Send ACK,content=', ack)
                    self.socket.sendto(ack, addr)
                else:
                    print('no_ack=', is_ack, 'ack_message=', ack)
            else:  # 获取到ack
                print('receive ACK,seq=', ret_seq, 'wait ACK=', self.seq)
                if ret_seq == self.seq:
                    self.seq = (self.seq + 1) % 2
                    self.wait_ack = False
        else:
            if self.wait_ack:
                self.timer = self.timer + 1
                if self.timer > MAX_TIMER:
                    self.__timeout()

    def begin_receive_with_loss(self):
        while True:
            self.receive_with_loss()

    def begin_receive(self):
        while True:
            self.__receive()

    def begin_receive_file(self):
        while True:
            order_mes = self.__receive()
            if order_mes == 'file':
                break
        print('order=', order_mes)
        while True:
            message = self.__receive().split()
            if len(message) == 2:
                break
        print('message=', message)
        paths = message[0].split('.')
        new_file_name = ''
        for i in range(len(paths) - 1):
            if i == len(paths) - 2:
                new_file_name = new_file_name + paths[i] + '(new).'
            else:
                new_file_name = new_file_name + paths[i] + '.'
        new_file_name = new_file_name + paths[len(paths) - 1]
        file_size = int(message[1])
        rcv_size = 0
        file = open(new_file_name, 'wb')
        print(new_file_name)
        print('rcv_size=', rcv_size)
        while rcv_size < file_size:
            rcv_size = self.__receive_file(file, rcv_size)
        file.close()

    def __timeout(self):
        # 重发数据
        print(self.name, ' Time Out,wait ack seq=', self.seq)
        self.timer = 0
        self.socket.sendto(self.send_cache[0], (self.remote_ip, self.remote_port))
        self.wait_ack = True


if __name__ == '__main__':
    main()
