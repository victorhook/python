#!/usr/bin/env

import random
import re
import socket
import struct
import sys
import time

ECHO_REQUEST = 8
ECHO_REPLY   = 0
__version__  = '1.0'
__doc__      = 'A simple ping utility made in python'
__author__   = 'victorhook' 
NAME         = 'hookPinger'
DEFAULT_SIZE = 40
DEFAULT_TTL  = 64


# --- CLASSES --- #

class Ping:

    def __init__(self, id_nbr):

        self.seq_nbr = 0
        self.id_nbr = id_nbr
        self.pings_made = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.ping_durations = []

class Flags:

    # booleans
    quiet        = False
    verbose      = False
    show_version = False
    help         = False
    bad_args     = False

    # integers
    ttl          = 64
    data_len     = 40
    interval     = 1

    # ip or hostname that will be used
    destination  = ''

    # integers, with non-default values
    count        = None    # default is infinite
    deadline     = None

    # verbose flags
    def __repr__(self):
        attrs = [attr for attr in dir(self) if attr[0] != '_']
        return '\n'.join(f'{attr}: {getattr(self, attr)}' for attr in attrs)

class Argument:

    def __init__(self, short, long, description):
        self.short = short
        self.long = long
        self.description = description


# --- FUNCTIONS --- #

# calculates checksum for icmp (1's complement)
def get_checksum(packet):
    
    chksum = index = 0
    stop = len(packet)

    # treat all bytes as 16-bit words and add them to total sum
    while index < stop:
        chksum += packet[index] + (packet[index + 1] << 8)
        index += 2

    # check if we stopped at uneven number (missed last one)
    if index < stop:
        chksum += packet[-1]

    # add the 'remainder-bits'
    chksum = (chksum >> 16) + (chksum & 0xffff)
    # once again, in case we got overflow from add above
    chksum += (chksum >> 16)

    # invert all bits and return 16-bit
    return (~chksum & 0xffff)
    
# creates a random identifier
def get_identifier():
    return random.randint(0, 0xffff)

# returns a list of random bytes with given length 
def get_default_data(length):
    return [random.randint(0, 255) for i in range(length)]

