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
        except OSError as e:
            raise RuntimeError(f"Could not create TUN (max interfaces reached?)") from e
        
        self.ctl_id = struct.unpack('I', ctl_info[:4])[0]
        self.fd.connect((self.ctl_id, 0))
        
        # Get valid unit number (0-255)
        opt_data = self.fd.getsockopt(SYSPROTO_CONTROL, 2, 16)
        unit = struct.unpack('I', opt_data[:4])[0] & 0xFF
        self.ifname = f"utun{unit}"


    def fileno(self):
        return self.fd.fileno()

    def close(self):
        self.fd.close()

def create_tun():
    try:
        return UTUNTun()
    except Exception as e:
        raise RuntimeError(f"Failed to create TUN interface: {str(e)}")

def cleanup_tun(tun):
    tun.close()