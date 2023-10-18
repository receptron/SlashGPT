#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from slashgpt import cli  # noqa: E402

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    cli(current_dir)
