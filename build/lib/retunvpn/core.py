# --- retunvpn/core.py ---
import time
import threading
from retunvpn import tunutils, rnsutils

def run_tunnel(gateway=False):
    print("[+] Starting Reticulum tunnel...")
    tun = tunutils.create_tun("retun0")
    destination, link = rnsutils.create_link()

    def read_loop():
        while True:
            data = tun.read(2048)
            if data:
                link.send(data)

    def write_loop():
        while True:
            if link.has_inbound():
                data = link.read()
                tun.write(data)

    threading.Thread(target=read_loop, daemon=True).start()
    threading.Thread(target=write_loop, daemon=True).start()

    print("[+] Tunnel is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[!] Shutting down tunnel.")
        tunutils.cleanup_tun("retun0")
