import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

def test_foo():
    assert 0