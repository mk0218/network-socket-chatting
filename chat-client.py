#!/usr/bin/env python3
import os
from socket import AF_INET, socket, SOCK_STREAM, SOCK_DGRAM
from threading import Thread
import pyaudio
import tkinter

BUFSIZ = 1024
PORT = 12345
# for voice 
HOST = '127.0.0.1'
RCV_HOST = '0.0.0.0'
recv_port = 12347
recv_frames = []
send_port = 12346
send_frames = []
  

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 10240
RECORD_SECONDS = 40


def receive_voice_frame():
    p_r = pyaudio.PyAudio()
    recv_stream = p_r.open(format=FORMAT,
                            channels = CHANNELS,
                            rate = RATE,
                            output = True,
                            frames_per_buffer = CHUNK)
    receive_udp_thread = Thread(target = receive_udp)
    receive_udp_thread.setDaemon(True)
    receive_udp_thread.start()
    play_voice_thread = Thread(target = play_voice, args = [recv_stream])
    play_voice_thread.setDaemon(True)
    play_voice_thread.start()    
        
def receive_udp():
    recv_udp_socket = socket(AF_INET, SOCK_DGRAM)
    recv_udp_socket.bind((RCV_HOST, recv_port))

    while True:   
        voice_data, recv_addr = recv_udp_socket.recvfrom(CHUNK*CHANNELS*2)
        if voice_data:
            recv_frames.append(voice_data)

    recv_udp_socket.close()

def play_voice(stream):
    while True:
        if len(recv_frames) >= 10 and len(recv_frames) > 0:
                    stream.write(recv_frames.pop(0), CHUNK)


def send_voice_frame():
    p_s = pyaudio.PyAudio()
    send_stream = p_s.open(format = FORMAT,
                            channels = CHANNELS,
                            rate = RATE,
                            input = True,
                            frames_per_buffer = CHUNK)
    send_udp_thread = Thread(target = send_udp)
    send_udp_thread.setDaemon(True)
    send_udp_thread.start()
    record_voice_thread = Thread(target =record_voice, args = [send_stream])
    record_voice_thread.setDaemon(True)
    record_voice_thread.start()

def send_udp() :
    send_udp_socket = socket(AF_INET, SOCK_DGRAM)
    while True:
        if len (send_frames) > 0 :
            send_udp_socket.sendto(send_frames.pop(0), (HOST, send_port))
    send_udp_socket.close()

def record_voice(stream):
    while True:
        send_frames.append(stream.read(CHUNK))



class Gui:
    def __init__(self, Master):
        self.master = Master
        Master.title("text/voice chat")
        Master.geometry("640x400+100+100")
        Master.resizable(False, False)
    
        self.masterFrame = tkinter.Frame(Master)
        self.masterFrame.pack()

        self.recv_frame = tkinter.Frame(self.masterFrame)
        self.recv_frame.pack()
        self.text_log = tkinter.Text(self.recv_frame, width = 60, height = 25)
        self.text_log.pack()

        self.button_frame = tkinter.Frame(self.masterFrame)
        self.button_frame.pack()
        self.text_to_send = tkinter.StringVar()
        self.text_box = tkinter.Entry(self.button_frame, width = 40, textvariable = self.text_to_send)
        self.text_box.bind("<Return>", self.pressSend)
        self.text_box.pack()
        self.send_button = tkinter.Button(self.button_frame, text="Send", command= self.send)
        self.send_button.pack()

    def pressSend(self, event):
        self.send()

    def receive(self):
        while True:
            try:
                msg = client_socket.recv(BUFSIZ).decode('utf-8')
                self.text_log.insert(tkinter.END, msg + '\n')
                if msg == '<quit>':
                    break   
            except OSError:
                break

    def send(self):
        msg = self.text_to_send.get()
        if msg == "<quit>":
            client_socket.send(b'<quit>')

        client_socket.send(msg.encode('utf-8'))
        self.text_log.insert(tkinter.END, msg + '\n')


if __name__ == '__main__':  
    window = tkinter.Tk()
    app = Gui(window)

    HOST = input("Enter host: ")

    ADDR = (HOST, PORT)
    client_socket = socket(AF_INET, SOCK_STREAM)

    receive_voice_frame()
    send_voice_frame()

    try:
        client_socket.connect(ADDR)
    except ConnectionRefusedError:
        print("Server is not found.")
    else:
        receive_thread = Thread(target=app.receive)
        receive_thread.start()
        window.mainloop()
