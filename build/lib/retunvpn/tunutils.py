import sys

if sys.platform.startswith("linux"):
    from .tun_linux import create_tun, cleanup_tun
elif sys.platform == "darwin":
    from .tun_macos import create_tun, cleanup_tun
else:
    raise NotImplementedError("Unsupported platform")