import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.manifest import Manifest

manifest_data = {}
manifest = Manifest(manifest_data, "empty-manifest")
    
def test_botname():
    assert manifest.botname() == "GPT"

def test_username():
    assert manifest.username() == "You(empty-manifest)"

