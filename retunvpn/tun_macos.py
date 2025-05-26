# tun_macos.py
import socket
import struct
import fcntl
import os
import stat

# macOS-specific constants
AF_SYSTEM = getattr(socket, 'AF_SYSTEM', 32)
SYSPROTO_CONTROL = getattr(socket, 'SYSPROTO_CONTROL', 2)
CTLIOCGINFO = 0xC0644E03  # From sys/ioccom.h

class UTUNTun:
    def __init__(self):
        self.fd = socket.socket(AF_SYSTEM, socket.SOCK_DGRAM, SYSPROTO_CONTROL)
        
        # Get control ID for utun
        ctl_info = struct.pack('I96s', 0, b'com.apple.net.utun_control'.ljust(96, b'\0'))
        ctl_info = fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        self.ctl_id = struct.unpack('I', ctl_info[:4])[0]
        
        # Connect to the control
        self.fd.connect((self.ctl_id, 0))
        
        # Get interface unit number (corrected buffer size)
        opt_data = self.fd.getsockopt(SYSPROTO_CONTROL, 2, 16)  # Request 16 bytes
        unit = struct.unpack('I', opt_data[:4])[0] & 0xFF  # Get first 4 bytes and mask
        
        self.ifname = f"utun{unit}"
        
        # Create device node if needed (macOS specific)
        dev_path = f"/dev/{self.ifname}"
        if not os.path.exists(dev_path):
            try:
                os.mknod(dev_path, 0o666 | stat.S_IFCHR, 
                        os.makedev(22, unit + 1))  # 22 = utun device major number
            except PermissionError:
                raise RuntimeError("Need sudo to create device node")

def create_tun():
    try:
        return UTUNTun()
    except Exception as e:
        raise RuntimeError(f"TUN creation failed: {str(e)}")