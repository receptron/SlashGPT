#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from slashgpt.cli import cli



if __name__ == "__main__":
    cli()
