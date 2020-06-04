from socket import *
import os
import select
import sys
import struct
import time
import threading

# Constants
ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
PACKET_FORMAT = 'bbHHh'
ICMP = getprotobyname('icmp')


class Pinger:

    def __init__(self, addr, timeout):
        self.addr = addr
        self.timeout = timeout
        self.icmp_seq = 1


    def get_checksum(self, data):
        sum = 0
        stop = len(data)
        count = 0
        while count < stop:
            sum += ord(data[count + 1]) * 256 + ord(data[count])
            sum &= 0xffffffff
            count += 2

        if stop < len(data):
            sum += ord(data[len(data) - 1])
            sum &= 0xffffffff

        sum = (sum >> 16) + (sum & 0xffff)
        sum += (sum >> 16)
        answer = ~sum
        answer &= 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer


    def send_one_ping(self, sock, addr, pid):
        checksum = 0
        header = struct.pack(PACKET_FORMAT, ICMP_ECHO_REQUEST, 0, 
                                    checksum, pid, self.icmp_seq)
        data = struct.pack('d', time.time())
        checksum = self.get_checksum(str(header + data))

        if sys.platform == 'darwin':
            checksum = htons(checksum) & 0xffff
        else:
            checksum = htons(checksum)

        # Construct the package with format:
        #     <------ 4 BYTES -------->
        # | TYPE | CODE |    CHECKSUM     |
        # |  Identifier | Sequence number |
        # |            DATA :::           |

        header = struct.pack(PACKET_FORMAT, ICMP_ECHO_REQUEST, 0, 
                                    checksum, pid, self.icmp_seq)
        packet = header + data

        self.icmp_seq += 1
        sock.sendto(packet, (addr, 1))
        


    def recieve_one_pong(self, sock, addr, pid, timeout):

        time_left = timeout

        while 1:
            
            # T0 Start polling the socket
            started_select = time.time()

            # select() blocks current thread until either a change is made in the 
            # sock (file descriptor) or the timout is reached
            ready_to_read = select.select([sock], [], [], timeout)[0]   

            # Only reaches this point if there's activity in the socket
            duration = time.time() - started_select
            
            if not ready_to_read:           # Empty socket
                return 'Request timed out'
            
            packet, address = sock.recvfrom(1024)
            ttl = ord(packet[8])
            packet = packet[20:28]
            packet_size = len(packet)

            # Unpacks the packet into the different headers
            _type, code, checksum, _id, seq = struct.unpack(PACKET_FORMAT, packet)
            
            time_left -= duration

            if time_left <= 0:
                return 'Request timed out'

            if _type == ICMP_ECHO_REPLY:
                return '{} bytes from {} {}: icmp_seq={} ttl={} time={} ms'.format(
                                     packet_size, gethostbyaddr(address[0])[0], address[0], 
                                     seq, ttl, round(duration * 1000, 3))


    def do_one_ping(self, addr, timeout):
        sock = socket(AF_INET, SOCK_RAW, ICMP)
        pid = os.getpid()

        self.send_one_ping(sock, addr, pid)
        delay = self.recieve_one_pong(sock, addr, pid, timeout)
        print(delay)
    

def ping(addr, timeout):
    pinger = Pinger(addr, timeout)

    for i in range(pings):
        ping = threading.Thread(target=pinger.do_one_ping, args=(addr, timeout))
        ping.start()
        ping.join()
        time.sleep(1)


if __name__ == '__main__':

    if len(sys.argv) == 1:
        print('You need to specify destination')
        sys.exit(0)

    addr = sys.argv[1]
    pings = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    ping(addr, 1)