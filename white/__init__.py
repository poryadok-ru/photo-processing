"""
White Background Processing Package
"""

from .main import main, WhiteBackgroundProcessor
from .config import Config
from .pixian_client import PixianClient

__version__ = "1.0.0"
__all__ = ['main', 'WhiteBackgroundProcessor', 'Config', 'PixianClient']