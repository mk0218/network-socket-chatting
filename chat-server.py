#!/usr/bin/env python3
from socket import socket, SOCK_STREAM, AF_INET
from threading import Thread, Lock

lock = Lock()


def accept_incoming_connections():
    while True:
        client, client_addr = SERVER.accept()
        print("{} has connected".format(client_addr))

        lock.acquire()
        addresses[client] = client_addr
        lock.release()

        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):
    client.send(b"Hello! Now you are in a chat room. Tell us your name!")
    name = client.recv(BUFSIZ).decode('utf-8')

    welcome_msg = 'Welcome {}! Type <quit> to exit.'\
                  .format(name)
    client.send(welcome_msg.encode('utf-8'))

    msg = "{} has joined the chat.".format(name)
    broadcast(msg)

    lock.acquire()
    clients[client] = name
    lock.release()

    while True:
        msg = client.recv(BUFSIZ).decode('utf-8')
        if msg != '<quit>':         # client send message
            broadcast(msg, name)
        else:                       # client tried to quit
            client_addr = addresses[client]
            lock.acquire()
            del clients[client]
            del addresses[client]
            lock.release()

            client.close()
            broadcast("{} has left the chat.".format(name))
            break
    print("{} has disconnected".format(client_addr))


def broadcast(message, sender=''):
    if sender:
        message = '{}: {}'.format(sender, message)
    for c in clients:
        c.send(message.encode('utf-8'))


clients = {}
addresses = {}

HOST = ''
PORT = 12345
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
