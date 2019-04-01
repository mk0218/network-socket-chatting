#!/usr/bin/env python3
import os
from socket import AF_INET, socket, SOCK_STREAM, SOCK_DGRAM
from threading import Thread
import pyaudio
import tkinter

BUFSIZ = 1024
PORT = 12345
# for voice 
recv_host = '127.0.0.1'
recv_port = 12347
recv_frames = []
send_host = '127.0.0.1'
send_port = 12346
send_frames = []
  

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 40

onPressReturn = 1

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
            #if os.name != 'nt':
            #    print(CLEAR_LINE, end='')
            client_socket.send(msg.encode('utf-8'))

        except OSError:
            break
    client_socket.close()


    # https://github.com/ami-GS/Network-Python/blob/master/Sound/soundTransferSer.py#L25
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
    recv_udp_socket.bind((recv_host, recv_port))

    while True:   
        voice_data, recv_addr = recv_udp_socket.recvfrom(CHUNK*CHANNELS*2)
        if voice_data:
            recv_frames.append(voice_data)
            print("receiving...")

    recv_udp_socket.close()

def play_voice(stream):
    while True:
        if len(recv_frames) >= 10 and len(recv_frames) > 0:
                    stream.write(recv_frames.pop(0), CHUNK)
                    print("playing...")


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
            send_udp_socket.sendto(send_frames.pop(0), (send_host, send_port))
            #print("sending...")
    send_udp_socket.close()

def record_voice(stream):
    while True:
        send_frames.append(stream.read(CHUNK))
        #print("recording...")

def initGUI():
    window=tkinter.Tk()
    window.title("text/voice chat")
    window.geometry("640x400+100+100")
    window.resizable(False, False)

    frame1 = tkinter.Frame()
    frame1.pack()
    label_var = tkinter.StringVar()
    label_var.set("communicated texts")
    label1 = tkinter.Label(frame1, textvariable = label_var)
    label1.pack()

    frame2 = tkinter.Frame()
    frame2.pack()
    text_log = tkinter.Text(frame2, width = 50, height = 25)
    text_log.pack()

    button_frame = tkinter.Frame()
    button_frame.pack()

    button_text = tkinter.StringVar()
    entry = tkinter.Entry(button_frame, width = 40, textvariable = button_text)
    entry.bind("<Return>", onPressReturn)
    entry.pack()
    exit_button = tkinter.Button(button_frame, text = "Exit") #, command=exitTrigger
    exit_button.pack(side=tkinter.RIGHT, padx=100)
    send_button = tkinter.Button(button_frame, text="Send") #, command=sendText
    send_button.pack()
		#self.button3 = tkinter.Button(frame3, text="Voice Recv On/Off", command=self.voiceRecvOnOff, bg='red')
		#self.button3.pack()
		#self.button4 = tkinter.Button(frame3, text="Voice Send On/Off", command=self.voiceSendOnOff, bg='red')
		#self.button4.pack()
        # 
    

if __name__ == '__main__':  
    initGUI()
    HOST = input("Enter host: ")
    
    print("port")

    ADDR = (HOST, PORT)
    client_socket = socket(AF_INET, SOCK_STREAM)

    receive_voice_frame()
    send_voice_frame()
    print("voice")

    try:
        client_socket.connect(ADDR)
    except ConnectionRefusedError:
        print("Server is not found.")
    else:
        receive_thread = Thread(target=receive)
        receive_thread.start()
        send_thread = Thread(target=send)
        send_thread.start()
        
