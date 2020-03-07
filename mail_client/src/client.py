import socket
import sys
import ssl

class Client:
    
    def __init__(self, ip, port, username, password):
        self.username = username
        self.password = password
        self.host = ip
        self.port = port
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_message(self, mail_from, mail_to, mail_body):

        context = ssl.create_default_context()

        with socket.create_connection((self.host, self.port)) as sock:
            with context.wrap_socket(sock, server_hostname=self.host) as ssl_socket:
                
                connect_response = ssl_socket.recv(1024)
                self.check_response(connect_response, '220')

                ssl_socket.send('HELO smtp\r\n'.encode())
                helo_response = ssl_socket.recv(1024)
                self.check_response(helo_response, '250')

                ssl_socket.send('AUTH LOGIN\r\n'.encode())
                auth_response = ssl_socket.recv(1024)
                self.check_response(auth_response, '334')

                ssl_socket.send(self.username.encode() + '\r\n'.encode())
                print(ssl_socket.recv(1024).decode())

                


        #self.connection.
        #print(self.connection.recv(1024))


    def close(self):
        try:
            print("Closing connection to" + self.connection.getpeername[0] + self.connection.getpeername[1])
        finally:
            self.connection.close()
            sys.exit(0)
        
    # Ensures that the server response is according the what's expected
    def check_response(self, response, expected_response):
        if response[:3] != expected_response.encode():
            print("Failed to connect to server")
            self.close()

   



MAIL_FROM = "victortesthook@gmail.com"
IP = "smtp.gmail.com"
PORT = 465

# Creates the TCP connection & connects to the given IP and PORT
client = Client(IP, PORT, MAIL_FROM, 'bollar123')
client.send_message(MAIL_FROM, MAIL_FROM, "Hej hej!!")


client.close()