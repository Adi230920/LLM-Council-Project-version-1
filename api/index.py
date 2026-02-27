"""
BouleAI — Vercel Serverless Entrypoint
=======================================
Vercel's Python runtime requires the FastAPI application to be importable
from a file inside the `api/` directory. This module simply re-exports
the configured FastAPI `app` from the root `main.py`.

Vercel will discover this file, install requirements.txt, and serve the
ASGI app via its built-in Mangum adapter (no additional code needed).
"""

import sys
import os

# Ensure the project root is on the Python path so that `main`, `routers`,
# `services`, `models`, and `utils` packages can be imported without issue.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: F401  — Vercel picks up `app` from this module

__all__ = ["app"]
