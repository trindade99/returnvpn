# RetunVPN

A lightweight VPN-over-Reticulum using Python.

## Features
- VPN using Reticulum's resilient mesh
- TUN interface for full tunnel or gateway
- Designed for LoRa and other low-bandwidth links

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# One-time setup (TUN + NAT)
sudo python3 cli.py configure --gateway

# Start the VPN link
sudo python3 cli.py start
```

## License

MIT