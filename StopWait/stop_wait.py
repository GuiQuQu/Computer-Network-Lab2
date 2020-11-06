# 停等协议
import select
from socket import *
from threading import Thread

from pip._vendor.distlib.compat import raw_input

MAX_TIMER = 3  # 最大计时器数字
CLIENT_HOST = '127.0.0.1'
CLIENT_PORT = 12330
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12340


def main():
    client = StopWait('client', CLIENT_PORT, SERVER_HOST, SERVER_PORT)
    server = StopWait('sever', SERVER_PORT, CLIENT_HOST, CLIENT_PORT)
    client_send_thread = Thread(target=client.begin_send())
    client_receive_thread = Thread(target=client.begin_receive())
    server_send_thread = Thread(target=server.begin_send())
    server_receive_thread = Thread(target=server.begin_receive())
    client_send_thread.start()
    client_receive_thread.start()
    server_send_thread.start()
    server_receive_thread.start()


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
        self.send_cache = b'0'
        self.wait_ack = False
        self.send_seq = 0

    def get_data(self):
        data = input(self.name + ',请输入要发送的信息:\n')
        return data

    def __send(self, data):
        # 发送完成数据之后，必须等待
        # 发送数据
        if not self.wait_ack:
            pkt = make_pkt(data, self.seq)
            self.send_cache = pkt
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

    # 接收数据，返回ack
    def __receive(self):
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        # 非阻塞方式
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            # 跳过数据包内容检查
            # 检查序号
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 正常接受数据
                ack = make_ack(ret_seq)
                if ret_seq == self.except_seq:
                    print(self.name, 'receive expected pkt,content=', message)
                    self.except_seq = (self.except_seq + 1) % 2
                else:
                    print('NO expected pkt,expect_seq=', self.except_seq, 'content=', message)
                self.socket.sendto(ack, addr)
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

    def receive_with_loss(self):  # 未修改
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        # 非阻塞方式
        if len(readable) > 0:
            byte, addr = self.socket.recvfrom(1024)
            message = byte.decode().split()
            # 跳过数据包内容检查
            # 检查序号
            ret_seq = int(message[0])
            if len(message) <= 1 or 'ack' != message[1]:  # 正常接受数据
                ack = make_ack(ret_seq)
                if ret_seq == self.except_seq:
                    print(self.name, 'receive expected pkt,content=', message)
                    self.except_seq = (self.except_seq + 1) % 2
                else:
                    print('NO expected pkt,expect_seq=', self.except_seq, 'content=', message)
                self.socket.sendto(ack, addr)
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

    def __timeout(self):
        # 重发数据
        print(self.name, ' Time Out,wait ack seq=', self.seq)
        self.timer = 0
        self.wait_ack = False
        self.__send(self.send_cache)


if __name__ == '__main__':
    main()
