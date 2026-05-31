"""Direct run this file to launch PA Agent.

Usage:
    python run.py

Or double-click run.py (if Python is associated).
"""
import sys
import os

# Ensure PA_Agent directory is in sys.path (works when run from any directory)
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

# Set UTF-8 output encoding for Windows console (avoids GBK errors on Unicode chars)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pa_agent.main import main

if __name__ == "__main__":
    raise SystemExit(main())
