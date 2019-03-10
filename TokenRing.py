import socket
from enum import Enum
import time
import sys

class Protocol(Enum):
    TCP = 0
    UDP = 1

CONNECT = 0
TOKEN = 1
VALIDATE = 2
DUP_CHECK = 3


def encode_message(msg_type, parameters):
    contents = [msg_type] + parameters
    return str(contents)[1:-1].replace(' ', '').encode('utf-8')



def decode_message(msg):
    def decoder(element):
        if '\'' in element:
            return element.replace('\'', '')
        else:
            return int(element)

    decoded = [decoder(num) for num in msg.decode('utf-8').split(',')]
    msg_type = decoded[0]
    parameters = decoded[1:]
    return msg_type, parameters


class Client:

    def __init__(self, rcv_ip, rcv_port, snd_ip=None, snd_port=None, token=False, protocol=Protocol.TCP):
        print(rcv_ip, rcv_port)
        self.rcv_ip = rcv_ip
        self.rcv_port = rcv_port
        self.token = token
        self.protocol = protocol
        self.snd_ip = snd_ip
        self.snd_port = snd_port
        self.buff_size = 1024
        self.snd_socket = None
        self.rcv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rcv_socket.bind((self.rcv_ip, self.rcv_port))
        self.rcv_socket.listen()

        if self.snd_ip is None:
            self.receive_tcp()
        else:
            self.connect()

    def handle_connect(self, msg_params):
        old_send_ip, old_send_port, new_send_ip, new_send_port = msg_params
        if old_send_ip == self.snd_ip and old_send_port == self.snd_port:
            self.snd_ip = new_send_ip
            self.snd_port = new_send_port
            msg = encode_message(VALIDATE, [0])
            self.send_tcp(msg)
        elif (self.snd_ip is None) and (self.snd_port is None):
            self.snd_ip = new_send_ip
            self.snd_port = new_send_port
            if self.token:
                self.handle_token([])
            msg = encode_message(VALIDATE, [0])
            self.send_tcp(msg)
        else:
            msg = encode_message(CONNECT, msg_params)
            self.send_tcp(msg)

    def handle_token(self, msg_params):
        msg = encode_message(TOKEN, [])
        time.sleep(5)
        self.send_tcp(msg)

    def handle_validate(self, msg_params):
        if self.token:
            self.handle_token([])
        self.receive_tcp()

    def handle_dup_check(self, msg_params):
        pass

    def receive_tcp(self):
        connection, client_address = self.rcv_socket.accept()
        buff, address = connection.recvfrom(1024)
        connection.close()
        msg_type, msg_params = decode_message(buff)
        print("[RECEIVED] msgtype: ", msg_type)
        handle_msg = {
            CONNECT: self.handle_connect,
            TOKEN: self.handle_token,
            VALIDATE: self.handle_validate,
            DUP_CHECK: self.handle_dup_check(),
        }
        handle_msg[msg_type](msg_params)

    def send_tcp(self, msg):
        self.snd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.snd_socket.connect((self.snd_ip, self.snd_port))
        self.snd_socket.sendall(msg)
        self.snd_socket.close()
        print("[SENT] msgtype: ", decode_message(msg)[0], " to: ", self.snd_ip, self.snd_port)
        self.receive_tcp()

    def receive_udp(self):
        pass

    def send_udp(self, msg):
        pass

    def connect(self):
        message = encode_message(CONNECT, [self.snd_ip, self.snd_port, self.rcv_ip, self.rcv_port])
        self.send_tcp(message)



def main():
    client = Client("127.0.0.1", 9008, "127.0.0.1", 9007)

if __name__ == '__main__':
    main()