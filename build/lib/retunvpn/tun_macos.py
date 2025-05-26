import socket
import fcntl
import struct
import os

UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
UTUN_OPT_IFNAME = 2
CTLIOCGINFO = 0xC0644E03  # ioctl code for CTLIOCGINFO

class UTUNTun:
    def __init__(self):
        # Create a system control socket
        self.fd = socket.socket(socket.AF_SYSTEM, socket.SOCK_DGRAM, socket.SYSPROTO_CONTROL)

        # Prepare the ctl_info structure with a mutable buffer
        ctl_info = bytearray(struct.pack('96sI', UTUN_CONTROL_NAME, 0))

        # Perform ioctl to get the control ID
        fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        _, ctl_id = struct.unpack('96sI', ctl_info)

        # Prepare the sockaddr_ctl structure
        sc = struct.pack('BBHIHH', socket.AF_SYSTEM, socket.SOCK_DGRAM, 0, ctl_id, 0, 0)

        # Connect the socket to the control ID
        self.fd.connect(sc)

        # Retrieve the interface name
        ifname = self.fd.getsockopt(socket.SYSPROTO_CONTROL, UTUN_OPT_IFNAME, 128)
        self.name = ifname.decode('utf-8').strip('\x00')
        print(f"[+] macOS UTUN interface created: {self.name}")

    def read(self, size):
        return self.fd.recv(size)[4:]  # Skip the 4-byte header

    def write(self, data):
        return self.fd.send(b'\x00\x00\x00\x02' + data)

    def fileno(self):
        return self.fd.fileno()