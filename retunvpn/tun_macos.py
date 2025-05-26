# retunvpn/tun_macos.py
import socket
import struct
import fcntl
import os

# Constants
AF_SYSTEM = 32
AF_SYS_CONTROL = 2
SYSPROTO_CONTROL = 2
UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
CTLIOCGINFO = 0xC0644E03
UTUN_OPT_IFNAME = 2

class UTUNTun:
    def __init__(self):
        # Create system control socket
        self.fd = socket.socket(AF_SYSTEM, socket.SOCK_DGRAM, SYSPROTO_CONTROL)

        # Prepare ctl_info struct
        ctl_info = struct.pack("96s", UTUN_CONTROL_NAME.ljust(96, b'\x00'))
        try:
            ctl_info = fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        except FileNotFoundError:
            raise RuntimeError("Unable to find utun kernel extension. Make sure the utun interface is available.")

        ctl_id = struct.unpack("I", ctl_info[:4])[0]

        # Prepare sockaddr_ctl
        sc = struct.pack("BBHIHH", AF_SYSTEM, AF_SYS_CONTROL, 0, ctl_id, 0, 0)
        self.fd.connect(sc)

        # Fetch interface name
        ifname = self.fd.getsockopt(SYSPROTO_CONTROL, UTUN_OPT_IFNAME, 128)
        self.ifname = ifname.strip(b'\x00').decode()

    def fileno(self):
        return self.fd.fileno()

    def close(self):
        self.fd.close()

def create_tun(name_hint=None):
    return UTUNTun()

def cleanup_tun(tun):
    tun.close()