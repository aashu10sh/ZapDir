from client.bcolors import bcolors
import socket
import os
import datetime
import sys
import dotenv
from database import Session, Employee,engine
import string, random, sys
import smtplib, ssl
from base64 import b64encode
import time

server_session = Session(bind=engine)

class Server():
    def __init__(self)->None:
        global server_session
        if not '.env' in os.listdir(os.getcwd()):
            self.make_configurations()
        config = dotenv.dotenv_values()
        try: 
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
                self.local_ip_address :str = s.getsockname()[0]
                self.path = config['BASE_DIR']
                print("Loaded Hosting Path :"+self.path)
                # print(os.listdir(self.path))
                listing = ""
                for item in os.listdir(self.path):
                    listing = item+"\n"+""+listing
                self.listing = listing.strip() 
                self.info = config['MSG']
                self.email = config['EMAIL_ADDRESS']
                self.email_password = config['EMAIL_PASSWORD']
        except Exception as e:
            print(e)
        print("Loaded Configurations")
        # print(self.listing)
        # print(config)
    
    def add_user(self):
        username = str(input("USERNAME :"))
        email = str(input("EMAIL :"))
        password = Server.make_random_password()
        if self.email_user(username, email, password):
            data = Employee(username=username, password=password, email=email)
            server_session.add(data)
            server_session.commit()
        else:
            print("Error Adding User, Quitting!")
    
    def make_configurations(self)->bool:
        username = str(input('What would you like your username to be : '))
        host_name = str(input('What would you like your hostname to be : '))
        base_directory = str(input('What would you like your base directory to be : '))
        configured :bool = True
        try:
            os.listdir(base_directory)
        except FileNotFoundError:
            print('No Such Directory!')
            configured = False
        except PermissionError:
            print('Permission Denied for that directory')
            configured = False
        except NotADirectoryError:
            print("Provided Path is not a directory")
            configured = False
        finally:
            if configured == False:
                print("Please Re Configure!")
                sys.exit(1)
            else:
                with open('.env','w') as dotwriter:
                    dotwriter.write(f'USER={username}\n')
                    dotwriter.write(f"HOST={host_name}\n")
                    dotwriter.write(f"BASE_DIR={base_directory}\n")
                    dotwriter.write("MSG=${USER}.${HOST}\n")
                print("Succesfully Configured")
                return true
            

    def authenticate(self, connection):
        connection.send('data?'.encode())
        username, password = connection.recv(1024).decode('utf8').strip('\n').split(',')
        found_user = server_session.query(Employee).filter(Employee.username == username).first()
        if found_user:
            if found_user.password == password:
                return True, connection, 'DONE'
            else:
                return False, connection, 'INCORRECT CREDENTIALS'
                #incorrect credentials
        else:
            return False, connection, 'NO SUCH USER, PLEASE CONTACT YOUR ADMINISTRATOR'
            # no such user, please contact your administrator



    def run(self):
        print(bcolors.OKGREEN+"Listening on port 2032"+bcolors.ENDC)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listner:
            try:
                listner.bind((self.local_ip_address,2032))
            except OSError:
                print(bcolors.FAIL+"[Server Cool Down] - Try again in 2 mins"+bcolors.ENDC)
                sys.exit(1)
            listner.listen(100)
            while True:
                connection, self.address = listner.accept()
                print(bcolors.OKGREEN+self.address[0]+"✔️"+bcolors.ENDC)
                message = str(connection.recv(5).decode()).strip('\n')
                # print(message)
                if message == 'auth':
                    v, connection_new, why = self.authenticate(connection)
                    if v:
                        connection_new.send("Authenticated".encode())
                        cmd = str(connection_new.recv(1024).decode()).strip('\n')
                        
                        if cmd == "dir" or cmd == "ls":
                            connection_new.send(self.get_directory_listing())
                            print('{\LS\}')
                            connection_new.close()

                        elif cmd[:8] == "download" :
                            self.handle_download(cmd,connection)
                            print("{\DOWN\}")
                        connection_new.close()
                    else:
                        connection_new.send(("Could not verify!\n"+why).encode())
                        connection_new.close()
                elif message == 'bro?':
                    connection.send("yes bro".encode())
                    print('\{CHECK\}')
                    connection.close()
                elif message == 'info?':
                    connection.send(self.info.encode())
                    print('\{INFO\}')
                    connection.close()
    
    def get_directory_listing(self):
        return self.listing.encode()
    
    def handle_download(self,message,download_ini_connection):
        file_name = message.split(';')[1]
        if file_name in os.listdir(self.path):
            # download_ini_connection.send(f"{file_name} Verified!, Initializing Secondary Port and Sending ...".encode())
            with open(os.path.join(self.path,file_name),'rb') as reader:
                data = b64encode(reader.read())
                print(len(data))
                time.sleep(1)
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
                try:
                    sock.connect((self.address[0],2033))
                    sock.send(data)
                except ConnectionRefusedError:
                    print("Problem Establishing Data Line!")
                    exit(1)
                finally:
                    download_ini_connection.send("DONE".encode())
                    download_ini_connection.close()
        else:
            download_ini_connection.send("No Such File Found!".encode())
            download_ini_connection.close()
    @staticmethod
    def make_random_password():
        samplespace = string.ascii_letters +string.digits
        return "".join(random.choices(samplespace,k=8))
    
    def email_user(self,username, email, password):
        context = ssl.create_default_context()
        message = f"""
        Hello {username}, This is your admistrator,
        This is your new password {password}
        Admin,
        Zapdir
        """
        error = False
        try :
            with smtplib.SMTP('smtp.gmail.com',587) as server:
                server.starttls(context=context)
                server.login(self.email,self.email_password)
                server.sendmail(self.email, email, message)
        except Exception as e:
            print(e)
            error = True

        return True if not error else  False


if __name__ == '__main__':
    serve = Server()
    # serve.add_user()
    serve.run()
