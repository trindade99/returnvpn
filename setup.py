# --- setup.py ---
from setuptools import setup, find_packages

setup(
    name="retunvpn",
    version="0.1",
    packages=find_packages(),
    install_requires=["reticulum", "pytun"],
    entry_points={
        'console_scripts': [
            'retunctl=cli:main',
        ],
    },
)