# returns the ip and hostname of the requested destination
def get_host_info(destination):
    
    if re.search(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', destination):
        # looks like ip format
        host = socket.gethostbyaddr(destination)
        hostname = host[0]
        ip = host[2][0]
        return ip, hostname
    
    # chosen destination is by name format
    return socket.gethostbyname(destination), destination
    
# creates an empty packet to calculate checksum to check if it matches reply
def make_compare_packet(id_nbr, seq_nbr, icmp_packet):
    comp_packet = [0, 0, 0, 0]
    comp_packet.extend([(id_nbr >> 8), id_nbr & 0xff])
    comp_packet.extend([(seq_nbr >> 8), seq_nbr & 0xff])
    comp_packet.extend(icmp_packet[8:])
    return comp_packet

# creates a packet
def make_packet(ping_type, seq_nbr, id_nbr, data):

    # ping type and code
    packet = [ ping_type, 0 ]
    
    # checksum
    chksum = 0
    packet.extend([chksum, chksum])
    # identifiter
    packet.extend([id_nbr >> 8, id_nbr & 0x00ff])
    # sequence number
    packet.extend([seq_nbr >> 8, seq_nbr & 0x00ff])
    # payload data
    packet.extend(data)
    
    # calculate checksum from payload and update the field
    chksum = get_checksum(packet)
    packet[2] = chksum & 0x00ff
    packet[3] = chksum >> 8

    return bytes(packet)

# helper function for _ping
def read_one_ping(sock, expected_id, expected_seq):

    # might fail because of timeout
    try:
        reply = sock.recv(1024)

        if reply:
            
            # trim of IP-headers (20 bytes)
            icmp = reply[20:]

            if icmp[0] == ECHO_REQUEST:
                # this is our ping request, read one more packet
                reply = sock.recv(1024)
                icmp = reply[20:]


            # reply packet recieved
            if icmp[0] == ECHO_REPLY:

                # unpack checksum, identifier and sequence to ensure they are correct
                chksum, id_nbr, seq_nbr = struct.unpack('>HHH', icmp[2:8])

                # construct a new package to calculate checksum
                comp_packet = make_compare_packet(id_nbr, seq_nbr, icmp)

                compare_chksum = get_checksum(comp_packet)
                compare_chksum = socket.htons(compare_chksum)

                return compare_chksum, chksum, id_nbr, seq_nbr

    except socket.timeout:
        return None

# helper function for _ping
def send_one_ping(sock, dst_ip, seq_nbr, id_nbr, data_len=40):
    data = get_default_data(data_len)
    packet = make_packet(ECHO_REQUEST, seq_nbr, id_nbr, data)
    sock.sendto(packet, (dst_ip, 0))

# helper function for ping()
# this function does the actualy pinging
def _ping(sock, ip, hostname, ttl, pinger, data_len):

    # start timer
    start = time.time()

    send_one_ping(sock, ip, pinger.seq_nbr, data_len)
    pinger.packets_sent += 1
    result = read_one_ping(sock, pinger.id_nbr, pinger.seq_nbr)

    duration = time.time() - start
    pinger.seq_nbr += 1

    # if result is None, an error occured (probably timeout)
    if result:
        compare_chksum, chksum, id_nbr, seq_nbr = result
        # icmp header is 8 bytes
        data_size = data_len + 8
        print(f'{data_len} bytes from {hostname} ({ip}): icmp_seq={seq_nbr} '  + 
               f'ttl={ttl} time={round(duration * 1000, 3)} ms')
        pinger.packets_received += 1
        return duration

    else:
        print('Timeout reached')
        return 0

# starter method for handling the pinging
def ping(sock, destination, ttl, delay, pings=None, data_len=40):

    try:
        start = time.time()

        ip, hostname = get_host_info(destination)

        # data + icmp headers + ip-headers
        total_packet_size = data_len + 8 + 20

        print(f'PING {hostname} ({ip}) {data_len}({total_packet_size}) ' +  
                'bytes of data')
        
        pinger = Ping(get_identifier())

        # if not chosen number of pings, we ping forever
        if not pings:
            pass

        else:
            # ping finite times
            for i in range(pings):
                ping_time = _ping(sock, ip, hostname, ttl, pinger, data_len)
                if ping_time:
                    pinger.ping_durations.append(ping_time)
                time.sleep(delay)

    except KeyboardInterrupt:
        pass

    finally:
        packet_loss = int(1 - (pinger.packets_received / pinger.packets_sent))
        total_time = int((time.time() - start) * 1000)
        print(f'\n--- {destination} ping statistics ---')
        print(f'{pinger.packets_sent} packets transmitted, {pinger.packets_received} ' + 
              f'received, {packet_loss}% packet loss, time {total_time} ms')





ARGS = [
    Argument('c', 'count', 'number of pings'),
    Argument('i', 'interval', 'time delay between pings'),
    Argument('s', 'size', f'number of bytes, default is {DEFAULT_SIZE}'),
    Argument('t', 'ttl', f'set specific Time To Live, default is {DEFAULT_TTL}'),
    Argument('w', 'deadline', 'deadline, program will exit after this time, not matter what'),
    Argument('v', 'verbose', 'verbose output'),
    Argument('V', 'version', 'show version'),
    Argument('q', 'quiet', 'quiet output'),
    Argument('h', 'help', 'show help'),
]

def display_help():
    print(f'-- {NAME} --')
    print(f'{__doc__}\n')
    print(f'Usage: {NAME} ip/host\n')
    for arg in ARGS:
        print(f'\t-{arg.short}, --{arg.long} \t = {arg.description}')
    print('\n')

def display_version():
    print(f'[*] -- {NAME} -- \n[*]')
    print(f'[*] {__doc__}')
    print(f'[*] Version: {__version__}')
    print(f'[*] Author: {__author__}')

def parse_args():

    flags = Flags()

    nbr_of_args = len(sys.argv)
    if nbr_of_args > 1:

        arg = 1
        while arg < nbr_of_args:

            argument = sys.argv[arg]

            # count, desired number of pings
            if argument == '-c' or argument == '--count':
                flags.count = sys.argv[arg + 1]
                arg += 1

            # interval, the time delay between pings
            elif argument == '-i' or argument == '--interval':
                flags.interval = sys.argv[arg + 1]
                arg += 1

            # chosen number of bytes. default is 40, which + icmp header is 48
            elif argument == '-s' or argument == '--size':
                flags.size = sys.argv[arg + 1]
                arg += 1

            # set specific Time To Live, default is 64
            elif argument == '-t' or argument == '--ttl':
                flags.ttl = sys.argv[arg + 1]
                arg += 1

            elif argument == '-w' or argument == '--deadline':
                flags.deadline = sys.argv[arg + 1]
                arg += 1

            # verbose output
            elif argument == '-v' or argument == '--verbose':
                flags.verbose = True

            # show version 
            elif argument == '-V' or argument == '--version':
                flags.show_version = True

            # quiet output (except for summary prinout)
            elif argument == '-q' or argument == '--quiet':
                flags.quiet = True

            # display help
            elif argument == '-h' or argument == '--help':
                flags.help = True

            elif is_ip(argument) or is_hostname(argument):
                flags.destination = argument

            else:
                flags.bad_args = True
                break
            
            arg += 1

    else:
        flags.bad_args = True

    # check if user wants help or just show the version
    if flags.help or flags.bad_args:
        display_help()
    elif flags.show_version:
        display_version()

    return flags



if __name__ == "__main__":

    flags = parse_args()

    """        
    random.seed()

    timeout = 1
    ttl = 64

    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
    sock.settimeout(timeout)

    destination = 'google.com'

    ping(sock, destination, ttl, 1, pings=5)
    """        

    