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
    ack seq
    """
    ack = str("ack " + str(seq))
    return ack.encode('utf-8')


# 要实现全双工通信，既要做服务器，也要做客户端
class StopWait:
    def __init__(self, name, my_port, remote_host, remote_port):
        self.name = name
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(('', my_port))
        self.timer = MAX_TIMER
        self.RemoteHost = remote_host
        self.RemotePort = remote_port
        self.data = ''

    def get_data(self):
        data = raw_input(self.name + ',请输入要发送的信息:')  # 阻塞其他线程，等待用户输入
        # file = open('test.txt', 'r')
        # data = file.readline()
        self.data = data

    def begin_send(self):
        seq = 0
        while True:
            self.get_data()
            self.__send(seq, self.data)
            seq = (seq + 1) % 2
        self.socket.close()

    def __send(self, seq, data):
        # 发送数据
        pkt = make_pkt(data, seq)
        self.socket.sendto(pkt, (self.RemoteHost, self.RemotePort))
        print('Client Send', 'Seq=', seq)
        self.timer = 0  # 启动定时器
        # 非阻塞方式
        # 处理ack的返回
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        while True:
            if len(readable) > 0:
                ack_bytes, addr = self.socket.recvfrom(1024)
                rcv_ack = ack_bytes.decode()
                if len(rcv_ack) > 0:
                    if 'ACK' in rcv_ack and seq in rcv_ack:
                        print(self.name, ' receive ack,seq=', seq)
                        self.timer = 0
                        break
                    else:  # ack有误，丢弃，继续等待
                        continue
            else:  # ack丢失或者pkt丢失
                self.timer = self.timer + 1
                if self.timer > MAX_TIMER:
                    self.__timeout(seq, data)
                    break

    # 接收数据，返回ack
    def __receive(self, expect_seq):
        ret_seq = expect_seq
        readable, writeable, errors = select.select([self.socket, ], [], [], 1)
        # 非阻塞方式
        if len(readable) > 0:
            rcv, addr = self.socket.recvfrom(1024)
            rcv_data = rcv.decode()
            # 跳过数据包内容检查
            # 检查序号
            str_list = rcv_data.split()
            rcv_seq = int(str_list[0])
            ack = make_ack(rcv_seq)
            if rcv_seq == expect_seq:  # 正确
                print(self.name, 'receive data,seq=', rcv_seq, ',data=', rcv_data)
                ret_seq = (expect_seq + 1) % 2
            self.socket.sendto(ack, addr)
        return ret_seq

    def begin_receive(self):
        expect_seq = 0
        while True:
            expect_seq = self.__receive(expect_seq)
        self.socket.close()

    def __timeout(self, seq, data):
        # 重发数据
        print(self.name, ' Time Out')
        self.timer = 0
        self.__send(seq, data)

    def __check_pkt(self, seq, check_sum):
        pass


if __name__ == '__main__':
    main()
