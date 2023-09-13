import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.manifest import Manifest  # noqa: E402


@pytest.fixture
def manifest():
    manifest_data = {}
    return Manifest(manifest_data, "", "empty-manifest")


def test_botname(manifest):
    assert manifest.botname() == "GPT"


def test_username(manifest):
    assert manifest.username() == "You(empty-manifest)"
