# core.py
import RNS
import os
import struct
import time
import threading
import signal
import sys
import subprocess
from .tun_macos import create_tun

class TunnelCore:
    def __init__(self, mode, peer_identity_path=None):
        self.mode = mode
        self.peer_identity_path = peer_identity_path
        self.tun = None  # Will be created during startup
        
        # Initialize Reticulum first
        self.reticulum = RNS.Reticulum(configdir="./reticulum_config")
        
        # Then create and configure TUN
        self._create_and_configure_tun()
        
        # Create TUN interface
        self.tun = create_tun()
        self._configure_tun()
        
        # Load or create identity
        self.identity = self._load_identity()
        
        # Initialize Reticulum components
        self.destination = None
        self.link = None
        self.link_established_event = threading.Event()
        
        self.running = False

    def _create_and_configure_tun(self):
        try:
            # Create TUN interface
            self.tun = create_tun()
            print(f"[+] Created TUN interface {self.tun.ifname}")
            
            # Wait for interface registration
            for _ in range(5):  # Retry for up to 5 seconds
                if self._interface_exists():
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Interface never appeared in system")
            
            # Configure interface
            subprocess.check_call([
                "sudo", "ifconfig", self.tun.ifname,
                "up",  # Bring interface up first
                "mtu", "1500"
            ])
            
            # Set IP addresses
            subprocess.check_call([
                "sudo", "ifconfig", self.tun.ifname,
                "inet", "10.7.0.1/24"  # CIDR notation for macOS
            ])
            
            print(f"[+] Configured {self.tun.ifname} with IP 10.7.0.1")

        except Exception as e:
            if self.tun:
                self.tun.fd.close()
            raise RuntimeError(f"TUN setup failed: {str(e)}")

    def _interface_exists(self):
        try:
            subprocess.check_call(["ifconfig", self.tun.ifname], 
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def _load_identity(self):
        identity_dir = "./reticulum_config/identities"
        os.makedirs(identity_dir, exist_ok=True)
        
        identity_file = f"{identity_dir}/{self.mode}_identity"
        if os.path.exists(identity_file):
            return RNS.Identity.from_file(identity_file)
        else:
            identity = RNS.Identity()
            identity.to_file(identity_file)
            return identity

    def _configure_tun(self):
        if self.mode == "server":
            self.tun_ip = "10.7.0.1"
            peer_ip = "10.7.0.2"
        else:
            self.tun_ip = "10.7.0.2"
            peer_ip = "10.7.0.1"

        try:
            # macOS requires this specific ifconfig format
            subprocess.check_call([
                "sudo", "ifconfig", self.tun.ifname,
                "inet", self.tun_ip, peer_ip,
                "netmask", "255.255.255.0",
                "mtu", "1500"
            ])
            
            subprocess.check_call([
                "sudo", "route", "-n", "add", "-net", "10.7.0.0/24",
                "-interface", self.tun.ifname
            ])
            
            print(f"[+] TUN interface {self.tun.ifname} configured")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Configuration failed (are you using VPN software?)")

    def _setup_server(self):
        # Server listens for incoming connections
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            "returnvpn",
            "tunnel",
            proof_strategy=RNS.Destination.PROVE_ALL
        )
        
        # Announce our presence
        self.destination.announce()
        print("[+] Server listening for connections...")

    def _setup_client(self):
        # Client connects to server
        if not self.peer_identity_path:
            raise ValueError("Client mode requires --peer argument with server identity")
            
        server_identity = RNS.Identity.from_file(self.peer_identity_path)
        
        self.destination = RNS.Destination(
            server_identity,
            RNS.Destination.OUT,
            RNS.Destination.SINGLE,
            "returnvpn",
            "tunnel"
        )
        
        print(f"[+] Connecting to server {RNS.prettyhexrep(server_identity.hash)}...")
        self.link = RNS.Link(self.destination)
        self.link.set_link_established_callback(self._link_established)

    def _link_established(self, link):
        print(f"\n[+] Link established with {RNS.prettyhexrep(link.destination.hash)}")
        self.link_established_event.set()

    def _tun_to_reticulum(self):
        while self.running:
            try:
                packet = self.tun.fd.recv(2048)
                if packet and self.link and self.link.established:
                    self.link.send(packet)
            except Exception as e:
                if self.running:
                    print(f"Error reading from TUN: {e}")
                break

    def _reticulum_to_tun(self):
        while self.running:
            try:
                if self.link and self.link.established:
                    data = self.link.receive()
                    if data:
                        self.tun.fd.send(data)
                else:
                    time.sleep(0.1)
            except Exception as e:
                if self.running:
                    print(f"Error reading from Reticulum: {e}")
                break

    def start(self):
        self.running = True
        
        if self.mode == "server":
            self._setup_server()
        else:
            self._setup_client()
            if not self.link_established_event.wait(30):
                raise RuntimeError("Connection to server timed out")

        # Start forwarding threads
        tun_thread = threading.Thread(target=self._tun_to_reticulum)
        ret_thread = threading.Thread(target=self._reticulum_to_tun)
        
        tun_thread.daemon = True
        ret_thread.daemon = True
        
        tun_thread.start()
        ret_thread.start()

        print("[+] Tunnel active. Press Ctrl+C to stop.")
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
        while self.running:
            time.sleep(1)

    def stop(self, signum=None, frame=None):
        self.running = False
        if self.tun:
            print(f"[+] Closing TUN interface {self.tun.ifname}")
            self.tun.fd.close()
        if self.link:
            self.link.teardown()
        self.tun.fd.close()
        print("\n[+] Tunnel stopped")
        
def configure_tun():
    tun = create_tun()
    print(f"[+] TUN interface {tun.ifname} created")

def run_tunnel(mode, peer_identity_path=None):
    tunnel = TunnelCore(mode=mode, peer_identity_path=peer_identity_path)
    tunnel.start()