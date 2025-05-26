# retunvpn/tun_macos.py

import socket
import fcntl
import os
import struct

# Constants specific to macOS
UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
UTUN_OPT_IFNAME = 2
CTLIOCGINFO = 0xC0644E03  # ioctl request code to get control ID

class UTUNTun:
    def __init__(self):
        self.fd = socket.socket(socket.AF_SYSTEM, socket.SOCK_DGRAM, 2)

        # Prepare the control info structure
        ctl_info = struct.pack('96sI', UTUN_CONTROL_NAME, 0)
        try:
            ctl_info = fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
        except FileNotFoundError:
            raise RuntimeError("Unable to find utun kernel extension. Make sure the utun interface is available.")

        ctl_id = struct.unpack('96sI', ctl_info)[1]

        # Build sockaddr_ctl structure
        # see: https://opensource.apple.com/source/xnu/xnu-7195.101.1/bsd/sys/kern_control.h.auto.html
        sockaddr_ctl = struct.pack('BBHIHH',
                                   socket.AF_SYSTEM,    # sc_len, sc_family
                                   socket.AF_SYS_CONTROL,
                                   0,                   # sc_sysaddr (set to 0)
                                   ctl_id,              # sc_id
                                   0,                   # sc_unit (0 means assign next available utun)
                                   0)                   # padding

        self.fd.connect(sockaddr_ctl)

        # Get the interface name assigned (e.g., "utun3")
        self.name = self.fd.getsockopt(socket.SYSPROTO_CONTROL, UTUN_OPT_IFNAME, 128).decode().strip('\x00')
        print(f"[+] macOS UTUN interface created: {self.name}")

    def read(self, size):
        return self.fd.recv(size)[4:]  # Skip the 4-byte header

    def write(self, data):
        return self.fd.send(b"\x00\x00\x00\x02" + data)

    def fileno(self):
        return self.fd.fileno()

def create_tun(ifname="utun"):
    return UTUNTun()

def cleanup_tun(ifname):
    os.system(f"ifconfig {ifname} down")  # Optional on macOS