#!/usr/bin/env python3
from socket import AF_INET, socket, SOCK_STREAM, SOCK_DGRAM
from threading import Thread
import pyaudio
import tkinter
import numpy
import cv2

BUFSIZ = 1024
VID_BUF = 90456
PORT = 12345
VID_PORT = 12348
# for voice
HOST = '127.0.0.1'
RCV_HOST = '0.0.0.0'
name = ''
recv_port = 12347
recv_frames = []
send_port = 12346
send_frames = []


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 10240
RECORD_SECONDS = 40


class Client:
    def __init__(self):
        pass


def receive_voice_frame():
    p_r = pyaudio.PyAudio()
    recv_stream = p_r.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           output=True,
                           frames_per_buffer=CHUNK)
    receive_udp_thread = Thread(target=receive_udp)
    receive_udp_thread.setDaemon(True)
    receive_udp_thread.start()
    play_voice_thread = Thread(target=play_voice, args=[recv_stream])
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
    send_stream = p_s.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK)
    send_udp_thread = Thread(target=send_udp)
    send_udp_thread.setDaemon(True)
    send_udp_thread.start()
    record_voice_thread = Thread(target=record_voice, args=[send_stream])
    record_voice_thread.setDaemon(True)
    record_voice_thread.start()


def send_udp():
    send_udp_socket = socket(AF_INET, SOCK_DGRAM)
    while True:
        if len(send_frames) > 0:
            send_udp_socket.sendto(send_frames.pop(0), (HOST, send_port))
    send_udp_socket.close()


def record_voice(stream):
    while True:
        send_frames.append(stream.read(CHUNK))


class Video:
    def __init__(self):
        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            self.cam = cv2.VideoCapture("default.mp4")

        self.width = 800
        self.height = 600

        def __del__(self):
            if self.cam.isOpend():
                self.cam.release()

    def send_video(self):
        while True:
            ret, frame = self.cam.read()
            # cv2.imshow('My WebCam', frame)
            # cv2.waitKey(1)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = numpy.array(imgencode)
            data = data.tostring()
            vid_socket.sendall(str(len(data)).ljust(16).encode('utf-8'))
            vid_socket.sendall(data)

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def rcv_video(self):
        while True:
            try:
                length = self.recvall(vid_socket, 16).decode('utf-8')
                data = self.recvall(vid_socket, int(length))
                frame = numpy.fromstring(data, dtype='uint8')
                frame = cv2.imdecode(frame, 1)
                # frame = numpy.reshape(frame, (800, 600, 3))
                cv2.imshow('Video', frame)
                cv2.waitKey(10)
            except OSError:
                break
        cv2.destroyAllWindows()

    def activate(self):
        Thread(target=self.send_video).start()
        Thread(target=self.rcv_video).start()

# def record_video():
#     capture = cv2.VideoCapture(0)
#     while True:
#         ret, frame = capture.read()
#         encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
#         result, imgencode = cv2.imencode('.jpg', frame, encode_param)
#         data = numpy.array(imgencode)
#         data = data.tostring()
#         vid_socket.send(data)


class GUI:
    def __init__(self):
        self.master = tkinter.Tk()
        self.master.mainloop()

    def destroy(self):
        self.master.quit()
        self.master.destroy()


class GetHostGUI(GUI):
    def __init__(self):
        self.master = tkinter.Tk()
        self.master.title("Input Host")
        self.master.geometry("400x100")

        self.msg = tkinter.Label(self.master,
                                 text="Please Input Host and Port.")
        self.msg.pack()

        self.hostframe = tkinter.Frame(self.master)
        self.hostframe.pack()
        self.hostlabel = tkinter.Label(self.hostframe, text="Host:", width=10)
        self.hostlabel.pack(side=tkinter.LEFT)
        self.hostinput = tkinter.Entry(self.hostframe)
        self.hostinput.bind("<Return>", self.press_return)
        self.hostinput.pack(side=tkinter.LEFT)

        self.portframe = tkinter.Frame(self.master)
        self.portframe.pack()
        self.portlabel = tkinter.Label(self.portframe, text="Port: ", width=10)
        self.portlabel.pack(side=tkinter.LEFT)
        self.portinput = tkinter.Entry(self.portframe)
        self.portinput.bind("<Return>", self.press_return)
        self.portinput.pack(side=tkinter.LEFT)

        self.submitbtn = tkinter.Button(self.master, text="submit",
                                        command=self.submit_host)
        self.submitbtn.pack()

        self.master.mainloop()

    def press_return(self, event):
        self.submit_host()

    def submit_host(self):
        global HOST, PORT
        HOST = self.hostinput.get()
        PORT = self.portinput.get()
        if not PORT:
            PORT = 12345
        else:
            PORT = int(PORT)

        try:
            client_socket.connect((HOST, PORT))
        except ConnectionRefusedError:
            self.msg.config(text="Server {}:{} is not found".format(HOST, PORT))
        else:
            self.destroy()


