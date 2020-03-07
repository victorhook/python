import random
from socket import *

server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(('', 12000))

server_online = True

while server_online:
    rand = random.randint(0, 10)

    message, address = server_socket.recvfrom(1024)
    message = message.decode().upper()

    print('Message recieved from: {}, saying: ', address, message.decode())

    if rand > 4:
        server_socket.sendto(message.encode(), address)
