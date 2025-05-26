# --- retunvpn/config.py ---
import os
import sys
import subprocess
import platform

if platform.system() == "Darwin":
    import socket
    import fcntl
    import struct

    UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
    UTUN_OPT_IFNAME = 2
    CTLIOCGINFO = 3227799043  # ioctl code for CTLIOCGINFO

    class UTUNTun:
        def __init__(self):
            self.fd = socket.socket(32, socket.SOCK_DGRAM, 2)

            ctl_info = struct.pack('96sI', UTUN_CONTROL_NAME, 0)
            ctl_id = fcntl.ioctl(self.fd.fileno(), CTLIOCGINFO, ctl_info)
            ctl_id = struct.unpack('96sI', ctl_id)[1]

            sockaddr_ctl = struct.pack('BBHIHH', 2, 0, 0, ctl_id, 0, 0)
            self.fd.connect(sockaddr_ctl)

            self.name = self.fd.getsockopt(socket.SYSPROTO_CONTROL, UTUN_OPT_IFNAME, 128).decode().strip('\x00')
            print(f"[+] macOS UTUN interface created: {self.name}")

        def read(self, size=1500):
            return self.fd.recv(size)[4:]  # skip 4 byte header

        def write(self, data):
            return self.fd.send(b'\x00\x00\x00\x02' + data)

        def fileno(self):
            return self.fd.fileno()

    def setup_tun(gateway=False):
        print("[+] Setting up TUN interface on macOS...")
        tun = UTUNTun()

        # Assign IP and bring interface up
        ip = "10.10.0.1"
        mask = "255.255.255.0"
        os.system(f"ifconfig {tun.name} {ip} netmask {mask} up")

        if gateway:
            print("[+] Enabling IP forwarding on macOS...")
            os.system("sysctl -w net.inet.ip.forwarding=1")

        return tun

    def cleanup_tun(ifname):
        os.system(f"ifconfig {ifname} down")

else:
    def setup_tun(gateway=False):
        print("[+] Setting up TUN interface on Linux...")
        subprocess.run(["ip", "tuntap", "add", "dev", "retun0", "mode", "tun"], check=True)
        subprocess.run(["ip", "addr", "add", "10.10.0.1/24", "dev", "retun0"], check=True)
        subprocess.run(["ip", "link", "set", "retun0", "up"], check=True)

        if gateway:
            print("[+] Enabling IP forwarding and NAT on Linux...")
            subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
            subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"], check=True)

        return "retun0"

    def cleanup_tun(ifname):
        os.system(f"ip link set {ifname} down")
        os.system(f"ip tuntap del dev {ifname} mode tun")