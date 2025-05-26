import socket
import struct
import fcntl
import time

AF_SYSTEM = getattr(socket, 'AF_SYSTEM', 32)
SYSPROTO_CONTROL = getattr(socket, 'SYSPROTO_CONTROL', 2)
CTLIOCGINFO = 0xC0644E03

class UTUNTun:
    def __init__(self):
        self.fd = socket.socket(AF_SYSTEM, socket.SOCK_DGRAM, SYSPROTO_CONTROL)
        
        # Request control ID
        ctl_info = struct.pack('I96s', 0, b'com.apple.net.utun_control'.ljust(96, b'\0'))
        ctl_info = fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        self.ctl_id = struct.unpack('I', ctl_info[:4])[0]
        
        # Connect to control
        self.fd.connect((self.ctl_id, 0))
        
        # Get valid interface unit number
        opt_data = self.fd.getsockopt(SYSPROTO_CONTROL, 2, 16)
        unit = struct.unpack('I', opt_data[:4])[0] & 0xFF
        self.ifname = f"utun{unit}"
        
        # Keep socket alive
        self.fd.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

def create_tun():
    try:
        return UTUNTun()
    except Exception as e:
        raise RuntimeError(f"TUN creation failed: {str(e)}")