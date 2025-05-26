# --- setup.py ---
from setuptools import setup, find_packages

setup(
    name="retunvpn",
    version="0.1",
    packages=find_packages(),
    install_requires=[
    "rns",
    'python-pytun; sys_platform == "linux"',
],
    entry_points={
        'console_scripts': [
            'retunctl=cli:main',
        ],
    },
)