# cli.py
import argparse
from retunvpn import core

def main():
    parser = argparse.ArgumentParser(description="ReturnVPN - Reticulum-based VPN")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Configure command
    config_parser = subparsers.add_parser('configure', help='Setup TUN interface')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start VPN tunnel')
    start_parser.add_argument('--mode', choices=['client', 'server'], required=True,
                            help='Operation mode: client or server')
    start_parser.add_argument('--peer', help='Path to peer identity file (for client mode)')

    args = parser.parse_args()
    
    if args.command == 'configure':
        core.configure_tun()
    elif args.command == 'start':
        core.run_tunnel(mode=args.mode, peer_identity_path=args.peer)

if __name__ == "__main__":
    main()