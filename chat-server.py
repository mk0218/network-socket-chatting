#!/usr/bin/env python3
from socket import socket, SOCK_STREAM, SOCK_DGRAM, AF_INET
from threading import Thread, Lock
import pyaudio
# import wave

# settings for pyaudio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 10240

# settings for socket
clients = {}
addresses = {}
HOST = ''
TXT_PORT = 12345
VCE_RCV_PORT = 12346
VCE_SEND_PORT = 12347
BUFSIZ = 1024


class Client:
    CREATED, RUNNING, QUIT = 0, 1, 2
    _lock = Lock()
    _instances = {}

    def __init__(self, name, addr, sock):
        self.name = name
        self.addr = addr
        self.sock = sock
        self.state = self.CREATED

        with self._lock:
            self._instances[self.name] = self

    def __str__(self):
        return "({}: {})".format(self.name, self.addr)

    def close_connection(self):
        if self.name in self._instances:
            with self._lock:
                del self._instances[self.name]
        self.sock.close()
        print("{} has disconnected".format(self.addr))

    @classmethod
    def exists(cls, name):
        return name in cls._instances

    @classmethod
    def get_client_with_name(cls, name):
        try:
            return cls._instances[name]
        except KeyError:
            return None

    @classmethod
    def get_client_with_address(cls, addr):
        for name in cls._instances:
            c = cls._instances[name]
            if c.addr == addr:
                return c
        return None

    @classmethod
    def broadcast(cls, msg):
        for name in cls._instances:
            cls._instances[name].send(msg)

    @classmethod
    def broadcast_voice(cls, sender, data):
        for name in cls._instances:
            if name != sender:
                cls._instances[name].send_voice(data)

    def send(self, msg):
        self.sock.send(msg.encode('utf-8'))

    def send_voice(self, data):
        VCE_SERVER.sendto(data, (self.addr[0], VCE_SEND_PORT))

    def rcv_text(self):
        while self.state == self.RUNNING:
            try:
                msg = self.sock.recv(BUFSIZ).decode('utf-8')
                if msg != '<quit>':         # client send message
                    msg = "{}: {}".format(self.name, msg)
                    self.broadcast(msg)
                else:                       # client tried to quit
                    self.state = self.QUIT
            except ConnectionResetError:
                self.state = self.QUIT
        self.close_connection()

    def handle(self):
        self.state = self.RUNNING
        self.send("Welcome {}! Type <quit> to exit.".format(self.name))
        self.broadcast("{} has joined the chat".format(self.name))
        Thread(target=self.rcv_text).start()


def accept_incoming_connections():
    while True:
        client_sock, client_addr = SERVER.accept()
        print("{} has connected".format(client_addr))

        # when a client connected, ask name
        client_sock.send(b"Type your name: ")
        name = client_sock.recv(BUFSIZ).decode('utf-8')

        # if the name already exists, client must choose another name
        # must change
        while Client.exists(name):
            client_sock.send("The name {} already exists. \
                             Please choose another name."
                             .format(name).encode('utf-8'))
            name = client_sock.recv(BUFSIZ).decode('utf-8')

        # save client information and handle client
        c = Client(name, client_addr, client_sock)
        c.handle()


def handle_voice():
    while True:
        data, addr = VCE_SERVER.recvfrom(CHUNK * CHANNELS * 2)
        sender = Client.get_client_with_address(addr).name
        # if the sender of voice data not in clients, ignore
        if sender:
            Client.broadcast_voice(sender, data)


if __name__ == "__main__":
    # open pyaudio stream
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)
    # open socket
    SERVER = socket(AF_INET, SOCK_STREAM)
    SERVER.bind((HOST, TXT_PORT))
    SERVER.listen(5)

    VCE_SERVER = socket(AF_INET, SOCK_DGRAM)
    VCE_SERVER.bind((HOST, VCE_RCV_PORT))

    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    VOICE_THREAD = Thread(target=handle_voice)
    ACCEPT_THREAD.start()
    VOICE_THREAD.start()
    ACCEPT_THREAD.join()
    VOICE_THREAD.join()
    SERVER.close()
    VCE_SERVER.close()
