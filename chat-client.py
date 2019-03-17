#!/usr/bin/env python3
import os
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

BUFSIZ = 1024


def receive():
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode('utf-8')
            if msg == '<quit>':
                break
            print(msg)
        except OSError:
            break


def send():
    CLEAR_LINE = '\x1b[1A\x1b[2K'
    while True:
        try:
            msg = input()
            if msg == "<quit>":
                client_socket.send(b'<quit>')
                break
            if os.name != 'nt':
                print(CLEAR_LINE, end='')
            client_socket.send(msg.encode('utf-8'))

        except OSError:
            break

    client_socket.close()


if __name__ == '__main__':  
    HOST = input('Enter host: ')
    PORT = input('Enter port: ')
    if not PORT:
        PORT = 12345
    else:
        PORT = int(PORT)

    ADDR = (HOST, PORT)
    client_socket = socket(AF_INET, SOCK_STREAM)

    try:
        client_socket.connect(ADDR)
    except ConnectionRefusedError:
        print("Server is not found.")
    else:
        receive_thread = Thread(target=receive)
        receive_thread.start()
        send_thread = Thread(target=send)
        send_thread.start()
