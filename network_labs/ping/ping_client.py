import socket
import time
import threading
import queue
import sys

# Sets up a UDP connection and sets default timeout at 1s
connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
connection.settimeout(1.0)

# Ensures that at host is given that will be pinged
if len(sys.argv) == 1:
    print("You must give a host name to ping")
    sys.exit(0)

# Default ping number is 10
nbr_of_pings = sys.argv[2] if len(sys.argv) > 2 else 10
HOST = sys.argv[1]
PORT = 12000

# Returns the data that will sent
def get_ping_data(sequence_number):
    return 'Ping {} {}'.format(sequence_number, time.strftime('%H:%M:%S', time.localtime())).encode()

# Performs the acutal ping and updates the packet statistics
def ping(sequence_number):
    try:
        global packets_recieved
        global packets_transmitted
        global total_packet_time

        t1 = time.time()
        data = get_ping_data(sequence_number)
        connection.sendto(data, (HOST, PORT))
        packets_transmitted += 1

        response, address = connection.recvfrom(1024)
        packets_recieved += 1
        dt = round((time.time() - t1) * 1000, 3)
        print('{} bytes from {}: ttl={} time={} ms'.format(data.__sizeof__(), address[0],
                                                       round(connection.gettimeout()), dt))
        total_packet_time += dt
    
    except:
        # An exception is raised when the timeout-time is reached
        return

packets_recieved = 0
packets_transmitted = 0
total_packet_time = 0

print('PING {} ({}) {} bytes of data'.format('127.0.0.1' if HOST == 'localhost' else HOST, 
                                    connection.getsockname()[0], get_ping_data(0).__sizeof__()))

# Queue for handling the pings in order, FiFo
queue = queue.Queue()
for i in range(1, nbr_of_pings):
    queue.put(threading.Thread(target=ping, args=(i,)))

# Each ping is given its own thread and the next ping isn't started until
# the previous ping is done
while not queue.empty():
    task = queue.get()
    task.start()
    task.join()

print(' --- Pings finished --- ')
print('{} packets transmitted, {} recieved, {}% packet loss, time {} ms'.format(
                                                    packets_transmitted, packets_recieved, 
                                                    round((packets_recieved / packets_transmitted), 2), total_packet_time))
    
    




    
