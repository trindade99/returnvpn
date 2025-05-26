# --- retunvpn/tunutils.py ---
import pytun
import os

def create_tun(ifname):
    tun = pytun.TunTapDevice(name=ifname, flags=pytun.IFF_TUN | pytun.IFF_NO_PI)
    tun.addr = "10.10.0.1"
    tun.netmask = "255.255.255.0"
    tun.mtu = 1500
    tun.up()
    return tun

def cleanup_tun(ifname):
    os.system(f"ip link set {ifname} down")
    os.system(f"ip tuntap del dev {ifname} mode tun")