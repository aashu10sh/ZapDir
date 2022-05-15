import socket
import argparse
# import scapy.all as scapy
import os
import sys
import ipaddress 
import datetime
from base64 import b64encode,b64decode
import dotenv
from bcolors import bcolors
import threading

def help(o=None):
    if not o:
        print('||INCORRECT USE||\nAvailable Options :\ncheck\ninfo\nlist\ndownload\ndir')
    if o == 'l':
        print("List command requires IP Address :\nuse: python3 main.py list 192.156.1.34")
    if o =='d':
        print('Download command requires an Ip address and a File name\nuse: python3 main.py download 192.178.2.43 info.txt')    


class Client():
    def __init__(self)->None:
        try: 
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
            self.local_ip_address :str = s.getsockname()[0]
        except Exception as e:
            pass
        has_config= self.handle_configurations()
        if not has_config :
            _ = self.make_config()
        config = dotenv.dotenv_values()
        self.username = config['USERNAME']

    def scan_network(self)->list: #USING SCAPY GETS ACTIVE IP's ON A NETWORK
        if os.getuid() != 0:
            print(bcolors.FAIL+"You will need super user privileges to run this feature")
            sys.exit(1)
        self.netmask : str = '.'.join(self.local_ip_address.split('.')[:2]) + '.1.1/24'

        # ip_addr = socket.gethostbyname(socket.gethostname())
        # netmask = ipaddress.IPv4Network(ip_addr).netmask
        # print(netmask)
        # iface = ipaddress.ip_interface(self.local_ip_address+"/"+str(netmask))
        # print(iface)

        (answered_list, unanswered_list) = scapy.arping(self.netmask,verbose=0)
        ip_list :list = []
        for element in answered_list:
            # print(element)
            ip_list.append(element[1].psrc)
        return list(set(ip_list))
    def checkServing(self,ip_list:list):
        print("Active Devices : ",ip_list)
        for address in ip_list:
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
                  try:
                    sock.connect((address,2032))
                    sock.send(b"You There?")
                  except ConnectionRefusedError as e:
                    print(f"{e} :: {address}") # USING SOCKET ONLY CHECKS ACTIVE IP's IN A NETWORK
    def checkByForce(self)->list:
        answered :list = []
        ip_arr = self.local_ip_address.split('.')
        ip = "".join( x+"." for x  in ip_arr[:-1])
        for i in range(0,256):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.settimeout(0.001)
                    ip_address =  f"{ip}{i}"
                    # print("CURRENT {}".format(ip_address),end="")
                    sock.connect((ip_address,2032))
                    try:
                        sock.send(b"bro?")
                    except BrokenPipeError:
                        pass
                    finally:
                        # print("FOUND {}".format(ip_address))
                        answered.append(ip_address)
                except (ConnectionRefusedError,OSError) as e:
                    pass
                    # print("NOPE {}".format(e),end="")

        return answered
    def handle_configurations(self):
        if '.env' in os.listdir(os.getcwd()):
            return True
        else :
            return  False
    def make_config(self):
        with open('.env','w') as writer:
            username = str(input("Please Enter Your Username : "))
            writer.write(f'USERNAME={username}')
        return True

    def get_additional_info(self,answered_list:list) ->dict:
        information_dict = {}
        for ip in answered_list:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, 2032))
                sock.send(b"info?\n")
                information = sock.recv(1024).decode()
                information_dict[ip] = information
        return information_dict

    def authenticate(self,address,listing=True,download=False,file_name=None):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as auth_sock:
            try:
                auth_sock.connect((address,2032))
            except ConnectionRefusedError:
                print("Server is Offline!, QUITTING!")
                exit(1)
            auth_sock.send('auth'.encode())
            auth_sock.recv(1024)
            password = input(f"Enter Password for {self.username} :")
            auth_sock.send((self.username+','+password).encode())
            result = auth_sock.recv(1024).decode()
            if result == "Authenticated":
                print("Succesfully Authenticated!")
                if listing == True:
                    print(bcolors.BOLD+"Printing Listing Files :"+bcolors.ENDC)
                    print(self.get_listing(auth_sock))
                if download == True and file_name !=None:
                    self.handle_download(auth_sock,file_name)
            else:
                print(result)
    def file_writer(self,file_name):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listner_sock:
            listner_sock.bind((self.local_ip_address,2033))
            listner_sock.listen(100)
            connection, address = listner_sock.accept()
            raw_data = connection.recv(50000000)
            print(len(raw_data))
            # raw_data = str(raw_data)+'=' * (-len(raw_data) % 4)
            with open(file_name,'wb') as binary_writer:
                binary_writer.write(b64decode(raw_data))        
    def handle_download(self,connection,file_name):
        connection.send(('download;'+file_name).encode())
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listner_sock:
            listner_sock.bind((self.local_ip_address,2033))
            listner_sock.listen(100)
            connection, address = listner_sock.accept()
            raw_data = connection.recv(50000000)
            print(len(raw_data))
            # raw_data = str(raw_data)+'=' * (-len(raw_data) % 4)
            with open(file_name,'wb') as binary_writer:
                binary_writer.write(b64decode(raw_data))
        # print(connection.recv(1024).decode())
    def get_listing(self,connection):
        connection.send('ls\n'.encode())
        listing = connection.recv(1024).decode()
        return listing



    def get_directory_listing(self,host:str)->list:
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.connect((host,2032))
            sock.send(b"ls")

            listing = sock.recv(1024).decode()
            listing = listing.strip('\n')
            return listing
    def download_file(self,file_name:str, host:str):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, 2032))
            cmd = "DOWNLOAD;{}".format(file_name)
            sock.send(cmd.encode())
            

if __name__ == '__main__':
    new = Client()
    print(sys.argv)
    if len(sys.argv) == 1:
        help()
        exit()
    # print(new.scan_network())
    if sys.argv[1] == 'check':
        addr = new.checkByForce()
        print(addr)
    if sys.argv[1] == "info":
        new_addr = new.checkByForce()
        info_d = new.get_additional_info(new_addr)
        print(info_d)
    if sys.argv[1] =='download':
        try:
            new.authenticate(sys.argv[2],download=True,file_name=sys.argv[3],listing=False)
        except IndexError:
            help('d')
            exit()
    if sys.argv[1] =='dir':
        try:
            new.authenticate(sys.argv[2],listing=True,download=False,file_name=None)
        except IndexError:
            help('l')
            exit()
        # listing = new.get_directory_listing()
        # print(listing)
    else:
        pass
