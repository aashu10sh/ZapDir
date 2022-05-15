from main import bcolors
import socket
import os
import datetime
import sys
class Server():
    def __init__(self,basedir,info)->None:
        print(bcolors.OKGREEN+"Listening on port 2032"+bcolors.ENDC)
        try: 
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
                self.local_ip_address :str = s.getsockname()[0]
                self.path = "/home/ash/Downloads"
                listing = ""
                for item in os.listdir(self.path):
                    listing = item+"\n"+""+listing
                self.listing = listing.strip() 
                self.info = info
        except Exception as e:
            print(e)
            pass
    
    def authenticate(self, key:str):
        pass
    def run(self):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            try:
                sock.bind((self.local_ip_address,2032))
            except OSError:
                print(bcolors.FAIL+"[Server Cool Down] - Try again in 2 mins"+bcolors.ENDC)
                sys.exit(1)
            sock.listen(100)
            quit = False
            while quit != True:
                connection, addr = sock.accept()
                print(f"{addr[0]} :::: {datetime.datetime.now()}")
                message = str(connection.recv(1024).decode())
                """
                Debug place here
                """
                if message == "INIT CHECK\n":
                    print("RECIEVED CHECK PING!")
                    connection.close()
                if message == "INFO?\n":
                    connection.send(("".join(self.info)).encode())
                    print("RECIEVED INFO PING.")
                    connection.close()
                if message == str("DIRLIST?\n"):
                    print("DIRLIST GIVING")
                    connection.send(self.listing.encode())
                    connection.close()

                if message[:8] == "DOWNLOAD":
                    try:
                        file_name = message.split(';')[1]
                        closed = False
                    except IndexError as e:
                        connection.send(("PROTOCOL ERROR ==2== ").encode())
                        connection.close()
                        file_name = "PRERR"
                        closed = True
                    if file_name in self.listing and file_name != "PRERR":
                        mes = f"[X] File Found\nSending File {file_name}"
                        connection.send(mes.encode())
                        connection.send(b"[+] Initializing Secondary Port to send file")
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fileSock:
                            full_path = os.path.join(self.path,file_name.strip('\n'))
                            fileSock.connect((addr[0],2033))
                            print("[+] Sending File")
                            with open(full_path,'rb') as file_handler:
                                content = file_handler.read()
                                content_to_send = b64encode(content)
                            fileSock.send(content_to_send)
                            fileSock.close()
                            print(bcolors.GREEN+"[ Sent File successfully ]"+bcolors.ENDC)
                        connection.close()
                    else:
                        print(f"{bcolors.GREEN} NO SUCH FILE {file_name} {bcolors.ENDC}")
                        if not closed:
                            mes = f"No Such File {file_name}"
                            connection.send(mes.encode())
                            connection.close()
        pass