class GetNameGUI(GUI):
    def __init__(self):
        self.master = tkinter.Tk()
        self.master.title("Input Name")
        self.master.geometry("400x100")

        initialmsg = "Successfully Connected to {}:{}".format(HOST, PORT)
        self.msg = tkinter.Label(self.master, text=initialmsg)
        self.msg.pack()

        self.nameframe = tkinter.Frame(self.master)
        self.nameframe.pack()
        self.namelabel = tkinter.Label(self.nameframe,
                                       text="Input Name: ", width=12)
        self.namelabel.pack(side=tkinter.LEFT)
        self.nameinput = tkinter.Entry(self.nameframe)
        self.nameinput.bind("<Return>", self.press_return)
        self.nameinput.pack(side=tkinter.LEFT)

        self.submitbtn = tkinter.Button(self.master, text="submit",
                                        command=self.submit_name)
        self.submitbtn.pack()

        self.master.mainloop()

    def press_return(self, event):
        self.submit_name()

    def submit_name(self):
        global name
        name = self.nameinput.get()
        client_socket.send(name.encode('utf-8'))
        result = client_socket.recv(BUFSIZ)
        print(result)
        if result == b'<Success>':
            self.destroy()
        else:
            self.msg.config(text="Name '{}' Already Exists. ".format(name) +
                            "Please Choose Another Name")


class MainGUI:
    def __init__(self, Master):
        self.master = Master
        Master.title("text/voice chat")
        Master.geometry("640x400+100+100")
        Master.resizable(False, False)

        self.masterFrame = tkinter.Frame(Master)
        self.masterFrame.pack()

        self.recv_frame = tkinter.Frame(self.masterFrame)
        self.recv_frame.pack()
        self.text_log = tkinter.Text(self.recv_frame, width=60, height=25)
        self.text_log.pack()

        self.button_frame = tkinter.Frame(self.masterFrame)
        self.button_frame.pack()
        self.text_to_send = tkinter.StringVar()
        self.text_box = tkinter.Entry(self.button_frame, width=40,
                                      textvariable=self.text_to_send)
        self.text_box.bind("<Return>", self.pressSend)
        self.text_box.pack()
        self.send_button = tkinter.Button(self.button_frame, text="Send",
                                          command=self.send)
        self.send_button.pack()

    # def update(self):
    #     ret, frame = self.vid.get_frame()
    #     if ret:
    #         self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
    #         self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW) 

    #     self.window.after(self.delay, self.update)

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

    # def rcv_video(self):
    #     while True:
    #         try:
    #             data = vid_socket.recv(BUFSIZ)
    #             self.video_frame.

    def send(self):
        msg = self.text_to_send.get()
        if msg == "<quit>":
            client_socket.send(b'<quit>')

        client_socket.send(msg.encode('utf-8'))
        self.text_log.insert(tkinter.END, msg + '\n')


if __name__ == '__main__':
    ADDR = (HOST, PORT)
    client_socket = socket(AF_INET, SOCK_STREAM)
    vid_socket = socket(AF_INET, SOCK_STREAM)
    get_host = GetHostGUI()
    get_name = GetNameGUI()
    try:
        vid_socket.connect((HOST, VID_PORT))
    except ConnectionRefusedError:
        print("Video Server is not found")
    else:
        vid_socket.send("Name: {}".format(name).encode('utf-8'))
        # receive_thread = Thread

    window = tkinter.Tk()
    app = MainGUI(window)

    receive_voice_frame()
    send_voice_frame()

    receive_thread = Thread(target=app.receive)
    receive_thread.start()
    v = Video()
    v.activate()
    window.mainloop()
