import socket
import threading
import time
import json
import sys

def get_server_host_port(servername):
    file = open("server_datas.json", "r")
    jobj = json.load(file)
    host = jobj[servername]["host"]
    port = jobj[servername]["port"]

    return host, port


def get_servername():
    servername = sys.argv[1]

    return servername

class Server:
    def __init__(self, host='localhost', port=8084):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servername = port
        
        self.server.bind((host, port))
        self.server.listen(10)
        self.clients = {}
        self.nicknames = []
        self.channels = {}

    def broadcast(self, message, nickname):
        for client in self.clients:
            if self.clients[client]["nickname"] != nickname:
                client.send(message)
    
    def broadcast_channel(self, channel, message, nickname):
        # c1 is the client of the channel that we pass in parameter
        for c1 in self.channels[channel]["clients"]:
            for client in self.clients.keys():
                if (self.clients[client]["nickname"] == c1) and (c1 != nickname):
                    client.send(message)
            #print("here", client)
            #client.send(str(message).encode())

    def nickname_to_client(self, nickname):
        for client in self.clients:
            if self.clients[client]["nickname"] == nickname:
                return client
        return None


    def help_function(self, client):
        message = "This is the available commands :"
        message += "\n- /away message : Indicate his absence when we are sent a message in private (in response a message can be sent)."\
                        "A new /away command reactivates the user."
        message +="\n- /help : Displays the list of available commands."
        message +="\n- /list : Displays the list of channels in IRC"
        message +="\n- /msg [canal|nick] message : To send a message to a user or on a channel (where we arepresent or not)."\
                    "The channel or nick arguments are optional."
        message +="\n- /names : Show users connected to a channel. If the channel is not specified,"\
                                    "shows all users of all channels" 
        
        client.send(message.encode("utf-8"))


    def list_function(self, client):
        message = ""
        for channel in self.channels:
            message += "- "+channel +" \n"
        client.send(message.encode("utf-8"))

    def nickname_function(self, client, message):
        # we receive the message /nickname koussix
        nickname = message.replace("/nickname ", "")
        self.nicknames.append(nickname)
        self.clients[client]["nickname"] = nickname
        self.clients[client]["status"] = "Available"
        self.clients[client]["channels"] = []
        #client.send(f"nickname_approved:{nickname}".encode())
        #self.clients[client] = nickname
        self.broadcast(f"\n{nickname} has joined the chat!".encode('utf-8'), nickname)

    def join_function(self, client, message):
        message = message.replace("/join ", "").split(" ")
        channel = message[0]
        if channel[0] == "#":
            cle = ""
            if(len(message) == 2):
                cle = message[1]

            joined = True

            if channel not in self.channels.keys():
                self.channels[channel] = {}
                self.channels[channel]["clients"] = [self.clients[client]["nickname"]]
                self.clients[client]["channels"] = [channel]
                self.channels[channel]["cle"] = cle # is "" or the key that the user entred
            # dict of channels {channel1 : [client1, client2 , ...], channel2 :[]}
            else:
                if(self.channels[channel]["cle"] == cle):
                    if(self.clients[client]["nickname"]  in self.channels[channel]["clients"]) :
                        client.send(f"\nYou are already in the channel {channel}".encode('utf-8'))
                        joined = False
                        #print("you are already in the channel", channel)
                    else:
                        self.channels[channel]["clients"].append(self.clients[client]["nickname"])
                        self.clients[client]["channels"].append(channel)

                    #self.channels[channel]["clients"].append(self.clients[client]["nickname"])
                else:
                    client.send("\nError : wrong channel password")
                    joined = False

            if joined:
                #print("joined ")
                client.send(f"\nYou have joined {channel}".encode('utf-8'))
                nickname = str(self.clients[client]["nickname"])
                msg = f'\n{channel}->{nickname} has joined the channel'
                self.broadcast_channel(channel, msg.encode('utf-8'), nickname)
        
        else:
            client.send("\n Command error : the name of the channel must start with '#' caracter retry with /join #<your_channel>".encode('utf-8'))

    
    def invite_function(self, client, message):
        message = message.replace("/invite ", "").split(" ")
        channel = ""
        user = message[0]

        if len(message) == 1:
            channel = self.clients[client]["channels"][-1] # last joined channel
        else:
            channel = message[1]
        
        client_invite = self.nickname_to_client(user)
        nickname = self.clients[client]["nickname"]
        cle = self.channels[channel]["cle"]
        message = f'\n{nickname} invite you to join {channel}, type /join {channel} {cle} to enter'
        client_invite.send(message.encode("utf-8"))

    
    def msg_function(self, client, message):
        message = message.replace("/msg ", "").split(" ")
        nickname = self.clients[client]["nickname"]
        content = " ".join(message[1:])

        if message[0].startswith("#"):
            channel = message[0]
            # [word]koceila: msg
            content = "["+channel+"]"+nickname+":" + content
            self.broadcast_channel(channel, str(content).encode("utf-8"), nickname)
        else:
            user = message[0]
            # [word]koceila: msg
            content = "[Private]"+nickname+":" + content
            client_private = self.nickname_to_client(user)
            client_private.send(content.encode("utf-8"))
            
            if self.clients[client_private]["status"] != "Available":
                status = self.clients[client_private]["status"]
                client.send(f'{user}[Not Available]: {status}'.encode('utf-8'))   


    def names_function(self, client, message):
        message = message.split(" ")
        channel = ""
        if len(message) == 2:
            channel = message[1]
            msg = f"Here is the users connected to {channel} \n"
            for c in self.channels[channel]["clients"]:
                msg += c +" ,"

            client.send(msg.encode('utf-8'))        
        else:
            msg = ""
            for channel in self.channels.keys():
                msg += f"\nHere is the users connected to {channel} : \n"
                for c in self.channels[channel]["clients"]:
                    msg += c +" ,"
            
            client.send(msg.encode('utf-8'))

    
    def away_function(self, client, message):
        message = message.replace("/away", "")
        if(len(message) !=0 ):
            self.clients[client]["status"] = message
        else:
            if self.clients[client]["status"] == "Available" : 
                self.clients[client]["status"] = "I'll be back soon"
            else:
                self.clients[client]["status"] = "Available"        

    
    def quit_function(self, client, message):
        nickname =  self.clients[client]["nickname"]
        del self.clients[client]
        client.send("/quit".encode('utf-8'))
        time.sleep(0.1)
        client.close()
        self.broadcast(f"{nickname} has left the chat!".encode('utf-8'), nickname)
        for channel in self.channels:
            if client in self.channels[channel]["clients"]:
                self.channels[channel]["clients"].remove(nickname)



    def handle(self, client):
        while True:
            
                message = client.recv(1024).decode('utf-8')
                
                if message.startswith("/help"):
                    self.help_function(client)
                    
                elif message.startswith("/list"):
                    self.list_function(client)

                elif message.startswith("/nickname"):
                    self.nickname_function(client, message)
                    
                elif message.startswith("/join"):
                    self.join_function(client, message)
                    
                elif message.startswith("/invite"):
                    self.invite_function(client, message)

                elif message.startswith("/msg"):
                     self.msg_function(client, message)
                        
                elif message.startswith("/names"):
                    self.names_function(client, message)

                elif message.startswith("/away"):
                    self.away_function(client, message)

                elif message == "/quit":
                    self.quit_function(client, message)
                    break

                elif message != "":
                    nickname = self.clients[client]["nickname"]
                    # we send the message in every channel where the user are
                    for channel in self.clients[client]["channels"]:
                        message = "["+channel+"]"+nickname+":" + message
                        self.broadcast_channel(channel, str(message).encode('utf-8'), nickname)



    def receive(self):
        while True:
            client, address = self.server.accept()
            client.send("\nWelcome to the chat!".encode('utf-8'))
            print(f"Connected with, {str(address)}")
            #client.send("nickname:".encode())
            self.clients[client] = {}
            self.clients[client]["address"] = address
            threading.Thread(target=self.handle, args=(client,)).start()

    def start(self):
        print("Server started!")
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()
        receive_thread.join()


host = "localhost"
port = 8084
if sys.argv == 2 :
    servername = get_servername()
    host, port = get_server_host_port(servername)

server = Server(host, port)
server.start()