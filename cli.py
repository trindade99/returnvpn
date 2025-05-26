# cli.py
import argparse
from retunvpn import core

# cli.py
def main():
    parser = argparse.ArgumentParser(description="ReturnVPN - Reticulum-based VPN")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Remove the 'configure' subcommand
    start_parser = subparsers.add_parser('start', help='Start VPN tunnel')
    start_parser.add_argument('--mode', choices=['client', 'server'], required=True,
                            help='Operation mode: client or server')
    start_parser.add_argument('--peer', help='Path to peer identity file (for client mode)')

    args = parser.parse_args()
    
    if args.command == 'start':
        core.run_tunnel(mode=args.mode, peer_identity_path=args.peer)
        
if __name__ == "__main__":
    main()