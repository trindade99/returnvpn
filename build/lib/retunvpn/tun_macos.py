import socket
import fcntl
import os
import struct
import select

UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
UTUN_OPT_IFNAME = 2

class UTUNTun:
    def __init__(self):
        self.fd = socket.socket(socket.AF_SYSTEM, socket.SOCK_DGRAM, 2)

        ctl_info = struct.pack('96sI', UTUN_CONTROL_NAME, 0)
        ctl_id = fcntl.ioctl(self.fd.fileno(), 3227799043, ctl_info)  # CTLIOCGINFO
        ctl_id = struct.unpack('96sI', ctl_id)[1]

        # Set up sockaddr_ctl
        sc = struct.pack('BBHIHH', 2, 0, 0, ctl_id, 0, 0)  # AF_SYSTEM, SOCK_DGRAM
        self.fd.connect(sc)

        # Get interface name
        self.name = self.fd.getsockopt(socket.SYSPROTO_CONTROL, UTUN_OPT_IFNAME, 128).decode().strip('\x00')
        print(f"[+] macOS UTUN interface created: {self.name}")

    def read(self, size):
        return self.fd.recv(size)[4:]  # Skip the 4-byte header

    def write(self, data):
        return self.fd.send(b"\x00\x00\x00\x02" + data)

    def fileno(self):
        return self.fd.fileno()

def create_tun(ifname="utun2"):
    return UTUNTun()

def cleanup_tun(ifname):
    os.system(f"ifconfig {ifname} down")  # optional on macOS
