import RNS

def create_link():
    # Initialize Reticulum with your config
    reticulum = RNS.Reticulum(configdir="./reticulum_config")
    
    # Create destination (make sure your identity is properly set up)
    identity = RNS.Identity()
    destination = RNS.Destination(
        identity,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        "returnvpn",
        "tunnel"
    )
    
    # Now create the link
    link = RNS.Link(destination)
    return destination, link