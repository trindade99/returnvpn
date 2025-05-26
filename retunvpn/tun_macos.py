import socket
import struct
import fcntl

# Define macOS-specific constants (not exposed in Python's socket module by default)
AF_SYSTEM = getattr(socket, 'AF_SYSTEM', 32)          # macOS system sockets
SYSPROTO_CONTROL = getattr(socket, 'SYSPROTO_CONTROL', 2)  # Kernel control protocol
CTLIOCGINFO = 0xC0644E03  # From sys/ioccom.h: _IOWR('N', 3, struct ctl_info)

class UTUNTun:
    def __init__(self):
        self.fd = socket.socket(AF_SYSTEM, socket.SOCK_DGRAM, SYSPROTO_CONTROL)
        
        CTL_NAME = b'com.apple.net.utun_control'
        ctl_info = struct.pack('I96s', 0, CTL_NAME.ljust(96, b'\0'))
        
        try:
            ctl_info = fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        except FileNotFoundError as e:
            raise RuntimeError("utun kernel extension not available") from e
        
        self.ctl_id = struct.unpack('I', ctl_info[:4])[0]
        
        # Connect to the control
        self.fd.connect((self.ctl_id, 0))  # 0 = auto-assign unit number
        
        # Corrected: Fetch interface name with proper buffer size
        # Get 16 bytes (sufficient for interface name data)
        opt_data = self.fd.getsockopt(SYSPROTO_CONTROL, 2, 16)
        # Extract unit number from first 4 bytes (unsigned int)
        unit = struct.unpack('I', opt_data[:4])[0]
        self.ifname = f"utun{unit}"


    def fileno(self):
        return self.fd.fileno()

    def close(self):
        self.fd.close()

def create_tun(name_hint=None):
    return UTUNTun()

def cleanup_tun(tun):
    tun.close()