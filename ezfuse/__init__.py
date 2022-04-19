"""
project metadata
"""

import importlib.metadata as importlib_metadata

__version__ = importlib_metadata.version(__name__)
__title__ = "ezfuse"
__description__ = "Quickly mount fuse filesystems in temporary directories"
