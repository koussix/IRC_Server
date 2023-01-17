import socket
import sys
import os
import json
import time
import threading
import queue

def get_server_host_port(servername):
    file = open("server_datas.json", "r")
    jobj = json.load(file)
    host = jobj[servername]["host"]
    port = jobj[servername]["port"]

    return host, port

class Client:
    def __init__(self, servername):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = get_server_host_port(servername)
        #print(host, port)
        self.client.connect((host, int(port)))
        self.nickname = None
        self.servername = servername
        self.channels = []

    def set_nickname(self, nickname):
        self.nickname = nickname
        self.client.send(f"/nickname {self.nickname}".encode('utf-8'))

    def set_servername(self, servername):
        self.servername = servername

    def join_channel(self):
        channel = input("Please enter the channel you want to join: ")
        self.client.send(f"/join {channel}".encode())
        #print(f"You have joined channel {channel}")
        self.channels.append(channel)

    def receive_messages(self):
        while True:
            message = self.client.recv(1024).decode('utf-8')
            if message == "/quit":
                self.client.close()
                break
            else:
                print(message)

    def send_message(self, message):
        self.client.send(f"{message}".encode('utf-8'))
    
    def close(self):
        self.client.send("/quit".encode('utf-8'))
        

def get_nickname_servername():
    assert len(sys.argv)==3, "Specify the nickname"
    nickname = sys.argv[1]
    servername = sys.argv[2]

    return nickname, servername


import tkinter as tk

class Client_GUI(tk.Tk):
    def __init__(self, servername, nickname):
        super().__init__()
        self.client = Client(servername)
        self.title("Client"+nickname)
        self.geometry("600x500")
        self.create_widgets()
        self.listen_thread = threading.Thread(target=self.receive_messages)
        self.listen_thread.start()
        
    def create_widgets(self):
        # Create message display panel
        self.messages_panel = tk.Frame(self, bg='white', width=450, height=400)
        self.messages_panel.place(x=25, y=25)
        self.messages_display = tk.Text(self.messages_panel, width=70, height=25)
        self.messages_display.pack()
        # Create message input field
        self.message_label = tk.Label(self, text="Enter message:")
        self.message_label.place(x=25, y=450)
        self.message_entry = tk.Entry(self)
        self.message_entry.place(x=150, y=450)
        # bind the send_message on the "enter" keyboard
        self.message_entry.bind("<Return>", self.send_message)
        # Create join channel button
        self.send_button = tk.Button(self, text="Send", command=self.send_message)
        self.send_button.place(x=400, y=450)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def receive_messages(self):
        #time.sleep(0.1)
        while True:
            message = self.client.client.recv(1024).decode('utf-8')
            if message == "/quit":
                self.client.close()
                super().destroy()
                break
            else:
                #self.messages_queue.put(message)
                self.messages_display.insert(tk.END, message+'\n')
                print(message)


    def set_nickname(self, nickname):
        self.client.set_nickname(nickname)

    def send_message(self, event=None):
        message = self.message_entry.get()
        self.client.send_message(message)
        self.message_entry.delete(0, tk.END)
        message = nickname+">"+message
        self.messages_display.insert(tk.END, message+'\n')

    def close(self):
        self.client.close()
        super().destroy()


nickname, servername = get_nickname_servername()
client = Client_GUI(servername, nickname)
client.set_nickname(nickname=nickname)
client.mainloop()



