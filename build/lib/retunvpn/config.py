import platform
import subprocess
import os

if platform.system() == "Darwin":
    from .tun_macos import create_tun, cleanup_tun
else:
    from .tun_linux import create_tun, cleanup_tun

def setup_tun(gateway=False):
    system = platform.system()
    print(f"[+] Setting up TUN interface on {system}...")

    if system == "Darwin":
        tun = create_tun()  # macOS will assign utunX automatically
        print(f"[+] TUN interface created: {tun.ifname}")
        # macOS: no need to run iptables or ip commands
        # If you want to add routing or firewall rules, add here as needed

    else:
        # Linux path (unchanged)
        subprocess.run(["ip", "tuntap", "add", "dev", "retun0", "mode", "tun"], check=True)
        subprocess.run(["ip", "addr", "add", "10.10.0.1/24", "dev", "retun0"], check=True)
        subprocess.run(["ip", "link", "set", "retun0", "up"], check=True)
        if gateway:
            print("[+] Enabling IP forwarding and NAT...")
            subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
            subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"], check=True)