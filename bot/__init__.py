"""
Zyuna Bot Package Initialization
Ensures core, utils, and cogs subpackages are discoverable and importable
regardless of whether the application is executed from root or the bot directory.
"""
import os
import sys

_bot_dir = os.path.dirname(os.path.abspath(__file__))
if _bot_dir not in sys.path:
    sys.path.insert(0, _bot_dir)
