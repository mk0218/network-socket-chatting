#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""

import sys
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            print(msg)
        except OSError:  # Possibly client has left the chat.
            break


def send(msg, event=None):  # event is passed by binders.
    """Handles sending of messages."""
    client_socket.send(bytes(msg, "utf8"))
    if msg == "<quit>":
        client_socket.close()


def on_closing(event=None):
    """This function is to be called when the window is closed."""
    send()


def main():
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    while True:
        msg = input()
        send(msg)
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)
        if msg == "<quit>":
            break


# ----Now comes the sockets part----
HOST = input('Enter host: ')
PORT = input('Enter port: ')
if not PORT:
    PORT = 33000
else:
    PORT = int(PORT)

BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
try:
    client_socket.connect(ADDR)
except ConnectionRefusedError:
    print("Server is not found.")
else:
    receive_thread = Thread(target=receive)
    receive_thread.start()

    main()
