"""Pytest root configuration and path setup."""

import os
import sys

# Ensure repository root directory is at index 0 of sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
