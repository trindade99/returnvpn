# --- retunvpn/config.py ---
import os
import subprocess

def setup_tun(gateway=False):
    print("[+] Setting up TUN interface...")
    subprocess.run(["ip", "tuntap", "add", "dev", "retun0", "mode", "tun"], check=True)
    subprocess.run(["ip", "addr", "add", "10.10.0.1/24", "dev", "retun0"], check=True)
    subprocess.run(["ip", "link", "set", "retun0", "up"], check=True)
    
    if gateway:
        print("[+] Enabling IP forwarding and NAT...")
        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"], check=True)
