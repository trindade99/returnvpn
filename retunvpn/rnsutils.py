# --- retunvpn/rnsutils.py ---
import RNS

identity = RNS.Identity()

def create_link():
    destination = RNS.Destination(identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "vpn")
    link = RNS.Link(destination, None)
    return destination, link
