from importlib.metadata import version
from pathlib import Path

VERSION = version("fico")
ASSETS = Path(__file__).parent / "assets"
