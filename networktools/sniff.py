from datetime import datetime
import socket
import struct

ETH_P_ALL = 3

class EthFrame:

    def __init__(self, raw_packet):
        self.dst = '.'.join(str(i) for i in raw_packet[:6])
        self.src = '.'.join(str(i) for i in raw_packet[6:14])

class IP4Packet:

    # ip protocols that will be loaded on first instance creation
    PROTOS = None

    def __init__(self, eth_frame, raw_packet):

        if not IP4Packet.PROTOS:
            IP4Packet.open_protos()

        self.eth_frame = eth_frame
        self._parse_headers(raw_packet)
        self._parse_ips(raw_packet)

    def _parse_ips(self, raw_packet):
        self.src_ip = '.'.join(str(i) for i in raw_packet[26:30])
        self.dst_ip = '.'.join(str(i) for i in raw_packet[30:34])

    def _parse_headers(self, packet):
        # | Version | Header len |  ToS  |    Total len   |
        vers_head_len, self.service_type, self.total_len, = struct.unpack('>BBH', packet[14:18])
        self.version = vers_head_len >> 4
        self.header_len = vers_head_len & 0x0f
        # |  Identification    |     Flags   |   Offset   |
        self.iden, flag_offset = struct.unpack('>HH', packet[18:22])
        self.flags = flag_offset >> 14
        self.offset = flag_offset & 0x3fff
        # |   TTL    |   Protocol |     Header checksum   |
        self.ttl, self.proto, self.chksum = struct.unpack('>BBH', packet[22:26])
        # |              Source address                   |
        # |              Destination address              |
        #self.src_ip, self.dst_ip, = struct.unpack('>LL', packet[26:34])


    @classmethod
    def open_protos(cls):
        import json
        try:
            with open('protos') as f:
                IP4Packet.PROTOS = json.load(f)
        except Exception as e:
            print(f'Failed to load IP protocols\n{e}')


    def __repr__(self):
        date = datetime.strftime(datetime.now(), '%y-%m-%d')
        time = datetime.strftime(datetime.now(), '%H:%M:%S')
        string =  '-----------------------------------------------\n'
        string += f' {date}\t NEW PACKET \t{time} \n'
        string += '-----------------------------------------------\n'
        string += f'Mac Destination:\t {self.eth_frame.dst}\n'
        string += f'Mac Source:\t\t {self.eth_frame.src}\n'
        string += f'Type of Service:\t {self.service_type} \n'
        string += f'Header len:\t\t {self.header_len}\n'
        string += f'Total len:\t\t {self.total_len}\n'
        string += f'Identification:\t\t {hex(self.iden)} ({self.iden})\n'
        string += f'Fragment offset:\t {self.offset} \n'
        string += f'TTL:\t\t\t {self.ttl} \n'
        string += f'Protocol:\t\t ({IP4Packet.PROTOS[str(self.proto)]}) {self.proto}\n'
        string += f'Header checksum:\t {self.chksum}\n'
        string += f'Source IP Address:\t {self.src_ip}\n'
        string += f'Destination IP Address:\t {self.dst_ip}\n'
        string += '-----------------------------------------------\n'
        return string


sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
sock.bind(('lo', 0))

while True:

    raw_packet = sock.recv(2048)
    eth_frame = EthFrame(raw_packet)
    packet = IP4Packet(eth_frame, raw_packet)        
    print(packet)