"""
Zyuna Bot Package Initialization
Ensures the core, utils, and cogs packages are discoverable from the repository root.
"""
import os
import sys

_project_dir = os.path.dirname(os.path.abspath(__file__))
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)
