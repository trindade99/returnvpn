import socket
import fcntl
import os
import struct

UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
UTUN_OPT_IFNAME = 2
CTLIOCGINFO = 0xC0644E03  # ioctl code

class UTUNTun:
    def __init__(self):
        self.fd = socket.socket(32, socket.SOCK_DGRAM, 2)  # AF_SYSTEM=32, SOCK_DGRAM, SYSPROTO_CONTROL=2

        ctl_info = bytearray(struct.pack('96sI', UTUN_CONTROL_NAME, 0))
        fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        ctl_id = struct.unpack('96sI', ctl_info)[1]

        sc = struct.pack('BBHIHH', 2, 0, 0, ctl_id, 0, 0)
        self.fd.connect(sc)

        self.name = self.fd.getsockopt(socket.SYSPROTO_CONTROL, UTUN_OPT_IFNAME, 128).decode().strip('\x00')
        print(f"[+] macOS UTUN interface created: {self.name}")

    def read(self, size):
        return self.fd.recv(size)[4:]  # Skip 4 byte header

    def write(self, data):
        return self.fd.send(b"\x00\x00\x00\x02" + data)

    def fileno(self):
        return self.fd.fileno()

def create_tun(ifname="utun2"):
    return UTUNTun()

def cleanup_tun(ifname):
    os.system(f"ifconfig {ifname} down")