# --- cli.py ---
import argparse
from retunvpn import config, core

def main():
    parser = argparse.ArgumentParser(description="Reticulum VPN CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Configure command
    configure_parser = subparsers.add_parser('configure', help='Set up the TUN interface and routing')
    configure_parser.add_argument('--gateway', action='store_true', help='Enable IP forwarding and NAT')

    # Start command
    start_parser = subparsers.add_parser('start', help='Run the VPN tunnel')
    start_parser.add_argument('--gateway', action='store_true', help='Run as a gateway node')

    args = parser.parse_args()

    if args.command == 'configure':
        config.setup_tun(gateway=args.gateway)
    elif args.command == 'start':
        core.run_tunnel(gateway=args.gateway)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

