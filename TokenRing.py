import socket
import threading
import time
import sys
import random


TCP = 0
UDP = 1


CONNECT = 0  # CONNECT old_send_ip, old_send_port, new_send_ip, new_send_port
TOKEN = 1
TOKEN_CONNECT = 0  # TOKEN TOKEN_CONNECT old_send_ip, old_send_port, new_send_ip, new_send_port
TOKEN_MSG = 1  # TOKEN TOKEN_MSG MSG_TO MSG_FROM MSG


def encode_message(msg_type, parameters):
    new_params =[]
    for param in parameters:
        if param*0 != 0:
            new_params.append(param.replace(' ', '|'))
        else:
            new_params.append(param)

    contents = [msg_type] + new_params
    return str(contents)[1:-1].replace(' ', '').encode('utf-8')


def decode_message(msg):
    def decoder(element):
        if '\'' in element:
            element = element.replace('\'', '')
            return element.replace('|', ' ')
        else:
            return int(element)

    decoded = [decoder(num) for num in msg.decode('utf-8').split(',')]
    msg_type = decoded[0]
    parameters = decoded[1:]
    return msg_type, parameters


class Client:

    def __init__(self, msg_queue, rcv_ip, rcv_port, snd_ip=None, snd_port=None, token=False, name="Andrzej", protocol=UDP):
        print(rcv_ip, rcv_port)
        self.name = name
        self.rcv_ip = rcv_ip
        self.rcv_port = rcv_port
        self.token = token
        self.protocol = protocol
        self.snd_ip = snd_ip
        self.snd_port = snd_port
        self.log_ip = "127.0.0.1"
        self.log_port = 8080
        self.buff_size = 1024
        self.snd_socket = None
        self.connect_queue = []
        self.msg_queue = msg_queue
        self.penalty = 1

        if protocol == TCP:
            self.mode = socket.SOCK_STREAM
        else:
            self.mode = socket.SOCK_DGRAM

        self.rcv_socket = socket.socket(socket.AF_INET, self.mode)
        self.rcv_socket.bind((self.rcv_ip, self.rcv_port))

        if protocol == TCP:
            self.rcv_socket.listen()

        if self.snd_ip is None:
            self.receive_wrap()
        else:
            self.connect()

    def handle_connect(self, msg_params):
        old_send_ip, old_send_port, new_send_ip, new_send_port = msg_params
        #print("[RECEIVED CONF MESSAGE]")
        if (self.snd_ip is None) or (self.snd_port is None):
            self.snd_ip = new_send_ip
            self.snd_port = new_send_port
            if self.token:
                self.handle_token([])
        else:
            self.connect_queue.append(msg_params)

    def get_message_from_queues(self):
        if len(self.connect_queue) == 0:
            if len(self.msg_queue) == 0:
                msg = encode_message(TOKEN, [])
            else:
                if 1.0/self.penalty >= random.randint(0, 1):
                    self.penalty += 2
                    params = self.msg_queue.pop(0)
                    msg = encode_message(TOKEN, [TOKEN_MSG] + params)
                else:
                    msg = encode_message(TOKEN, [])
                    if self.penalty > 1:
                        self.penalty -= 1
        else:
            params = self.connect_queue.pop(0)
            msg = encode_message(TOKEN, [TOKEN_CONNECT] + params)
        return msg

    def handle_token(self, msg_params):
        time.sleep(1)
        if len(msg_params[1:]) == 0:
            #print("[RECEIVED EMPTY TOKEN]")
            msg = self.get_message_from_queues()
        elif msg_params[0] == TOKEN_CONNECT:
            old_send_ip, old_send_port, new_send_ip, new_send_port = msg_params[1:]
            #print("[RECEIVED CONF TOKEN]: ", old_send_ip, ":", old_send_port, new_send_ip, ":", new_send_port)
            if (self.snd_ip == old_send_ip) and (self.snd_port == old_send_port):
                self.snd_ip = new_send_ip
                self.snd_port = new_send_port
                msg = encode_message(TOKEN, [])
            else:
                self.connect_queue.append(msg_params[1:])
                msg_params[1:] = self.connect_queue.pop(0)
                msg = encode_message(TOKEN, msg_params)
        else:
            name_to, name_from,  content = msg_params[2:]
            if name_to == self.name:
                print("[USER ", name_from, " WRITES]: ", content)
                msg = self.get_message_from_queues()
            else:
                msg = encode_message(TOKEN, msg_params)
        self.send_wrap(msg)

    def handle_message(self, encoded_message):
        msg_type, msg_params = decode_message(encoded_message)
        handle_msg = {
            CONNECT: self.handle_connect,
            TOKEN: self.handle_token,
        }
        handle_msg[msg_type](msg_params)

    def send_wrap(self, msg):
        send_via = {
            TCP: self.send_tcp,
            UDP: self.send_udp,
        }
        send_via[self.protocol](msg)

    def receive_wrap(self):
        receive_via = {
            TCP: self.receive_tcp,
            UDP: self.receive_udp,
        }
        receive_via[self.protocol]()

    def receive_tcp(self):
        connection, client_address = self.rcv_socket.accept()
        buff, address = connection.recvfrom(1024)
        connection.close()
        self.handle_message(buff)
        self.receive_tcp()

    def send_tcp(self, msg):
        self.snd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.snd_socket.connect((self.snd_ip, self.snd_port))
        self.snd_socket.send(msg)
        self.snd_socket.close()
        #print("[SENT] msgtype: ", decode_message(msg)[0], " to: ", self.snd_ip, self.snd_port)

    def receive_udp(self):
        buff, address = self.rcv_socket.recvfrom(1024)
        self.handle_message(buff)
        self.receive_udp()

    def send_udp(self, msg):
        self.snd_socket = socket.socket(socket.AF_INET, self.mode)
        self.snd_socket.sendto(msg, (self.snd_ip, self.snd_port))
        #print("[SENT] msgtype: ", decode_message(msg)[0], " to: ", self.snd_ip, self.snd_port)

    def log(self, msg):
        self.snd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.snd_socket.sendto(msg, (self.log_ip, self.log_port))

    def connect(self):
        message = encode_message(CONNECT, [self.snd_ip, self.snd_port, self.rcv_ip, self.rcv_port])
        self.send_wrap(message)
        if self.token:
            message = encode_message(TOKEN, [TOKEN_MSG])
            self.send_wrap(message)
        self.receive_wrap()

def main():

    def background(msg_queue, name, rcv_ip, rcv_port, snd_ip, snd_port, token, protocol):
        client = Client(msg_queue,rcv_ip, rcv_port, snd_ip, snd_port, token, name, protocol)

    for arg in sys.argv:
        print(arg)

    queue = []
    name_from = sys.argv[1]
    rcv_ip = "127.0.0.1"
    rcv_port = int(sys.argv[2])

    if sys.argv[3] == "None":
        snd_ip = None
        snd_port = None
    else:
        snd_ip = "127.0.0.1"
        snd_port = int(sys.argv[3])

    if sys.argv[4] == "True":
        token = True
    else:
        token = False
    if sys.argv[5] == "TCP":
        protocol = TCP
    else:
        protocol = UDP

    threading1 = threading.Thread(target=background, args=(queue, name_from, rcv_ip, rcv_port, snd_ip, snd_port, token, protocol))
    threading1.daemon = True
    threading1.start()

    while True:
        name_to, msg = input().split(" ", 1)
        queue.append([TOKEN_MSG, name_to, name_from,  msg])

main()