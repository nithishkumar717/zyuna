"""
Legacy entry point for backward compatibility with hosts configured to run CodeX.py.
Redirects execution to zyuna.py.
"""
import runpy
from pathlib import Path

if __name__ == "__main__":
    zyuna_path = Path(__file__).parent / "zyuna.py"
    runpy.run_path(str(zyuna_path), run_name="__main__")
