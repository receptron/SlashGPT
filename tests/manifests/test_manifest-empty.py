import sys

import pytest

from lib.manifest import Manifest


@pytest.fixture
def manifest():
    manifest_data = {}
    return Manifest(manifest_data, "empty-manifest")


def test_botname(manifest):
    assert manifest.botname() == "GPT"


def test_username(manifest):
    assert manifest.username() == "You(empty-manifest)"
