import RNS
import struct
import time
import threading
import signal
import sys
from .tun_macos import create_tun

class TunnelCore:
    def __init__(self, gateway=None):
        # Initialize Reticulum
        self.reticulum = RNS.Reticulum(configdir="./reticulum_config")
        
        # Create TUN interface
        self.tun = create_tun()
        self.tun_ip = "10.7.0.2"
        self.peer_ip = "10.7.0.1"
        
        # Setup interface and routes
        self._configure_tun()
        
        # Reticulum components
        self.identity = RNS.Identity()
        self.destination = None
        self.link = None
        
        # Thread control
        self.running = False

    def _configure_tun(self):
        # Configure TUN interface IP addresses
        import subprocess
        subprocess.call(["sudo", "ifconfig", self.tun.ifname, self.tun_ip, self.peer_ip, "up"])
        subprocess.call(["sudo", "route", "-n", "add", "-net", "10.7.0.0/24", "-interface", self.tun.ifname])
        
        print(f"[+] TUN interface {self.tun.ifname} configured with {self.tun_ip}")

    def _setup_reticulum(self):
        # Create Reticulum destination
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "returnvpn",
            "tunnel"
        )
        
        # Wait for link establishment
        self.link = RNS.Link(self.destination)
        while not self.link.established:
            time.sleep(0.1)
            print("Waiting for link establishment...")
        
        print(f"[+] Reticulum link established with {self.destination}")

    def _tun_to_reticulum(self):
        while self.running:
            try:
                packet = self.tun.fd.recv(2048)
                if packet:
                    # Encapsulate and send via Reticulum
                    self.link.send(packet)
            except Exception as e:
                if self.running:
                    print(f"Error reading from TUN: {e}")
                break

    def _reticulum_to_tun(self):
        while self.running:
            try:
                data = self.link.receive()
                if data:
                    # Decapsulate and write to TUN
                    self.tun.fd.send(data)
            except Exception as e:
                if self.running:
                    print(f"Error reading from Reticulum: {e}")
                break

    def start(self):
        self.running = True
        self._setup_reticulum()
        
        # Start packet forwarding threads
        tun_thread = threading.Thread(target=self._tun_to_reticulum)
        ret_thread = threading.Thread(target=self._reticulum_to_tun)
        
        tun_thread.daemon = True
        ret_thread.daemon = True
        
        tun_thread.start()
        ret_thread.start()
        
        print("[+] Tunnel started. Press Ctrl+C to stop.")
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
        while self.running:
            time.sleep(1)

    def stop(self, signum=None, frame=None):
        self.running = False
        self.link.teardown()
        self.tun.fd.close()
        print("\n[+] Tunnel stopped")

def run_tunnel(gateway=None):
    tunnel = TunnelCore(gateway=gateway)
    tunnel.start()