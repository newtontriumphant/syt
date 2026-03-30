#!/usr/bin/env python3

import sys
import os
import re
import json
import shutil
import signal
import subprocess
import argparse
import platform
from pathlib import Path

# ascii art generator my goat :3

LOGO = r"""
  ███████╗██╗   ██╗████████╗
  ██╔════╝╚██╗ ██╔╝╚══██╔══╝
  ███████╗ ╚████╔╝    ██║   
  ╚════██║  ╚██╔╝     ██║   
  ███████║   ██║      ██║   
  ╚══════╝   ╚═╝      ╚═╝   
     simple youtube downloader
"""

SUPPORTS_COLOR = (
    hasattr(sys.stdout, "isatty")
    and sys.stdout.isatty()
    and os.environ.get("NO_COLOR") is None
)

def _c(code, text):
    if SUPPORTS_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text

def bold(t): return _c("1", t)
def dim(t): return _c("2", t)
def bold(t): return _c("1", t)
def bold(t): return _c("1", t)
def bold(t): return _c("1", t)
def bold(t): return _c("1", t)
def bold(t): return _c("1", t)